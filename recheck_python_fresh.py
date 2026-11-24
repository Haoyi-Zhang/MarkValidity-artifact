#!/usr/bin/env python3
"""Fresh-input Python execution of the original semantic rows and mutants.

This is a new execution, with tagged v2 observations. Archived raw results and
their observation identifiers are not rewritten. Every original Python
semantic-audit row is executed, including repeated source identities.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from covewm.benchmark import canonical_json, render_program
from covewm.observations import (FRESH_MODULE_INITIALIZATION_ID,
                                V2_OBSERVATION_RULE_ID,
                                observe_python_fresh)
from covewm.source_admission import admit_python
from covewm.tasks import TASK_BY_NAME, domain_cases


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_text(value):
    return sha_bytes(value.encode('utf-8'))


def need(condition, message):
    if not condition:
        raise ValueError(message)


def csv_rows(path):
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def first_difference(left, right):
    return next((i for i, pair in enumerate(zip(left, right)) if pair[0] != pair[1]), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=ROOT / 'results/revision-reproduction')
    parser.add_argument('--evidence', type=Path, default=ROOT / 'results/revision-source-joint')
    parser.add_argument('--out', type=Path, default=ROOT / 'results/revision-python-fresh')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    semantic = [r for r in csv_rows(args.results / 'raw/semantic_audit.csv') if r['language'] == 'python']
    mutants = [r for r in csv_rows(args.results / 'raw/mutants.csv') if r['language'] == 'python']
    need(len(semantic) == 252 and len(mutants) == 36, 'unexpected original Python audit coverage')
    required = {(r['task'], r['source_sha256']) for r in semantic}
    sources = {}
    with gzip.open(args.evidence / 'sources.jsonl.gz', 'rt', encoding='utf-8') as handle:
        for line in handle:
            row = json.loads(line)
            key = (row['task'], row['source_sha256'])
            if row['language'] == 'python' and key in required:
                need(sha_text(row['source']) == row['source_sha256'], 'stored source digest mismatch')
                need(key not in sources, 'duplicate source identity')
                sources[key] = row['source']
    need(set(sources) == required, 'original audit source is missing from the full inventory')

    runtime = dict(implementation=platform.python_implementation(), version=platform.python_version(),
                   platform=platform.platform())
    references, domains, nominals = {}, {}, {}
    rows, vector_records, historical_differences = [], [], []
    total_domain_calls = total_nominal_calls = 0

    def execute(task, source, role, program_id, metadata=None):
        nonlocal total_domain_calls, total_nominal_calls
        cases, nominal = domains[task], nominals[task]
        observations, observation_hash = observe_python_fresh(source, cases)
        nominal_observations, nominal_hash = observe_python_fresh(source, nominal)
        total_domain_calls += len(cases)
        total_nominal_calls += len(nominal)
        reference = references.get(task)
        mismatch = None if reference is None else first_difference(reference[0], observations)
        nominal_mismatch = None if reference is None else first_difference(reference[1], nominal_observations)
        contract = dict(task=task, language='python',
                        reference_sha256=sha_text(render_program(TASK_BY_NAME[task].python_reference, 'python', None)),
                        domain_sha256=sha_text(canonical_json(cases)),
                        observation_rule=V2_OBSERVATION_RULE_ID,
                        initialization_rule=FRESH_MODULE_INITIALIZATION_ID, runtime=runtime)
        row = dict(program_id=program_id, role=role, task=task, language='python',
                   source_sha256=sha_text(source), contract_sha256=sha_text(canonical_json(contract)),
                   domain_cases=len(cases), nominal_cases=len(nominal),
                   bounded_equivalent=mismatch is None, nominal_equal=nominal_mismatch is None,
                   first_mismatch_index='' if mismatch is None else mismatch,
                   domain_observations_sha256=observation_hash, nominal_observations_sha256=nominal_hash)
        rows.append(row)
        vector_records.append(dict(**row, source=source, contract=contract,
                                   observations=[json.loads(x) for x in observations],
                                   nominal_observations=[json.loads(x) for x in nominal_observations],
                                   metadata=metadata or {}))
        return observations, nominal_observations, row

    for task, spec in TASK_BY_NAME.items():
        domains[task] = domain_cases(task)
        nominals[task] = [list(args) for args in spec.nominal_cases]
        source = render_program(spec.python_reference, 'python', None)
        admit_python(task, source)
        observations, nominal_observations, row = execute(task, source, 'reference', f'{task}:reference')
        references[task] = (observations, nominal_observations)

    for number, old in enumerate(semantic):
        task = old['task']
        source = sources[(task, old['source_sha256'])]
        # This guards the owned execution universe against added ambient-state
        # code; the label below is still measured by complete fresh execution.
        admit_python(task, source)
        _, _, row = execute(task, source, 'original-semantic-pair', f'semantic:{number:03d}',
                            dict(scheme=old['scheme'], condition=old['condition'],
                                 archived_source_sha256=old['source_sha256']))
        need(row['domain_cases'] == int(old['domain_cases']), 'domain count changed')
        for key in ('bounded_equivalent', 'nominal_equal'):
            if str(row[key]) != old[key]:
                historical_differences.append(dict(program_id=row['program_id'], field=key,
                                                   old=old[key], fresh=row[key]))

    for old in mutants:
        task, index = old['task'], int(old['mutant_id']) - 1
        source = render_program(TASK_BY_NAME[task].python_mutants[index], 'python', None)
        need(sha_text(source) == old['source_sha256'], 'frozen mutant source changed')
        _, _, row = execute(task, source, 'frozen-mutant', f'{task}:mutant:{index + 1}',
                            dict(mutant_id=index + 1, description=old['description'],
                                 trusted_source_basis='exact frozen task-registry mutant'))
        for current, previous in [('bounded_equivalent', 'full_domain_equal'),
                                  ('nominal_equal', 'nominal_equal'),
                                  ('first_mismatch_index', 'first_mismatch_index')]:
            if str(row[current]) != old[previous]:
                historical_differences.append(dict(program_id=row['program_id'], field=current,
                                                   old=old[previous], fresh=row[current]))

    write_csv(args.out / 'executions.csv', rows)
    with (args.out / 'observations.jsonl.gz').open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as handle:
            for record in vector_records:
                handle.write((canonical_json(record) + '\n').encode('utf-8'))
    references_csv = [dict(task=r['task'], domain_cases=r['domain_cases'],
                           observation_rule=V2_OBSERVATION_RULE_ID,
                           initialization_rule=FRESH_MODULE_INITIALIZATION_ID,
                           domain_observations_sha256=r['domain_observations_sha256'],
                           nominal_observations_sha256=r['nominal_observations_sha256'])
                      for r in rows if r['role'] == 'reference']
    write_csv(args.out / 'references.csv', references_csv)
    summary = dict(
        schema='markvalidity-python-fresh-execution-v2',
        status='PASS' if not historical_differences else 'DIFFERENCES',
        started_at_utc=started, elapsed_seconds=round(time.monotonic() - clock, 3),
        observation_rule=V2_OBSERVATION_RULE_ID,
        initialization_rule=FRESH_MODULE_INITIALIZATION_ID, runtime=runtime,
        execution_scope='Fresh module instance for each declared input; owned terminating task registry and exact restricted prefixes, without ambient external-state dependence.',
        reference_programs=12, original_semantic_pairs_executed=252,
        distinct_semantic_sources_executed=len(required), frozen_mutant_programs_executed=36,
        program_records=len(rows), domain_function_calls=total_domain_calls,
        nominal_function_calls=total_nominal_calls,
        semantic_pairs_equivalent=sum(r['bounded_equivalent'] for r in rows if r['role'] == 'original-semantic-pair'),
        effective_mutants=sum(not r['bounded_equivalent'] for r in rows if r['role'] == 'frozen-mutant'),
        effective_mutants_passing_nominal=sum(not r['bounded_equivalent'] and r['nominal_equal']
                                             for r in rows if r['role'] == 'frozen-mutant'),
        historical_outcome_differences=historical_differences,
        input_sha256={
            'semantic_audit.csv': sha_bytes((args.results / 'raw/semantic_audit.csv').read_bytes()),
            'mutants.csv': sha_bytes((args.results / 'raw/mutants.csv').read_bytes()),
            'sources.jsonl.gz': sha_bytes((args.evidence / 'sources.jsonl.gz').read_bytes()),
        },
        code_sha256={str(path.relative_to(ROOT)): sha_bytes(path.read_bytes()) for path in
                     [Path(__file__).resolve(), ROOT / 'src/covewm/observations.py',
                      ROOT / 'src/covewm/tasks.py', ROOT / 'src/covewm/source_admission.py']},
        output_sha256={name: sha_bytes((args.out / name).read_bytes()) for name in
                       ['executions.csv', 'observations.jsonl.gz', 'references.csv']})
    (args.out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
