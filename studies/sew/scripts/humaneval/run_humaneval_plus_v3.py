"""All frozen EvalPlus inputs on original HumanEval reference vs stock SEW.

This checks a finite exact observational relation, not official EvalPlus task
scoring.  All tasks and inputs remain in the ledger, including unavailable ones.
"""
import argparse
import collections
import datetime
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time




def sha(data):
    return hashlib.sha256(data).hexdigest()


def execute(request, destination, runner):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONOPTIMIZE", None)
    env["PYTHONHASHSEED"] = "0"
    pair_count = len(request["base_input"]) + len(request["plus_input"])
    seconds = math.ceil(15 + pair_count * (2 * request["invocation_seconds"] + .02))
    process_status = {"wall_seconds_limit": seconds}
    observations = []
    with tempfile.TemporaryDirectory(prefix="markvalidity-he-plus-v3-") as temporary:
        raw = Path(temporary) / "pair-log.jsonl"
        with raw.open("w") as output:
            child = subprocess.Popen([sys.executable, "-B", "-S", str(runner)],
                                     cwd=temporary, env=env, stdin=subprocess.PIPE, stdout=output,
                                     stderr=subprocess.PIPE, text=True)
            try:
                _, stderr = child.communicate(json.dumps(request), timeout=seconds)
                process_status.update({"status": "finished", "returncode": child.returncode, "stderr": stderr})
            except subprocess.TimeoutExpired:
                child.kill()
                _, stderr = child.communicate()
                process_status.update({"status": "wall_timeout", "returncode": child.returncode, "stderr": stderr})
        # Copy even a truncated line into raw compressed evidence.  Parse only
        # complete JSON records and expose their count instead of dropping them.
        with raw.open("rb") as source, destination.open("wb") as target:
            with gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as zipped:
                for line in source:
                    zipped.write(line)
        parse_failures = []
        summaries = []
        with raw.open() as source:
            for lineno, line in enumerate(source, 1):
                try:
                    record = json.loads(line)
                except ValueError as exc:
                    parse_failures.append({"line": lineno, "error": str(exc)})
                    continue
                if record.get("kind") == "pair":
                    observations.append(record)
                else:
                    summaries.append(record)
    return observations, process_status, summaries, parse_failures


def main():
    parser = argparse.ArgumentParser()
    for argument in ("data", "plus-data", "candidate-run", "runner", "out"):
        parser.add_argument("--" + argument, type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=False)
    original_data = args.data.resolve()
    plus_data = args.plus_data.resolve()
    candidate_directory = args.candidate_run.resolve()
    runner = args.runner.resolve()
    assert sha(original_data.read_bytes()) == "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"
    assert sha(plus_data.read_bytes()) == "272720b90ac375502c8ed23cd791c2a93dfb22a911641a494da74a426c09f101"
    original_tasks = [json.loads(x) for x in gzip.decompress(original_data.read_bytes()).decode().splitlines()]
    plus_tasks = [json.loads(x) for x in gzip.decompress(plus_data.read_bytes()).decode().splitlines()]
    originals = {t["task_id"]: t for t in original_tasks}
    plus = {t["task_id"]: t for t in plus_tasks}
    stock = {r["task_id"]: r for r in json.loads((candidate_directory / "rows.json").read_text())
             if r["key_id"] == "upstream_default" and r.get("variant", "stock") == "stock"}
    assert len(originals) == len(plus) == len(stock) == 164
    assert set(originals) == set(plus) == set(stock)
    contract = {
        "reference_source": "Exact original HumanEval prompt + canonical_solution, not EvalPlus corrected source.",
        "input_source": "All base_input and plus_input tuples in frozen HumanEvalPlus v0.1.10, in their original order.",
        "domain": "Finite tuples from both input lists; one independent fresh module namespace per invocation.",
        "relation": "Exact typed return-or-invocation-exception envelope; matching reference exceptions are not watermark failures.",
        "additional_observations": "Argument poststate and stdout/stderr equality are reported separately.",
        "observer": "native_pairs_v3.py: builtin value trees with integer hex, float.hex, list/tuple/dict/set tags. No heap-identity/alias-graph observation.",
        "program_exception_boundary": "Only non-resource, non-interruption exceptions from entry_point(*args) form exception envelopes. Uncaught MemoryError, OSError(errno=ENOMEM), KeyboardInterrupt, initialization/copying/encoding errors, and elapsed observation guards are unavailable, including a swallowed alarm.",
        "process": "CPython -B -S, PYTHONHASHSEED=0, random.seed(0) reset per invocation, temporary cwd, no inherited PYTHONPATH.",
        "per_invocation_wall_seconds": .5,
        "memory_bytes": 1024 * 1024 * 1024,
        "worker_cpu_budget": "ceil(10 + number_of_pairs * (2 * 0.5 + 0.02)) seconds",
        "worker_wall_budget": "ceil(15 + number_of_pairs * (2 * 0.5 + 0.02)) seconds",
        "failure_retention": "Per-pair JSON lines flush immediately; partial/broken worker evidence retained and missing input indexes marked unavailable.",
        "not_claimed": "This is not official EvalPlus task-correctness scoring, population prevalence, arbitrary Python equivalence, or a security sandbox.",
    }
    contract_sha = sha(json.dumps(contract, sort_keys=True, separators=(",", ":")).encode())
    spec = {
        "schema": "markvalidity-sew-humaneval-plus-pilot-v3", "contract": contract, "contract_sha256": contract_sha,
        "dataset_sha256": sha(original_data.read_bytes()), "plus_dataset_sha256": sha(plus_data.read_bytes()),
        "tasks": [t["task_id"] for t in original_tasks], "selection": "All 164 tasks and all frozen input tuples; no exclusions.",
        "key_id": "upstream_default", "key_hex": "76" * 16,
        "python": platform.python_version(), "platform": platform.platform(),
        "candidate_producer": str(candidate_directory / "rows.json"),
        "candidate_producer_note": "Saved stock default-key sources from raw or normalized rows, without re-embedding",
        "producer_sha256": sha(Path(__file__).read_bytes()), "native_worker_sha256": sha((runner).read_bytes()),
        "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "supersedes": "Expanded observer v2 is superseded: uncaught MemoryError, OSError(errno=ENOMEM), and KeyboardInterrupt could be misclassified as program exceptions; an invocation could catch an alarm. Normal successful value encoding is unchanged.",
    }
    (out / "specification.json").write_text(json.dumps(spec, indent=2) + "\n")
    rows = []
    started = time.monotonic()
    for ordinal, task in enumerate(original_tasks, 1):
        task_id = task["task_id"]
        inputs = plus[task_id]
        source = task["prompt"] + task["canonical_solution"]
        original_record = stock[task_id]
        candidate = (candidate_directory / original_record.get("candidate_path", original_record.get("source_path"))).read_text()
        assert sha(source.encode()) == original_record["reference_sha256"]
        assert sha(candidate.encode()) == original_record["candidate_sha256"]
        file_name = task_id.replace("/", "-") + ".jsonl.gz"
        request = {"reference": source, "candidate": candidate, "entry_point": task["entry_point"],
                   "base_input": inputs["base_input"], "plus_input": inputs["plus_input"], "invocation_seconds": .5}
        records, process, worker_summaries, parse_failures = execute(request, out / file_name, runner)
        expected = {(split, index) for split in ("base_input", "plus_input") for index in range(len(inputs[split]))}
        recorded = [(r["split"], r["index"]) for r in records]
        assert len(set(recorded)) == len(recorded) and set(recorded) <= expected
        missing = sorted(expected - set(recorded))
        unavailable = sum(r["return_equal"] is None for r in records)
        mismatches = [r for r in records if r["return_equal"] is False]
        # A recorded disagreement is usable only when both sides have valid
        # observations; timeouts and reference errors remain unavailable.
        label = "contradicted" if mismatches else "unavailable" if unavailable or missing else "supported"
        outcome_counts = collections.Counter()
        for r in records:
            for side in ("reference", "candidate"):
                outcome_counts[side + ":" + r[side]["status"] + ":" + str(r[side].get("outcome", [None])[0])] += 1
        row = {
            "task_id": task_id, "key_id": "upstream_default", "reference_sha256": sha(source.encode()),
            "candidate_sha256": sha(candidate.encode()), "contract_sha256": contract_sha,
            "input_tuples_sha256": sha(json.dumps({x: inputs[x] for x in ("base_input", "plus_input")}, sort_keys=True, separators=(",", ":")).encode()),
            "detected": original_record["detected"], "expected_pairs": len(expected), "recorded_pairs": len(records),
            "missing_pairs": len(missing), "missing_indexes": missing, "unavailable_pairs": unavailable,
            "return_mismatches": len(mismatches), "post_argument_mismatches": sum(r["post_arguments_equal"] is False for r in records),
            "stream_mismatches": sum(r["streams_equal"] is False for r in records), "label": label,
            "outcome_counts": dict(outcome_counts), "process": process, "worker_summaries": worker_summaries,
            "parse_failures": parse_failures, "observations_file": file_name, "observations_sha256": sha((out / file_name).read_bytes()),
            "first_mismatch_index": [mismatches[0]["split"], mismatches[0]["index"]] if mismatches else None,
        }
        rows.append(row)
        # Checkpoint compact rows so an interruption does not discard tasks.
        (out / "rows.json").write_text(json.dumps(rows, indent=2) + "\n")
        if ordinal % 20 == 0 or label != "supported":
            print(json.dumps({"tasks_finished": ordinal, "task_id": task_id, "label": label, "unavailable_pairs": unavailable,
                              "missing_pairs": len(missing), "elapsed_seconds": round(time.monotonic() - started, 3)}), flush=True)
    joint_lower = sum(r["detected"] and r["label"] == "supported" for r in rows)
    joint_upper = sum(r["detected"] and r["label"] != "contradicted" for r in rows)
    summary = {
        "status": "COMPLETE", "tasks": len(rows), "labels": dict(collections.Counter(r["label"] for r in rows)),
        "expected_pairs": sum(r["expected_pairs"] for r in rows), "recorded_pairs": sum(r["recorded_pairs"] for r in rows),
        "missing_pairs": sum(r["missing_pairs"] for r in rows), "unavailable_pairs": sum(r["unavailable_pairs"] for r in rows),
        "return_mismatches": sum(r["return_mismatches"] for r in rows),
        "post_argument_mismatches": sum(r["post_argument_mismatches"] for r in rows),
        "stream_mismatches": sum(r["stream_mismatches"] for r in rows),
        "detected": sum(r["detected"] for r in rows), "joint_numerator_lower": joint_lower, "joint_numerator_upper": joint_upper,
        "joint_denominator": len(rows), "detected_contradictions": sum(r["detected"] and r["label"] == "contradicted" for r in rows),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "non_supported_tasks": [r["task_id"] for r in rows if r["label"] != "supported"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
