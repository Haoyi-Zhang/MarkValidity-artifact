#!/usr/bin/env python3
"""Independently receive a fresh native audit from public inputs and new stdout.

No historical candidate labels or candidate observation files are opened. Bounds
at every audit prefix are rebuilt with the exact Fraction reference, and query
selection is checked independently from public coefficients and received labels.
The only output is a new independent-receiving receipt beside the audit.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from fractions import Fraction as F
import gzip
import hashlib
import json
import math
from pathlib import Path

from conditional_bounds import conditional_bounds, conditional_comparison, joint_comparison
from verify_natural_results import reconstruct, check_snapshot

ALIASES = {'stock': 'stock', 's1': 's1', 's1_literal_predecessor': 's1',
           's4': 's4', 's4_return_boundary': 's4', 's1_s4': 's1_s4'}
CERTIFICATES = {'left_strict', 'right_strict', 'tie'}
CASES = [('HumanEval', 'stock', 's1', 'J', 'joint_width_per_suite'),
         ('HumanEval', 'stock', 's1', 'C', 'conditional_differences_first'),
         ('mbpp_sanitized', 'stock', 's4', 'J', 'joint_width_per_suite'),
         ('mbpp_sanitized', 'stock', 's4', 'C', 'conditional_differences_first')]
FORBIDDEN = {'validity_label', 'validity', 'candidate_status', 'joint', 'observation_path',
             'candidate_elapsed_seconds', 'candidate_function_invocations', 'assertion_entries'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(content):
    return hashlib.sha256(content).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def group_identity(record):
    return digest(canonical({k: record[k] for k in
                             ('reference_sha256', 'candidate_sha256', 'contract_sha256')}))


def bounded_path(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root), 'receiving path escapes its declared root')
    return path


def strict_label(value):
    require(value is None or type(value) is bool, 'a received label must be Boolean or unavailable')
    return value


def receive_humaneval(stdout, returncode, interruption):
    """Receive the whole original-suite envelope; incomplete envelopes stay unknown."""
    try:
        result = json.loads(stdout)
    except (ValueError, TypeError):
        return None
    require(isinstance(result, dict), 'HumanEval envelope must be an object')
    status = result.get('status')
    require(status in {'passed', 'failed', 'unavailable'}, 'unknown HumanEval status')
    require(isinstance(result.get('observations'), list), 'missing HumanEval observation vector')
    if returncode != 0 or interruption:
        return None
    if status == 'unavailable':
        return None
    if status == 'passed':
        require(result.get('error') is None, 'passing HumanEval envelope carries an error')
        return True
    problem = result.get('error')
    require(isinstance(problem, dict), 'failure lacks a program witness')
    require(problem.get('phase') in {'compile_source', 'initialize_source', 'original_suite'},
            'test or observer setup is not a HumanEval program-failure witness')
    require(problem.get('type') not in {'builtins.MemoryError', 'builtins.KeyboardInterrupt'}
            and problem.get('errno') not in (12, 'ENOMEM') and not problem.get('reason'),
            'resource/observer failure was represented as a program contradiction')
    return False


def receive_mbpp(stdout, expected_tests, returncode, interruption):
    """Receive v2 streamed assertions, preserving a complete failure witness."""
    events = []
    incomplete_tail = False
    lines = stdout.splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            # A process can be interrupted partway through its final output
            # line. Earlier complete envelopes retain their evidential role.
            require(index == len(lines) - 1 and (interruption or returncode != 0),
                    'malformed complete MBPP output')
            incomplete_tail = True
            break
        require(isinstance(event, dict), 'MBPP event must be an object')
        require(event.get('status') in {'passed', 'failed', 'unavailable', 'evidence_rejected'},
                'unknown MBPP event status')
        events.append(event)
    require(not any(e['status'] == 'evidence_rejected' for e in events),
            'rejected MBPP evidence cannot supply a behavioral label')
    compiles = [e for e in events if e.get('event') == 'source_compile']
    tests = [e for e in events if e.get('event') == 'test_result']
    completed = [e for e in events if e.get('event') == 'complete']
    require(len(compiles) <= 1 and len(completed) <= 1, 'duplicate MBPP lifecycle event')
    indices = [e.get('test_index') for e in tests]
    require(all(type(i) is int and 0 <= i < expected_tests for i in indices), 'invalid MBPP assertion index')
    require(len(indices) == len(set(indices)), 'duplicate MBPP assertion evidence')
    witnessed_failure = False
    for event in compiles + tests:
        if event['status'] != 'failed':
            continue
        problem = event.get('error')
        require(isinstance(problem, dict), 'MBPP failure lacks an exception witness')
        require(problem.get('type') not in {'builtins.MemoryError', 'builtins.KeyboardInterrupt'},
                'resource interruption cannot contradict the MBPP program')
        if event.get('event') == 'source_compile':
            require(problem.get('phase') == 'compile_source'
                    and problem.get('type') in {'builtins.SyntaxError', 'builtins.IndentationError', 'builtins.TabError'},
                    'non-syntax source-compiler error cannot contradict the program')
        else:
            require(problem.get('phase') in {'initialize_source', 'original_assertion'},
                    'test setup or observation failure cannot contradict the MBPP program')
        witnessed_failure = True
    if witnessed_failure:
        return False
    if returncode != 0 or interruption or incomplete_tail:
        return None
    if (len(compiles) != 1 or compiles[0]['status'] != 'passed'
            or len(tests) != expected_tests or set(indices) != set(range(expected_tests))
            or any(e['status'] != 'passed' for e in tests) or len(completed) != 1):
        return None
    terminal = completed[0]
    require(terminal.get('evidence_schema') == 'markvalidity-mbpp-original-assertions-v2',
            'MBPP terminal event is not the declared v2 envelope')
    if terminal['status'] != 'passed':
        return None
    require(terminal.get('scheduled_tests') == terminal.get('completed_tests') == expected_tests,
            'MBPP completion count disagrees with the contract')
    require(terminal.get('passed_tests') == expected_tests
            and all(terminal.get(k) == 0 for k in ('failed_tests', 'unavailable_tests', 'rejected_tests')),
            'MBPP terminal counters disagree with its passing assertions')
    return True


def relation(lower, upper):
    return ('left_strict' if lower > 0 else 'right_strict' if upper < 0
            else 'tie' if lower == upper == 0 else 'unresolved')


def separate_bounds(models, metric):
    if metric in ('J', 'A'):
        coordinate = 'detected_mass' if metric == 'J' else 'mass'
        known = [m.known_joint if metric == 'J' else m.known_valid for m in models]
        extra = [sum((getattr(g, coordinate) for g in m.unknown), F()) for m in models]
        lower, upper = known[0] - known[1] - extra[1], known[0] + extra[0] - known[1]
        return lower, upper, relation(lower, upper)
    left, right = map(conditional_bounds, models)
    if not left['defined_for_some_completion'] or not right['defined_for_some_completion']:
        return None, None, 'undefined_everywhere_for_at_least_one_side'
    lower, upper = left['lower'] - right['upper'], left['upper'] - right['lower']
    decision = (relation(lower, upper) if left['defined_for_all_completions'] and right['defined_for_all_completions']
                else 'undefined_possible')
    return lower, upper, decision


def verify_snapshot(snapshot, left, right, admitted):
    check_snapshot(snapshot, left, right, admitted)
    models = (reconstruct(left, admitted), reconstruct(right, admitted))
    for metric in ('J', 'A', 'C'):
        lower, upper, decision = separate_bounds(models, metric)
        observed = snapshot['independent_' + metric]
        require((lower, upper, decision) == (None if observed['lower'] is None else F(observed['lower']),
                                            None if observed['upper'] is None else F(observed['upper']),
                                            observed['decision']), 'separate baseline is not the exact same-information interval')
    return models


def target_decision(models, target):
    if target == 'J':
        return joint_comparison(*models)['relation']
    result = conditional_comparison(*models)['decision']
    return 'undefined_everywhere_for_at_least_one_side' if result == 'undefined_everywhere' else result


def next_public_query(left, right, admitted, attempted, policy):
    universe = set(left) | set(right)
    remaining = universe - attempted
    if not remaining:
        return None
    pairs = {g: (left.get(g, (0, 0)), right.get(g, (0, 0))) for g in universe}
    if policy == 'joint_width_per_suite':
        return min(remaining, key=lambda g: (-abs(pairs[g][0][0] - pairs[g][1][0]), g))
    require(policy == 'conditional_differences_first', 'unexpected native audit policy')
    different = {g for g, (l, r) in pairs.items() if tuple(l) != tuple(r)}
    pending = different - attempted
    if pending:
        return min(pending, key=lambda g: (-sum(abs(x - y) for x, y in zip(*pairs[g])), g))
    if different - set(admitted):
        return min(remaining)
    models = (reconstruct(left, admitted), reconstruct(right, admitted))
    dn = models[0].known_joint - models[1].known_joint
    dm = models[1].known_valid - models[0].known_valid
    return min(remaining, key=lambda g: (-abs(dn * pairs[g][0][1] + dm * pairs[g][0][0]), g))


def receiving_controls():
    checks = []
    good = {'status': 'passed', 'error': None, 'observations': []}
    require(receive_humaneval(json.dumps(good), 0, None) is True, 'HE positive control')
    checks.append('whole HumanEval support requires a completed successful envelope')
    require(receive_humaneval(json.dumps(good), None, 'wall_timeout') is None, 'HE timeout control')
    require(receive_humaneval('{"status":', None, 'wall_timeout') is None, 'HE truncated envelope')
    checks.append('HumanEval interruption and incomplete JSON remain unavailable')
    unknown = dict(good, status='unavailable', error={'reason': 'observer_error'})
    require(receive_humaneval(json.dumps(unknown), 0, None) is None, 'HE observer boundary')
    checks.append('HumanEval observer failure is unavailable')
    compile_ok = {'event': 'source_compile', 'status': 'passed', 'error': None}
    failed = {'event': 'test_result', 'test_index': 0, 'status': 'failed',
              'error': {'phase': 'original_assertion', 'type': 'builtins.AssertionError'}}
    resource = {'event': 'test_result', 'test_index': 1, 'status': 'unavailable',
                'error': {'phase': 'original_assertion', 'type': 'builtins.MemoryError'}}
    stream = lambda es: '\n'.join(json.dumps(e) for e in es) + '\n'
    require(receive_mbpp(stream([compile_ok, failed]), 2, None, 'wall_timeout') is False, 'retained failed assertion')
    require(receive_mbpp(stream([compile_ok, failed, resource]), 2, 0, None) is False, 'failed plus resource')
    require(receive_mbpp(stream([compile_ok, failed]) + '{"event":', 2, None, 'wall_timeout') is False, 'failed plus partial tail')
    checks.append('a complete MBPP contradiction survives timeout, resource failure, or a truncated later record')
    require(receive_mbpp(stream([compile_ok, resource]), 2, 0, None) is None, 'resource-only unknown')
    checks.append('resource-only MBPP evidence remains unavailable')
    malformed = dict(resource, status='failed')
    try:
        receive_mbpp(stream([compile_ok, malformed]), 2, 0, None)
    except ValueError:
        checks.append('MemoryError mislabeled as a contradiction is rejected')
    else:
        raise ValueError('false resource contradiction accepted')
    for bad in ([compile_ok, failed, failed],
                [compile_ok, dict(failed, status='evidence_rejected')]):
        try:
            receive_mbpp(stream(bad), 2, 0, None)
        except ValueError:
            pass
        else:
            raise ValueError('duplicate or rejected evidence accepted')
    checks.append('duplicate assertions and rejected contracts do not supply labels')
    return checks


def verify(artifact, registry_path, audit, destination):
    artifact, audit = artifact.resolve(), audit.resolve()
    registry_bytes = registry_path.read_bytes()
    registry = json.loads(registry_bytes)
    receipt_bytes = (audit / 'receipt.json').read_bytes()
    receipt = json.loads(receipt_bytes)
    require(receipt.get('status') == 'PASS', 'producer did not complete the native replay')
    require(receipt['public_registry_sha256'] == digest(registry_bytes), 'public registry changed')
    here = Path(__file__).resolve().parent
    require(receipt['driver_sha256'] == digest((here / 'audit_native.py').read_bytes()), 'native driver code changed after execution')
    require(receipt['analysis_sha256'] == digest((here / 'natural_analysis.py').read_bytes()), 'analysis code changed after native execution')
    require(receipt['candidate_observation_files_read_before_selection'] == 0, 'native driver reports historical candidate reads')
    groups, rows = registry['groups'], registry['rows']
    by_version = {v: set() for v in ('stock', 's1', 's4', 's1_s4')}
    for row in rows:
        require(not (FORBIDDEN & set(row)), 'candidate evidence leaked into a public row')
        require(type(row['suite_cost']) is int and row['suite_cost'] == 1, 'unexpected suite cost')
        require(type(row['detected']) is bool, 'unobserved detector outcome')
        g = group_identity(row)
        require(g == row['source_contract_sha256'] and g in groups, 'invalid row-to-group binding')
        for field in ('dataset', 'task_id', 'reference_sha256', 'candidate_sha256', 'contract_sha256'):
            require(row[field] == groups[g][field], 'row/group metadata disagreement')
        workload = tuple(row[k] for k in ('dataset', 'task_id', 'key_id', 'key_hex'))
        version = ALIASES[row['variant']]
        require(workload not in by_version[version], 'duplicate workload row')
        by_version[version].add(workload)
    require(all(s == by_version['stock'] for s in by_version.values()), 'mismatched attempted workload')
    require(set(groups) == {row['source_contract_sha256'] for row in rows}, 'orphan or missing public group')
    asset_cache, contracts, references_identical = {}, {}, set()
    roles = defaultdict(set)

    def asset(relative, role, expected=None):
        path = bounded_path(artifact, relative)
        roles[role].add(path.relative_to(artifact).as_posix())
        if path not in asset_cache:
            asset_cache[path] = path.read_bytes()
        content = asset_cache[path]
        require(expected is None or digest(content) == expected, f'{role} digest mismatch')
        return content

    def check_observer(directory, expected):
        candidates = sorted((artifact / directory).glob('native_runner*.py'))
        matches = [path for path in candidates if digest(path.read_bytes()) == expected]
        require(bool(matches), 'no installed native observer matches the contract digest')
        return asset(matches[0].relative_to(artifact).as_posix(), 'native_observer', expected)

    environment = receipt['environment']
    for g, info in groups.items():
        require(group_identity(info) == g, 'invalid group identity')
        source = asset(info['source_file'], 'candidate_source', info['candidate_sha256'])
        reference = asset(info['reference_file'], 'reference_source', info['reference_sha256'])
        contract = json.loads(asset(info['contract_file'], 'contract'))
        require(digest(canonical(contract)) == info['contract_sha256'], 'contract identity mismatch')
        contracts[g] = contract
        raw = asset(info['reference_observation_file'], 'reference_setup', info['reference_observation_sha256'])
        if info['reference_observation_file'].endswith('.gz'):
            raw = gzip.decompress(raw)
        setup = json.loads(raw)
        require(setup.get('status') == 'passed', 'reference setup is not qualified')
        if source == reference:
            require(info['candidate_sha256'] == info['reference_sha256'], 'equal source bytes have unequal digest declarations')
            references_identical.add(g)
        if info['dataset'] == 'HumanEval':
            require(contract['interpreter_executable_sha256'] == environment['interpreter_executable_sha256']
                    and contract['platform'] == environment['platform'], 'HumanEval runtime differs from declared execution')
            check_observer('external-studies/sew_natural/scripts/humaneval', contract['observer_sha256'])
            require(receive_humaneval(json.dumps(setup), 0, None) is True, 'HumanEval reference envelope not supported')
        else:
            native = contract.get('native_contract', contract.get('original_native_contract', contract))
            env = contract.get('execution_environment', native.get('execution_environment', {}))
            require(env.get('interpreter_executable_sha256') == environment['interpreter_executable_sha256']
                    and env.get('platform') == environment['platform'], 'MBPP runtime differs from declared execution')
            check_observer('external-studies/sew_natural/mbpp/scripts', native['native_runner_sha256'])
            reference_stdout = '\n'.join(json.dumps(e) for e in setup['events'])
            require(receive_mbpp(reference_stdout, len(native['test_list']), setup['returncode'], setup.get('interruption')) is True,
                    'MBPP reference envelopes not supported')
    require(len(receipt['cases']) == len(CASES), 'unexpected native comparison inventory')
    checked_prefixes = checked_queries = 0
    case_reports = []
    file_bindings = {'receipt.json': digest(receipt_bytes)}
    for expected, entry in zip(CASES, receipt['cases']):
        dataset, left_name, right_name, target, policy = expected
        name = f'{dataset}__{left_name}__{right_name}__{target}'
        require(entry['case'] == name, 'native case inventory or order changed')
        certificate_path = bounded_path(audit, name + '/certificate.json')
        trace_path = bounded_path(audit, name + '/trace.json')
        certificate_bytes, trace_bytes = certificate_path.read_bytes(), trace_path.read_bytes()
        certificate, trace = json.loads(certificate_bytes), json.loads(trace_bytes)
        require({k: v for k, v in certificate.items() if k != 'queries'} == entry,
                'receipt case summary disagrees with its certificate')
        require(tuple(certificate[k] for k in ('dataset', 'left', 'right', 'target', 'policy')) == expected,
                'native comparison metadata changed')
        file_bindings[name + '/certificate.json'] = digest(certificate_bytes)
        file_bindings[name + '/trace.json'] = digest(trace_bytes)
        coefficients = {left_name: defaultdict(lambda: [0, 0]), right_name: defaultdict(lambda: [0, 0])}
        for row in rows:
            version = ALIASES[row['variant']]
            if row['dataset'] != dataset or version not in coefficients:
                continue
            c = coefficients[version][row['source_contract_sha256']]
            c[0] += row['detected']; c[1] += 1
        left, right = coefficients[left_name], coefficients[right_name]
        denominator = sum(b for a, b in left.values())
        require(denominator == sum(b for a, b in right.values()) == certificate['denominator'], 'workload denominator mismatch')
        universe = set(left) | set(right)
        admitted = {g: True for g in universe & references_identical}
        attempted = set(admitted)
        require(len(admitted) == certificate['initial_reference_groups'], 'free admission was not exact reference identity')
        queries = certificate['queries']
        require(len(queries) == certificate['candidate_suite_queries'] and len(trace) == len(queries) + 1,
                'query and prefix trace lengths disagree')
        elapsed = 0.0
        for step in range(len(queries) + 1):
            models = verify_snapshot(trace[step], left, right, admitted)
            decision = target_decision(models, target)
            checked_prefixes += 1
            if step == len(queries):
                require(decision in CERTIFICATES and decision == certificate['decision'], 'final native evidence does not certify the claimed comparison')
                require(trace[step] == certificate['final_snapshot'], 'final trace and certificate disagree')
                break
            require(decision not in CERTIFICATES, 'native audit continued after its first certificate')
            query = queries[step]
            require(query['step'] == step + 1, 'nonconsecutive query index')
            g = query['group']
            require(g in universe and g not in attempted, 'queried a free, repeated, or unrelated group')
            require(next_public_query(left, right, admitted, attempted, policy) == g, 'query choice differs from the public policy at this received history')
            path = bounded_path(audit, query['evidence_file'])
            blob = path.read_bytes()
            require(digest(blob) == query['evidence_sha256'], 'fresh observation digest mismatch')
            file_bindings[query['evidence_file']] = digest(blob)
            observation = json.loads(blob)
            require(observation['group'] == g and observation['source_sha256'] == groups[g]['candidate_sha256']
                    and observation['contract_sha256'] == groups[g]['contract_sha256'], 'fresh observation bound to the wrong obligation')
            cost = observation['elapsed_seconds']
            require(type(cost) in (float, int) and math.isfinite(cost) and cost >= 0, 'invalid recorded elapsed duration')
            elapsed += cost
            if dataset == 'HumanEval':
                received = receive_humaneval(observation['stdout'], observation['returncode'], observation['interruption'])
            else:
                native = contracts[g].get('native_contract', contracts[g].get('original_native_contract', contracts[g]))
                received = receive_mbpp(observation['stdout'], len(native['test_list']), observation['returncode'], observation['interruption'])
            require(strict_label(observation['received_label']) is received and strict_label(query['received_label']) is received,
                    'reported native label disagrees with actual stdout evidence')
            attempted.add(g)
            if received is not None:
                admitted[g] = received
            checked_queries += 1
        require(certificate['seconds'] + 1e-6 >= elapsed, 'case elapsed time is below its suite durations')
        case_reports.append(dict(case=name, target=target, policy=policy, candidate_suite_queries=len(queries),
                                 decision=certificate['decision'], reference_groups=certificate['initial_reference_groups'],
                                 candidate_elapsed_seconds_sum=elapsed, case_elapsed_seconds=certificate['seconds']))
    require(checked_queries == receipt['total_candidate_suite_queries'], 'total suite-query count mismatch')
    controls = receiving_controls()
    report = dict(status='PASS', schema='markvalidity-independent-native-receiving-v1',
                  public_registry_sha256=digest(registry_bytes), native_receipt_sha256=digest(receipt_bytes),
                  verifier_sha256=digest(Path(__file__).read_bytes()),
                  exact_prototype_sha256=digest((here / 'conditional_bounds.py').read_bytes()),
                  prefix_verifier_sha256=digest((here / 'verify_natural_results.py').read_bytes()),
                  cases=case_reports, received_candidate_suite_records=checked_queries,
                  independently_recomputed_prefixes=checked_prefixes,
                  historical_candidate_labels_read=0, historical_candidate_observation_files_read=0,
                  new_native_suites_executed_by_verifier=0,
                  checked_asset_files_by_role={role: len(paths) for role, paths in roles.items()},
                  receiving_boundary_controls=controls, bound_fresh_files_sha256=file_bindings)
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'received_candidate_suite_records', 'independently_recomputed_prefixes', 'cases')}, indent=2))
    return report


if __name__ == '__main__':
    if not __debug__:
        raise SystemExit('Run without -O: the independent Fraction checks require assertions.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path)
    parser.add_argument('--registry', type=Path)
    parser.add_argument('--audit', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({'status': 'PASS', 'controls': receiving_controls()}, indent=2))
    else:
        if not all((args.artifact, args.registry, args.audit)):
            parser.error('--artifact, --registry and --audit are required')
        verify(args.artifact, args.registry, args.audit,
               args.output or args.audit / 'independent-receiving.json')
