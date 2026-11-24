#!/usr/bin/env python3
"""Receive every new native observation and independently reconstruct stopping.

Reads the public registry, qualified references and the newly recorded stdout
only. It does not open historical candidate labels, replay analyses or producer
policy/state code. Repeated identical histories reuse an already independently
reconstructed arithmetic state; each raw execution record is still received.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path

from independent import ANALYSIS, bounds, check_bounds, coefficients, next_query, require
from verify_native_audit import receive_humaneval, receive_mbpp


CERTIFICATES = {'left_strict', 'right_strict', 'tie'}
FORBIDDEN = {'validity_label', 'validity', 'candidate_status', 'joint', 'observation_path',
             'candidate_elapsed_seconds', 'candidate_function_invocations', 'assertion_entries'}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def sha(content):
    return hashlib.sha256(content).hexdigest()


def bounded(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root), 'input path escapes its declared root')
    return path


def native_record(stdout, dataset, expected_tests, returncode, interruption):
    if dataset == 'HumanEval':
        try:
            json.loads(stdout)
        except (ValueError, TypeError):
            require(interruption or returncode != 0, 'malformed completed HumanEval evidence')
        # This is the earlier independent receiver, separate from admission.py.
        return receive_humaneval(stdout, returncode, interruption)
    label = receive_mbpp(stdout, expected_tests, returncode, interruption)
    events = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue  # The reference receiver already validates incomplete tails.
        events.append(value)
    require(all(event.get('event') in {'source_compile', 'test_result', 'complete'} for event in events),
            'unexpected MBPP event')
    for event in events:
        if event.get('event') == 'complete':
            continue
        if event['status'] == 'passed':
            require(event.get('error') is None, 'passing MBPP record has an exception')
        elif event['status'] == 'failed':
            problem = event['error']
            require(isinstance(problem.get('type'), str) and problem['type']
                    and problem.get('errno') not in (12, 'ENOMEM') and not problem.get('reason'),
                    'MBPP resource/observer interruption is not a program contradiction')
    tests = [event for event in events if event.get('event') == 'test_result']
    terminal = [event for event in events if event.get('event') == 'complete']
    if terminal:
        require(events[-1] is terminal[0], 'records follow MBPP completion')
        require(terminal[0]['evidence_schema'] == 'markvalidity-mbpp-original-assertions-v2',
                'unexpected MBPP envelope version')
        counts = Counter(event['status'] for event in tests)
        require(terminal[0]['scheduled_tests'] == expected_tests
                and terminal[0]['completed_tests'] == len(tests), 'contradictory MBPP terminal count')
        for field, status in [('passed_tests', 'passed'), ('failed_tests', 'failed'),
                              ('unavailable_tests', 'unavailable'), ('rejected_tests', 'evidence_rejected')]:
            require(type(terminal[0][field]) is int and terminal[0][field] == counts[status], 'terminal event contradicts assertion statuses')
        if label is False:
            require(terminal[0]['status'] == 'failed', 'terminal contradicts retained failure witness')
        if terminal[0]['status'] == 'failed':
            require(label is False, 'terminal failure lacks a complete program witness')
        if terminal[0]['status'] == 'passed':
            compiles = [event for event in events if event.get('event') == 'source_compile']
            require(len(compiles) == 1 and compiles[0]['status'] == 'passed'
                    and len(tests) == expected_tests and counts['passed'] == expected_tests,
                    'terminal support lacks all required passing records')
    return label


def receive(root, registry_path, native):
    root, native = root.resolve(), native.resolve()
    top = json.loads((native / 'receipt.json').read_text())
    protocol = json.loads((native / 'protocol.json').read_text())
    setup = json.loads((native / 'common-registration.json').read_text())
    registry_bytes = registry_path.read_bytes()
    registry = json.loads(registry_bytes)
    require(top['status'] == 'COMPLETE' and protocol['repeats'] == 3 and len(top['runs']) == 24, 'incomplete timing matrix')
    require(top['protocol_sha256'] == sha((native / 'protocol.json').read_bytes()), 'changed frozen run order')
    require(top['common_registration_sha256'] == sha((native / 'common-registration.json').read_bytes()), 'changed public registration')
    require(sha(registry_bytes) == top['public_registry_sha256'] == protocol['public_registry_sha256'] == setup['public_registry_sha256'],
            'changed public registry')
    require(not top['cross_run_candidate_label_reuse'] and not protocol['candidate_label_cache_between_runs'], 'cross-run candidate cache is outside the protocol')
    rows, groups, contracts = registry['rows'], registry['groups'], {}
    for row in rows:
        require(not FORBIDDEN & set(row), 'public candidate-label leak')
        identifier = sha(canonical({key: row[key] for key in ('reference_sha256', 'candidate_sha256', 'contract_sha256')}))
        require(identifier == row['source_contract_sha256'] and identifier in groups, 'changed row identity')
    actual_assets = {}

    def checked(relative, expected=None):
        data = bounded(root, relative).read_bytes()
        checksum = sha(data)
        require(expected is None or checksum == expected, 'changed public asset ' + relative)
        actual_assets[relative] = checksum
        return data

    for group, metadata in groups.items():
        require(not FORBIDDEN & set(metadata), 'public group-label leak')
        identity = {key: metadata[key] for key in ('reference_sha256', 'candidate_sha256', 'contract_sha256')}
        require(sha(canonical(identity)) == group, 'changed group identity')
        checked(metadata['source_file'], metadata['candidate_sha256'])
        checked(metadata['reference_file'], metadata['reference_sha256'])
        contract = json.loads(checked(metadata['contract_file']))
        require(sha(canonical(contract)) == metadata['contract_sha256'], 'changed contract')
        data = checked(metadata['reference_observation_file'], metadata['reference_observation_sha256'])
        if metadata['reference_observation_file'].endswith('.gz'):
            data = gzip.decompress(data)
        require(json.loads(data)['status'] == 'passed', 'reference is not qualified')
        contracts[group] = contract
    require(actual_assets == setup['asset_files_sha256'], 'public registration inventory differs')
    paths = {'native_timing.py': Path(__file__).with_name('native_timing.py'),
             'policies.py': Path(__file__).with_name('policies.py'),
             'analyze.py': Path(__file__).with_name('analyze.py'),
             'admission.py': Path(__file__).with_name('admission.py'),
             'natural_analysis.py': ANALYSIS / 'natural_analysis.py',
             'humaneval_runner': root / 'external-studies/sew_natural/scripts/humaneval/native_runner_v3.py',
             'mbpp_runner': root / 'external-studies/sew_natural/mbpp/scripts/native_runner_v2.py'}
    if protocol.get('counterbalance_block') == 'complementary_reverse_order':
        paths['native_timing_reverse.py'] = Path(__file__).with_name('native_timing_reverse.py')
    require(set(paths) == set(protocol['source_sha256']), 'missing or unexpected producer dependency')
    for name, path in paths.items():
        require(sha(path.read_bytes()) == protocol['source_sha256'][name], 'changed timing producer dependency ' + name)
    snapshots = (native / 'source-snapshots' if 'source_snapshot_manifest_sha256' in protocol
                 else native.parent / 'source-snapshots' / native.name)
    snapshot_bytes = (snapshots / 'manifest.json').read_bytes()
    snapshot_inventory = json.loads(snapshot_bytes)
    if 'source_snapshot_manifest_sha256' in protocol:
        require(sha(snapshot_bytes) == protocol['source_snapshot_manifest_sha256'], 'changed pre-execution source snapshot inventory')
    else:
        require(snapshot_inventory['protocol_sha256'] == top['protocol_sha256'], 'source snapshots refer to a different first block')
    require(set(snapshot_inventory['files']) == set(paths), 'source snapshot inventory incomplete')
    for name, item in snapshot_inventory['files'].items():
        require(bounded(root, item['original_path']) == paths[name].resolve(), 'snapshot has a different original source path')
        require(sha(bounded(snapshots.resolve(), item['snapshot_file']).read_bytes()) == item['sha256'] == protocol['source_sha256'][name],
                'snapshot bytes do not match the frozen producer')
    cache, reports = {}, []
    received, prefixes = 0, 0
    for ordinal, (planned, summary) in enumerate(zip(protocol['run_order'], top['runs']), start=1):
        require(summary['ordinal'] == ordinal and all(summary[k] == v for k, v in planned.items()), 'run differs from frozen interleaving')
        folder = bounded(native, summary['directory'])
        record = json.loads((folder / 'receipt.json').read_text())
        require({k: value for k, value in record.items() if k != 'queries'} == summary, 'per-run receipt differs from aggregate')
        phases = record['phase_seconds']
        require(all(type(value) is float and math.isfinite(value) and value >= 0 for value in phases.values()), 'invalid measured phase time')
        require(math.isfinite(record['audit_total_seconds']) and record['audit_total_seconds'] >= sum(phases.values()), 'phase accounting exceeds total time')
        require(abs(record['unallocated_loop_seconds'] - (record['audit_total_seconds'] - sum(phases.values()))) < 1e-9, 'loop-time accounting differs')
        trace_bytes = (folder / 'trace.json').read_bytes()
        require(sha(trace_bytes) == record['trace_sha256'], 'changed native prefix trace')
        trace = json.loads(trace_bytes)
        left, right, denominator = coefficients(rows, planned['dataset'], planned['left'], planned['right'])
        require(denominator == record['denominator'], 'wrong native workload denominator')
        seeds = {group: True for group in set(left) | set(right)
                 if groups[group]['reference_sha256'] == groups[group]['candidate_sha256']}
        admitted, attempted = dict(seeds), set(seeds)
        require(len(seeds) == record['initial_reference_groups'], 'wrong initial reference admissions')
        queries = record['queries']
        require(len(queries) == record['candidate_suite_queries'] and len(trace) == len(queries) + 1, 'missing native execution or prefix')
        history = hashlib.sha256(canonical(sorted(seeds.items())))
        case = (planned['dataset'], planned['left'], planned['right'], planned['method'], planned['target'])
        for step, snapshot in enumerate(trace):
            require(snapshot['step'] == step and snapshot['groups_admitted'] == len(admitted), 'changed prefix position or admissions')
            key = (case, history.hexdigest())
            if key not in cache:
                expectation = bounds(left, right, admitted, planned['method'], planned['target'])
                selected = (next_query(left, right, admitted, attempted, planned['method'], planned['target'])
                            if expectation['decision'] not in CERTIFICATES else None)
                cache[key] = (expectation, selected)
            expected, selected = cache[key]
            check_bounds(snapshot['bounds'], expected)
            prefixes += 1
            if step == len(queries):
                require(expected['decision'] in CERTIFICATES and record['decision'] == expected['decision'], 'final native state is not a certificate')
                check_bounds(record['final_bounds'], expected)
                break
            require(expected['decision'] not in CERTIFICATES, 'native execution continued past its first certificate')
            query = queries[step]
            require(query['step'] == step + 1 and query['group'] == selected and selected not in attempted, 'selection used something outside the public policy/history')
            evidence_bytes = bounded(native, query['evidence_file']).read_bytes()
            require(sha(evidence_bytes) == query['evidence_sha256'], 'changed native execution record')
            evidence = json.loads(evidence_bytes)
            metadata, contract = groups[selected], contracts[selected]
            require(evidence['group'] == selected and evidence['source_sha256'] == metadata['candidate_sha256']
                    and evidence['contract_sha256'] == metadata['contract_sha256'], 'execution has wrong source or contract')
            original = contract.get('native_contract', contract.get('original_native_contract', contract))
            expected_tests = len(original['test_list']) if planned['dataset'] == 'mbpp_sanitized' else None
            label = native_record(evidence['stdout'], planned['dataset'], expected_tests,
                                  evidence['returncode'], evidence['interruption'])
            require(query['received_label'] is None or type(query['received_label']) is bool, 'non-Boolean native label')
            require(label is query['received_label'] and label is evidence['received_label'], 'native label does not follow from new stdout')
            attempted.add(selected)
            if label is not None:
                admitted[selected] = label
            history.update(canonical((selected, label)))
            received += 1
        reports.append({'directory': record['directory'], 'candidate_suite_queries': len(queries),
                        'first_certificate': record['decision'], 'all_query_identities_and_prefixes_checked': True})
    require(received == top['total_candidate_suite_queries'], 'aggregate native query count differs')
    output = {'schema': 'markvalidity-independent-native-cost-receiving-v1', 'status': 'PASS',
              'scope': 'Every raw new candidate execution and every prefix checked from public coefficients and admitted replies. Exact Fraction reconstruction and public-policy choice are independent of producer state and policy code.',
              'public_registry_sha256': sha(registry_bytes), 'native_receipt_sha256': sha((native/'receipt.json').read_bytes()),
              'runs_received': len(reports), 'candidate_suite_records_received': received,
              'prefixes_received': prefixes, 'distinct_arithmetic_prefixes_reconstructed': len(cache),
              'historical_candidate_labels_read': 0, 'historical_candidate_observation_files_read': 0,
              'candidate_programs_executed_by_receiver': 0,
              'counterbalance_block': protocol.get('counterbalance_block', 'initial_order'),
              'source_snapshots_received': len(paths), 'source_snapshot_manifest_sha256': sha(snapshot_bytes),
              'identical_history_cache': 'An already independently reconstructed public/history state is reused across repetitions; every new raw stdout and its identity is still checked.',
              'source_sha256': {name: sha(Path(__file__).with_name(name).read_bytes()) for name in ('verify_native.py', 'independent.py')},
              'reference_math_sha256': sha((ANALYSIS/'conditional_bounds.py').read_bytes()),
              'independent_admission_reference_sha256': sha((ANALYSIS/'verify_native_audit.py').read_bytes()),
              'runs': reports}
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--out', type=Path, help='Write a fresh receiving report; omission performs read-only receiving.')
    args = parser.parse_args()
    output = receive(args.artifact, args.registry, args.native)
    if args.out:
        if args.out.exists():
            raise ValueError('fresh independent receiving report required')
        args.out.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({k: output[k] for k in ('status', 'runs_received', 'candidate_suite_records_received', 'prefixes_received', 'distinct_arithmetic_prefixes_reconstructed')}, indent=2))


if __name__ == '__main__':
    main()
