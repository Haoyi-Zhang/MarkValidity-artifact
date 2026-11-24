"""Normalize the four-factor HumanEval runs without rerunning or relabeling.

The contract identity is independent of method/key and includes the actual
suite, observer, interpreter, seed, and resource policy. Byte-identical sources
may share a label only within that identical contract. Repeated observations
are checked for semantic consistency before any source coupling is exported.
"""
import argparse
import collections
from fractions import Fraction
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import platform
import shutil
import sys

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def identity(value):
    return sha(canonical(value))


def semantic_observation(result):
    return {key: result.get(key) for key in ("status", "error", "observations", "stdout", "stderr")}


def save_compressed(path, value):
    with path.open("wb") as target:
        with gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as zipped:
            zipped.write(canonical(value) + b"\n")


def pair_summary(left_name, right_name, rows):
    left = [r for r in rows if r["variant"] == left_name]
    right = [r for r in rows if r["variant"] == right_name]
    assert len(left) == len(right)
    n = len(left)
    groups = {}
    for sign, selected in ((1, left), (-1, right)):
        for row in selected:
            group = groups.setdefault(row["source_contract_sha256"], {
                "coefficient": 0, "calls": row["candidate_function_invocations"], "validity_label": row["validity_label"],
                "task_id": row["task_id"], "candidate_sha256": row["candidate_sha256"],
            })
            assert group["calls"] == row["candidate_function_invocations"]
            assert group["validity_label"] == row["validity_label"]
            group["coefficient"] += sign * int(row["detected"])
    nonzero = [g for g in groups.values() if g["coefficient"]]
    lower = sum(min(0, g["coefficient"]) for g in nonzero)
    upper = sum(max(0, g["coefficient"]) for g in nonzero)
    complete_gap = sum(g["coefficient"] for g in groups.values() if g["validity_label"] == "supported")
    assert all(g["validity_label"] != "unavailable" for g in groups.values())
    left_by_key = {(r["task_id"], r["key_id"]): r for r in left}
    right_by_key = {(r["task_id"], r["key_id"]): r for r in right}
    assert left_by_key.keys() == right_by_key.keys()
    return {
        "left": left_name, "right": right_name, "configurations_per_variant": n,
        "unique_source_contracts": len(groups), "nonzero_gap_source_groups": len(nonzero),
        "zero_gap_source_groups": len(groups) - len(nonzero),
        "grouped_gap_interval_if_all_labels_withheld": [str(Fraction(lower, n)), str(Fraction(upper, n))],
        "grouped_width": str(Fraction(upper - lower, n)),
        "separate_score_subtraction_width": str(Fraction(sum(r["detected"] for r in left + right), n)),
        "complete_gap": str(Fraction(complete_gap, n)),
        "native_function_calls_all_source_contracts_once": sum(g["calls"] for g in groups.values()),
        "native_function_calls_nonzero_gap_groups_once": sum(g["calls"] for g in nonzero),
        "raw_row_candidate_function_invocations": sum(r["candidate_function_invocations"] for r in left + right),
        "suite_queries_all_source_contracts_once": len(groups),
        "suite_queries_nonzero_gap_groups_once": len(nonzero),
        "raw_row_suite_queries": sum(r["suite_cost"] for r in left + right),
        "coefficient_distribution": dict(collections.Counter(str(g["coefficient"]) for g in nonzero)),
        "paired_byte_identical_outputs": sum(left_by_key[k]["candidate_sha256"] == right_by_key[k]["candidate_sha256"] for k in left_by_key),
        "paired_detector_disagreements": sum(left_by_key[k]["detected"] != right_by_key[k]["detected"] for k in left_by_key),
        "scope": "Exact reconstruction from retained observations under deliberate label withholding; no new online query policy or prevalence inference is claimed.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--variant", action="append", required=True, help="NAME:RUN_DIRECTORY, relative paths resolved against pilot root")
    args = parser.parse_args()
    variants = []
    for item in args.variant:
        name, location = item.split(":", 1)
        path = Path(location)
        variants.append((name, path if path.is_absolute() else HERE / path))
    assert len({name for name, _ in variants}) == len(variants)
    assert sys.flags.optimize == 0
    out = args.out
    out.mkdir(parents=True, exist_ok=False)
    for name in ("sources", "observations", "contracts", "upstream-specifications", "data"):
        (out / name).mkdir()
    dataset_file = HERE / "data/HumanEval.jsonl.gz"
    dataset_sha = sha(dataset_file.read_bytes())
    tasks = [json.loads(x) for x in gzip.decompress(dataset_file.read_bytes()).decode().splitlines()]
    task_by_id = {t["task_id"]: t for t in tasks}
    assert len(task_by_id) == 164
    observer_sha = sha((HERE / "native_runner.py").read_bytes())
    interpreter_sha = sha(Path(sys.executable).read_bytes())
    contract_ids = {}
    reference_rows = {}
    reference_semantics = {}
    rows = []
    observed_groups = {}
    seen = set()
    variant_metadata = []
    for variant, directory in variants:
        specification = json.loads((directory / "specification.json").read_text())
        assert specification["dataset_sha256"] == dataset_sha
        assert specification["native_runner_sha256"] == observer_sha
        assert specification["python"] == platform.python_version()
        key_bytes = {k["key_id"]: k["hex"] for k in specification["keys"]}
        original_rows = json.loads((directory / "rows.json").read_text())
        assert len(original_rows) == len(tasks) * len(key_bytes)
        with gzip.open(directory / "reference-observations.jsonl.gz", "rt") as handle:
            references = {r["task_id"]: r for r in map(json.loads, handle)}
        assert references.keys() == task_by_id.keys()
        spec_path = "upstream-specifications/" + variant + ".json"
        shutil.copyfile(directory / "specification.json", out / spec_path)
        vendor = Path(specification.get("variant_vendor", HERE.parents[2] / "work/MarkValidity_TOSEM/artifact/external-studies/sew_aliasing/vendor"))
        vendor_files = {str(p.relative_to(vendor)): sha(p.read_bytes()) for p in sorted(vendor.rglob("*"))
                        if p.is_file() and "__pycache__" not in p.parts and p.name not in ("patch.json", "change.patch")}
        assert vendor_files
        variant_metadata.append({"variant": variant, "original_run": str(directory.relative_to(HERE)) if directory.is_relative_to(HERE) else str(directory),
                                 "specification_path": spec_path, "specification_sha256": sha((out / spec_path).read_bytes()),
                                 "producer_sha256": specification["producer_sha256"], "keys": specification["keys"],
                                 "vendor_package_sha256": identity(vendor_files), "vendor_files_sha256": vendor_files,
                                 "patch_sha256": sha((vendor / "change.patch").read_bytes()) if (vendor / "change.patch").exists() else None})
        for record in original_rows:
            task_id = record["task_id"]
            task = task_by_id[task_id]
            key = (variant, task_id, record["key_id"])
            assert key not in seen
            seen.add(key)
            reference = (task["prompt"] + task["canonical_solution"]).encode()
            assert record["reference_sha256"] == sha(reference) == references[task_id]["source_sha256"]
            source = (directory / record["candidate_path"]).read_bytes()
            assert sha(source) == record["candidate_sha256"]
            contract = {
                "schema": "markvalidity-original-humaneval-suite-contract-v1", "dataset": "HumanEval", "task_id": task_id,
                "dataset_sha256": dataset_sha, "reference_source_sha256": sha(reference),
                "original_test_utf8_sha256": sha(task["test"].encode()), "entry_point": task["entry_point"],
                "test_body": task["test"], "obligation": "Unchanged original check(candidate) suite completes without error, conditional on the same reference suite passing.",
                "invocation": "check(observed_entry_point), with every argument/return/poststate observed and the returned value passed unchanged to the original tests.",
                "observer_sha256": observer_sha,
                "python": specification["python"], "interpreter_executable_sha256": interpreter_sha,
                "python_build": sys.version, "platform": platform.platform(),
                "flags": ["-B", "-S"], "PYTHONHASHSEED": "0", "random_seed": 0,
                "assertions_active": True, "optimization_level": 0,
                "random_seed_schedule": "Once before source initialization and test execution in each process.",
                "namespace_schedule": "One fresh process and namespace per whole original suite; state persists between that suite's calls.",
                "working_directory": "Fresh empty temporary directory", "inherited_PYTHONPATH": False,
                "cpu_seconds": 10, "address_space_bytes": 1073741824, "parent_wall_seconds": 15,
                "observation_scope": "Builtin typed value trees; exact returns, exception envelopes, before/after arguments, stdout/stderr. Not heap identity or arbitrary side-effect equivalence.",
            }
            contract_sha = identity(contract)
            if task_id in contract_ids:
                assert contract_ids[task_id] == contract_sha
            else:
                contract_ids[task_id] = contract_sha
                (out / "contracts" / (contract_sha + ".json")).write_bytes(canonical(contract) + b"\n")
            for source_bytes in (source, reference):
                path = out / "sources" / (sha(source_bytes) + ".py")
                if not path.exists():
                    path.write_bytes(source_bytes)
            result = json.loads((directory / record["observations_path"]).read_text())
            ref_result = references[task_id]["result"]
            ref_semantic = identity(semantic_observation(ref_result))
            if task_id in reference_semantics:
                assert reference_semantics[task_id] == ref_semantic
            else:
                reference_semantics[task_id] = ref_semantic
                ref_path = "observations/reference-" + task_id.replace("/", "-") + ".json.gz"
                save_compressed(out / ref_path, semantic_observation(ref_result))
                reference_rows[task_id] = {"task_id": task_id, "reference_sha256": sha(reference), "contract_sha256": contract_sha,
                                           "source_path": "sources/" + sha(reference) + ".py", "status": ref_result["status"],
                                           "observations_path": ref_path, "observations_sha256": sha((out / ref_path).read_bytes()),
                                           "semantic_observation_sha256": ref_semantic, "calls": len(ref_result["observations"])}
            primary = "supported" if ref_result["status"] == result["status"] == "passed" else (
                "contradicted" if ref_result["status"] == "passed" and result["status"] == "failed" else "unavailable")
            assert primary == "supported" if record["test_supported"] else primary != "supported"
            assert record["detected"] == (record["detector"]["verdict"] == "Watermark detected")
            source_contract = identity({"reference_sha256": sha(reference), "candidate_sha256": sha(source), "contract_sha256": contract_sha})
            semantic = identity(semantic_observation(result))
            if source_contract in observed_groups:
                assert observed_groups[source_contract] == (primary, semantic, len(result["observations"]))
            else:
                observed_groups[source_contract] = (primary, semantic, len(result["observations"]))
            observation_path = "observations/" + semantic + ".json.gz"
            if not (out / observation_path).exists():
                save_compressed(out / observation_path, semantic_observation(result))
            row = {
                "dataset": "HumanEval", "task_id": task_id, "variant": variant,
                "key_id": record["key_id"], "key_hex": key_bytes[record["key_id"]],
                "reference_sha256": sha(reference), "candidate_sha256": sha(source),
                "contract_sha256": contract_sha, "source_contract_sha256": source_contract,
                "source_path": "sources/" + sha(source) + ".py",
                "observation_path": observation_path, "observation_sha256": sha((out / observation_path).read_bytes()),
                "semantic_observation_sha256": semantic, "candidate_function_invocations": len(result["observations"]),
                "suite_cost": 1, "candidate_suite_executions": 1,
                "detected": record["detected"], "validity_label": primary,
                "joint": record["detected"] and primary == "supported", "reference_status": ref_result["status"],
                "candidate_status": result["status"], "full_call_records_equal": result["observations"] == ref_result["observations"],
                "embedding": record["embedding"], "detector": record["detector"], "reference_detector": record["reference_detector"],
                "variant_weight_denominator": len(original_rows), "candidate_elapsed_seconds": result.get("elapsed_seconds"),
            }
            rows.append(row)
    shutil.copyfile(dataset_file, out / "data/HumanEval.jsonl.gz")
    shutil.copyfile(HERE / "data/LICENSE", out / "data/LICENSE")
    shutil.copyfile(HERE / "native_runner.py", out / "native_runner.py")
    summaries = []
    for variant, _ in variants:
        selected = [r for r in rows if r["variant"] == variant]
        summaries.append({"variant": variant, "configurations": len(selected),
                          "validity_labels": dict(collections.Counter(r["validity_label"] for r in selected)),
                          "detected": sum(r["detected"] for r in selected), "joint": sum(r["joint"] for r in selected),
                          "detected_contradicted": sum(r["detected"] and r["validity_label"] == "contradicted" for r in selected),
                          "reference_detections": sum(r["reference_detector"]["verdict"] == "Watermark detected" for r in selected),
                          "candidate_function_invocations": sum(r["candidate_function_invocations"] for r in selected),
                          "candidate_suite_executions": sum(r["candidate_suite_executions"] for r in selected),
                          "complete_call_record_agreement": sum(r["full_call_records_equal"] for r in selected)})
    comparisons = [pair_summary(a, b, rows) for a, b in itertools.combinations([name for name, _ in variants], 2)]
    (out / "rows.json").write_text(json.dumps(rows, indent=2) + "\n")
    (out / "references.json").write_text(json.dumps(list(reference_rows.values()), indent=2) + "\n")
    (out / "summary.json").write_text(json.dumps({"variants": summaries, "tasks": len(tasks), "rows": len(rows),
                                                "unique_source_contracts": len(observed_groups), "pairwise_comparisons": comparisons}, indent=2) + "\n")
    (out / "specification.json").write_text(json.dumps({"schema": "markvalidity-normalized-external-study-v1",
        "dataset": "HumanEval", "dataset_commit": "b9453e8f1865df0a0057a1383767caa400acfbcf", "dataset_sha256": dataset_sha,
        "selection": "All 164 tasks, all declared keys, all declared variants, no result-based exclusions.",
        "contract_identity": "SHA-256 of UTF-8 JSON, ensure_ascii=False, sort_keys=True, separators=(',', ':'), of the full task contract; variant/key deliberately excluded.",
        "source_contract_identity": "SHA-256 of the same canonical JSON containing reference_sha256, candidate_sha256, and contract_sha256.",
        "variants": variant_metadata, "normalizer_sha256": sha(Path(__file__).read_bytes()),
        "coupling_validation": "Repeated source/contract observations had identical status, error, call records, streams, and invocation counts before pooling.",
        "source_coupling_scope": "Descriptive withholding reconstruction. suite_cost=1 is one candidate contract query; candidate_function_invocations is the separate measured entry-point count. No adaptive online experiment claimed.",
    }, indent=2) + "\n")
    print(json.dumps({"output": str(out), "rows": len(rows), "variants": summaries, "unique_source_contracts": len(observed_groups)}, indent=2))


if __name__ == "__main__":
    main()
