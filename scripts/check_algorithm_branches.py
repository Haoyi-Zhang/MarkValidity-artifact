#!/usr/bin/env python3
"""Re-run the fourteen finite branch checks from the round-4 manuscript review.

Run with ``python -B -S artifact/scripts/check_algorithm_branches.py`` from the
delivery root, or invoke this file from any working directory.  The checker uses
only the standard library, imports the delivered analysis module by its path,
prints one JSON report to stdout, and writes no files.  These finite coefficient
examples check algorithm branches; they are not corpus or program executions.

The original check was executed inline.  Its exact models, disclosure sequence,
invalid-query inputs, expected outcomes, and fourteen case names were recovered
from that execution.  This portable form adds explicit input vectors and source
digests; it does not retroactively claim that a script file existed at that time.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


sys.dont_write_bytecode = True

ANALYSIS_RELATIVE = "external-studies/sew_natural/analysis/natural_analysis.py"
ORIGINAL_ANALYSIS_SHA256 = (
    "bcf19e3111d68b43fbb144cff23ad844f7a9aeb9d9af18aff0f24a69e98e3551"
)

INPUT_VECTORS = {
    "models": {
        "identical": {
            "left": {"g": [1, 1]},
            "right": {"g": [1, 1]},
            "denominator": 1,
        },
        "shared_remainder": {
            "left": {"common": [0, 5], "left-only": [4, 5]},
            "right": {"common": [0, 5], "right-only": [3, 5]},
            "denominator": 10,
        },
    },
    "experiments": [
        {
            "id": "identical_then_supported",
            "model": "identical",
            "initial_labels": [],
            "reveals_after_initial_snapshot": [["g", True]],
            "check_numbers": [1, 2, 3, 4],
        },
        {
            "id": "all_invalid",
            "model": "identical",
            "initial_labels": [],
            "reveals": [["g", False]],
            "check_numbers": [5],
        },
        {
            "id": "common_remainder",
            "model": "shared_remainder",
            "initial_labels": [],
            "reveals": [["left-only", True], ["right-only", True]],
            "check_numbers": [6, 7],
        },
        {
            "id": "unavailable_difference",
            "model": "shared_remainder",
            "initial_labels": [],
            "policy": "conditional_differences_first",
            "oracle_responses_in_query_order": [None, True, None],
            "invalid_reveals_after_schedule": [
                ["left-only", True], ["not-a-group", True]
            ],
            "check_numbers": [8, 9, 10, 11, 12, 13],
        },
        {
            "id": "integer_label",
            "model": "identical",
            "initial_labels": [],
            "invalid_reveals": [["g", 1]],
            "check_numbers": [14],
        },
    ],
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_analysis(path):
    spec = importlib.util.spec_from_file_location("review_natural_api", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the delivered analysis module")
    api = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = api
    spec.loader.exec_module(api)
    return api


def check_branches(api):
    checks = []

    def state(model_name):
        model = INPUT_VECTORS["models"][model_name]
        return api.PairState(model["left"], model["right"], model["denominator"])

    def record(name, expected, actual):
        checks.append({
            "case": name,
            "expected": expected,
            "actual": actual,
            "status": "PASS" if actual == expected else "FAIL",
        })

    s = state("identical")
    snap = s.snapshot()
    record("identical unresolved joint is a tie", "tie",
           snap["coupled_J"]["decision"])
    record("identical unresolved conditional retains undefinedness", "undefined_possible",
           snap["coupled_C"]["decision"])
    record("identical conditional ties only on defined subset before support", "tie",
           snap["coupled_C"]["relation_on_defined"])
    s.reveal("g", True)
    record("identical supported conditional certifies tie", "tie",
           s.snapshot()["coupled_C"]["decision"])

    s = state("identical")
    s.reveal("g", False)
    record("all-invalid conditional stays undefined",
           "undefined_everywhere_for_at_least_one_side",
           s.snapshot()["coupled_C"]["decision"])

    s = state("shared_remainder")
    s.reveal("left-only", True)
    s.reveal("right-only", True)
    record("common-remainder strict certificate survives overlapping separate intervals",
           ("left_strict", "unresolved"),
           (s.snapshot()["coupled_C"]["decision"],
            s.snapshot()["independent_C"]["decision"]))
    record("common group need not be attempted", False, "common" in s.attempted)

    s = state("shared_remainder")
    p = api.AuditPolicy("conditional_differences_first", s)
    queries = []
    for label in (None, True, None):
        group = p.next_group(s)
        queries.append(group)
        s.reveal(group, label)
    record("unavailable difference does not become resolved", True,
           "left-only" in s.different and "left-only" not in s.admitted)
    record("query attempts include unavailable responses", 3, len(s.attempted))
    record("unknown differences fall back to remaining identity order",
           ["left-only", "right-only", "common"], queries)
    record("exhausted policy never reissues unavailable group", None, p.next_group(s))
    for group, label, case in [
        ("left-only", True, "duplicate query rejected"),
        ("not-a-group", True, "unknown identity rejected"),
    ]:
        try:
            s.reveal(group, label)
        except ValueError:
            actual = "rejected"
        else:
            actual = "accepted"
        record(case, "rejected", actual)

    s = state("identical")
    try:
        s.reveal("g", 1)
    except ValueError:
        actual = "rejected"
    else:
        actual = "accepted"
    record("noncanonical integer label rejected by PairState", "rejected", actual)
    return checks


def main():
    checker_path = Path(__file__).resolve()
    artifact_root = checker_path.parents[1]
    analysis_path = artifact_root / ANALYSIS_RELATIVE
    analysis_sha256 = sha256(analysis_path)
    report = {
        "schema": "markvalidity-algorithm-branch-checks-v1",
        "scope": (
            "Read-only branch verification on finite Boolean coefficient examples; "
            "no corpus or program-execution claims."
        ),
        "origin": {
            "kind": "portable_recovery_of_original_inline_check",
            "description": (
                "Recovered the exact original input vectors, disclosure sequence, "
                "invalid-query inputs, expected results, and fourteen case names "
                "from the round-4 inline execution. This run is a fresh recheck; "
                "the earlier QA receipt is not modified."
            ),
            "original_analysis_sha256": ORIGINAL_ANALYSIS_SHA256,
            "analysis_matches_original_execution": (
                analysis_sha256 == ORIGINAL_ANALYSIS_SHA256
            ),
        },
        "source_sha256": {
            checker_path.relative_to(artifact_root).as_posix(): sha256(checker_path),
            ANALYSIS_RELATIVE: analysis_sha256,
        },
        "input_vectors": INPUT_VECTORS,
    }
    try:
        report["checks"] = check_branches(load_analysis(analysis_path))
        report["checked_count"] = len(report["checks"])
        report["status"] = (
            "PASS" if report["checked_count"] == 14
            and all(c["status"] == "PASS" for c in report["checks"])
            else "FAIL"
        )
    except Exception as exc:
        report["status"] = "ERROR"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
