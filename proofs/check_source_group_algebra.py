"""Independently reconstruct finite source-group scores with exact arithmetic.

This reads admitted source rows. It does not import the producer, its grouping
implementation, or its verifier, and it does not re-attest source execution.
The concrete risk checked is a denominator or shared-label error in the new
source-joint mixture and pairwise claims.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path


def read_csv(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def group_key(row):
    return tuple(row[field] for field in
                 ("task", "language", "receiver_reference_sha256",
                  "semantic_contract_id", "source_sha256"))


def run(source):
    source = Path(source)
    rows = read_csv(source / "rows.csv.gz")
    if len(rows) != 76032:
        raise ValueError("unexpected source universe")
    schemes = ("lexical", "structural", "hybrid")
    languages = ("python", "javascript")
    labels, counts = {}, defaultdict(int)
    for row in rows:
        status = row["validity_status"]
        if status not in {"valid", "invalid", "unknown"}:
            raise ValueError("unexpected validity label")
        value = {"valid": True, "invalid": False, "unknown": None}[status]
        key = group_key(row)
        if key in labels and labels[key] is not None and value is not None and labels[key] != value:
            raise ValueError("inconsistent source validity")
        if key not in labels or value is not None:
            labels[key] = value
        if row["detected"] not in {"0", "1"}:
            raise ValueError("nonbinary detection")
        counts[(row["language"], row["scheme"], row["attack"], row["severity"])] += 1
    if len(counts) != 396 or set(counts.values()) != {192}:
        raise ValueError("incomplete source strata")
    attacks = ("rename", "normalize", "random_flip", "strip", "mixed")
    weights = {
        "balanced": dict.fromkeys(attacks, F(1, 5)),
        "rename-heavy": dict(zip(attacks, (F(54,100), F(0), F(24,100), F(22,100), F(0)))),
        "structure-heavy": dict(zip(attacks, (F(0), F(54,100), F(24,100), F(22,100), F(0)))),
    }
    score_file = read_csv(source / "mixture_scores.csv")
    gap_file = read_csv(source / "pairwise_source_bounds.csv")
    score_lookup = {(r["language"], r["mixture"], r["scheme"]): r for r in score_file}
    gap_lookup = {(r["language"], r["mixture"], r["left"], r["right"]): r for r in gap_file}
    verified_scores, verified_gaps, witnesses = 0, 0, []
    for scope in (*languages, "combined"):
        scoped = rows if scope == "combined" else [r for r in rows if r["language"] == scope]
        stratum_size = 384 if scope == "combined" else 192
        for mixture, family_weights in weights.items():
            coefficients = {s: defaultdict(F) for s in schemes}
            total_weights = defaultdict(F)
            for row in scoped:
                weight = family_weights.get(row["attack"], F(0)) / (11 * stratum_size)
                total_weights[row["scheme"]] += weight
                coefficients[row["scheme"]][group_key(row)] += weight * int(row["detected"])
            if any(total_weights[s] != 1 for s in schemes):
                raise ValueError("weights do not sum to one per carrier")
            for scheme, values in coefficients.items():
                low = sum((c for g,c in values.items() if labels[g] is True), F(0))
                high = sum((c for g,c in values.items() if labels[g] is not False), F(0))
                record = score_lookup[(scope, mixture, scheme)]
                if (low, high) != (F(record["joint_lower_exact"]), F(record["joint_upper_exact"])):
                    raise ValueError("score mismatch")
                verified_scores += 1
            for a,b in (("lexical","structural"), ("lexical","hybrid"), ("structural","hybrid")):
                groups = set(coefficients[a]) | set(coefficients[b])
                low = high = F(0)
                for g in groups:
                    difference = coefficients[a].get(g, F(0)) - coefficients[b].get(g, F(0))
                    if labels[g] is None:
                        low += min(F(0), difference)
                        high += max(F(0), difference)
                    elif labels[g]:
                        low += difference
                        high += difference
                record = gap_lookup[(scope, mixture, a, b)]
                if (low, high) != (F(record["lower_exact"]), F(record["upper_exact"])):
                    raise ValueError("pairwise gap mismatch")
                verified_gaps += 1
                if scope == "combined":
                    witnesses.append(dict(mixture=mixture,left=a,right=b,
                                          lower=str(low),upper=str(high)))
    if verified_scores != 27 or verified_gaps != 27:
        raise ValueError("incomplete derived comparison")
    return dict(status="PASS", source_rows=len(rows), source_groups=len(labels),
                exactly_reconstructed_scores=verified_scores,
                exactly_reconstructed_pairwise_bounds=verified_gaps,
                source_program_executions=0,
                scope="Algebra on admitted source rows, not execution attestation or new trials",
                combined_gap_witnesses=witnesses,
                input_sha256={name:hashlib.sha256((source/name).read_bytes()).hexdigest()
                              for name in ("rows.csv.gz","mixture_scores.csv","pairwise_source_bounds.csv")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
        default=Path(__file__).resolve().parents[1]/"results/revision-source-joint")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.source)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered)
