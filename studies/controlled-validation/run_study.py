"""Run the pre-declared controlled-validation study (parts A and B).

    python3 -B studies/controlled-validation/run_study.py --out results/controlled-validation

Reads protocol.json and results/controlled/raw/robustness.csv; writes only to --out.
Node.js (for the compile-only JavaScript syntax check) is taken from $NODE or PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "src"))

from common import (ARTIFACT, PROTOCOL_PATH, Rule, check_rule_against_benchmark, load_protocol,
                    load_robustness, read_csv_bytes, row_key, sha256_bytes, write_csv)
import matched_effort
import source_validation as sv


def js_syntax(items: list[tuple[str, str]]) -> tuple[dict, str]:
    node = os.environ.get("NODE") or shutil.which("node")
    if not node:
        raise SystemExit("node not found: set NODE or PATH (needed for the JavaScript syntax check)")
    with tempfile.TemporaryDirectory(prefix="cv-js-") as tmp:
        path = Path(tmp) / "sources.jsonl"
        path.write_text("".join(json.dumps({"id": i, "source": s}) + "\n" for i, s in items), encoding="utf-8")
        out = subprocess.run([node, str(HERE / "js_syntax_check.js"), str(path)], check=True,
                             capture_output=True, text=True).stdout
    data = json.loads(out)
    return data["results"], data["node_version"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"output directory exists: {out}")
    t0 = time.time()
    protocol = load_protocol()
    rule = Rule(protocol)
    check_rule_against_benchmark(rule)
    rows, digest = load_robustness()
    dense = {row_key(r): r for r in rows}

    # ---- Part A ------------------------------------------------------------
    derived = ARTIFACT / "results/controlled/derived"
    nominal_mix = read_csv_bytes((derived / "mixture_scores.csv").read_bytes())
    nominal_fam = read_csv_bytes((derived / "attack_family_means.csv").read_bytes())
    records = matched_effort.effort_records(rows, rule)
    curves, rankings, family, mixture, summary_a = matched_effort.analyze(records, protocol, nominal_mix, nominal_fam)

    # ---- Part B ------------------------------------------------------------
    primary, variants, js_items = [], [], []
    for cfg in sv.sample(False):
        rec, src = sv.evaluate(rule, dense, *cfg)
        primary.append(rec)
        if rec["language"] == "javascript":
            js_items.append((f"p{len(primary) - 1}", src))
    for cfg in sv.sample(True):
        rec, src = sv.evaluate(rule, dense, *cfg)
        variants.append(rec)
        if rec["language"] == "javascript":
            js_items.append((f"v{len(variants) - 1}", src))
    js_results, node_version = js_syntax(js_items)
    for ident, ok in js_results.items():
        (primary if ident[0] == "p" else variants)[int(ident[1:])]["javascript_syntax_ok"] = ok

    def overall(recs):
        n = len(recs)
        res = {"n": n, **{f"agree_{f}": sum(r[f"agree_{f}"] for r in recs)
                          for f in sv.PRIMARY_FIELDS + sv.SECONDARY_FIELDS}}
        res["agree_primary"] = sum(r["agree_primary"] for r in recs)
        res["agree_secondary"] = sum(r["agree_secondary"] for r in recs)
        res["configs_all_24_sites_agree"] = sum(r["sites_agreeing_with_state"] == 24 for r in recs)
        res["site_observations_agree"] = sum(r["sites_agreeing_with_state"] for r in recs)
        res["site_observations_total"] = 24 * n
        bi = [r for r in recs if r["byte_identical_to_state_render"] != ""]
        res["byte_identity_eligible"] = len(bi)
        res["byte_identical_to_state_render"] = sum(r["byte_identical_to_state_render"] for r in bi)
        py = [r for r in recs if r["language"] == "python"]
        js = [r for r in recs if r["language"] == "javascript"]
        res["python_syntax_ok"] = f"{sum(r['python_syntax_ok'] for r in py)}/{len(py)}"
        res["javascript_syntax_ok"] = f"{sum(r['javascript_syntax_ok'] for r in js)}/{len(js)}"
        res["state_detected"] = sum(int(r["state_detected"]) for r in recs)
        res["source_detected"] = sum(int(r["source_detected"]) for r in recs)
        causes = {}
        for r in recs:
            if r["cause"]:
                causes[r["cause"]] = causes.get(r["cause"], 0) + 1
        res["disagreement_causes"] = dict(sorted(causes.items()))
        return res

    summary_b = {"primary": overall(primary), "primary_strata": sv.strata_summary(primary),
                 "variants": {v: overall([r for r in variants if r["variant"] == v]) for v in sv.VARIANTS},
                 "variant_strata": {v: sv.strata_summary([r for r in variants if r["variant"] == v]) for v in sv.VARIANTS}}
    summary_b["state_model_validated_on_sample"] = summary_b["primary"]["agree_primary"] == summary_b["primary"]["n"]

    # ---- Write -------------------------------------------------------------
    out.mkdir(parents=True)
    write_csv(out / "effort_records.csv", records)
    write_csv(out / "matched_effort_curves.csv", curves)
    write_csv(out / "matched_effort_rankings.csv", rankings)
    write_csv(out / "matched_effort_family_scores.csv", family)
    write_csv(out / "matched_effort_mixture_scores.csv", mixture)
    write_csv(out / "source_validation_records.csv", primary)
    write_csv(out / "source_variant_records.csv", variants)
    disagreements = [r for r in primary + variants if not r["agree_primary"] or r["disagreeing_sites"]]
    write_csv(out / "source_disagreements.csv", disagreements, list(primary[0]))
    strata_rows = []
    for scope, strata in [("primary", summary_b["primary_strata"])] + [(v, summary_b["variant_strata"][v]) for v in sv.VARIANTS]:
        for name, cells in strata.items():
            for key, c in cells.items():
                strata_rows.append({"scope": scope, "stratum": name, "cell": key, **c})
    write_csv(out / "source_agreement_strata.csv", strata_rows)
    producers = ["protocol.json", "common.py", "matched_effort.py", "source_attacks.py", "source_validation.py",
                 "js_syntax_check.js", "run_study.py"]
    summary = {
        "schema": "markvalidity-controlled-validation-summary-v1",
        "protocol_sha256": sha256_bytes(PROTOCOL_PATH.read_bytes()),
        "robustness_csv_sha256": digest,
        "producer_sha256": {p: sha256_bytes((HERE / p).read_bytes()) for p in producers},
        "imported_sha256": {p: sha256_bytes((ARTIFACT / p).read_bytes()) for p in ("src/covewm/benchmark.py", "src/covewm/tasks.py")},
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "node": node_version},
        "elapsed_seconds": round(time.time() - t0, 1),
        "A_matched_effort": summary_a,
        "B_source_level_validation": summary_b,
        "new_program_executions": 0,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"A_reversal": summary_a["reversal_decision"], "B_primary": summary_b["primary"],
                      "B_variants": summary_b["variants"]}, indent=1))


if __name__ == "__main__":
    main()
