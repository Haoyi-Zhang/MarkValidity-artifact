"""Part A: carrier comparison at matched realized effort (reviewer R2).

Uses only the retained robustness.csv rows; E3 (attempted operations) is
recomputed from the declared site-selection rule. No program is executed.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import csv
import math

from common import (ATTACKS, FAMILIES, SCHEMES, Rule, predicted_state, load_protocol)

MEASURES = ("nominal_severity", "E1_realized_edits", "E2_requested_operations_bin", "E3_attempted_operations")
PAIRS = (("lexical", "structural"), ("lexical", "hybrid"), ("structural", "hybrid"))


def fmt(value: Fraction | None, places: int = 12) -> str:
    """Half-even decimal rounding, as run_all.format_fraction."""
    if value is None:
        return ""
    from decimal import Decimal, ROUND_HALF_EVEN, localcontext
    with localcontext() as context:
        context.prec = 80
        d = Decimal(value.numerator) / Decimal(value.denominator)
        return format(d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN), f".{places}f")


def e2_bin(requested: str) -> int:
    return int(math.floor(float(requested) / 2.0)) * 2


def effort_records(rows: list[dict], rule: Rule) -> list[dict]:
    records = []
    for row in rows:
        expected, observed, present, attempted = predicted_state(
            rule, row["scheme"], row["attack"], row["severity"], row["task"], row["language"], int(row["payload_index"]))
        changes = sum(1 for k in range(24) if present[k] and observed[k] != expected[k])
        deletions = sum(1 for k in range(24) if not present[k])
        survivors = 24 - deletions
        matches = survivors - changes
        if (changes, deletions, survivors, matches) != (int(row["realized_bit_changes"]), int(row["deletions"]),
                                                        int(row["surviving_sites"]), int(row["match_count"])):
            raise SystemExit("declared rule does not reproduce retained row: " + repr(row))
        records.append({
            "scheme": row["scheme"], "attack": row["attack"], "severity": row["severity"], "task": row["task"],
            "language": row["language"], "payload_index": row["payload_index"],
            "realized_bit_changes": changes, "deletions": deletions,
            "E1_realized_edits": changes + deletions,
            "requested_operations": row["requested_operations"],
            "E2_requested_operations_bin": e2_bin(row["requested_operations"]),
            "E3_attempted_operations": attempted,
            "detected": int(row["detected"]),
        })
    return records


def effort_value(record: dict, measure: str):
    if measure == "nominal_severity":
        return record["severity"]
    return int(record[measure])


def analyze(records: list[dict], protocol: dict, nominal_mixture_rows: list[dict], nominal_family_rows: list[dict]):
    spec = protocol["A_matched_effort"]
    n_min = 30
    weights = {
        "balanced": {"rename": "0.2", "normalize": "0.2", "random_flip": "0.2", "strip": "0.2", "mixed": "0.2"},
        "rename-heavy": {"rename": "0.54", "normalize": "0", "random_flip": "0.24", "strip": "0.22", "mixed": "0"},
        "structure-heavy": {"rename": "0", "normalize": "0.54", "random_flip": "0.24", "strip": "0.22", "mixed": "0"},
    }
    from covewm.benchmark import MIXTURE_WEIGHTS
    for m, w in weights.items():
        for a, v in w.items():
            if Fraction(v) != Fraction(str(MIXTURE_WEIGHTS[m][a])):
                raise SystemExit("mixture weights differ from benchmark")
    # counts[measure][attack][scheme][value] = [n, detected]
    counts = {m: {a: {s: defaultdict(lambda: [0, 0]) for s in SCHEMES} for a in ATTACKS} for m in MEASURES}
    for r in records:
        for m in MEASURES:
            c = counts[m][r["attack"]][r["scheme"]][effort_value(r, m)]
            c[0] += 1
            c[1] += r["detected"]

    def sort_values(m, values):
        return sorted(values, key=(lambda v: float(v)) if m == "nominal_severity" else int)

    curves, rankings = [], []
    cell = {}  # (m, rel, a, s, b) -> (n, d)
    for m in MEASURES:
        for a in ATTACKS:
            domain = sort_values(m, set().union(*(counts[m][a][s].keys() for s in SCHEMES)))
            for rel in ("eq", "le"):
                if m == "nominal_severity" and rel == "le":
                    continue
                for s in SCHEMES:
                    cum_n = cum_d = 0
                    for b in domain:
                        n, d = counts[m][a][s].get(b, [0, 0])
                        cum_n += n
                        cum_d += d
                        nn, dd = (n, d) if rel == "eq" else (cum_n, cum_d)
                        cell[(m, rel, a, s, b)] = (nn, dd)
                        rate = Fraction(dd, nn) if nn else None
                        curves.append({"effort_measure": m, "relation": rel, "attack": a, "carrier": s, "effort": b,
                                       "n": nn, "detected": dd, "rate": "" if rate is None else f"{float(rate):.6f}",
                                       "rate_exact": "" if rate is None else f"{rate.numerator}/{rate.denominator}"})
                for b in domain:
                    entry = {"effort_measure": m, "relation": rel, "attack": a, "effort": b}
                    supported = []
                    for s in SCHEMES:
                        nn, dd = cell[(m, rel, a, s, b)]
                        entry[f"n_{s}"] = nn
                        entry[f"rate_{s}"] = "" if not nn else fmt(Fraction(dd, nn), 6)
                        if nn >= n_min:
                            supported.append(s)
                    entry["supported"] = ";".join(supported)
                    entry["common_support"] = int(len(supported) == 3)
                    if supported:
                        rates = {s: Fraction(cell[(m, rel, a, s, b)][1], cell[(m, rel, a, s, b)][0]) for s in supported}
                        top = max(rates.values())
                        ws = [s for s in supported if rates[s] == top]
                        entry["winner_set"] = ";".join(ws)
                        entry["all_supported_equal"] = int(len(set(rates.values())) == 1)
                    else:
                        entry["winner_set"] = ""
                        entry["all_supported_equal"] = ""
                    rankings.append(entry)

    # Direct standardization over common support (relation eq).
    family_scores, family_lookup = [], {}
    for m in MEASURES:
        for a in ATTACKS:
            domain = sort_values(m, set().union(*(counts[m][a][s].keys() for s in SCHEMES)))
            groups = [("all", SCHEMES)] + [("pair:" + "-".join(p), p) for p in PAIRS]
            for gname, members in groups:
                support = [b for b in domain if all(cell[(m, "eq", a, s, b)][0] >= n_min for s in members)]
                total = sum(cell[(m, "eq", a, s, b)][0] for b in support for s in members)
                for s in members:
                    fam_n = sum(cell[(m, "eq", a, s, b)][0] for b in domain)
                    cov_n = sum(cell[(m, "eq", a, s, b)][0] for b in support)
                    if support:
                        score = sum((Fraction(sum(cell[(m, "eq", a, t, b)][0] for t in members), total)
                                     * Fraction(cell[(m, "eq", a, s, b)][1], cell[(m, "eq", a, s, b)][0])
                                     for b in support), Fraction(0))
                    else:
                        score = None
                    family_lookup[(m, gname, a, s)] = score
                    family_scores.append({"effort_measure": m, "comparison": gname, "attack": a, "carrier": s,
                                          "common_support_values": ";".join(str(b) for b in support),
                                          "n_common_support_values": len(support),
                                          "carrier_rows": fam_n, "rows_in_common_support": cov_n,
                                          "coverage": fmt(Fraction(cov_n, fam_n), 6) if fam_n else "",
                                          "standardized_rate": fmt(score)})
    groups_members = {"all": SCHEMES, **{"pair:" + "-".join(p): p for p in PAIRS}}
    for row in family_scores:
        members = groups_members[row["comparison"]]
        vals = {s: family_lookup[(row["effort_measure"], row["comparison"], row["attack"], s)] for s in members}
        if all(v is not None for v in vals.values()):
            top = max(vals.values())
            row["winner_set"] = ";".join(s for s in members if vals[s] == top)
        else:
            row["winner_set"] = ""

    mixture_scores, mixture_summary = [], {}
    for m in MEASURES:
        mixture_summary[m] = {}
        for mix, w in weights.items():
            scores = {}
            for s in SCHEMES:
                total = Fraction(0)
                for a in FAMILIES:
                    weight = Fraction(w[a])
                    if weight == 0:
                        continue
                    v = family_lookup[(m, "all", a, s)]
                    if v is None:
                        total = None
                        break
                    total += weight * v
                scores[s] = total
            if all(v is not None for v in scores.values()):
                top = max(scores.values())
                winners = [s for s in SCHEMES if scores[s] == top]
            else:
                winners = []
            undefined = [a for a in FAMILIES if Fraction(w[a]) and family_lookup[(m, "all", a, SCHEMES[0])] is None]
            for s in SCHEMES:
                mixture_scores.append({"effort_measure": m, "mixture": mix, "carrier": s, "score": fmt(scores[s]),
                                       "winner_set": ";".join(winners),
                                       "undefined_families": ";".join(undefined)})
            mixture_summary[m][mix] = {"scores": {s: fmt(scores[s]) for s in SCHEMES}, "winner_set": winners,
                                       "unique_winner": winners[0] if len(winners) == 1 else None,
                                       "undefined_families": undefined}

    # Nominal comparator must reproduce the retained derived tables.
    retained_family = {(r["scheme"], r["attack"]): r["mean_detection_rate"] for r in nominal_family_rows}
    for s in SCHEMES:
        for a in ATTACKS:
            if fmt(family_lookup[("nominal_severity", "all", a, s)]) != retained_family[(s, a)]:
                raise SystemExit(f"nominal family mean differs from retained table: {s} {a}")
    retained_mix = {(r["mixture"], r["scheme"]): r["score"] for r in nominal_mixture_rows}
    for mix in weights:
        for s in SCHEMES:
            if mixture_summary["nominal_severity"][mix]["scores"][s] != retained_mix[(mix, s)]:
                raise SystemExit(f"nominal mixture score differs from retained table: {mix} {s}")

    # Carrier invariance: detected is a function of (realized_bit_changes, deletions).
    by_pair = defaultdict(set)
    for r in records:
        by_pair[(r["realized_bit_changes"], r["deletions"])].add(r["detected"])
    invariance = {"distinct_change_deletion_pairs": len(by_pair),
                  "pairs_with_conflicting_decisions": sum(len(v) > 1 for v in by_pair.values()),
                  "detecting_pairs": sorted([list(k) for k, v in by_pair.items() if v == {1}])}
    equal_cells = {}
    for m in MEASURES[1:]:
        equal_cells[m] = {}
        for a in FAMILIES:
            cs = [r for r in rankings if r["effort_measure"] == m and r["relation"] == "eq" and r["attack"] == a and r["common_support"] == 1]
            equal_cells[m][a] = {"common_support_cells": len(cs),
                                 "cells_all_three_rates_equal": sum(r["all_supported_equal"] == 1 for r in cs),
                                 "cells_unique_winner": {s: sum(r["winner_set"] == s for r in cs) for s in SCHEMES}}
    nominal = mixture_summary["nominal_severity"]
    decisions = {}
    for m in MEASURES[1:]:
        ms = mixture_summary[m]
        persists = ms["rename-heavy"]["unique_winner"] == "structural" and ms["structure-heavy"]["unique_winner"] == "lexical"
        decisions[m] = {"reversal_persists": persists,
                        "winners": {mix: ms[mix]["winner_set"] for mix in weights},
                        "undefined_families": {mix: ms[mix]["undefined_families"] for mix in weights}}
    family_winners = {m: {a: next(r["winner_set"] for r in family_scores if r["effort_measure"] == m and r["comparison"] == "all" and r["attack"] == a)
                          for a in FAMILIES} for m in MEASURES}
    summary = {
        "rows": len(records),
        "n_min": n_min,
        "nominal_winners": {mix: nominal[mix]["winner_set"] for mix in weights},
        "nominal_reversal_present": nominal["rename-heavy"]["unique_winner"] == "structural" and nominal["structure-heavy"]["unique_winner"] == "lexical",
        "reversal_decision": decisions,
        "primary_measure": "E1_realized_edits",
        "reversal_persists_at_matched_realized_edits": decisions["E1_realized_edits"]["reversal_persists"],
        "family_winner_sets": family_winners,
        "mixture_scores": mixture_summary,
        "detection_function_of_changes_and_deletions": invariance,
        "common_support_equal_rate_cells": equal_cells,
        "rule_reproduces_all_rows": True,
    }
    return curves, rankings, family_scores, mixture_scores, summary
