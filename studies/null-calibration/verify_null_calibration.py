"""Independent stdlib-only receiver for the null-calibration study.

Run from the artifact root:
    python3 -B -S studies/null-calibration/verify_null_calibration.py --results results/null-calibration

Checks:
  * protocol / raw-file SHA-256 bindings;
  * Part 1: recomputes controlled-correlated-null.json from first principles (exact fractions, Polya-urn
    recursion for the beta-binomial, independent tail/threshold derivation, 325 calls of the controlled
    detector implementation) and requires equality of every field;
  * Part 2: re-derives population identities (164 HumanEval, 427 MBPP, 120 project modules), the declared
    1,003 keys and the vendor hashes, then recomputes every SEW number of summary.json from the raw
    per-source files (Clopper-Pearson by bisection on the binomial CDF), including agreement with the
    retained reference_detector records;
  * Part 3: re-extracts the CREST readings from studies/crest/accepted and recomputes their summary.
Exits 1 on any mismatch.
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import json
import math
import statistics
import sys
from fractions import Fraction
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

FAIL = []


def check(cond, msg):
    if not cond:
        FAIL.append(msg)


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- Part 1 (first principles)
ALPHA = Fraction(1e-4)
NBITS = 24


def tail(n, m):
    if n <= 0:
        return Fraction(1)
    return Fraction(sum(comb(n, i) for i in range(m, n + 1)), 1 << n)


def threshold(n):
    ok = [m for m in range(n + 1) if tail(n, m) <= ALPHA]
    return min(ok) if ok else None


def polya_pmf(n, rho):
    """Distribution of the number of matches in n draws of a Polya urn with a = b = (1-rho)/(2 rho)."""
    if rho == 0:
        dist = [Fraction(1)]
        for _ in range(n):
            dist = [(dist[s] if s < len(dist) else 0) * Fraction(1, 2) + (dist[s - 1] if s >= 1 else 0) * Fraction(1, 2)
                    for s in range(len(dist) + 1)]
        return dist
    if rho == 1:
        d = [Fraction(0)] * (n + 1)
        d[0] += Fraction(1, 2)
        d[n] += Fraction(1, 2)
        return d
    a = (1 - rho) / (2 * rho)
    dist = [Fraction(1)]
    for t in range(n):
        new = [Fraction(0)] * (t + 2)
        for s, pr in enumerate(dist):
            up = (a + s) / (2 * a + t)
            new[s + 1] += pr * up
            new[s] += pr * (1 - up)
        dist = new
    return dist


def dec40(num, den, digits=40):
    if num == 0:
        return "0"
    e = 0
    # find e with 10^e <= num/den < 10^(e+1)
    while (num * 10 ** max(0, -e)) < den * 10 ** max(0, e):
        e -= 1
    while (num * 10 ** max(0, -(e + 1))) >= den * 10 ** max(0, e + 1):
        e += 1
    s = digits - 1 - e
    N = num * 10 ** s if s >= 0 else num
    D = den if s >= 0 else den * 10 ** (-s)
    q, r = divmod(N, D)
    if 2 * r > D or (2 * r == D and q & 1):
        q += 1
    t = str(q)
    if len(t) > digits:
        t, e = t[:-1], e + 1
    return t[0] + "." + t[1:] + "e" + str(e)


def rend(x):
    return {"exact": "%d/%d" % (x.numerator, x.denominator), "decimal40": dec40(x.numerator, x.denominator), "float": float(x)}


def anyk(p, K):
    d, n = p.denominator, p.numerator
    dk = pow(d, K)
    s = dec40(dk - pow(d - n, K), dk)
    return {"K": K, "independent_any_accept_decimal40": s, "independent_any_accept_float": float(s),
            "arbitrary_dependence_lower": rend(p), "arbitrary_dependence_upper_union": rend(min(Fraction(1), K * p))}


def expected_controlled(protocol):
    from covewm import benchmark
    p1 = protocol["part1_controlled_detector"]
    rho_grid = p1["null_models"]["rho_grid"]
    blocks = [1, 2, 3, 4, 6, 8, 12, 24]
    Kg = p1["multiple_queries"]["K_grid"]
    th = {n: threshold(n) for n in range(NBITS + 1)}
    acc = []
    for n in range(NBITS + 1):
        for m in range(n + 1):
            st = [benchmark.CarrierState(i, "lexical", 0, 0 if i < m else 1, i < n, "none") for i in range(NBITS)]
            got = benchmark.detector(st)["detected"]
            check(got == int(th[n] is not None and m >= th[n]), "controlled detector disagrees at n=%d m=%d" % (n, m))
            if got:
                acc.append([n, m])
    fair = {}
    tables = []
    for r in rho_grid:
        rho = Fraction(r)
        rows = []
        for n in range(NBITS + 1):
            pmf = polya_pmf(n, rho)
            check(sum(pmf) == 1, "pmf does not sum to one")
            p = sum(pmf[th[n]:], Fraction(0)) if th[n] is not None else Fraction(0)
            if rho == 0:
                fair[n] = p
                check(p == (tail(n, th[n]) if th[n] is not None else 0), "fair accept != tail")
            rows.append({"n": n, "kstar": th[n], "accept_probability": rend(p),
                         "ratio_to_independent_fair": rend(p / fair[n]) if fair[n] > 0 else None})
        tables.append({"rho": r, "beta_a": ("%d/%d" % (((1 - rho) / (2 * rho)).numerator, ((1 - rho) / (2 * rho)).denominator)
                                            if 0 < rho < 1 else None), "rows": rows})
    brow = []
    for c in blocks:
        nb, need = NBITS // c, -(-th[NBITS] // c)
        # enumerate all 2^(24/c) block words explicitly
        cnt = sum(1 for w in range(1 << nb) if c * bin(w).count("1") >= th[NBITS])
        p = Fraction(cnt, 1 << nb)
        brow.append({"c": c, "blocks": nb, "blocks_needed": need, "accept_probability": rend(p),
                     "ratio_to_independent_fair": rend(p / fair[NBITS])})
    return {
        "schema": "markvalidity-null-calibration-controlled-v1",
        "protocol_sha256": sha((ROOT / "studies/null-calibration/protocol.json").read_bytes()),
        "benchmark_sha256": sha((ROOT / "src/covewm/benchmark.py").read_bytes()),
        "alpha_float": 1e-4, "alpha_exact_binary_value": "%d/%d" % (ALPHA.numerator, ALPHA.denominator),
        "payload_bits": NBITS,
        "thresholds": [{"n": n, "kstar": th[n], "tail_at_kstar": rend(tail(n, th[n])) if th[n] is not None else None}
                       for n in range(NBITS + 1)],
        "detector_confirmation": {"calls": 325, "all_agree": True, "accepting_n_m_pairs": acc},
        "rho_grid": rho_grid, "block_grid": blocks, "K_grid": Kg,
        "beta_binomial": tables,
        "duplicated_site_blocks_n24": brow,
        "multiple_queries_n24_beta_binomial": [
            {"rho": t["rho"], "n": NBITS, "per_query": t["rows"][NBITS]["accept_probability"],
             "K_table": [anyk(Fraction(t["rows"][NBITS]["accept_probability"]["exact"]), K) for K in Kg]} for t in tables],
        "multiple_queries_n24_blocks": [
            {"c": b["c"], "n": NBITS, "per_query": b["accept_probability"],
             "K_table": [anyk(Fraction(b["accept_probability"]["exact"]), K) for K in Kg]} for b in brow],
        "multiple_queries_fair_all_n": [
            {"n": n, "per_query": rend(fair[n]), "K_table": [anyk(fair[n], K) for K in Kg]} for n in range(NBITS + 1) if fair[n] > 0],
    }


# ---------------------------------------------------------------- statistics
def log_pmf(n, k, p):
    if p <= 0:
        return 0.0 if k == 0 else -math.inf
    if p >= 1:
        return 0.0 if k == n else -math.inf
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * math.log(p) + (n - k) * math.log1p(-p)


def cdf(n, x, p):  # P(X <= x)
    return min(1.0, sum(math.exp(log_pmf(n, k, p)) for k in range(0, x + 1)))


def cp_bounds(x, n):
    def solve(f, target):  # f increasing in p? we bisect generically on sign
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid) < target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    lower = 0.0 if x == 0 else solve(lambda p: 1 - cdf(n, x - 1, p), 0.025)  # P(X >= x) increasing in p
    upper = 1.0 if x == n else solve(lambda p: -cdf(n, x, p), -0.025)        # P(X <= x) decreasing in p
    return [lower, upper]


_TAIL = {}


def lower_above(x, n, nominal=Fraction(1, 100)):
    """CP lower bound > nominal  <=>  P_nominal(X >= x) < 0.025 (exact rational)."""
    if x == 0:
        return False
    key = (x, n)
    if key not in _TAIL:
        _TAIL[key] = sum(comb(n, k) * nominal ** k * (1 - nominal) ** (n - k) for k in range(x, n + 1)) < Fraction(1, 40)
    return _TAIL[key]


def rate(x, n):
    return {"positives": x, "n": n, "rate": x / n if n else None, "cp95": cp_bounds(x, n) if n else None}


def q999(n=1003, p=Fraction(1, 100)):
    c = Fraction(0)
    for q in range(n + 1):
        c += comb(n, q) * p ** q * (1 - p) ** (n - q)
        if c >= Fraction(999, 1000):
            return q


# ---------------------------------------------------------------- Part 2
def verify_population(units):
    by = collections.defaultdict(list)
    for u in units:
        by[u["corpus"]].append(u)
    raw = (ROOT / "results/sew/humaneval/data/HumanEval.jsonl.gz").read_bytes()
    check(sha(raw) == "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef", "HumanEval data hash")
    he = [json.loads(x) for x in gzip.decompress(raw).decode().splitlines()]
    ret = {r["task_id"]: r["reference_sha256"] for r in json.loads((ROOT / "results/sew/humaneval/references.json").read_text())}
    exp = [(t["task_id"], sha((t["prompt"] + t["canonical_solution"]).encode())) for t in he]
    check([(u["source_id"], u["sha256"]) for u in by["humaneval"]] == exp, "HumanEval population identity")
    check(all(ret[t] == s for t, s in exp) and len(exp) == 164, "HumanEval retained reference identity")
    mb = json.loads((ROOT / "studies/sew/mbpp/sanitized-mbpp.json").read_text())
    ret = {r["task_id"]: r["source_sha256"] for r in json.loads((ROOT / "results/sew/mbpp/factors/stock/references.json").read_text())}
    exp = [("MBPP/%d" % t["task_id"], sha(t["code"].encode())) for t in mb]
    check([(u["source_id"], u["sha256"]) for u in by["mbpp"]] == exp, "MBPP population identity")
    check(all(ret[t["task_id"]] == sha(t["code"].encode()) for t in mb) and len(exp) == 427, "MBPP retained reference identity")
    with (ROOT / "corpus/transfer_manifest.csv").open(newline="", encoding="utf-8") as f:
        man = list(csv.DictReader(f))
    check(len(man) == 120 and [u["source_id"] for u in by["projects"]] == [r["module_id"] for r in man], "project population identity")
    for u, r in zip(by["projects"], man):
        p = ROOT / "corpus/transfer" / r["project_slug"] / ("module-%s.py" % r["module_id"].rsplit("-", 1)[1])
        actual = sha(p.read_bytes()) if p.is_file() else None
        check(u.get("sha256") == actual and u["identity_ok"] == (actual == r["source_sha256"]), "project identity " + r["module_id"])
        check((u["status"] == "unavailable") == (not u["identity_ok"] or u.get("unavailable_reason") is not None),
              "project availability " + r["module_id"])
    for u in units:
        if u["status"] == "available":
            check(len(u["results"]) == 1003, "result length " + u["source_id"])
    return by


def code(u, k):
    return "U" if u["status"] != "available" else u["results"][k][0]


def sew_corpus(units, nk):
    out = {"sources": len(units), "available_sources": sum(u["status"] == "available" for u in units),
           "unavailable_sources": [{"source_id": u["source_id"], "reason": u.get("unavailable_reason")} for u in units if u["status"] != "available"]}
    s1 = []
    for k in range(3):
        cs = [code(u, k) for u in units]
        av = [c for c in cs if c != "U"]
        e = {"key_index": k, "verdicts": dict(sorted(collections.Counter(cs).items())),
             "all_sources": rate(cs.count("D"), len(cs)), "available_sources": rate(av.count("D"), len(av))}
        e["exceeds_nominal"] = lower_above(cs.count("D"), len(cs))
        s1.append(e)
    out["S1_paper_keys"] = s1
    a3 = sum(any(code(u, k) == "D" for k in range(3)) for u in units)
    out["S2_any_paper_key"] = {**rate(a3, len(units)), "nominal_union_bound": 0.03, "nominal_independent": 1 - 0.99 ** 3}
    per_key = [sum(code(u, k) == "D" for u in units) for k in range(nk)]
    per_src = [sum(code(u, k) == "D" for k in range(nk)) for u in units]
    q = q999()
    out["S3_all_keys"] = {"keys": nk, "pairs": len(units) * nk, "pooled_positives": sum(per_key),
                          "pooled_rate": sum(per_key) / (len(units) * nk),
                          "per_key_positive_count": {"min": min(per_key), "median": statistics.median(per_key), "max": max(per_key)},
                          "keys_with_cp95_lower_above_nominal": sum(lower_above(x, len(units)) for x in per_key),
                          "per_source_positive_key_count_histogram": {str(a): b for a, b in sorted(collections.Counter(per_src).items())},
                          "sources_any_positive_key": sum(x > 0 for x in per_src), "q999_binomial_1003_0.01": q,
                          "sources_exceeding_q999": sum(x > q for x in per_src), "nominal_expected_positive_keys_per_source": nk * 0.01}
    pv = [u["results"][k][1] for u in units if u["status"] == "available" for k in range(nk) if u["results"][k][0] != "U"]
    T = [0.001, 0.01, 0.05, 0.1, 0.5]
    out["S4_p_value_profile"] = {"available_pairs": len(pv),
                                 "verdicts_all_pairs": dict(sorted(collections.Counter(code(u, k) for u in units for k in range(nk)).items())),
                                 "fraction_p_at_most": {str(t): sum(p <= t for p in pv) / len(pv) for t in T},
                                 "count_p_at_most": {str(t): sum(p <= t for p in pv) for t in T}, "min_p": min(pv)}
    # decision-rule consistency of every available pair: D <=> n_grades >= 5 and p < 0.01
    for u in units:
        if u["status"] != "available":
            continue
        for k, row in enumerate(u["results"]):
            if row[0] == "U":
                continue
            st = row[6] if len(row) > 6 else u["structure"]
            want = "I" if (st["parse_abstention"] or st["n_grades"] < 5) else ("D" if row[1] < 0.01 else "N")
            check(row[0] == want, "verdict rule violated %s key %d" % (u["source_id"], k))
            if not st["parse_abstention"]:
                check(row[1] == min(1.0, 2 * min(row[2], row[3])), "Bonferroni p mismatch %s key %d" % (u["source_id"], k))
    return out


def recon(u, k):
    names = {"D": "Watermark detected", "N": "No watermark evidence", "I": "Insufficient evidence"}
    row = u["results"][k]
    if row[0] == "U":
        return None
    st = row[6] if len(row) > 6 else u["structure"]
    if st["parse_abstention"]:
        return {"verdict": names[row[0]], "reason": "parse", "p": row[1], "n_grades": st["n_grades"]}
    return {"verdict": names[row[0]], "p": row[1], "p_all": row[2], "p_syntax": row[3], "n_grades": st["n_grades"],
            "k_grades": row[4], "n_syntax": st["n_syntax"], "k_syntax": row[5], "n_sites": st["n_sites"]}


def agreement(by, keys):
    ret = {}
    for r in json.loads((ROOT / "results/sew/humaneval/rows.json").read_text()):
        if r["variant"] == "stock":
            ret[(r["task_id"], r["key_id"])] = r["reference_detector"]
    for r in json.loads((ROOT / "results/sew/mbpp/factors/stock/rows.json").read_text()):
        ret[("MBPP/%d" % r["task_id"], r["key_id"])] = r.get("reference_detector")
    out = {}
    for c in ("humaneval", "mbpp"):
        n = eq = 0
        diff = []
        for u in by[c]:
            for k in range(3):
                n += 1
                f = recon(u, k) if u["status"] == "available" else None
                if f is not None and f == ret.get((u["source_id"], keys[k]["key_id"])):
                    eq += 1
                else:
                    diff.append([u["source_id"], keys[k]["key_id"]])
        out[c] = {"compared": n, "equal": eq, "unequal": diff}
    return out


# ---------------------------------------------------------------- Part 3
def crest(binding):
    heads = ["rf", "logreg_l1", "logreg_l2"]
    check(binding["heads"] == heads, "CREST heads")
    out = {}
    for study in ("reference", "gpt4o", "qwen"):
        path = ROOT / "studies/crest/accepted" / study / "results.json"
        raw = path.read_bytes()
        rows = json.loads(raw)
        b = binding["studies"][study]
        check(b["source_sha256"] == sha(raw), "CREST source hash " + study)
        check(len(rows) == len(b["rows"]), "CREST row count " + study)
        for r, x in zip(rows, b["rows"]):
            det = r.get("reference_detector") or {}
            check(x["task_id"] == r.get("task_id") and x["dataset"] == r.get("dataset") and x["qualified_reference"] == r.get("qualified_reference")
                  and x["reference_detector_status"] == det.get("status"), "CREST row identity " + study)
            for h in heads:
                c = (det.get("classifiers") or {}).get(h)
                want = None if c is None else {k: c.get(k) for k in ("probability", "threshold", "constraint", "detected")}
                check(x["heads"][h] == want, "CREST head binding %s %s" % (study, h))
                if c is not None:
                    check(c["detected"] == (c["probability"] >= c["threshold"]), "CREST threshold rule %s %s %s" % (study, x["task_id"], h))
        hs = {}
        for h in heads:
            det = [r["heads"][h]["detected"] if (r["reference_detector_status"] == "completed" and r["heads"][h]) else None for r in b["rows"]]
            comp = [d for d in det if d is not None]
            qual = [d for r, d in zip(b["rows"], det) if r["qualified_reference"] is True]
            hs[h] = {"thresholds": sorted({r["heads"][h]["threshold"] for r in b["rows"] if r["heads"][h]}),
                     "all_rows": rate(sum(d is True for d in det), len(det)),
                     "completed_rows": rate(sum(d is True for d in comp), len(comp)),
                     "qualified_reference_rows": rate(sum(d is True for d in qual), len(qual)),
                     "unavailable_rows": sum(d is None for d in det)}
            hs[h]["exceeds_nominal"] = lower_above(hs[h]["all_rows"]["positives"], len(det))
        anyh = sum(any(r["heads"][h] and r["heads"][h]["detected"] is True and r["reference_detector_status"] == "completed" for h in heads)
                   for r in b["rows"])
        out[study] = {"programs": len(b["rows"]), "source_sha256": sha(raw),
                      "reference_detector_status": dict(sorted(collections.Counter(str(r["reference_detector_status"]) for r in b["rows"]).items())),
                      "heads": hs, "any_head": rate(anyh, len(b["rows"])), "nominal_operating_point": 0.01}
    return out


# ---------------------------------------------------------------- comparison
def same(a, b, path="$"):
    if isinstance(a, bool) or isinstance(b, bool):
        check(a is b, "mismatch at %s: %r vs %r" % (path, a, b))
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, int) and isinstance(b, int):
            check(a == b, "mismatch at %s: %r vs %r" % (path, a, b))
        else:
            check(abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b)), "mismatch at %s: %r vs %r" % (path, a, b))
    elif isinstance(a, dict) and isinstance(b, dict):
        check(set(a) == set(b), "key set mismatch at %s: %s" % (path, sorted(set(a) ^ set(b))))
        for k in set(a) & set(b):
            same(a[k], b[k], path + "." + str(k))
    elif isinstance(a, list) and isinstance(b, list):
        check(len(a) == len(b), "length mismatch at %s" % path)
        for i, (x, y) in enumerate(zip(a, b)):
            same(x, y, "%s[%d]" % (path, i))
    else:
        check(a == b, "mismatch at %s: %r vs %r" % (path, a, b))


def headline(c):
    return {"thresholds_kstar": {str(t["n"]): t["kstar"] for t in c["thresholds"]},
            "n24_accept_probability_by_rho": {t["rho"]: t["rows"][24]["accept_probability"]["exact"] for t in c["beta_binomial"]},
            "n24_ratio_to_fair_by_rho": {t["rho"]: t["rows"][24]["ratio_to_independent_fair"]["decimal40"] for t in c["beta_binomial"]},
            "max_over_n_accept_probability_by_rho": {t["rho"]: list(max((r["accept_probability"]["float"], r["n"]) for r in t["rows"])) for t in c["beta_binomial"]},
            "n24_blocks_accept_probability": {str(b["c"]): b["accept_probability"]["exact"] for b in c["duplicated_site_blocks_n24"]},
            "n24_any_of_K_independent_by_rho": {m["rho"]: {str(k["K"]): k["independent_any_accept_decimal40"] for k in m["K_table"]} for m in c["multiple_queries_n24_beta_binomial"]},
            "n24_any_of_K_union_upper_by_rho": {m["rho"]: {str(k["K"]): k["arbitrary_dependence_upper_union"]["exact"] for k in m["K_table"]} for m in c["multiple_queries_n24_beta_binomial"]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, required=True)
    a = ap.parse_args()
    res = a.results if a.results.is_absolute() else Path.cwd() / a.results
    protocol = json.loads((ROOT / "studies/null-calibration/protocol.json").read_text())
    summary = json.loads((res / "summary.json").read_text())
    psha = sha((ROOT / "studies/null-calibration/protocol.json").read_bytes())
    check(summary["protocol_sha256"] == psha, "summary protocol hash")
    for name, h in summary["raw_files_sha256"].items():
        check(sha((res / name).read_bytes()) == h, "raw file hash " + name)

    # Part 1
    controlled = json.loads((res / "controlled-correlated-null.json").read_text())
    same(controlled, expected_controlled(protocol), "$controlled")
    same(summary["part1_controlled"], headline(controlled), "$summary.part1")
    print("part1: controlled correlated-null tables recomputed (%d checks failed so far)" % len(FAIL))

    # Part 2
    run = json.loads((res / "sew-run.json").read_text())
    check(run["protocol_sha256"] == psha, "run protocol hash")
    keys = [("upstream_default", "76" * 16), ("integer_0", "00" * 16), ("integer_1", "00" * 15 + "01")]
    keys += [("integer_%d" % i, i.to_bytes(16, "big").hex()) for i in range(2, 1002)]
    check([(k["key_id"], k["hex"]) for k in run["keys"]] == keys, "declared keys")
    spec = json.loads((ROOT / "results/sew/humaneval/specification.json").read_text())
    stock = [v for v in spec["variants"] if v["variant"] == "stock"][0]["vendor_files_sha256"]
    vend = ROOT / "studies/sew/variants/stock"
    actual = {p.relative_to(vend).as_posix(): sha(p.read_bytes()) for p in sorted(vend.rglob("*"))
              if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    check(run["vendor_files_sha256"] == stock == actual, "stock vendor hashes")
    check(run["tree_sitter"] == "0.23.2" and run["tree_sitter_python"] == "0.23.6", "tree-sitter versions")
    units = []
    for c in ("humaneval", "mbpp", "projects"):
        name = "sew-null-%s.jsonl.gz" % c
        check(run["files_sha256"][name] == sha((res / name).read_bytes()), "run file hash " + name)
        with gzip.open(res / name, "rt", encoding="utf-8") as f:
            units += [json.loads(line) for line in f]
    by = verify_population(units)
    by["references"] = by["humaneval"] + by["mbpp"]
    exp2 = {"nominal_per_query_level": 0.01, "paper_key_ids": ["upstream_default", "integer_0", "integer_1"], "keys_total": 1003,
            "corpora": {c: sew_corpus(by[c], 1003) for c in ("humaneval", "mbpp", "references", "projects")},
            "S5_retained_reference_detector_agreement": agreement(by, run["keys"])}
    same(summary["part2_sew"], exp2, "$summary.part2")
    print("part2: SEW empirical null recomputed (%d checks failed so far)" % len(FAIL))

    # Part 3
    binding = json.loads((res / "crest-unmarked-programs.json").read_text())
    same(summary["part3_crest"], crest(binding), "$summary.part3")
    print("part3: CREST unmarked-program readings re-bound (%d checks failed so far)" % len(FAIL))

    check(set(summary) == {"schema", "protocol_sha256", "raw_files_sha256", "part1_controlled", "part2_sew", "part3_crest"}, "summary sections")
    if FAIL:
        for m in FAIL[:50]:
            print("FAIL:", m)
        print("null-calibration: FAIL (%d mismatches)" % len(FAIL))
        sys.exit(1)
    print("null-calibration: PASS")


if __name__ == "__main__":
    main()
