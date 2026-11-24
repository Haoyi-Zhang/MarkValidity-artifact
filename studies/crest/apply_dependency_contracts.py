#!/usr/bin/env python3
"""Apply only the two declared paired execution-contract amendments."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    source = ROOT / 'dependency-contracts'
    original = json.loads((source / 'receipts.json').read_text())
    selected = [r for r in original if r['cohort'] == 'gpt4o']
    selected += json.loads((source / 'numpy-receipts.json').read_text())
    assert len(selected) == 4
    previous = []
    for cohort, task_id in [('gpt4o', 'HumanEval/150'), ('qwen', 'HumanEval/32')]:
        target = ROOT / 'validated' / cohort
        rows = json.loads((target / 'results.json').read_text())
        applicable = [r for r in selected if r['cohort'] == cohort]
        assert {r['side'] for r in applicable} == {'reference', 'candidate'}
        assert all(r['task_id'] == task_id for r in applicable)
        row = next(r for r in rows if r['task_id'] == task_id)
        for item in applicable:
            name = item['side'] + '_native'
            assert row[name]['execution_request'] == item['native']['execution_request']
            previous.append({'cohort': cohort, 'task_id': task_id, 'side': item['side'],
                             'native': row[name]})
            row[name] = item['native']
        assert row['reference_native']['execution_environment'] == row['candidate_native']['execution_environment']
        assert row['reference_native']['observer_source_sha256'] == row['candidate_native']['observer_source_sha256']
        row['qualified_reference'] = row['reference_native']['label'] is True
        row['validity'] = row['candidate_native']['label'] if row['qualified_reference'] else None
        for model, record in row['classifiers'].items():
            d, v = record['detected'], row['validity']
            record['joint'] = False if v is False or d is False else (True if v is True and d is True else None)
        row['execution_contract_amendment'] = 'contract-amendment.json'
        row['reexecution_comparison'] = {'prior_contract': 'site-packages disabled',
                                         'reason': 'Declared third-party imports require site-enabled paired execution; NumPy numeric-scalar encoding is explicit.'}
        protocol = {
            'scope': 'Only this declared task execution environment and, for NumPy, observation encoding. Exact archived source, official prompt/test and CREST generation/detection remain unchanged.',
            'cohort': cohort, 'task_id': task_id,
            'dependency_protocol': 'dependency-contracts/protocol.json',
            'dependency_protocol_sha256': digest(source / 'protocol.json'),
            'import_incidence_sha256': digest(source / 'import-incidence.json'),
            'receipts_file': 'dependency-contracts/' + ('receipts.json' if cohort == 'gpt4o' else 'numpy-receipts.json'),
            'receipts_sha256': digest(source / ('receipts.json' if cohort == 'gpt4o' else 'numpy-receipts.json')),
            'observer_protocol': 'dependency-contracts/numpy-observer-protocol.json' if cohort == 'qwen' else None,
            'observer_protocol_sha256': digest(source / 'numpy-observer-protocol.json') if cohort == 'qwen' else None,
            'execution_environment': row['reference_native']['execution_environment'],
            'observer_file': row['reference_native']['observer_file'],
            'observer_source_sha256': row['reference_native']['observer_source_sha256']}
        write(target / 'contract-amendment.json', protocol)
        stem = row['dataset'].lower() + '-' + str(row['task_id']).replace('/', '-')
        write(target / 'records' / (stem + '.json'), row)
        write(target / 'results.json', rows)
        # This is a current-result index; original generation records are kept
        # separately and are never admitted as current behavioral evidence.
        (target / 'completed.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    historical = source / 'replaced-standard-library-receipts.json'
    if not historical.exists():
        write(historical, previous)
    write(source / 'final-receipts.json', selected)
    print(json.dumps({'status': 'PASS', 'amended_task_pairs': 2,
                      'final_labels': [{k: r[k] for k in ('cohort', 'task_id', 'side')} |
                                       {'label': r['native']['label']} for r in selected]}))


if __name__ == '__main__':
    main()
