"""Join the four complete MBPP factors without treating pilots as extra samples.

Paths in normalized records are relative to the MBPP study directory containing
sanitized-mbpp.json. One suite_cost is one complete candidate assertion contract,
not one assertion entry, function call, CPU second, or independent program.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
_parser = argparse.ArgumentParser()
_parser.add_argument('--results-root', type=Path, default=SCRIPT_DIR.parent)
_parser.add_argument('--dataset', type=Path, default=SCRIPT_DIR.parent / 'sanitized-mbpp.json')
_parser.add_argument('--pilot-results', type=Path)
_args = _parser.parse_args()
ROOT = _args.results_root.resolve()
HERE = ROOT / 'factors'
FACTORS = ('stock', 's1_literal_predecessor', 's4_return_boundary', 's1_s4')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def ratio(num, den):
    return num / den if den else None


def summarize(rows):
    n = len(rows)
    detected = sum(r['detected'] is True for r in rows)
    valid = sum(r['validity_label'] == 1 for r in rows)
    joint = sum(r['joint'] == 1 for r in rows)
    unknown_v = sum(r['validity_label'] is None for r in rows)
    unknown_d = sum(r['detected'] is None for r in rows)
    return {'attempts': n, 'tasks': len({r['task_id'] for r in rows}),
            'reference_statuses': dict(collections.Counter(r['reference_status'] for r in rows)),
            'candidate_statuses': dict(collections.Counter(r['candidate_status'] for r in rows)),
            'detected': detected, 'valid': valid, 'joint': joint,
            'invalid': sum(r['validity_label'] == 0 for r in rows),
            'detected_invalid': sum(r['detected'] is True and r['validity_label'] == 0 for r in rows),
            'unknown_validity': unknown_v, 'unknown_detection': unknown_d,
            'unknown_joint': sum(r['joint'] is None for r in rows),
            'A': ratio(valid, n) if not unknown_v else None,
            'D': ratio(detected, n) if not unknown_d else None,
            'J': ratio(joint, n) if not any(r['joint'] is None for r in rows) else None,
            'C': ratio(joint, valid) if not unknown_v and not unknown_d else None,
            'distinct_candidate_bytes': len({r['candidate_sha256'] for r in rows if r['candidate_sha256']}),
            'distinct_source_contracts': len({r['source_contract_sha256'] for r in rows if r['source_contract_sha256']}),
            'suite_cost_per_attempt': 1,
            'scheduled_original_assertion_entries': sum(r['assertion_entries'] for r in rows),
            'observed_original_assertion_entries': sum(r['observed_assertion_entries'] for r in rows)}


def main():
    dataset = json.loads(_args.dataset.read_text())
    by_task = {t['task_id']: t for t in dataset}
    receiving = {v: json.loads((HERE / (v + '-receiving.json')).read_text()) for v in FACTORS}
    for variant, report in receiving.items():
        require(report['status'] == 'PASS' and report['variant'] == variant, 'A complete fresh factor receiver is required')
        require(report['reference_sources_reexecuted'] == 427 and report['candidate_sources_reexecuted'] == 1281,
                'Fresh runtime evidence must cover every source')
    environment = receiving[FACTORS[0]]['execution_environment']
    require(all(r['execution_environment'] == environment for r in receiving.values()), 'Factor receiving environments differ')
    normalized_contracts = HERE / 'normalized-contracts'
    normalized_contracts.mkdir(exist_ok=True)
    records, input_hashes, specs = [], {}, {}
    for variant in FACTORS:
        folder = HERE / variant
        spec = json.loads((folder / 'specification.json').read_text())
        require(receiving[variant]['summary_sha256'] == sha((folder / 'summary.json').read_bytes()),
                'Fresh receiver is not bound to this frozen factor summary')
        require(receiving[variant]['upstream_embedding_detection_pairs_replayed'] == 1281,
                'Fresh method replay is incomplete')
        rows = json.loads((folder / 'rows.json').read_text())
        refs = {r['task_id']: r for r in json.loads((folder / 'references.json').read_text())}
        require(spec['variant'] == variant, 'Factor identity mismatch')
        require(spec['evidence_schema'] == 'markvalidity-mbpp-original-assertions-v2', 'A v2 evidence producer is required')
        expected = {(t['task_id'], k['key_id']) for t in dataset for k in spec['keys']}
        require(len(rows) == len(expected) == 1281, 'Full frozen grid is required')
        require({(r['task_id'], r['key_id']) for r in rows} == expected, 'Configuration population differs')
        input_hashes[variant] = {n: sha((folder / n).read_bytes()) for n in
                                ('specification.json', 'rows.json', 'references.json', 'summary.json', 'files-sha256.json')}
        input_hashes[variant]['fresh_runtime_receiving_sha256'] = sha((HERE / (variant + '-receiving.json')).read_bytes())
        specs[variant] = spec
        for row in rows:
            require(row['evidence_admission'] != 'rejected', 'Rejected contracts require resolution before reporting numerical scores')
            task = by_task[row['task_id']]
            ref = refs[row['task_id']]
            contract_path = folder / 'contracts' / ('MBPP-%04d.json' % row['task_id'])
            contract = json.loads(contract_path.read_text())
            require(sha(canonical(contract)) == row['contract_sha256'], 'Contract digest mismatch')
            require(sha(task['code'].encode()) == row['reference_sha256'], 'Reference source mismatch')
            require(contract['test_list'] == task['test_list'] and contract['test_imports'] == task['test_imports'], 'Original tests changed')
            exact_contract = {'schema': 'markvalidity-mbpp-runtime-bound-contract-v1',
                              'native_contract': contract, 'native_contract_sha256': row['contract_sha256'],
                              'execution_environment': environment}
            exact_contract_sha = sha(canonical(exact_contract))
            exact_contract_path = normalized_contracts / ('MBPP-%04d.json' % row['task_id'])
            write(exact_contract_path, exact_contract)
            validity = {'supported': 1, 'contradicted': 0, 'unavailable': None}[row['validity_status']]
            detected = row['detected']
            joint = 0 if validity == 0 or detected is False else (1 if validity == 1 and detected is True else None)
            candidate_path = folder / row['candidate_path'] if row.get('candidate_path') else None
            observation_path = folder / row['observations_path'] if row.get('observations_path') else None
            if candidate_path:
                require(sha(candidate_path.read_bytes()) == row['candidate_sha256'], 'Candidate source mismatch')
            observation = json.loads(observation_path.read_text()) if observation_path else None
            identity = {'reference_sha256': row['reference_sha256'],
                        'candidate_sha256': row.get('candidate_sha256'),
                        'contract_sha256': exact_contract_sha}
            record = {'dataset': 'mbpp_sanitized', 'task_id': 'MBPP/' + str(row['task_id']),
                      'original_task_id': row['task_id'], 'dataset_index': row['dataset_index'],
                      'variant': variant, 'key_id': row['key_id'], 'key_hex': row['key_hex'],
                      **identity,
                      'native_contract_sha256': row['contract_sha256'],
                      'source_contract_sha256': sha(canonical(identity)) if candidate_path else None,
                      'detected': detected, 'validity_label': validity, 'joint': joint,
                      'reference_status': row['reference_status'], 'candidate_status': row['candidate_status'],
                      'evidence_admission': row['evidence_admission'],
                      'evidence_schema': spec['evidence_schema'],
                      'embedding_status': row.get('embedding', {}).get('status', 'error'),
                      'candidate_compile_status': row.get('candidate_compile_status', 'unavailable'),
                      'source_changed': row.get('source_changed'),
                      'suite_cost': 1, 'suite_cost_unit': 'whole_candidate_contract_execution',
                      'candidate_suite_executions': int(observation_path is not None),
                      'assertion_entries': len(task['test_list']),
                      'observed_assertion_entries': sum(e['event'] == 'test_result' and e['assertion_reached'] for e in observation['events']) if observation else 0,
                      'source_path': candidate_path.relative_to(ROOT).as_posix() if candidate_path else None,
                      'reference_path': (folder / row['reference_path']).relative_to(ROOT).as_posix(),
                      'contract_path': exact_contract_path.relative_to(ROOT).as_posix(),
                      'native_contract_path': contract_path.relative_to(ROOT).as_posix(),
                      'observation_path': observation_path.relative_to(ROOT).as_posix() if observation_path else None,
                      'observation_sha256': sha(observation_path.read_bytes()) if observation_path else None,
                      'reference_observation_path': (folder / ref['observation_path']).relative_to(ROOT).as_posix(),
                      'reference_observation_sha256': sha((folder / ref['observation_path']).read_bytes()),
                      'runtime_receiving_path': (HERE / (variant + '-receiving.json')).relative_to(ROOT).as_posix(),
                      'runtime_receiving_sha256': sha((HERE / (variant + '-receiving.json')).read_bytes()),
                      'failed_test_indices': row.get('failed_test_indices', [])}
            records.append(record)
    require(len(records) == 4 * 427 * 3, 'All four factors must be present')
    write(HERE / 'normalized_rows.json', records)
    groups = collections.defaultdict(list)
    for index, record in enumerate(records):
        if record['source_contract_sha256']:
            groups[record['source_contract_sha256']].append(index)
    identities = []
    for digest, indices in sorted(groups.items()):
        labels = {records[i]['validity_label'] for i in indices}
        require(len(labels) == 1, 'Same source-contract identity received conflicting observations')
        identities.append({'source_contract_sha256': digest, 'row_indices': indices,
                           'configurations': len(indices), 'validity_label': next(iter(labels))})
    write(HERE / 'source_contract_groups.json', identities)
    per_variant = {v: summarize([r for r in records if r['variant'] == v]) for v in FACTORS}
    comparisons = {}
    baseline = {(r['task_id'], r['key_id']): r for r in records if r['variant'] == 'stock'}
    for variant in FACTORS[1:]:
        after = [r for r in records if r['variant'] == variant]
        transitions = collections.Counter()
        for row in after:
            before = baseline[(row['task_id'], row['key_id'])]
            transitions[(before['validity_label'], row['validity_label'], before['detected'], row['detected'])] += 1
        comparisons[variant] = {
            'same_candidate_bytes': sum(r['candidate_sha256'] == baseline[(r['task_id'], r['key_id'])]['candidate_sha256'] for r in after),
            'changed_candidate_bytes': sum(r['candidate_sha256'] != baseline[(r['task_id'], r['key_id'])]['candidate_sha256'] for r in after),
            'paired_transitions': [{'stock_validity': a, 'variant_validity': b, 'stock_detected': c, 'variant_detected': d, 'count': n}
                                   for (a,b,c,d), n in transitions.items()]}
    pilot = json.loads((_args.pilot_results / 'rows.json').read_text()) if _args.pilot_results else None
    current_stock = json.loads((HERE / 'stock/rows.json').read_text())
    repeat_fields = ('task_id', 'key_id', 'key_hex', 'reference_sha256', 'candidate_sha256', 'source_changed',
                     'candidate_status', 'candidate_compile_status', 'detected', 'validity_status', 'failed_test_indices',
                     'embedding', 'detector', 'reference_detector')
    require(pilot is None or [{k:r.get(k) for k in repeat_fields} for r in pilot] == [{k:r.get(k) for k in repeat_fields} for r in current_stock],
            'Fresh stock run differs from prior pilot on frozen source/outcome fields')
    summary = {'scope': 'Complete sanitized MBPP427 x three fixed keys x four named factors. Pilots are repeatability checks, not extra samples.',
               'programs': 427, 'factor_configurations': len(records), 'keys_per_factor': 3,
               'per_variant_all_attempts': per_variant,
               'per_variant_reference_passing_subset': {v: summarize([r for r in records if r['variant'] == v and r['reference_status'] == 'passed']) for v in FACTORS},
               'paired_comparisons_to_stock': comparisons,
               'source_contract_groups': len(identities),
               'shared_source_contract_groups': sum(g['configurations'] > 1 for g in identities),
               'maximum_configurations_in_shared_group': max(g['configurations'] for g in identities),
               'conflicting_observations_in_shared_groups': 0,
               'stock_pilot_source_and_outcome_repetition': 'PASS' if pilot is not None else 'NOT_REQUESTED',
               'same_contract_across_variants': all(len({r['contract_sha256'] for r in records if r['task_id'] == 'MBPP/' + str(t['task_id'])}) == 1 for t in dataset)}
    write(HERE / 'comparison_summary.json', summary)
    provenance = {'schema': 'markvalidity-mbpp-four-factor-normalized-v3',
                  'evidence_schema': 'markvalidity-mbpp-original-assertions-v2',
                  'data_root': 'Paths resolve relative to the MBPP results root containing factors/.',
                  'source_contract_identity': 'SHA256 of UTF8 JSON object with reference_sha256, candidate_sha256, contract_sha256; sort_keys=True, ensure_ascii=False, separators=(comma,colon).',
                  'method_identity': 'Each factor specification binds all retained upstream and patch bytes; method identity is outside the behavioral contract.',
                  'runtime_contract_binding': 'Normalized contracts wrap each unchanged native task contract with the complete execution environment of a fresh full receiver. Original native hashes and individual runtime-receiving reports remain separate row fields; method identity and elapsed time are excluded from the shared contract.',
                  'execution_environment': environment,
                  'suite_cost': 'One complete candidate contract query. Assertion entries are a separate MBPP observation count, not directly comparable to HumanEval function invocations.',
                  'input_hashes': input_hashes,
                  'normalizer_sha256': sha(Path(__file__).read_bytes()),
                  'normalized_rows_sha256': sha((HERE / 'normalized_rows.json').read_bytes()),
                  'groups_sha256': sha((HERE / 'source_contract_groups.json').read_bytes()),
                  'comparison_summary_sha256': sha((HERE / 'comparison_summary.json').read_bytes())}
    write(HERE / 'normalization_provenance.json', provenance)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
