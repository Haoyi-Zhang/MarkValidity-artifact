#!/usr/bin/env python3
"""Compare completed native audits with their retained retrospective prefixes.

This post-execution check reads both result sets. It is separate from native
selection and independent receiving, which do not read historical candidate
outcomes. Matching costs alone are insufficient: identities, received labels,
initial information and the complete final snapshots must also match.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compare(analysis, audit, output):
    bindings = {}

    def read(root, relative, role):
        data = (root / relative).read_bytes()
        bindings[role + '/' + relative] = sha(data)
        return json.loads(data)

    comparisons = read(analysis, 'comparisons.json', 'retrospective')
    groups = read(analysis, 'group_index.json', 'retrospective')
    retrospective = read(analysis, 'certificate_receiving.json', 'retrospective')
    receipt = read(audit, 'receipt.json', 'native')
    independent = read(audit, 'independent-receiving.json', 'native')
    require(retrospective['status'] == receipt['status'] == independent['status'] == 'PASS',
            'both result sets must first pass their independent receiving checks')
    require(independent['native_receipt_sha256'] == bindings['native/receipt.json'],
            'native independent receiving is stale')
    for name in ('comparisons.json', 'group_index.json'):
        require(retrospective['files_sha256'][name] == bindings['retrospective/' + name],
                'retrospective receiving is stale')
    reports = []
    for entry in receipt['cases']:
        certificate = read(audit, entry['case'] + '/certificate.json', 'native')
        require(independent['bound_fresh_files_sha256'][entry['case'] + '/certificate.json']
                == bindings['native/' + entry['case'] + '/certificate.json'],
                'native certificate changed after independent receiving')
        scope = {'HumanEval': 'humaneval', 'mbpp_sanitized': 'mbpp'}[entry['dataset']]
        case = comparisons[f"{scope}__{entry['left']}__{entry['right']}"]
        schedule = case['schedules'][entry['policy']]
        first = schedule['first_certificates']['coupled_' + entry['target']]
        queries = certificate['queries']
        count = len(queries)
        require(case['initialization'] == 'reference_identity_known'
                and case['reference_identity_known_groups'] == entry['initial_reference_groups'],
                'the two runs did not begin with the same admitted reference groups')
        require(case['denominator'] == entry['denominator'], 'different attempted workloads')
        require(count == entry['candidate_suite_queries'] == first['suite_queries'],
                'different first-certificate suite counts')
        require(entry['decision'] == first['decision']
                and entry['final_snapshot'] == first['snapshot'],
                'different final bounds or comparison decisions')
        expected_groups = [groups[index]['source_contract_sha256']
                           for index in schedule['schedule'][:count]]
        require(expected_groups == [q['group'] for q in queries],
                'different group-selection prefixes')
        trace = analysis / 'traces' / schedule['trace_file']
        bindings['retrospective/traces/' + schedule['trace_file']] = sha(trace.read_bytes())
        require(bindings['retrospective/traces/' + schedule['trace_file']] == schedule['trace_sha256'],
                'retrospective trace changed')
        with gzip.open(trace, 'rt') as stream:
            records = csv.DictReader(stream)
            initial = next(records)
            require(initial['step'] == '0' and initial['received_label'] == '',
                    'retrospective trace lacks its initialization')
            for step, query in enumerate(queries, 1):
                record = next(records)
                value = {'1': True, '0': False, '?': None}[record['received_label']]
                require(int(record['step']) == step
                        and groups[int(record['group_index'])]['source_contract_sha256'] == query['group']
                        and value is query['received_label'],
                        'fresh and historical received labels or identities differ')
        reports.append(dict(case=entry['case'], candidate_suite_queries=count,
                            decision=entry['decision'], prefix_identities_equal=True,
                            received_labels_equal=True, complete_final_snapshot_equal=True))
    report = dict(status='PASS', schema='markvalidity-native-retrospective-agreement-v1',
                  purpose='Post-execution comparison; neither native query selection nor independent native receiving reads these retrospective outcomes.',
                  checker_sha256=sha(Path(__file__).read_bytes()), cases=reports,
                  checked_queries=sum(r['candidate_suite_queries'] for r in reports),
                  files_sha256=bindings)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'checked_queries', 'cases')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    compare(args.analysis, args.audit, args.output or args.audit / 'retrospective-agreement.json')
