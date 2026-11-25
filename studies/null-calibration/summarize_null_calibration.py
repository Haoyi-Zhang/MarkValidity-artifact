"""Build results/null-calibration/summary.json from the raw files (uses scipy for Clopper-Pearson).

Usage (artifact root):
    python -B studies/null-calibration/summarize_null_calibration.py --results results/null-calibration
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
import statistics
from fractions import Fraction
from math import comb
from pathlib import Path

from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[2]
NOMINAL_SEW = 0.01
NOMINAL_CREST = 0.01
PAPER_KEYS = 3
P_THRESHOLDS = [0.001, 0.01, 0.05, 0.1, 0.5]
CORPORA = ("humaneval", "mbpp", "references", "projects")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def cp(x, n, conf=0.95):
    a = (1 - conf) / 2
    lo = 0.0 if x == 0 else float(beta.ppf(a, x, n - x + 1))
    hi = 1.0 if x == n else float(beta.ppf(1 - a, x + 1, n - x))
    return [lo, hi]


def rate(x, n):
    return {"positives": x, "n": n, "rate": (x / n if n else None), "cp95": (cp(x, n) if n else None)}


def q999(n=1003, p=Fraction(1, 100), level=Fraction(999, 1000)):
    cdf = Fraction(0)
    for q in range(n + 1):
        cdf += comb(n, q) * p ** q * (1 - p) ** (n - q)
        if cdf >= level:
            return q


def load_sew(results):
    units = []
    for c in ("humaneval", "mbpp", "projects"):
        with gzip.open(results / ("sew-null-%s.jsonl.gz" % c), "rt", encoding="utf-8") as f:
            units += [json.loads(line) for line in f]
    return units


def code_of(u, k):
    if u["status"] != "available":
        return "U"
    return u["results"][k][0]


def sew_corpus(units, nkeys, q):
    out = {"sources": len(units), "available_sources": sum(u["status"] == "available" for u in units),
           "unavailable_sources": [{"source_id": u["source_id"], "reason": u.get("unavailable_reason")} for u in units if u["status"] != "available"]}
    per_key = []
    for k in range(PAPER_KEYS):
        codes = [code_of(u, k) for u in units]
        avail = [c for c in codes if c != "U"]
        per_key.append({"key_index": k, "verdicts": dict(sorted(collections.Counter(codes).items())),
                        "all_sources": rate(codes.count("D"), len(codes)),
                        "available_sources": rate(avail.count("D"), len(avail))})
        per_key[-1]["exceeds_nominal"] = per_key[-1]["all_sources"]["cp95"][0] > NOMINAL_SEW
    out["S1_paper_keys"] = per_key
    any3 = sum(any(code_of(u, k) == "D" for k in range(PAPER_KEYS)) for u in units)
    out["S2_any_paper_key"] = {**rate(any3, len(units)), "nominal_union_bound": PAPER_KEYS * NOMINAL_SEW,
                               "nominal_independent": 1 - (1 - NOMINAL_SEW) ** PAPER_KEYS}
    counts_per_key = [sum(code_of(u, k) == "D" for u in units) for k in range(nkeys)]
    per_source = [sum(code_of(u, k) == "D" for k in range(nkeys)) for u in units]
    pairs = len(units) * nkeys
    codes_all = collections.Counter(code_of(u, k) for u in units for k in range(nkeys))
    keys_lo = sum(cp(x, len(units))[0] > NOMINAL_SEW for x in counts_per_key)
    out["S3_all_keys"] = {"keys": nkeys, "pairs": pairs, "pooled_positives": sum(counts_per_key),
                          "pooled_rate": sum(counts_per_key) / pairs,
                          "per_key_positive_count": {"min": min(counts_per_key), "median": statistics.median(counts_per_key), "max": max(counts_per_key)},
                          "keys_with_cp95_lower_above_nominal": keys_lo,
                          "per_source_positive_key_count_histogram": {str(a): b for a, b in sorted(collections.Counter(per_source).items())},
                          "sources_any_positive_key": sum(x > 0 for x in per_source),
                          "q999_binomial_1003_0.01": q,
                          "sources_exceeding_q999": sum(x > q for x in per_source),
                          "nominal_expected_positive_keys_per_source": nkeys * NOMINAL_SEW}
    pvals = [u["results"][k][1] for u in units if u["status"] == "available" for k in range(nkeys) if u["results"][k][0] != "U"]
    out["S4_p_value_profile"] = {"available_pairs": len(pvals), "verdicts_all_pairs": dict(sorted(codes_all.items())),
                                 "fraction_p_at_most": {str(t): sum(p <= t for p in pvals) / len(pvals) for t in P_THRESHOLDS},
                                 "count_p_at_most": {str(t): sum(p <= t for p in pvals) for t in P_THRESHOLDS},
                                 "min_p": min(pvals)}
    return out


def reconstruct(u, k):
    row = u["results"][k]
    names = {"D": "Watermark detected", "N": "No watermark evidence", "I": "Insufficient evidence"}
    if row[0] == "U":
        return None
    st = dict(u["structure"])
    if len(row) > 6:
        st = row[6]
    if st["parse_abstention"]:
        return {"verdict": names[row[0]], "reason": "parse", "p": row[1], "n_grades": st["n_grades"]}
    return {"verdict": names[row[0]], "p": row[1], "p_all": row[2], "p_syntax": row[3], "n_grades": st["n_grades"],
            "k_grades": row[4], "n_syntax": st["n_syntax"], "k_syntax": row[5], "n_sites": st["n_sites"]}


def retained_agreement(units, keys):
    he = json.loads((ROOT / "results/sew/humaneval/rows.json").read_text())
    mb = json.loads((ROOT / "results/sew/mbpp/factors/stock/rows.json").read_text())
    ret = {}
    for r in he:
        if r["variant"] == "stock":
            ret[(r["task_id"], r["key_id"])] = r["reference_detector"]
    for r in mb:
        ret[("MBPP/%d" % r["task_id"], r["key_id"])] = r.get("reference_detector")
    out = {}
    for corpus in ("humaneval", "mbpp"):
        cmp_, eq, diffs = 0, 0, []
        for u in units:
            if u["corpus"] != corpus:
                continue
            for k in range(PAPER_KEYS):
                cmp_ += 1
                fresh = reconstruct(u, k) if u["status"] == "available" else None
                if fresh is not None and fresh == ret.get((u["source_id"], keys[k]["key_id"])):
                    eq += 1
                else:
                    diffs.append([u["source_id"], keys[k]["key_id"]])
        out[corpus] = {"compared": cmp_, "equal": eq, "unequal": diffs}
    return out


def crest_summary(binding):
    out = {}
    for study, s in binding["studies"].items():
        rows = s["rows"]
        heads = {}
        for h in binding["heads"]:
            det = [r["heads"][h]["detected"] if (r["reference_detector_status"] == "completed" and r["heads"][h]) else None for r in rows]
            comp = [d for d in det if d is not None]
            qual = [d for r, d in zip(rows, det) if r["qualified_reference"] is True]
            heads[h] = {"thresholds": sorted({r["heads"][h]["threshold"] for r in rows if r["heads"][h]}),
                        "all_rows": rate(sum(d is True for d in det), len(det)),
                        "completed_rows": rate(sum(d is True for d in comp), len(comp)),
                        "qualified_reference_rows": rate(sum(d is True for d in qual), len(qual)),
                        "unavailable_rows": sum(d is None for d in det)}
            heads[h]["exceeds_nominal"] = heads[h]["all_rows"]["cp95"][0] > NOMINAL_CREST
        anyh = sum(any(r["heads"][h] and r["heads"][h]["detected"] is True and r["reference_detector_status"] == "completed"
                       for h in binding["heads"]) for r in rows)
        out[study] = {"programs": len(rows), "source_sha256": s["source_sha256"],
                      "reference_detector_status": dict(sorted(collections.Counter(str(r["reference_detector_status"]) for r in rows).items())),
                      "heads": heads, "any_head": rate(anyh, len(rows)), "nominal_operating_point": NOMINAL_CREST}
    return out


def controlled_headline(c):
    return {"thresholds_kstar": {str(t["n"]): t["kstar"] for t in c["thresholds"]},
            "n24_accept_probability_by_rho": {t["rho"]: t["rows"][24]["accept_probability"]["exact"] for t in c["beta_binomial"]},
            "n24_ratio_to_fair_by_rho": {t["rho"]: t["rows"][24]["ratio_to_independent_fair"]["decimal40"] for t in c["beta_binomial"]},
            "max_over_n_accept_probability_by_rho": {t["rho"]: max((r["accept_probability"]["float"], r["n"]) for r in t["rows"]) for t in c["beta_binomial"]},
            "n24_blocks_accept_probability": {str(b["c"]): b["accept_probability"]["exact"] for b in c["duplicated_site_blocks_n24"]},
            "n24_any_of_K_independent_by_rho": {m["rho"]: {str(k["K"]): k["independent_any_accept_decimal40"] for k in m["K_table"]} for m in c["multiple_queries_n24_beta_binomial"]},
            "n24_any_of_K_union_upper_by_rho": {m["rho"]: {str(k["K"]): k["arbitrary_dependence_upper_union"]["exact"] for k in m["K_table"]} for m in c["multiple_queries_n24_beta_binomial"]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, required=True)
    args = ap.parse_args()
    res = args.results
    run = json.loads((res / "sew-run.json").read_text())
    keys = run["keys"]
    units = load_sew(res)
    q = q999()
    groups = {"humaneval": [u for u in units if u["corpus"] == "humaneval"],
              "mbpp": [u for u in units if u["corpus"] == "mbpp"],
              "projects": [u for u in units if u["corpus"] == "projects"]}
    groups["references"] = groups["humaneval"] + groups["mbpp"]
    controlled = json.loads((res / "controlled-correlated-null.json").read_text())
    binding = json.loads((res / "crest-unmarked-programs.json").read_text())
    raw_files = ["controlled-correlated-null.json", "crest-unmarked-programs.json", "sew-run.json",
                 "sew-null-humaneval.jsonl.gz", "sew-null-mbpp.jsonl.gz", "sew-null-projects.jsonl.gz"]
    summary = {
        "schema": "markvalidity-null-calibration-summary-v1",
        "protocol_sha256": sha((ROOT / "studies/null-calibration/protocol.json").read_bytes()),
        "raw_files_sha256": {n: sha((res / n).read_bytes()) for n in raw_files},
        "part1_controlled": controlled_headline(controlled),
        "part2_sew": {"nominal_per_query_level": NOMINAL_SEW, "paper_key_ids": [k["key_id"] for k in keys[:PAPER_KEYS]],
                      "keys_total": len(keys),
                      "corpora": {c: sew_corpus(groups[c], len(keys), q) for c in CORPORA},
                      "S5_retained_reference_detector_agreement": retained_agreement(units, keys)},
        "part3_crest": crest_summary(binding),
    }
    (res / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary["part2_sew"]["S5_retained_reference_detector_agreement"], indent=None)[:500])


if __name__ == "__main__":
    main()
