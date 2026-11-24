#!/usr/bin/env python3
"""Derive publication tables from frozen own-order analyses and native receipts."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
from statistics import median


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interval(values):
    values = list(values)
    return {'median': median(values), 'minimum': min(values), 'maximum': max(values),
            'values_in_repeat_order': values}


def derive(root, results):
    bound = {}

    def read(relative):
        path = results / relative
        bound[relative] = sha(path)
        return json.loads(path.read_text())

    analyses = {mode: read(folder + '/analysis.json') for mode, folder in
                [('reference_identity_known', 'retrospective-primary'),
                 ('all_withheld', 'retrospective-all-withheld')]}
    block_names = ('native-timing', 'native-timing-reverse')
    blocks = []
    for name, receiving_file in zip(block_names, ('native-receiving.json', 'native-receiving-reverse.json')):
        blocks.append({'block': name, 'receipt': read(name + '/receipt.json'),
                       'protocol': read(name + '/protocol.json'),
                       'common': read(name + '/common-registration.json'),
                       'receiving': read(receiving_file)})
    first_protocol, second_protocol = [block['protocol'] for block in blocks]
    if second_protocol['complement_of_protocol_sha256'] != bound['native-timing/protocol.json']:
        raise ValueError('second timing block is not bound to the distributed first block')
    if (first_protocol['public_registry_sha256'] != second_protocol['public_registry_sha256']
            or first_protocol['environment'] != second_protocol['environment']):
        raise ValueError('timing blocks use different public inputs or runtime')
    for name, checksum in first_protocol['source_sha256'].items():
        if second_protocol['source_sha256'].get(name) != checksum:
            raise ValueError('common timing dependency changed across blocks: ' + name)
    first_order, second_order = first_protocol['run_order'], second_protocol['run_order']
    if len(first_order) != 24 or len(second_order) != 24:
        raise ValueError('complete complementary blocks require 24 runs each')
    for index in range(0, 24, 2):
        if second_order[index:index + 2] != list(reversed(first_order[index:index + 2])):
            raise ValueError('second block does not reverse each method pair while retaining case order')
    retrospective_received = read('retrospective-receiving.json')
    policy_controls = read('policy-controls.json')
    admission_controls = read('admission-controls.json')
    if any(report['status'] != 'COMPLETE' for report in analyses.values()) or any(block['receipt']['status'] != 'COMPLETE' for block in blocks):
        raise ValueError('incomplete comparison evidence')
    if any(report['status'] != 'PASS' for report in (retrospective_received, policy_controls, admission_controls)) or any(block['receiving']['status'] != 'PASS' for block in blocks):
        raise ValueError('failed comparison receiving or controls')
    pairs = []
    for mode, analysis in analyses.items():
        for case, report in analysis['reports'].items():
            row = {'case': case, 'initialization': mode, 'scope': report['scope'],
                   'left': report['left'], 'right': report['right'], 'denominator': report['denominator']}
            for name, run in report['runs'].items():
                row[name + '_queries'] = run['first_certificate']['suite_queries']
            for method, witness in report['hindsight_joint_witness'].items():
                row[method + '_J_hindsight_minimum'] = witness['minimum_queries']
            pairs.append(row)
    grouped = defaultdict(list)
    for block in blocks:
        for run in block['receipt']['runs']:
            value = dict(run, block=block['block'], run_path=block['block'] + '/' + run['directory'])
            grouped[(run['scope'], run['left'], run['right'], run['target'], run['method'])].append(value)
    timing = []
    for key in sorted(grouped, key=lambda key: (key[0], key[3] != 'J', key[4] != 'coupled')):
        runs = sorted(grouped[key], key=lambda run: (block_names.index(run['block']), run['repeat']))
        if [(run['block'], run['repeat']) for run in runs] != [(block, repeat) for block in block_names for repeat in (1, 2, 3)]:
            raise ValueError('six complete serial repeats, identified by block and repeat, are required')
        positions = ['first' if run['ordinal'] % 2 else 'second' for run in runs]
        if positions.count('first') != 3 or positions.count('second') != 3:
            raise ValueError('method order is not balanced three first and three second')
        counts = {run['candidate_suite_queries'] for run in runs}
        if len(counts) != 1:
            raise ValueError('native stopping counts differed across repeats')
        case = '__'.join(key[:3])
        expected = analyses['reference_identity_known']['reports'][case]['runs'][key[4] + '_' + key[3]]['first_certificate']
        if counts != {expected['suite_queries']} or any(run['decision'] != expected['decision'] for run in runs):
            raise ValueError('new native result disagrees with fixed-ledger analysis')
        row = {'case': case, 'scope': key[0], 'left': key[1], 'right': key[2],
               'target': key[3], 'method': key[4], 'policy': runs[0]['policy'],
               'candidate_suite_queries': counts.pop(), 'repeats': 6,
               'additional_audit_seconds': interval(run['audit_total_seconds'] for run in runs),
               'phase_seconds': {phase: interval(run['phase_seconds'][phase] for run in runs)
                                for phase in runs[0]['phase_seconds']},
               'unallocated_loop_seconds': interval(run['unallocated_loop_seconds'] for run in runs),
               'run_directories': [run['run_path'] for run in runs],
               'measurement_order': [{'block': run['block'], 'repeat': run['repeat'],
                                      'within_case_position': position, 'run_path': run['run_path']}
                                     for run, position in zip(runs, positions)]}
        timing.append(row)
    preparations = [dict(block=block['block'], **{key: block['common'][key] for key in
                                                ('load_seconds', 'validate_register_seconds', 'total_seconds',
                                                 'public_rows', 'public_groups', 'candidate_observation_files_read', 'scope')})
                    for block in blocks]
    receiving_fields = ('runs_received', 'candidate_suite_records_received', 'prefixes_received',
                        'historical_candidate_labels_read', 'historical_candidate_observation_files_read')
    received = {'status': 'PASS', **{key: sum(block['receiving'][key] for block in blocks) for key in receiving_fields},
                'arithmetic_prefixes_reconstructed_across_blocks': sum(block['receiving']['distinct_arithmetic_prefixes_reconstructed'] for block in blocks),
                'arithmetic_count_scope': 'Distinct histories are counted within each independently received block; a history repeated in the other block is reconstructed again.',
                'by_block': [{'block': block['block'], **{key: block['receiving'][key] for key in
                             (*receiving_fields, 'distinct_arithmetic_prefixes_reconstructed', 'source_snapshots_received')}} for block in blocks]}
    output = {
        'schema': 'markvalidity-comparison-cost-summary-v1', 'status': 'COMPLETE',
        'scope': 'Own-order retrospective analyses of fixed actual benchmark observations, plus new serial native audit timing. No embedding/detection-generation speed or population timing inference.',
        'source_sha256': {'summarize.py': sha(Path(__file__))}, 'input_sha256': bound,
        'policies': {
            'coupled_J': 'Descending absolute a_L-a_R, then group identity.',
            'independent_J': 'Descending a_L+a_R, skip zero contribution, then group identity.',
            'coupled_C': 'Resolve coefficient-different H first, then descending absolute common-remainder margin coefficient; deterministic identity tie break.',
            'independent_C': 'Minimize worst Boolean next-response sum of individual conditional interval widths; public coefficient-equivalent groups share calculation but not labels; identity tie break. Empty defined subset has span zero only for this heuristic, never for certification.'},
        'pair_comparisons': pairs,
        'native_timing': {
            'repeats': 6, 'repeats_per_block': 3, 'blocks': 2,
            'runs': sum(len(block['receipt']['runs']) for block in blocks),
            'candidate_suite_executions': sum(block['receipt']['total_candidate_suite_queries'] for block in blocks),
            'cross_run_candidate_label_reuse': any(block['receipt']['cross_run_candidate_label_reuse'] for block in blocks),
            'common_preparation': dict(preparations[0], compatibility_note='First block only; both separately measured preparation times are in common_preparations.'),
            'common_preparations': preparations,
            'phase_definitions': first_protocol['phase_definitions'], 'environment': first_protocol['environment'],
            'run_order': [dict(item, block=block['block']) for block in blocks for item in block['protocol']['run_order']],
            'counterbalance': {'status': 'PASS', 'first_positions_per_case_method': 3,
                               'second_positions_per_case_method': 3,
                               'design': 'Two complementary blocks preserve case rotation and reverse each within-case method pair. The first block is retained unchanged; the second block is bound to its exact protocol.'},
            'rows': timing,
            'accounting': 'Additional audit totals exclude public preparation, measured once in each of two blocks and reported separately. They include per-run coefficient/state/policy registration, query selection, requested bounds, real worker execution, admission, raw-record I/O and loop overhead. A fresh whole-audit invocation adds its preparation to either method. Medians of separate phases need not sum to the median total.',
            'interpretation': 'Six serial repeats per case and method, in two complementary blocks, describe these native executions on this recorded host. All 48 runs remain in the ranges. Public source/contract data are reused in memory within a block; candidate labels are not reused across runs, and OS caches are not claimed to be cleared. No statistical significance claim is made.'},
        'receiving': received,
        'retrospective_receiving': {key: retrospective_received[key] for key in
                                    ('status', 'case_initializations_received', 'schedules_received',
                                     'prefixes_received', 'historical_disclosures_received',
                                     'joint_hindsight_minima_received', 'new_candidate_program_executions')},
        'hindsight_scope': 'Exact minimum number of additional unit-cost group queries for the stated joint endpoint certificate, with fixed initial admissions and all realized labels known. This is a post hoc witness diagnostic, not an executable query strategy or a claim about additional semantic inference.',
        'nonoptimal_policy_example': {
            'case': 'humaneval__stock__s1', 'method': 'coupled', 'target': 'J',
            'observed_policy_queries': analyses['reference_identity_known']['reports']['humaneval__stock__s1']['runs']['coupled_J']['first_certificate']['suite_queries'],
            'hindsight_minimum_queries': analyses['reference_identity_known']['reports']['humaneval__stock__s1']['hindsight_joint_witness']['coupled']['minimum_queries'],
            'meaning': 'The width-based shared policy does not minimize first-certificate queries on this actual finite ledger.'},
        'structural_controls': 'HumanEval stock/S4 and S1/S1+S4 have identical output relations; their zero-query shared certificates are structural identity controls, not independent empirical speedup cases.'}
    return output


def table_bytes(summary):
    tables = {}
    stream = io.StringIO(newline='')
    pairs = summary['pair_comparisons']
    writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
    writer.writeheader()
    writer.writerows(pairs)
    tables['all-pair-query-costs.csv'] = stream.getvalue()
    rows = []
    for value in summary['native_timing']['rows']:
        row = {key: value[key] for key in ('case', 'scope', 'target', 'method', 'candidate_suite_queries', 'repeats')}
        for field in ('median', 'minimum', 'maximum'):
            row['additional_audit_seconds_' + field] = value['additional_audit_seconds'][field]
        for phase, stats in value['phase_seconds'].items():
            for field in ('median', 'minimum', 'maximum'):
                row[phase + '_' + field] = stats[field]
        rows.append(row)
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    tables['native-audit-costs.csv'] = stream.getvalue()
    return tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--write', action='store_true', help='Write derived summary and CSV tables; otherwise verify them read-only.')
    args = parser.parse_args()
    summary = derive(args.artifact.resolve(), args.results.resolve())
    content = json.dumps(summary, indent=2) + '\n'
    outputs = {'summary.json': content, **table_bytes(summary)}
    for relative, expected in outputs.items():
        path = args.results / relative
        if args.write:
            path.write_text(expected, newline='')
        else:
            with path.open(newline='') as stream:
                if stream.read() != expected:
                    raise ValueError('derived summary/table is stale: ' + relative)
    print(json.dumps({'status': 'PASS', 'mode': 'write' if args.write else 'read-only',
                      'pairs': len(summary['pair_comparisons']), 'timing_rows': len(summary['native_timing']['rows']),
                      'outputs': list(outputs)}, indent=2))


if __name__ == '__main__':
    main()
