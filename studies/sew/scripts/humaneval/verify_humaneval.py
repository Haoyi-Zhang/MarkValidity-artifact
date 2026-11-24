"""Read-only receiver for the frozen HumanEval primary-v3 and enhanced-v3 ledgers.

This program reopens the delivered bytes and independently reconstructs labels,
the recorded detector event, source sharing, and score bounds. It executes no
candidate, reference, emitter, detector, or normalizer. It writes only a JSON
receipt to stdout; callers may save that receipt separately from the evidence.
"""
import argparse
import collections
from fractions import Fraction
import gzip
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import re
import sys

HUMANEVAL_SHA = "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"
PLUS_SHA = "272720b90ac375502c8ed23cd791c2a93dfb22a911641a494da74a426c09f101"
PRIMARY_OBSERVER_SHA = "232a7d6f47011501356a9c9ac07e17bf325bde345d9c707d32c4fae668367012"
ENHANCED_OBSERVER_SHA = "7bddddcc0f58593e38345c8150eb104b726424af96b0fac116ef332109bc8670"
VARIANTS = ("stock", "s1", "s4", "s1_s4")
KEYS = {"upstream_default": "76" * 16, "integer_0": "00" * 16, "integer_1": "00" * 15 + "01"}
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")


class VerificationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def identity(value):
    return sha(canonical(value))


def load_json(path):
    return json.loads(path.read_bytes())


def inside(root, relative):
    require(type(relative) is str, "A retained-file path is not a string")
    rel = Path(relative)
    require(not rel.is_absolute(), "A retained-file path is absolute")
    path = (root / rel).resolve()
    require(path.is_relative_to(root.resolve()), "A retained-file path escapes its result directory")
    require(path.is_file(), "A retained file is missing: " + relative)
    return path


def require_hash(value, description):
    require(type(value) is str and HASH_RE.fullmatch(value) is not None, "Invalid SHA-256: " + description)


class RetainedBytes:
    def __init__(self):
        self.cache = {}

    def verified(self, path, expected):
        require_hash(expected, str(path.name))
        key = str(path.resolve())
        if key not in self.cache:
            data = path.read_bytes()
            self.cache[key] = (sha(data), data)
        digest, data = self.cache[key]
        require(digest == expected, "Retained-byte digest mismatch: " + str(path))
        return data


def validate_value(value):
    require(type(value) is list and bool(value) and type(value[0]) is str, "Malformed tagged value")
    tag = value[0]
    if tag == "none":
        require(len(value) == 1, "Malformed None value")
        return
    require(len(value) == 2, "Malformed value payload: " + tag)
    payload = value[1]
    if tag == "bool":
        require(type(payload) is bool, "Malformed bool value")
    elif tag == "int":
        require(type(payload) is str and re.fullmatch(r"-?(?:0|[1-9][0-9]*)", payload) is not None, "Malformed decimal integer value")
    elif tag == "int_hex":
        require(type(payload) is str and re.fullmatch(r"-?0x[0-9a-f]+", payload) is not None, "Malformed hexadecimal integer value")
    elif tag == "float":
        require(type(payload) is str, "Malformed float value")
        try:
            float.fromhex(payload)
        except ValueError as exc:
            raise VerificationError("Malformed float representation") from exc
    elif tag == "str":
        require(type(payload) is str, "Malformed string value")
    elif tag == "bytes":
        require(type(payload) is str and len(payload) % 2 == 0 and re.fullmatch(r"[0-9a-f]*", payload) is not None, "Malformed bytes value")
    elif tag in ("list", "tuple", "set", "frozenset"):
        require(type(payload) is list, "Malformed sequence value")
        for item in payload:
            validate_value(item)
    elif tag == "dict":
        require(type(payload) is list, "Malformed dictionary value")
        for pair in payload:
            require(type(pair) is list and len(pair) == 2, "Malformed dictionary entry")
            validate_value(pair[0])
            validate_value(pair[1])
    else:
        raise VerificationError("Unknown value tag: " + tag)


def validate_outcome(value):
    require(type(value) is list and bool(value), "Missing outcome envelope")
    if value[0] == "return":
        require(len(value) == 2, "Malformed return envelope")
        validate_value(value[1])
    elif value[0] == "exception":
        require(len(value) == 3 and type(value[1]) is str and type(value[2]) is str, "Malformed exception envelope")
    else:
        raise VerificationError("Outcome lacks a disjoint return/exception tag")


def validate_primary_observation(result):
    require(set(result) == {"status", "error", "observations", "stdout", "stderr"}, "Unexpected primary semantic-record fields")
    require(result["status"] in ("passed", "failed", "unavailable", "timeout", "process_error", "invalid_output"), "Unknown primary execution status")
    require(type(result["stdout"]) is str and type(result["stderr"]) is str, "Non-string primary streams")
    require(type(result["observations"]) is list, "Missing primary call records")
    if result["status"] == "passed":
        require(result["error"] is None, "Passed suite contains an error")
    if result["status"] == "failed":
        require(type(result["error"]) is dict, "Failed suite lacks its error witness")
        require(result["error"].get("reason") not in ("observer_error", "resource_unavailable", "interrupted", "test_or_entry_setup_error"), "Observer or resource failure was labeled as program failure")
    for observation in result["observations"]:
        require(set(observation) == {"before", "result", "after"}, "Incomplete primary call record")
        for field in ("before", "after"):
            require(set(observation[field]) == {"args", "kwargs"}, "Malformed argument-state record")
            require(observation[field]["args"][0] == "tuple" and observation[field]["kwargs"][0] == "dict", "Wrong argument container tags")
            validate_value(observation[field]["args"])
            validate_value(observation[field]["kwargs"])
        validate_outcome(observation["result"])


def suite_label(reference, candidate):
    if reference["status"] != "passed":
        return "unavailable"
    if candidate["status"] == "passed":
        return "supported"
    if candidate["status"] == "failed":
        return "contradicted"
    return "unavailable"


def detector_event(record):
    for field in ("n_grades", "k_grades", "n_syntax", "k_syntax", "n_sites"):
        require(type(record.get(field)) is int and record[field] >= 0, "Malformed detector count: " + field)
    require(record["k_grades"] <= record["n_grades"] <= record["n_sites"], "Inconsistent all-grade detector counts")
    require(record["k_syntax"] <= record["n_syntax"] <= record["n_grades"], "Inconsistent syntax-grade detector counts")
    for field in ("p", "p_all", "p_syntax"):
        require(type(record.get(field)) in (int, float) and math.isfinite(record[field]) and 0 <= record[field] <= 1, "Malformed detector probability: " + field)
    p = min(1.0, 2 * min(record["p_all"], record["p_syntax"]))
    require(record["p"] == p, "Combined detector probability differs from released rule")
    detected = record["n_grades"] >= 5 and p < .01
    verdict = "Insufficient evidence" if record["n_grades"] < 5 else "Watermark detected" if detected else "No watermark evidence"
    require(record.get("verdict") == verdict, "Detector verdict differs from counts and threshold")
    return detected


def group_identity(row):
    return identity({key: row[key] for key in ("reference_sha256", "candidate_sha256", "contract_sha256")})


def primary_contract(root, digest, task, observer_sha, store):
    require_hash(digest, "primary contract")
    path = inside(root, "contracts/" + digest + ".json")
    contract = load_json(path)
    require(identity(contract) == digest, "Primary contract identity mismatch")
    reference = (task["prompt"] + task["canonical_solution"]).encode()
    require(contract["task_id"] == task["task_id"] and contract["dataset_sha256"] == HUMANEVAL_SHA, "Primary contract corpus binding mismatch")
    require(contract["reference_source_sha256"] == sha(reference), "Primary contract reference binding mismatch")
    require(contract["entry_point"] == task["entry_point"], "Primary entry-point binding mismatch")
    require(contract["test_body"] == task["test"] and contract["original_test_utf8_sha256"] == sha(task["test"].encode()), "Primary suite bytes differ from upstream")
    require(contract["observer_sha256"] == observer_sha, "Primary contract uses another observer")
    require(contract["schema"] == "markvalidity-original-humaneval-suite-contract-v3", "Primary event-boundary contract is not v3")
    require("OSError(errno=ENOMEM)" in contract["failure_boundary"] and "KeyboardInterrupt" in contract["failure_boundary"], "Primary resource/interruption boundary is missing")
    require(contract["flags"] == ["-B", "-S"] and contract["assertions_active"] is True and contract["optimization_level"] == 0, "Primary interpreter flags changed")
    require(contract["PYTHONHASHSEED"] == "0" and contract["random_seed"] == 0, "Primary seed policy changed")
    require(contract["cpu_seconds"] == 10 and contract["parent_wall_seconds"] == 15 and contract["address_space_bytes"] == 1073741824, "Primary resource policy changed")
    require_hash(contract["interpreter_executable_sha256"], "primary interpreter")
    return contract


def verify_primary(args, tasks, store):
    root = args.main_results.resolve()
    rows_path = inside(root, "rows.json")
    rows = load_json(rows_path)
    specification = load_json(inside(root, "specification.json"))
    summary = load_json(inside(root, "summary.json"))
    require(specification["dataset_sha256"] == HUMANEVAL_SHA, "Primary dataset fingerprint mismatch")
    runner = args.primary_runner.resolve() if args.primary_runner else inside(root, "native_runner.py")
    store.verified(runner, PRIMARY_OBSERVER_SHA)
    if (root / "data/HumanEval.jsonl.gz").exists():
        store.verified(root / "data/HumanEval.jsonl.gz", HUMANEVAL_SHA)
    metadata = {x["variant"]: x for x in specification["variants"]}
    require(set(metadata) == set(VARIANTS), "Primary method set differs from the declared four factors")
    for name, item in metadata.items():
        snapshot = json.loads(store.verified(inside(root, item["specification_path"]), item["specification_sha256"]))
        require(snapshot["native_runner_sha256"] == PRIMARY_OBSERVER_SHA, "Historical producer snapshot uses another primary observer")
        require({x["key_id"]: x["hex"] for x in snapshot["keys"]} == KEYS, "Producer key set mismatch")
        require(identity(item["vendor_files_sha256"]) == item["vendor_package_sha256"], "Vendor package manifest identity mismatch")
        if args.variants_root:
            for relative, digest in item["vendor_files_sha256"].items():
                store.verified(inside(args.variants_root / name, relative), digest)
    references = load_json(inside(root, "references.json"))
    require(len(references) == len(tasks), "Wrong reference-row count")
    references_by_id = {r["task_id"]: r for r in references}
    require(set(references_by_id) == set(tasks), "Reference task coverage mismatch")
    reference_observations = {}
    contract_cache = {}
    for task_id, record in references_by_id.items():
        task = tasks[task_id]
        expected = (task["prompt"] + task["canonical_solution"]).encode()
        require(record["reference_sha256"] == sha(expected), "Reference source hash does not match frozen task")
        retained = store.verified(inside(root, record.get("source_path", "sources/" + record["reference_sha256"] + ".py")), record["reference_sha256"])
        require(retained == expected, "Reference source bytes differ from upstream")
        digest = record["contract_sha256"]
        contract_cache[digest] = primary_contract(root, digest, task, PRIMARY_OBSERVER_SHA, store)
        observed = json.loads(gzip.decompress(store.verified(inside(root, record["observations_path"]), record["observations_sha256"])))
        validate_primary_observation(observed)
        require(identity(observed) == record["semantic_observation_sha256"], "Reference semantic observation identity mismatch")
        require(observed["status"] == record["status"] == "passed", "Frozen reference lacks a completed successful suite")
        require(len(observed["observations"]) == record["calls"], "Reference call count mismatch")
        reference_observations[task_id] = observed
    expected_coverage = set(itertools.product(tasks, VARIANTS, KEYS))
    seen = set()
    observation_cache = {}
    group_records = {}
    computed = {v: collections.Counter() for v in VARIANTS}
    stock_default = {}
    for row in rows:
        key = (row["task_id"], row["variant"], row["key_id"])
        require(key in expected_coverage and key not in seen, "Primary task/version/key coverage is duplicate or unexpected")
        seen.add(key)
        task_id, variant, key_id = key
        require(row["dataset"] == "HumanEval" and row["key_hex"] == KEYS[key_id], "Primary corpus or key identity mismatch")
        reference = references_by_id[task_id]
        require(row["reference_sha256"] == reference["reference_sha256"] and row["contract_sha256"] == reference["contract_sha256"], "Primary row changed its reference or behavioral contract")
        store.verified(inside(root, row["source_path"]), row["candidate_sha256"])
        group = group_identity(row)
        require(group == row["source_contract_sha256"], "Primary source/contract group identity mismatch")
        observation_path = row["observation_path"]
        if observation_path not in observation_cache:
            payload = store.verified(inside(root, observation_path), row["observation_sha256"])
            observation_cache[observation_path] = json.loads(gzip.decompress(payload))
        else:
            store.verified(inside(root, observation_path), row["observation_sha256"])
        observed = observation_cache[observation_path]
        validate_primary_observation(observed)
        semantic_sha = identity(observed)
        require(semantic_sha == row["semantic_observation_sha256"], "Candidate semantic observation identity mismatch")
        reference_observed = reference_observations[task_id]
        label = suite_label(reference_observed, observed)
        require(label == row["validity_label"], "Primary validity label differs from retained oracle outcomes")
        require(row["candidate_status"] == observed["status"] and row["reference_status"] == reference_observed["status"], "Primary status projection mismatch")
        require(row["candidate_function_invocations"] == len(observed["observations"]), "Candidate function-invocation count mismatch")
        require(row["suite_cost"] == row["candidate_suite_executions"] == 1, "Whole-suite cost was changed or mixed with call counts")
        detected = detector_event(row["detector"])
        reference_detected = detector_event(row["reference_detector"])
        require(type(row["detected"]) is bool and row["detected"] is detected, "Recorded D differs from retained detector statistics")
        joint = detected and label == "supported"
        require(row["joint"] is joint, "Primary joint label mismatch")
        agreement = observed["observations"] == reference_observed["observations"]
        require(row["full_call_records_equal"] is agreement, "Differential call-record claim mismatch")
        group_record = (label, semantic_sha, row["candidate_function_invocations"])
        if group in group_records:
            require(group_records[group] == group_record, "One shared behavioral group has conflicting retained evidence")
        else:
            group_records[group] = group_record
        c = computed[variant]
        c["configurations"] += 1
        c[label] += 1
        c["detected"] += detected
        c["joint"] += joint
        c["detected_contradicted"] += detected and label == "contradicted"
        c["reference_detections"] += reference_detected
        c["candidate_function_invocations"] += len(observed["observations"])
        c["complete_call_record_agreement"] += agreement
        if variant == "stock" and key_id == "upstream_default":
            stock_default[task_id] = row
    require(seen == expected_coverage and len(rows) == len(expected_coverage), "Primary attempt denominator is incomplete")
    declared = {s["variant"]: s for s in summary["variants"]}
    methods = []
    for variant in VARIANTS:
        c = computed[variant]
        entry = {"variant": variant, "configurations": c["configurations"],
                 "validity_labels": {k: c[k] for k in ("supported", "contradicted", "unavailable") if c[k]},
                 **{k: c[k] for k in ("detected", "joint", "detected_contradicted", "reference_detections", "candidate_function_invocations", "complete_call_record_agreement")},
                 "candidate_suite_executions": c["configurations"]}
        require(entry == declared[variant], "Primary aggregate summary mismatch for " + variant)
        methods.append(entry)
    require(summary["rows"] == len(rows) and summary["tasks"] == len(tasks) and summary["unique_source_contracts"] == len(group_records), "Primary total summary mismatch")
    comparison_receipts = []
    declared_comparisons = {(c["left"], c["right"]): c for c in summary["pairwise_comparisons"]}
    for left, right in itertools.combinations(VARIANTS, 2):
        coefficients = collections.Counter()
        all_groups = set()
        for row in rows:
            if row["variant"] not in (left, right):
                continue
            all_groups.add(row["source_contract_sha256"])
            coefficients[row["source_contract_sha256"]] += (1 if row["variant"] == left else -1) * int(row["detected"])
        n = computed[left]["configurations"]
        require(n == computed[right]["configurations"], "Paired finite denominators differ")
        lower = Fraction(sum(min(c, 0) for c in coefficients.values()), n)
        upper = Fraction(sum(max(c, 0) for c in coefficients.values()), n)
        independent_width = Fraction(computed[left]["detected"] + computed[right]["detected"], n)
        gap = Fraction(computed[left]["joint"] - computed[right]["joint"], n)
        target = declared_comparisons[left, right]
        nonzero = sum(c != 0 for c in coefficients.values())
        require(target["grouped_gap_interval_if_all_labels_withheld"] == [str(lower), str(upper)] and target["grouped_width"] == str(upper - lower), "Withheld source-coupled interval mismatch")
        require(target["separate_score_subtraction_width"] == str(independent_width) and target["complete_gap"] == str(gap), "Independent width or complete gap mismatch")
        require(target["unique_source_contracts"] == len(all_groups) and target["nonzero_gap_source_groups"] == nonzero, "Pairwise source-group count mismatch")
        comparison_receipts.append({"left": left, "right": right, "unique_source_contracts": len(all_groups), "nonzero_gap_source_groups": nonzero,
                                    "withheld_gap_interval": [str(lower), str(upper)], "complete_gap": str(gap)})
    return {"rows_sha256": sha(rows_path.read_bytes()), "specification_sha256": sha((root / "specification.json").read_bytes()),
            "tasks": len(tasks), "rows": len(rows), "unique_source_contracts": len(group_records),
            "reference_function_invocations": sum(len(x["observations"]) for x in reference_observations.values()),
            "observer_sha256": PRIMARY_OBSERVER_SHA, "variants": methods, "pairwise_checks": comparison_receipts}, stock_default


def validate_enhanced_side(side):
    require(side.get("status") in ("observed", "unavailable"), "Unknown enhanced side status")
    require(type(side.get("stdout")) is str and type(side.get("stderr")) is str, "Malformed enhanced streams")
    if side["status"] == "observed":
        validate_outcome(side["outcome"])
        validate_value(side["post_arguments"])
    else:
        require(side.get("reason") in ("per_invocation_guard", "initialization_or_observer_error", "resource_unavailable", "interrupted"), "Unavailable enhanced side lacks a known reason")
        require(type(side.get("phase")) is str, "Unavailable enhanced side lacks a phase")


def verify_enhanced(args, tasks, plus, stock_default, store):
    root = args.enhanced_results.resolve()
    rows_path = inside(root, "rows.json")
    rows = load_json(rows_path)
    specification = load_json(inside(root, "specification.json"))
    summary = load_json(inside(root, "summary.json"))
    require(specification["data_sha256"] == HUMANEVAL_SHA and specification["plus_data_sha256"] == PLUS_SHA, "Enhanced dataset binding mismatch")
    runner = args.enhanced_runner.resolve() if args.enhanced_runner else inside(root, "native_pairs_v3.py")
    store.verified(runner, ENHANCED_OBSERVER_SHA)
    require(specification["observer_sha256"] == ENHANCED_OBSERVER_SHA, "Enhanced specification uses another observer")
    seen = set()
    totals = collections.Counter()
    labels = collections.Counter()
    exception_types = collections.Counter()
    guards = collections.Counter()
    unknown_tasks = []
    for row in rows:
        task_id = row["task_id"]
        require(task_id in tasks and task_id not in seen, "Enhanced task coverage is duplicate or unexpected")
        seen.add(task_id)
        require(row["variant"] == "stock" and row["key_id"] == "upstream_default" and row["key_hex"] == KEYS["upstream_default"], "Enhanced source is not the declared stock/default configuration")
        primary = stock_default[task_id]
        require(row["reference_sha256"] == primary["reference_sha256"] and row["candidate_sha256"] == primary["candidate_sha256"], "Enhanced/primary candidate source linkage mismatch")
        require(row["detected"] is primary["detected"], "Enhanced detector event differs from the same primary source/version/key")
        store.verified(inside(root, row["source_path"]), row["candidate_sha256"])
        store.verified(inside(root, row["reference_source_path"]), row["reference_sha256"])
        require(group_identity(row) == row["source_contract_sha256"], "Enhanced source/contract group identity mismatch")
        digest = row["contract_sha256"]
        require_hash(digest, "enhanced contract")
        contract = load_json(inside(root, "contracts/" + digest + ".json"))
        require(identity(contract) == digest, "Enhanced contract identity mismatch")
        require(contract["schema"] == "markvalidity-human-eval-expanded-input-contract-v3", "Enhanced event-boundary contract is not v3")
        require("OSError(errno=ENOMEM)" in contract["observer_boundary"] and "KeyboardInterrupt" in contract["observer_boundary"], "Enhanced resource/interruption boundary is missing")
        inputs = {split: plus[task_id][split] for split in ("base_input", "plus_input")}
        require(canonical(contract["inputs"]) == canonical(inputs), "Enhanced contract input tuples differ from the full release")
        require(contract["task_id"] == task_id and contract["reference_sha256"] == row["reference_sha256"] and contract["entry_point"] == tasks[task_id]["entry_point"], "Enhanced reference/entry-point binding mismatch")
        require(contract["original_dataset_sha256"] == HUMANEVAL_SHA and contract["expanded_input_dataset_sha256"] == PLUS_SHA and contract["observer_sha256"] == ENHANCED_OBSERVER_SHA, "Enhanced contract provenance mismatch")
        count = sum(len(values) for values in inputs.values())
        require(contract["per_invocation_wall_seconds"] == .5 and contract["worker_cpu_seconds"] == math.ceil(10 + count * 1.02) and contract["worker_wall_seconds"] == math.ceil(15 + count * 1.02), "Enhanced observation budget mismatch")
        require(contract["address_space_bytes"] == 1073741824 and contract["random_seed"] == 0 and contract["PYTHONHASHSEED"] == "0" and contract["flags"] == ["-B", "-S"], "Enhanced runtime policy mismatch")
        require(row["suite_cost"] == row["candidate_suite_executions"] == 1, "Enhanced suite cost mismatch")
        # Large observation logs are streamed and not retained in the receiver's
        # cache, so receiving does not create another copy of the corpus.
        path = inside(root, row["observation_path"])
        compressed = path.read_bytes()
        require(sha(compressed) == row["observation_sha256"], "Enhanced observation digest mismatch")
        expected = {(split, index) for split, values in inputs.items() for index in range(len(values))}
        actual = set()
        counts = collections.Counter()
        worker_summaries = []
        with gzip.open(io.BytesIO(compressed), "rt") as handle:
            for line in handle:
                record = json.loads(line)
                if record.get("kind") == "worker_summary":
                    worker_summaries.append(record)
                    continue
                require(record.get("kind") == "pair", "Unknown enhanced log-record type")
                key = (record["split"], record["index"])
                require(key in expected and key not in actual, "Enhanced input record is duplicate or outside the declared domain")
                actual.add(key)
                left, right = record["reference"], record["candidate"]
                for name, side in (("reference", left), ("candidate", right)):
                    validate_enhanced_side(side)
                    if side["status"] == "unavailable":
                        guards[name, side["reason"], side["phase"]] += 1
                    elif side["outcome"][0] == "exception":
                        exception_types[name, side["outcome"][1], side["outcome"][2]] += 1
                if left["status"] == right["status"] == "observed":
                    equal = left["outcome"] == right["outcome"]
                    post_equal = left["post_arguments"] == right["post_arguments"]
                    stream_equal = (left["stdout"], left["stderr"]) == (right["stdout"], right["stderr"])
                else:
                    equal = post_equal = stream_equal = None
                require(record["return_equal"] is equal and record["post_arguments_equal"] is post_equal and record["streams_equal"] is stream_equal, "Enhanced equality flag differs from raw observations")
                counts["unavailable_input_pairs"] += equal is None
                counts["return_mismatches"] += equal is False
                counts["post_argument_mismatches"] += post_equal is False
                counts["stream_mismatches"] += stream_equal is False
        counts["declared_input_pairs"] = len(expected)
        counts["recorded_input_pairs"] = len(actual)
        counts["missing_input_pairs"] = len(expected - actual)
        counts["comparable_input_pairs"] = len(actual) - counts["unavailable_input_pairs"]
        for field in ("declared_input_pairs", "recorded_input_pairs", "missing_input_pairs", "unavailable_input_pairs", "comparable_input_pairs", "return_mismatches", "post_argument_mismatches", "stream_mismatches"):
            require(row[field] == counts[field], "Enhanced per-task count mismatch: " + task_id + " / " + field)
        label = "contradicted" if counts["return_mismatches"] else "unavailable" if counts["unavailable_input_pairs"] or counts["missing_input_pairs"] else "supported"
        require(row["validity_label"] == label, "Enhanced task label differs from pair records")
        require(worker_summaries == row["worker_summaries"], "Enhanced worker-summary projection mismatch")
        labels[label] += 1
        totals.update(counts)
        totals["detected"] += row["detected"]
        totals["joint_numerator_lower"] += row["detected"] and label == "supported"
        totals["joint_numerator_upper"] += row["detected"] and label != "contradicted"
        if label == "unavailable":
            unknown_tasks.append(task_id)
    require(seen == set(tasks) and len(rows) == len(tasks), "Enhanced task denominator is incomplete")
    reconstructed = {"tasks": len(rows), "labels": dict(labels), **{field: totals[field] for field in (
        "declared_input_pairs", "recorded_input_pairs", "comparable_input_pairs", "unavailable_input_pairs", "missing_input_pairs",
        "return_mismatches", "post_argument_mismatches", "stream_mismatches", "detected", "joint_numerator_lower", "joint_numerator_upper")},
        "joint_denominator": len(rows)}
    require(reconstructed == summary, "Enhanced aggregate summary mismatch")
    return {**reconstructed, "rows_sha256": sha(rows_path.read_bytes()), "specification_sha256": sha((root / "specification.json").read_bytes()),
            "observer_sha256": ENHANCED_OBSERVER_SHA,
            "unavailable_tasks": unknown_tasks,
            "program_exception_counts": [{"side": key[0], "type": key[1], "message": key[2], "count": count} for key, count in sorted(exception_types.items())],
            "unavailable_observation_counts": [{"side": key[0], "reason": key[1], "phase": key[2], "count": count} for key, count in sorted(guards.items())]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("main-results", "enhanced-results", "data", "plus-data"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("primary-runner", "enhanced-runner", "variants-root"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    try:
        store = RetainedBytes()
        data = store.verified(args.data.resolve(), HUMANEVAL_SHA)
        plus_data = store.verified(args.plus_data.resolve(), PLUS_SHA)
        task_rows = [json.loads(line) for line in gzip.decompress(data).decode().splitlines() if line.strip()]
        plus_rows = [json.loads(line) for line in gzip.decompress(plus_data).decode().splitlines() if line.strip()]
        tasks = {task["task_id"]: task for task in task_rows}
        plus = {task["task_id"]: task for task in plus_rows}
        require(len(task_rows) == len(tasks) == len(plus_rows) == len(plus) == 164 and set(tasks) == set(plus), "Frozen dataset coverage mismatch")
        primary, stock_default = verify_primary(args, tasks, store)
        enhanced = verify_enhanced(args, tasks, plus, stock_default, store)
        receipt = {"status": "PASS", "mode": "read-only receiving; no source execution", "receiver_sha256": sha(Path(__file__).read_bytes()),
                   "candidate_execution_performed": False, "reference_execution_performed": False, "emitter_execution_performed": False,
                   "detector_execution_performed": False, "normalizer_execution_performed": False,
                   "detector_check": "Reconstructed p=min(1,2*min(p_all,p_syntax)), minimum five grades, strict p<0.01, and verdict from retained statistics; no re-estimation of tail probabilities or calibration.",
                   "vendor_tree_verification": "verified" if args.variants_root else "not requested",
                   "data_sha256": HUMANEVAL_SHA, "plus_data_sha256": PLUS_SHA, "primary": primary, "enhanced": enhanced,
                   "trust_boundary": "Checks retained-byte bindings, complete coverage, typed observations, label consistency, and aggregation. It does not attest that an external producer executed the programs."}
        print(json.dumps(receipt, indent=2))
    except (VerificationError, KeyError, TypeError, ValueError, OSError, IndexError) as exc:
        print(json.dumps({"status": "FAIL", "mode": "read-only receiving; no source execution", "error_type": type(exc).__name__, "error": str(exc)}, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
