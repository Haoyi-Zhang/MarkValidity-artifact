"""Independent receiver for results/controlled-validation (stdlib only).

    python3 -B -S studies/controlled-validation/verify_controlled_validation.py --results results/controlled-validation

Recomputes every number in summary.json and every derived CSV from the
per-configuration records and results/controlled/raw/robustness.csv, and
re-runs the text-level attacks plus extraction for the complete part-B sample
(Python and JavaScript sources; both are transformed and extracted in pure
Python). Python syntax is re-checked with compile(); JavaScript syntax needs
Node.js ($NODE or PATH) and is reported as SKIPPED when Node is absent
(--require-node makes that a failure). Exit status 1 on any mismatch.
The aggregation code below is written independently of matched_effort.py and
run_study.py.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parent.parent
S = ("lexical", "structural", "hybrid")
ATT = ("format", "rename", "normalize", "random_flip", "strip", "mixed")
FAM = ("rename", "normalize", "random_flip", "strip", "mixed")
MEAS = ("nominal_severity", "E1_realized_edits", "E2_requested_operations_bin", "E3_attempted_operations")
PAIRS = (("lexical", "structural"), ("lexical", "hybrid"), ("structural", "hybrid"))
WEIGHTS = {"balanced": dict(zip(FAM, ("0.2",) * 5)),
           "rename-heavy": {"rename": "0.54", "normalize": "0", "random_flip": "0.24", "strip": "0.22", "mixed": "0"},
           "structure-heavy": {"rename": "0", "normalize": "0.54", "random_flip": "0.24", "strip": "0.22", "mixed": "0"}}
NMIN = 30
FAILURES: list[str] = []
SKIPPED: list[str] = []


def check(cond: bool, what: str) -> None:
    if not cond:
        FAILURES.append(what)
        if len(FAILURES) <= 30:
            print("MISMATCH:", what)


def table(path: Path) -> list[dict]:
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))


def f12(x: Fraction | None, places: int = 12) -> str:
    if x is None:
        return ""
    with localcontext() as c:
        c.prec = 80
        d = Decimal(x.numerator) / Decimal(x.denominator)
        return format(d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN), f".{places}f")


def u01(text: str) -> float:
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big") / 2**64


def attempted_ops(protocol, row) -> int:
    rule = protocol["declared_site_selection_rule"]
    s, a, sev = row["scheme"], row["attack"], row["severity"]
    if a == "format":
        return 0
    key = f"{rule['salts'][s][a]}|{s}|{a}|{float(sev):.1f}|{row['task']}|{row['language']}|{row['payload_index']}"
    p = min(1.0, max(0.0, float(sev) * rule["multipliers"][s][a]))
    op = {"rename": "rename", "normalize": "normalize", "random_flip": "flip", "strip": "strip", "mixed": "mixedapply"}[a]
    chans = ["lexical"] * 24 if s == "lexical" else ["structural"] * 24 if s == "structural" else ["lexical"] * 12 + ["structural"] * 12
    n = 0
    for k in range(24):
        if a == "rename" and chans[k] != "lexical":
            continue
        if a == "normalize" and chans[k] != "structural":
            continue
        n += u01(f"{key}|{op}|{k}") < p
    return n


def verify_a(res: Path, protocol, dense_rows, summary):
    recs = table(res / "effort_records.csv")
    check(len(recs) == len(dense_rows) == 76032, "A: effort record count")
    for r, d in zip(recs, dense_rows):
        same = all(r[f] == d[f] for f in ("scheme", "attack", "severity", "task", "language", "payload_index",
                                           "realized_bit_changes", "deletions", "requested_operations", "detected"))
        if not same:
            check(False, f"A: effort record differs from robustness row {d['scheme']} {d['attack']} {d['severity']} {d['task']}")
            break
        check(int(r["E1_realized_edits"]) == int(d["realized_bit_changes"]) + int(d["deletions"]), "A: E1 definition")
        check(int(r["E2_requested_operations_bin"]) == 2 * math.floor(float(d["requested_operations"]) / 2), "A: E2 bin")
        check(int(r["E3_attempted_operations"]) == attempted_ops(protocol, d), "A: E3 recomputation")
        check(int(r["E3_attempted_operations"]) >= int(r["E1_realized_edits"]), "A: attempted >= realized")
    if FAILURES:
        return
    val = lambda r, m: r["severity"] if m == "nominal_severity" else int(r[m])
    cnt = {(m, a, s): defaultdict(lambda: [0, 0]) for m in MEAS for a in ATT for s in S}
    for r in recs:
        for m in MEAS:
            c = cnt[(m, r["attack"], r["scheme"])][val(r, m)]
            c[0] += 1
            c[1] += int(r["detected"])
    key_order = lambda m: (lambda v: float(v)) if m == "nominal_severity" else int
    # curves
    exp_curves, cell = [], {}
    for m in MEAS:
        for a in ATT:
            dom = sorted({v for s in S for v in cnt[(m, a, s)]}, key=key_order(m))
            for rel in (("eq",) if m == "nominal_severity" else ("eq", "le")):
                for s in S:
                    cn = cd = 0
                    for b in dom:
                        n, d = cnt[(m, a, s)].get(b, [0, 0])
                        cn, cd = cn + n, cd + d
                        nn, dd = (n, d) if rel == "eq" else (cn, cd)
                        cell[(m, rel, a, s, b)] = (nn, dd)
                        fr = Fraction(dd, nn) if nn else None
                        exp_curves.append([m, rel, a, s, str(b), str(nn), str(dd),
                                           "" if fr is None else f"{float(fr):.6f}",
                                           "" if fr is None else f"{fr.numerator}/{fr.denominator}"])
    got = [[r[k] for k in ("effort_measure", "relation", "attack", "carrier", "effort", "n", "detected", "rate", "rate_exact")]
           for r in table(res / "matched_effort_curves.csv")]
    check(got == exp_curves, "A: matched_effort_curves.csv")
    # rankings
    exp_rank = []
    for m in MEAS:
        for a in ATT:
            dom = sorted({v for s in S for v in cnt[(m, a, s)]}, key=key_order(m))
            for rel in (("eq",) if m == "nominal_severity" else ("eq", "le")):
                for b in dom:
                    sup = [s for s in S if cell[(m, rel, a, s, b)][0] >= NMIN]
                    rates = {s: Fraction(cell[(m, rel, a, s, b)][1], cell[(m, rel, a, s, b)][0]) for s in sup}
                    win = [s for s in sup if rates[s] == max(rates.values())] if sup else []
                    exp_rank.append([m, rel, a, str(b)] +
                                    [str(cell[(m, rel, a, s, b)][0]) for s in S] +
                                    [f12(Fraction(cell[(m, rel, a, s, b)][1], cell[(m, rel, a, s, b)][0]), 6) if cell[(m, rel, a, s, b)][0] else "" for s in S] +
                                    [";".join(sup), str(int(len(sup) == 3)), ";".join(win),
                                     "" if not sup else str(int(len(set(rates.values())) == 1))])
    cols = ["effort_measure", "relation", "attack", "effort"] + [f"n_{s}" for s in S] + [f"rate_{s}" for s in S] + \
           ["supported", "common_support", "winner_set", "all_supported_equal"]
    rank_rows = table(res / "matched_effort_rankings.csv")
    check([[r[c] for c in cols] for r in rank_rows] == exp_rank, "A: matched_effort_rankings.csv")
    # family scores (direct standardization over common support, relation eq)
    fam = {}
    exp_fam = []
    groups = [("all", S)] + [("pair:" + "-".join(p), p) for p in PAIRS]
    for m in MEAS:
        for a in ATT:
            dom = sorted({v for s in S for v in cnt[(m, a, s)]}, key=key_order(m))
            for g, mem in groups:
                sup = [b for b in dom if all(cell[(m, "eq", a, s, b)][0] >= NMIN for s in mem)]
                tot = sum(cell[(m, "eq", a, s, b)][0] for b in sup for s in mem)
                for s in mem:
                    fam[(m, g, a, s)] = None if not sup else sum(
                        Fraction(sum(cell[(m, "eq", a, t, b)][0] for t in mem), tot) *
                        Fraction(cell[(m, "eq", a, s, b)][1], cell[(m, "eq", a, s, b)][0]) for b in sup)
                vals = {s: fam[(m, g, a, s)] for s in mem}
                win = ";".join(s for s in mem if vals[s] == max(vals.values())) if sup else ""
                for s in mem:
                    total_rows = sum(cell[(m, "eq", a, s, b)][0] for b in dom)
                    in_sup = sum(cell[(m, "eq", a, s, b)][0] for b in sup)
                    exp_fam.append([m, g, a, s, ";".join(map(str, sup)), str(len(sup)), str(total_rows), str(in_sup),
                                    f12(Fraction(in_sup, total_rows), 6), f12(fam[(m, g, a, s)]), win])
    cols = ["effort_measure", "comparison", "attack", "carrier", "common_support_values", "n_common_support_values",
            "carrier_rows", "rows_in_common_support", "coverage", "standardized_rate", "winner_set"]
    check([[r[c] for c in cols] for r in table(res / "matched_effort_family_scores.csv")] == exp_fam,
          "A: matched_effort_family_scores.csv")
    # nominal comparator equals retained derived tables
    derived = ARTIFACT / "results/controlled/derived"
    for r in table(derived / "attack_family_means.csv"):
        check(f12(fam[("nominal_severity", "all", r["attack"], r["scheme"])]) == r["mean_detection_rate"],
              f"A: nominal family mean {r['scheme']} {r['attack']}")
    retained_mix = {(r["mixture"], r["scheme"]): r["score"] for r in table(derived / "mixture_scores.csv")}
    # mixtures
    exp_mix, mix_sum = [], {}
    for m in MEAS:
        mix_sum[m] = {}
        for mix, w in WEIGHTS.items():
            sc = {}
            for s in S:
                parts = [(Fraction(w[a]), fam[(m, "all", a, s)]) for a in FAM if Fraction(w[a])]
                sc[s] = None if any(v is None for _, v in parts) else sum(x * v for x, v in parts)
            win = [s for s in S if sc[s] == max(sc.values())] if all(v is not None for v in sc.values()) else []
            und = [a for a in FAM if Fraction(w[a]) and fam[(m, "all", a, S[0])] is None]
            mix_sum[m][mix] = {"scores": {s: f12(sc[s]) for s in S}, "winner_set": win,
                               "unique_winner": win[0] if len(win) == 1 else None, "undefined_families": und}
            for s in S:
                exp_mix.append([m, mix, s, f12(sc[s]), ";".join(win), ";".join(und)])
                if m == "nominal_severity":
                    check(f12(sc[s]) == retained_mix[(mix, s)], f"A: nominal mixture {mix} {s}")
    cols = ["effort_measure", "mixture", "carrier", "score", "winner_set", "undefined_families"]
    check([[r[c] for c in cols] for r in table(res / "matched_effort_mixture_scores.csv")] == exp_mix,
          "A: matched_effort_mixture_scores.csv")
    A = summary["A_matched_effort"]
    check(A["mixture_scores"] == mix_sum, "A: summary mixture_scores")
    check(A["rows"] == 76032 and A["n_min"] == NMIN, "A: summary rows/n_min")
    nom = mix_sum["nominal_severity"]
    check(A["nominal_winners"] == {k: v["winner_set"] for k, v in nom.items()}, "A: nominal winners")
    check(A["nominal_reversal_present"] == (nom["rename-heavy"]["unique_winner"] == "structural" and nom["structure-heavy"]["unique_winner"] == "lexical"), "A: nominal reversal")
    for m in MEAS[1:]:
        persists = mix_sum[m]["rename-heavy"]["unique_winner"] == "structural" and mix_sum[m]["structure-heavy"]["unique_winner"] == "lexical"
        d = A["reversal_decision"][m]
        check(d["reversal_persists"] == persists, f"A: reversal decision {m}")
        check(d["winners"] == {k: v["winner_set"] for k, v in mix_sum[m].items()}, f"A: decision winners {m}")
        check(d["undefined_families"] == {k: v["undefined_families"] for k, v in mix_sum[m].items()}, f"A: undefined {m}")
    check(A["reversal_persists_at_matched_realized_edits"] == A["reversal_decision"]["E1_realized_edits"]["reversal_persists"], "A: primary decision")
    for m in MEAS:
        for a in FAM:
            rows = [r for r in table(res / "matched_effort_family_scores.csv") if r["effort_measure"] == m and r["comparison"] == "all" and r["attack"] == a]
            check(A["family_winner_sets"][m][a] == rows[0]["winner_set"], f"A: family winner {m} {a}")
    by_pair = defaultdict(set)
    for r in dense_rows:
        by_pair[(int(r["realized_bit_changes"]), int(r["deletions"]))].add(int(r["detected"]))
    inv = A["detection_function_of_changes_and_deletions"]
    check(inv["distinct_change_deletion_pairs"] == len(by_pair), "A: invariance pairs")
    check(inv["pairs_with_conflicting_decisions"] == sum(len(v) > 1 for v in by_pair.values()), "A: invariance conflicts")
    check(inv["detecting_pairs"] == sorted([list(k) for k, v in by_pair.items() if v == {1}]), "A: detecting pairs")
    for m in MEAS[1:]:
        for a in FAM:
            cs = [r for r in rank_rows if r["effort_measure"] == m and r["relation"] == "eq" and r["attack"] == a and r["common_support"] == "1"]
            e = A["common_support_equal_rate_cells"][m][a]
            check(e["common_support_cells"] == len(cs), f"A: cs cells {m} {a}")
            check(e["cells_all_three_rates_equal"] == sum(r["all_supported_equal"] == "1" for r in cs), f"A: equal cells {m} {a}")
            check(e["cells_unique_winner"] == {s: sum(r["winner_set"] == s for r in cs) for s in S}, f"A: unique cells {m} {a}")
    print(f"A matched-effort: checked 76032 effort records and all derived tables; reversal persists at E1: "
          f"{A['reversal_persists_at_matched_realized_edits']}")


PRIM = ("surviving_sites", "match_count", "detected")
SEC = ("realized_bit_changes", "deletions", "p_value")
STRATA = {"carrier": ("scheme",), "attack": ("attack",), "severity": ("severity",), "language": ("language",),
          "carrier_x_attack": ("scheme", "attack"), "attack_x_severity": ("attack", "severity"),
          "carrier_x_attack_x_language": ("scheme", "attack", "language"),
          "carrier_x_attack_x_severity_x_language": ("scheme", "attack", "severity", "language")}
VARIANTS = {"format_whitespace": "format", "strip_statement_only": "strip", "rename_no_digit_split": "rename"}


def verify_b(res: Path, protocol, dense, summary, require_node: bool):
    prim = table(res / "source_validation_records.csv")
    var = table(res / "source_variant_records.csv")
    sev = protocol["B_source_level_validation"]["sample"]["severities"]
    sys.path.insert(0, str(ARTIFACT / "src"))
    from covewm.tasks import TASK_BY_NAME
    tasks = sorted(TASK_BY_NAME)
    exp_p = [("primary", s, a, v, t, l, str(p)) for s, a, v, t, l, p in itertools.product(S, ATT, sev, tasks, ("python", "javascript"), range(16))]
    exp_v = [(vn, s, base, v, t, l, str(p)) for vn, base in VARIANTS.items() for s, v, t, l, p in itertools.product(S, sev, tasks, ("python", "javascript"), range(16))]
    kf = ("variant", "scheme", "attack", "severity", "task", "language", "payload_index")
    check([tuple(r[k] for k in kf) for r in prim] == exp_p and len(prim) == 34560, "B: primary sample is the declared grid")
    check([tuple(r[k] for k in kf) for r in var] == exp_v and len(var) == 17280, "B: variant sample is the declared grid")
    for r in prim + var:
        d = dense[(r["scheme"], r["attack"], r["severity"], r["task"], r["language"], int(r["payload_index"]))]
        for f in PRIM + SEC:
            check(r[f"state_{f}"] == d[f], f"B: state field {f} differs from robustness.csv")
            check(r[f"agree_{f}"] == str(int(r[f"source_{f}"] == d[f])), f"B: agree flag {f}")
        check(r["agree_primary"] == str(int(all(r[f"source_{f}"] == d[f] for f in PRIM))), "B: agree_primary")
        check(r["agree_secondary"] == str(int(all(r[f"source_{f}"] == d[f] for f in SEC))), "B: agree_secondary")
        bad = [x for x in r["disagreeing_sites"].split(";") if x]
        check(int(r["sites_agreeing_with_state"]) == 24 - len(bad), "B: site count")
        check(bool(r["cause"]) == (bool(bad) or r["agree_primary"] == "0"), "B: cause present iff disagreement")
    if FAILURES:
        return

    def overall(recs):
        out = {"n": len(recs)}
        for f in PRIM + SEC:
            out[f"agree_{f}"] = sum(r[f"agree_{f}"] == "1" for r in recs)
        out["agree_primary"] = sum(r["agree_primary"] == "1" for r in recs)
        out["agree_secondary"] = sum(r["agree_secondary"] == "1" for r in recs)
        out["configs_all_24_sites_agree"] = sum(r["sites_agreeing_with_state"] == "24" for r in recs)
        out["site_observations_agree"] = sum(int(r["sites_agreeing_with_state"]) for r in recs)
        out["site_observations_total"] = 24 * len(recs)
        bi = [r for r in recs if r["byte_identical_to_state_render"] != ""]
        out["byte_identity_eligible"] = len(bi)
        out["byte_identical_to_state_render"] = sum(r["byte_identical_to_state_render"] == "1" for r in bi)
        py = [r for r in recs if r["language"] == "python"]
        js = [r for r in recs if r["language"] == "javascript"]
        out["python_syntax_ok"] = f"{sum(r['python_syntax_ok'] == '1' for r in py)}/{len(py)}"
        out["javascript_syntax_ok"] = f"{sum(r['javascript_syntax_ok'] == '1' for r in js)}/{len(js)}"
        out["state_detected"] = sum(int(r["state_detected"]) for r in recs)
        out["source_detected"] = sum(int(r["source_detected"]) for r in recs)
        causes = defaultdict(int)
        for r in recs:
            if r["cause"]:
                causes[r["cause"]] += 1
        out["disagreement_causes"] = dict(sorted(causes.items()))
        return out

    def strata(recs):
        out = {}
        for name, dims in STRATA.items():
            cells = {}
            for r in recs:
                c = cells.setdefault("|".join(r[d] for d in dims), {"n": 0, "agree_primary": 0, **{f"agree_{f}": 0 for f in PRIM}})
                c["n"] += 1
                c["agree_primary"] += r["agree_primary"] == "1"
                for f in PRIM:
                    c[f"agree_{f}"] += r[f"agree_{f}"] == "1"
            out[name] = dict(sorted(cells.items()))
        return out

    B = summary["B_source_level_validation"]
    check(B["primary"] == overall(prim), "B: summary primary overall")
    check(B["primary_strata"] == strata(prim), "B: summary primary strata")
    for v in VARIANTS:
        sub = [r for r in var if r["variant"] == v]
        check(B["variants"][v] == overall(sub), f"B: summary variant {v}")
        check(B["variant_strata"][v] == strata(sub), f"B: variant strata {v}")
    check(B["state_model_validated_on_sample"] == (overall(prim)["agree_primary"] == len(prim)), "B: validation decision")
    strata_rows = table(res / "source_agreement_strata.csv")
    exp = []
    for scope, st in [("primary", strata(prim))] + [(v, strata([r for r in var if r["variant"] == v])) for v in VARIANTS]:
        for name, cells in st.items():
            for key, c in cells.items():
                exp.append([scope, name, key] + [str(c[k]) for k in ("n", "agree_primary", "agree_surviving_sites", "agree_match_count", "agree_detected")])
    check([[r[k] for k in ("scope", "stratum", "cell", "n", "agree_primary", "agree_surviving_sites", "agree_match_count", "agree_detected")] for r in strata_rows] == exp,
          "B: source_agreement_strata.csv")
    dis = table(res / "source_disagreements.csv")
    check([tuple(r[k] for k in kf) for r in dis] == [tuple(r[k] for k in kf) for r in prim + var if r["agree_primary"] == "0" or r["disagreeing_sites"]],
          "B: source_disagreements.csv lists every disagreement")
    print(f"B summary: recomputed from {len(prim)} primary and {len(var)} variant records")

    # ---- re-run the text-level attacks and extraction ----------------------
    sys.path.insert(0, str(HERE))
    from common import Rule
    from source_attacks import attack_source
    from covewm.benchmark import (CarrierState, carrier_only_states, detector, extract_carriers,
                                  payload_bits, render_program)
    rule = Rule(protocol)
    js_items = []
    for idx, r in enumerate(prim + var):
        spec = TASK_BY_NAME[r["task"]]
        lang = r["language"]
        exp_bits = payload_bits(r["task"], lang, int(r["payload_index"]))
        st0 = carrier_only_states(exp_bits, r["scheme"])
        src0 = render_program(spec.python_reference if lang == "python" else spec.javascript_reference, lang, st0)
        src1, log = attack_source(src0, lang, rule, r["scheme"], r["attack"], r["severity"], r["task"], int(r["payload_index"]), r["variant"])
        ext = extract_carriers(src1, lang)
        det = detector([CarrierState(i, s.channel, exp_bits[i], ext.get(i, 0), i in ext, "x") for i, s in enumerate(st0)])
        det["p_value"] = f"{det['p_value']:.18g}"
        ok = (hashlib.sha256(src1.encode()).hexdigest() == r["source_sha256"]
              and ";".join(f"{k}:{op}:{int(c)}" for k, op, c in log) == r["op_log"]
              and str(len(log)) == r["selected_sites"]
              and all(str(det[f]) == r[f"source_{f}"] for f in PRIM + SEC))
        check(ok, f"B: re-run differs for {[r[k] for k in kf]}")
        if lang == "python":
            try:
                compile(src1, "<x>", "exec")
                syn = "1"
            except SyntaxError:
                syn = "0"
            check(syn == r["python_syntax_ok"], f"B: python syntax {[r[k] for k in kf]}")
        else:
            js_items.append((str(idx), src1, r["javascript_syntax_ok"]))
    print(f"B re-run: {len(prim) + len(var)} text-level attacks re-executed and re-extracted (Python and JavaScript sources)")
    node = os.environ.get("NODE") or shutil.which("node")
    if not node:
        msg = "JavaScript syntax re-check SKIPPED: node not found (set NODE or PATH); recorded javascript_syntax_ok values not re-verified"
        SKIPPED.append(msg)
        print(msg)
        if require_node:
            check(False, "node required (--require-node) but not found")
        return
    with tempfile.TemporaryDirectory(prefix="cv-verify-") as tmp:
        p = Path(tmp) / "s.jsonl"
        p.write_text("".join(json.dumps({"id": i, "source": s}) + "\n" for i, s, _ in js_items), encoding="utf-8")
        data = json.loads(subprocess.run([node, str(HERE / "js_syntax_check.js"), str(p)], check=True,
                                         capture_output=True, text=True).stdout)
    for i, _, recorded in js_items:
        check(str(data["results"][i]) == recorded, f"B: javascript syntax record {i}")
    print(f"B JavaScript syntax: {len(js_items)} sources re-compiled with Node {data['node_version']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--require-node", action="store_true")
    args = ap.parse_args()
    res = args.results.resolve()
    summary = json.loads((res / "summary.json").read_text(encoding="utf-8"))
    protocol_bytes = (HERE / "protocol.json").read_bytes()
    protocol = json.loads(protocol_bytes)
    check(hashlib.sha256(protocol_bytes).hexdigest() == summary["protocol_sha256"], "protocol.json differs from the one used")
    for name, digest in summary["producer_sha256"].items():
        check(hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, f"producer changed: {name}")
    for name, digest in summary["imported_sha256"].items():
        check(hashlib.sha256((ARTIFACT / name).read_bytes()).hexdigest() == digest, f"imported module changed: {name}")
    data = (ARTIFACT / protocol["inputs"]["robustness_csv"]).read_bytes()
    check(hashlib.sha256(data).hexdigest() == protocol["inputs"]["robustness_csv_sha256"] == summary["robustness_csv_sha256"], "robustness.csv hash")
    dense_rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    dense = {(r["scheme"], r["attack"], r["severity"], r["task"], r["language"], int(r["payload_index"])): r for r in dense_rows}
    check(len(dense) == len(dense_rows) == 76032, "robustness.csv inventory")
    check(summary.get("new_program_executions") == 0, "no program executions")
    if not FAILURES:
        verify_a(res, protocol, dense_rows, summary)
    if not FAILURES:
        verify_b(res, protocol, dense, summary, args.require_node)
    if FAILURES:
        print(f"FAIL: {len(FAILURES)} mismatches")
        return 1
    print("PASS" + (f" (with {len(SKIPPED)} SKIPPED check: {SKIPPED[0]})" if SKIPPED else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
