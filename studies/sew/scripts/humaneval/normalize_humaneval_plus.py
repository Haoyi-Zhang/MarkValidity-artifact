"""Export the enhanced finite contract with exact per-task identities and logs."""
import argparse
import collections
import gzip
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def identity(value):
    return sha(canonical(value))


def read_jsonl_gzip(path):
    with gzip.open(path, "rt") as source:
        return [json.loads(line) for line in source if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    for name in ("data", "plus-data", "candidate-run", "enhanced-run", "runner", "controls", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=False)
    for name in ("sources", "contracts", "records"):
        (out / name).mkdir()
    dataset_sha = sha(args.data.read_bytes())
    plus_sha = sha(args.plus_data.read_bytes())
    tasks = read_jsonl_gzip(args.data)
    plus = {t["task_id"]: t for t in read_jsonl_gzip(args.plus_data)}
    producer_rows = json.loads((args.enhanced_run / "rows.json").read_text())
    producer_by_id = {r["task_id"]: r for r in producer_rows}
    spec = json.loads((args.enhanced_run / "specification.json").read_text())
    source_rows = {r["task_id"]: r for r in json.loads((args.candidate_run / "rows.json").read_text())
                   if r["key_id"] == "upstream_default" and r.get("variant", "stock") == "stock"}
    assert len(tasks) == len(plus) == len(producer_by_id) == len(producer_rows) == len(source_rows) == 164
    assert {t["task_id"] for t in tasks} == plus.keys() == producer_by_id.keys() == source_rows.keys()
    assert dataset_sha == spec["dataset_sha256"] and plus_sha == spec["plus_dataset_sha256"]
    observer_sha = sha(args.runner.read_bytes())
    assert observer_sha == spec["native_worker_sha256"]
    assert spec["python"] == platform.python_version() and spec["platform"] == platform.platform()
    rows = []
    totals = collections.Counter()
    for task in tasks:
        task_id = task["task_id"]
        original = producer_by_id[task_id]
        source_record = source_rows[task_id]
        reference = (task["prompt"] + task["canonical_solution"]).encode()
        candidate = (args.candidate_run / source_record.get("candidate_path", source_record.get("source_path"))).read_bytes()
        assert sha(reference) == original["reference_sha256"] == source_record["reference_sha256"]
        assert sha(candidate) == original["candidate_sha256"] == source_record["candidate_sha256"]
        inputs = {name: plus[task_id][name] for name in ("base_input", "plus_input")}
        count = sum(len(v) for v in inputs.values())
        contract = {
            "schema": "markvalidity-human-eval-expanded-input-contract-v2", "dataset": "HumanEval+ input tuples on original HumanEval source",
            "task_id": task_id, "reference_sha256": sha(reference), "entry_point": task["entry_point"],
            "original_dataset_sha256": dataset_sha, "expanded_input_dataset_sha256": plus_sha,
            "inputs": inputs, "input_materialization": "Python standard-library json decoding; positional argument tuples copied independently for each invocation.",
            "relation": "Exact typed return or invocation-exception envelope on every declared input; matching reference exceptions count as equal observations, not as task-correctness evidence.",
            "additional_observations": "Argument poststate and separate stdout/stderr equality, reported independently of the return relation.",
            "observer_sha256": observer_sha, "observer_representation": "Builtin value trees; integer hexadecimal, float.hex, type tags, ordered dictionary entries and canonical set members.",
            "observer_boundary": "Only entry_point(*args) exceptions are program outcomes. Initialization, copying, encoding, resource, and missing-record events are unavailable.",
            "identity_scope": "No heap-object identity, alias graph, arbitrary external side effects, or official EvalPlus special oracle.",
            "python": spec["python"], "platform": spec["platform"], "python_build": sys.version,
            "interpreter_executable_sha256": sha(Path(sys.executable).read_bytes()),
            "flags": ["-B", "-S"], "PYTHONHASHSEED": "0", "random_seed": 0,
            "random_seed_schedule": "Reset independently before every source initialization and entry-point invocation.",
            "namespace_schedule": "Fresh module namespace for every input and source; one task-pair worker process.",
            "working_directory": "Fresh empty temporary directory", "inherited_PYTHONPATH": False,
            "per_invocation_wall_seconds": .5, "worker_cpu_seconds": math.ceil(10 + count * 1.02),
            "worker_wall_seconds": math.ceil(15 + count * 1.02), "address_space_bytes": 1073741824,
        }
        contract_sha = identity(contract)
        (out / "contracts" / (contract_sha + ".json")).write_bytes(canonical(contract) + b"\n")
        for source in (reference, candidate):
            path = out / "sources" / (sha(source) + ".py")
            if not path.exists():
                path.write_bytes(source)
        log = args.enhanced_run / original["observations_file"]
        assert sha(log.read_bytes()) == original["observations_sha256"]
        records = read_jsonl_gzip(log)
        pairs = [r for r in records if r["kind"] == "pair"]
        expected = {(split, index) for split, values in inputs.items() for index in range(len(values))}
        actual = [(r["split"], r["index"]) for r in pairs]
        assert len(actual) == len(set(actual)) and set(actual) <= expected
        mismatch_count = 0
        unavailable_count = 0
        post_mismatches = 0
        stream_mismatches = 0
        for record in pairs:
            left, right = record["reference"], record["candidate"]
            if left["status"] == right["status"] == "observed":
                equal = left["outcome"] == right["outcome"]
                post_equal = left["post_arguments"] == right["post_arguments"]
                stream_equal = (left["stdout"], left["stderr"]) == (right["stdout"], right["stderr"])
            else:
                equal = post_equal = stream_equal = None
            assert record["return_equal"] is equal
            assert record["post_arguments_equal"] is post_equal
            assert record["streams_equal"] is stream_equal
            mismatch_count += equal is False
            unavailable_count += equal is None
            post_mismatches += post_equal is False
            stream_mismatches += stream_equal is False
        missing_count = len(expected - set(actual))
        label = "contradicted" if mismatch_count else "unavailable" if unavailable_count or missing_count else "supported"
        assert label == original["label"]
        assert count == original["expected_pairs"] and len(pairs) == original["recorded_pairs"]
        assert mismatch_count == original["return_mismatches"] and unavailable_count == original["unavailable_pairs"]
        assert missing_count == original["missing_pairs"] and post_mismatches == original["post_argument_mismatches"]
        assert stream_mismatches == original["stream_mismatches"]
        relative = "records/" + log.name
        shutil.copyfile(log, out / relative)
        row = {
            "dataset": "HumanEval-expanded-inputs", "task_id": task_id, "variant": "stock", "key_id": "upstream_default", "key_hex": "76" * 16,
            "reference_sha256": sha(reference), "candidate_sha256": sha(candidate), "contract_sha256": contract_sha,
            "source_contract_sha256": identity({"reference_sha256": sha(reference), "candidate_sha256": sha(candidate), "contract_sha256": contract_sha}),
            "source_path": "sources/" + sha(candidate) + ".py", "reference_source_path": "sources/" + sha(reference) + ".py",
            "detected": original["detected"], "validity_label": label,
            "suite_cost": 1, "candidate_suite_executions": 1,
            "declared_input_pairs": count, "recorded_input_pairs": len(pairs), "missing_input_pairs": missing_count,
            "unavailable_input_pairs": unavailable_count, "comparable_input_pairs": len(pairs) - unavailable_count,
            "return_mismatches": mismatch_count, "post_argument_mismatches": post_mismatches, "stream_mismatches": stream_mismatches,
            "observation_path": relative, "observation_sha256": original["observations_sha256"],
            "process": original["process"], "worker_summaries": original["worker_summaries"],
            "reference_exceptions_policy": "Equal exception envelopes are finite observational agreement; no task-correctness or watermark-failure claim follows.",
        }
        rows.append(row)
        totals[label] += 1
    for filename in ("specification.json", "summary.json", "observation-audit.json"):
        source_file = args.enhanced_run / filename
        if filename == "observation-audit.json" and not source_file.exists():
            continue  # Optional independent audit; a fresh producer need not contain it.
        shutil.copyfile(source_file, out / ("producer-" + filename))
    shutil.copyfile(args.runner, out / "native_pairs_v2.py")
    shutil.copyfile(args.controls, out / "observer-controls.json")
    (out / "rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    summary = {
        "tasks": len(rows), "labels": dict(totals), "declared_input_pairs": sum(r["declared_input_pairs"] for r in rows),
        "recorded_input_pairs": sum(r["recorded_input_pairs"] for r in rows), "comparable_input_pairs": sum(r["comparable_input_pairs"] for r in rows),
        "unavailable_input_pairs": sum(r["unavailable_input_pairs"] for r in rows), "missing_input_pairs": sum(r["missing_input_pairs"] for r in rows),
        "return_mismatches": sum(r["return_mismatches"] for r in rows), "post_argument_mismatches": sum(r["post_argument_mismatches"] for r in rows),
        "stream_mismatches": sum(r["stream_mismatches"] for r in rows), "detected": sum(r["detected"] for r in rows),
        "joint_numerator_lower": sum(r["detected"] and r["validity_label"] == "supported" for r in rows),
        "joint_numerator_upper": sum(r["detected"] and r["validity_label"] != "contradicted" for r in rows), "joint_denominator": len(rows),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "specification.json").write_text(json.dumps({
        "schema": "markvalidity-normalized-enhanced-humaneval-v2", "data_sha256": dataset_sha, "plus_data_sha256": plus_sha,
        "observer_sha256": observer_sha, "normalizer_sha256": sha(Path(__file__).read_bytes()),
        "contract_identity": "SHA-256 of UTF-8 JSON with ensure_ascii=False, sort_keys=True, separators=(',', ':'), including the actual input lists.",
        "source_contract_identity": "SHA-256 of the same canonical JSON containing reference_sha256, candidate_sha256, and contract_sha256.",
        "selection": "All 164 tasks and every input tuple in the full frozen v0.1.10 asset; all unknown outcomes retained.",
        "primary_study_separation": "This is a distinct expanded-input contract. It is never pooled with the original-suite four-factor labels.",
        "verification": "Every retained pair record was reopened; exact outcome, poststate, and stream equalities and every task label were independently reconstructed.",
    }, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
