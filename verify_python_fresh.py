#!/usr/bin/env python3
"""Receive the saved fresh-input Python observations without rerunning programs.

This checker reconstructs source coverage, canonical stream digests, equality
decisions and first witnesses from the saved vectors. It does not call the
fresh-execution producer and does not attest that an execution producer is
honest. Reference values are also matched to the prior independent-language
parity record after removal of the new outcome tag.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from covewm.tasks import TASK_BY_NAME, domain_cases

OBSERVATION_RULE = 'covewm-tagged-return-or-exception-type-and-message-canonical-json-v2'
INITIALIZATION_RULE = 'covewm-fresh-module-instance-per-input-v1'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_text(value):
    return digest_bytes(value.encode('utf-8'))


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def stream_digest(values):
    accumulator = hashlib.sha256()
    for value in values:
        accumulator.update((canonical(value) + '\n').encode('utf-8'))
    return accumulator.hexdigest()


def validate_observation(value):
    need(type(value) is dict, 'observation must be a tagged map')
    if value.get('kind') == 'return':
        need(set(value) == {'kind', 'value'}, 'invalid return envelope')
    elif value.get('kind') == 'exception':
        need(set(value) == {'kind', 'type', 'message'}, 'invalid exception envelope')
        need(type(value['type']) is str and value['type'] and type(value['message']) is str,
             'exception type/message must be strings')
    else:
        raise ValueError('unknown observation kind')
    canonical(value)


def first_mismatch(left, right):
    need(len(left) == len(right), 'missing input observations')
    return next((i for i, (a, b) in enumerate(zip(left, right)) if canonical(a) != canonical(b)), None)


def verify(results, evidence, fresh):
    summary = json.loads((fresh / 'summary.json').read_text())
    need(summary['status'] == 'PASS', 'producer did not report success')
    need(summary['observation_rule'] == OBSERVATION_RULE and
         summary['initialization_rule'] == INITIALIZATION_RULE, 'fresh observation contract mismatch')
    for name, expected in summary['output_sha256'].items():
        need(digest_bytes((fresh / name).read_bytes()) == expected, f'output digest mismatch: {name}')
    paths = {'semantic_audit.csv': results / 'raw/semantic_audit.csv',
             'mutants.csv': results / 'raw/mutants.csv',
             'sources.jsonl.gz': evidence / 'sources.jsonl.gz'}
    for name, path in paths.items():
        need(digest_bytes(path.read_bytes()) == summary['input_sha256'][name], f'input digest mismatch: {name}')
    semantic = [r for r in read_csv(paths['semantic_audit.csv']) if r['language'] == 'python']
    mutants = [r for r in read_csv(paths['mutants.csv']) if r['language'] == 'python']
    need(len(semantic) == 252 and len(mutants) == 36, 'original row coverage differs')
    needed = {(r['task'], r['source_sha256']) for r in semantic}
    sources = {}
    with gzip.open(paths['sources.jsonl.gz'], 'rt', encoding='utf-8') as handle:
        for line in handle:
            row = json.loads(line)
            key = (row['task'], row['source_sha256'])
            if row['language'] == 'python' and key in needed:
                need(key not in sources and digest_text(row['source']) == key[1], 'source identity conflict')
                sources[key] = row['source']
    need(set(sources) == needed, 'original source coverage incomplete')
    expected = {}
    for task, spec in TASK_BY_NAME.items():
        source = spec.python_reference.replace('__CARRIERS__', '').rstrip() + '\n'
        expected[f'{task}:reference'] = ('reference', task, source)
    for index, row in enumerate(semantic):
        expected[f'semantic:{index:03d}'] = ('original-semantic-pair', row['task'],
                                           sources[(row['task'], row['source_sha256'])])
    for row in mutants:
        task, index = row['task'], int(row['mutant_id']) - 1
        source = TASK_BY_NAME[task].python_mutants[index].replace('__CARRIERS__', '').rstrip() + '\n'
        need(digest_text(source) == row['source_sha256'], 'mutant source changed')
        expected[f'{task}:mutant:{index + 1}'] = ('frozen-mutant', task, source)
    vectors = {}
    with gzip.open(fresh / 'observations.jsonl.gz', 'rt', encoding='utf-8') as handle:
        for line in handle:
            record = json.loads(line)
            identity = record['program_id']
            need(identity in expected and identity not in vectors, 'unknown or duplicate program vector')
            role, task, source = expected[identity]
            need((record['role'], record['task'], record['language']) == (role, task, 'python'), 'program identity changed')
            need(record['source'] == source and record['source_sha256'] == digest_text(source), 'program source differs')
            cases, nominal = domain_cases(task), TASK_BY_NAME[task].nominal_cases
            need(len(record['observations']) == len(cases) == record['domain_cases'], 'domain observations incomplete')
            need(len(record['nominal_observations']) == len(nominal) == record['nominal_cases'], 'nominal observations incomplete')
            reference_source = expected[f'{task}:reference'][2]
            contract = dict(task=task, language='python', reference_sha256=digest_text(reference_source),
                            domain_sha256=digest_text(canonical(cases)), observation_rule=OBSERVATION_RULE,
                            initialization_rule=INITIALIZATION_RULE, runtime=summary['runtime'])
            need(record['contract'] == contract and record['contract_sha256'] == digest_text(canonical(contract)),
                 'source observation contract is stale')
            for field, digest_field in [('observations', 'domain_observations_sha256'),
                                        ('nominal_observations', 'nominal_observations_sha256')]:
                for value in record[field]:
                    validate_observation(value)
                need(stream_digest(record[field]) == record[digest_field], 'observation stream digest mismatch')
            vectors[identity] = record
    need(set(vectors) == set(expected), 'missing program vectors')
    old_parity = {r['task']: r for r in read_csv(results / 'raw/cross_language_parity.csv')}
    for task in TASK_BY_NAME:
        reference = vectors[f'{task}:reference']['observations']
        need(all(r['kind'] == 'return' for r in reference), 'unexpected exception in frozen reference')
        need(stream_digest([r['value'] for r in reference]) == old_parity[task]['python_hash'],
             'fresh reference differs from prior Python/JavaScript parity observation')
    csv_records = read_csv(fresh / 'executions.csv')
    need(len(csv_records) == len(vectors) == 300, 'execution table coverage differs')
    seen, equivalents, effective, nominal_survivors = set(), 0, 0, 0
    domain_calls = nominal_calls = 0
    for row in csv_records:
        identity = row['program_id']
        need(identity in vectors and identity not in seen, 'unknown or duplicate execution row')
        seen.add(identity)
        record = vectors[identity]
        reference = vectors[f"{record['task']}:reference"]
        mismatch = first_mismatch(reference['observations'], record['observations'])
        nominal_mismatch = first_mismatch(reference['nominal_observations'], record['nominal_observations'])
        need(record['bounded_equivalent'] == (mismatch is None) and
             record['nominal_equal'] == (nominal_mismatch is None), 'declared equality differs from vector')
        need(record['first_mismatch_index'] == ('' if mismatch is None else mismatch), 'wrong first witness')
        for field, value in row.items():
            need(value == str(record[field]), f'execution row differs from vector: {field}')
        domain_calls += record['domain_cases']
        nominal_calls += record['nominal_cases']
        equivalents += record['role'] == 'original-semantic-pair' and mismatch is None
        effective += record['role'] == 'frozen-mutant' and mismatch is not None
        nominal_survivors += record['role'] == 'frozen-mutant' and mismatch is not None and nominal_mismatch is None
    need(equivalents == summary['semantic_pairs_equivalent'] == 252, 'semantic equality count differs')
    need(effective == summary['effective_mutants'] == 36, 'mutant effectiveness count differs')
    need(nominal_survivors == summary['effective_mutants_passing_nominal'] == 3, 'nominal survivor count differs')
    need(domain_calls == summary['domain_function_calls'] and nominal_calls == summary['nominal_function_calls'],
         'execution counts differ')
    return dict(status='PASS', scope='Saved tagged vectors, program/contract identity, equality and first witnesses; no task program executed by this receiver.',
                reference_vectors_verified=12, reference_legacy_parity_hashes_matched=12,
                original_semantic_pairs_verified=252, distinct_semantic_sources_verified=len(needed),
                frozen_mutants_verified=36, effective_mutants=effective, nominal_survivors=nominal_survivors,
                domain_observations_verified=domain_calls, nominal_observations_verified=nominal_calls,
                task_program_executions=0,
                receiver_sha256=digest_bytes(Path(__file__).read_bytes()),
                summary_sha256=digest_bytes((fresh / 'summary.json').read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=ROOT / 'results/revision-reproduction')
    parser.add_argument('--evidence', type=Path, default=ROOT / 'results/revision-source-joint')
    parser.add_argument('--fresh', type=Path, default=ROOT / 'results/revision-python-fresh')
    args = parser.parse_args()
    print(json.dumps(verify(args.results, args.evidence, args.fresh), indent=2))


if __name__ == '__main__':
    main()
