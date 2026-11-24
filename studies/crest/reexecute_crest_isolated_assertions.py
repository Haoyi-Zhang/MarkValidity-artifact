#!/usr/bin/env python3
"""Fresh whole-cohort original-assertion execution for published completions.

Generation, operating points, all input files and official tests are retained.
The current typed-observation studies remain untouched as additional evidence.
This producer evaluates original suites on actual Python values in separate program and test namespaces, preserving candidate globals.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
STATE = {}
MODELS = ('rf', 'logreg_l1', 'logreg_l2')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def receive(stdout, returncode, interruption):
    if returncode != 0 or interruption:
        return None
    item = json.loads(stdout)
    if not isinstance(item,dict) or item.get('schema') != 'crest-isolated-original-assertions':
        raise ValueError('Unexpected native envelope')
    if item['status'] == 'passed':
        if item['error'] is not None or item['check_finished'] is not True:
            raise ValueError('Passing result without a completed original check')
        return True
    if item['status'] == 'failed':
        error = item['error']
        if (item['check_finished'] is not False or error.get('reason') or
                error['phase'] not in ('compile_source', 'initialize_source', 'resolve_entry_point', 'original_suite') or
                error['type'] in ('builtins.MemoryError', 'builtins.KeyboardInterrupt')):
            raise ValueError('Observer/resource error is not a witnessed program failure')
        return False
    if item['status'] != 'unavailable' or item['check_finished'] is not False:
        raise ValueError('Malformed unavailable evidence')
    return None


def initialize(source, target, environment):
    STATE.update(source=Path(source), target=Path(target), environment=environment)


def child_environment():
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONOPTIMIZE', None)
    env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    return env


def probe_execution_environment():
    # Query the same clean interpreter, flags, temporary working directory and
    # environment as workers; parent PYTHONPATH cannot shadow these packages.
    code = '''import importlib.metadata,json,os,platform,sys
print(json.dumps({'python':sys.version,'platform':platform.platform(),
'hash_seed':os.environ['PYTHONHASHSEED'],'optimization_disabled':sys.flags.optimize==0,
'invocation_flags':['-B'],'site_initialization':'enabled' if not sys.flags.no_site else 'disabled',
'pythonpath_removed':'PYTHONPATH' not in os.environ,'OMP_NUM_THREADS':os.environ['OMP_NUM_THREADS'],
'OPENBLAS_NUM_THREADS':os.environ['OPENBLAS_NUM_THREADS'],
'declared_dependencies':{name:importlib.metadata.version(name) for name in ('numpy','sympy')}}))'''
    with tempfile.TemporaryDirectory(prefix='crest-environment-probe-') as tmp:
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=tmp,
                                env=child_environment(), text=True, capture_output=True,
                                timeout=15, check=True)
    environment = json.loads(result.stdout)
    if not environment['optimization_disabled'] or environment['site_initialization'] != 'enabled':
        raise ValueError('Original assertions and declared dependencies must remain enabled')
    environment.update(wall_timeout_seconds=15, cpu_seconds=10,
                       address_space_bytes=1073741824)
    return environment


def native(request):
    runner = ROOT / 'isolated_assertion_native_runner.py'
    env = child_environment()
    start = time.monotonic()
    interruption = None
    with tempfile.TemporaryDirectory(prefix='crest-original-suite-') as tmp:
        try:
            result = subprocess.run([sys.executable, '-B', str(runner)], cwd=tmp,
                                    env=env, input=json.dumps(request), text=True,
                                    capture_output=True, timeout=15)
            stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as exception:
            stdout, stderr, returncode = exception.stdout or '', exception.stderr or '', None
            if isinstance(stdout, bytes):
                stdout = stdout.decode('utf-8', errors='replace')
            if isinstance(stderr, bytes):
                stderr = stderr.decode('utf-8', errors='replace')
            interruption = 'wall_timeout'
    try:
        label, rejected = receive(stdout, returncode, interruption), None
    except (ValueError, KeyError, TypeError) as exception:
        label, rejected = None, str(exception)
    return {'label': label, 'evidence_rejected': rejected, 'stdout': stdout,
            'stderr': stderr, 'returncode': returncode, 'interruption': interruption,
            'elapsed_seconds': time.monotonic() - start,
            'execution_request': request,
            'observer_root': 'empirical', 'observer_file': runner.name,
            'observer_source_sha256': digest(runner),
            'execution_environment': STATE['environment']}


def process(job):
    cohort, task, previous = job
    source, target = STATE['source'] / cohort, STATE['target'] / cohort
    row = {k: v for k, v in previous.items() if k not in
           {'reference_native', 'candidate_native', 'qualified_reference', 'validity',
            'classifiers', 'reexecution_comparison', 'execution_contract_amendment'}}
    for side in ('reference', 'candidate'):
        if side + '_source' not in row:
            continue
        relative = row[side + '_source']
        (target / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target / relative)
        request = {'source': task['context_prompt'] + (target / relative).read_bytes().decode('utf-8'),
                   'test': task['test'], 'entry_point': task['entry_point']}
        row[side + '_native'] = native(request)
    row['qualified_reference'] = row['reference_native']['label'] is True
    row['validity'] = row.get('candidate_native', {}).get('label') if row['qualified_reference'] else None
    row['classifiers'] = {}
    for model in MODELS:
        d = row.get('candidate_detector', {}).get('classifiers', {}).get(model, {}).get('detected')
        v = row['validity']
        joint = False if v is False or d is False else (True if v is True and d is True else None)
        row['classifiers'][model] = {'detected': d, 'joint': joint}
    row['comparison_to_typed_observation'] = {
        side: {'typed_label': previous.get(side + '_native', {}).get('label'),
               'assertion_label': row.get(side + '_native', {}).get('label')}
        for side in ('reference', 'candidate') if side + '_native' in row}
    stem = task['dataset'].lower() + '-' + str(task['task_id']).replace('/', '-')
    write(target / 'records' / (stem + '.json'), row)
    return cohort, row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--workers', type=int, default=4)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Fresh output directory required')
    environment = probe_execution_environment()
    jobs, completed, streams = [], {}, {}
    for cohort in ('gpt4o', 'qwen'):
        source, target = args.source / cohort, args.output / cohort
        target.mkdir(parents=True)
        tasks = json.loads((source / 'tasks.json').read_text())
        original_rows = json.loads((source / 'results.json').read_text())
        records = {(r['dataset'], str(r['task_id'])): r for r in original_rows}
        task_keys = {(t['dataset'], str(t['task_id'])) for t in tasks}
        if not (len(tasks) == len(original_rows) == len(records) == len(task_keys) == 1138 and
                task_keys == set(records)):
            raise ValueError('The complete published population is required')
        for task in tasks:
            compile(task['test'], '<official-test-preflight>', 'exec')
            if not task['entry_point'].isidentifier():
                raise ValueError('Unexpected official entry point')
        old_protocol = json.loads((source / 'protocol.json').read_text())
        protocol = {
            'status': 'FIXED_BEFORE_EXECUTION',
            'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'study': cohort, 'execution_contract': 'official_original_assertions_isolated_namespaces',
            'generation_origin': old_protocol['generation_origin'],
            'generation_results_sha256': old_protocol['generation_results_sha256'],
            'input_task_table_sha256': old_protocol['input_task_table_sha256'],
            'producer_files': {name: digest(ROOT / name) for name in
                               ('reexecute_crest_isolated_assertions.py', 'isolated_assertion_native_runner.py')},
            'official_assembly_source': 'mxeval-execution.py',
            'official_assembly_source_sha256': digest(ROOT / 'mxeval-execution.py'),
            'assembly': 'Execute exact prompt + completion in program_globals; bind the original entry object; execute exact original test in dict(program_globals); call test_globals[check](candidate) without wrappers or value encoding',
            'typed_evidence_source': str(source.resolve()),
            'typed_evidence_results_sha256': digest(source / 'results.json'),
            'typed_evidence_used_for_decisions': False,
            'source_text_policy': 'UTF-8 with universal-newline decoding; exact submitted text retained, archive bytes independently checked.',
            'environment': environment,
            'qualification': 'Execute all originals first within each task pair; preservation is conditional on a passing original, while full-population output utility retains every attempted file.',
            'emission_policy': 'Completed recorded precheck rejection is E=0 with zero output yield; raw V and D remain N/A. Interrupted emission remains unknown.',
            'resources': 'Resource exhaustion/interruption and malformed native receipts remain unavailable, not semantic failure.',
            'scope': 'Official prompt and assertion bodies are unchanged. Program and test namespaces are isolated uniformly to retain the candidate entry and its original globals. This declared functional contract differs from literal official executor assembly; the complete literal-assembly study is retained as contract sensitivity evidence.',
            'workers': args.workers, 'timing_claim': 'Correctness-only execution; no speed comparison.'}
        write(target / 'tasks.json', tasks)
        write(target / 'protocol.json', protocol)
        streams[cohort] = (target / 'completed.jsonl').open('w')
        completed[cohort] = []
        jobs.extend((cohort, task, records[(task['dataset'], str(task['task_id']))]) for task in tasks)
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers, initializer=initialize,
                initargs=(str(args.source.resolve()), str(args.output.resolve()), environment)) as pool:
            futures = [pool.submit(process, job) for job in jobs]
            for count, future in enumerate(concurrent.futures.as_completed(futures), 1):
                cohort, row = future.result()
                completed[cohort].append(row)
                streams[cohort].write(json.dumps(row) + '\n')
                streams[cohort].flush()
                if count % 100 == 0:
                    print(json.dumps({'completed_input_pairs': count, 'scheduled_input_pairs': len(jobs)}), flush=True)
    finally:
        for stream in streams.values():
            stream.close()
    summary = {}
    for cohort, rows in completed.items():
        rows.sort(key=lambda row: (row['dataset'] != 'HumanEval', row['dataset_index']))
        write(args.output / cohort / 'results.json', rows)
        summary[cohort] = {'rows': len(rows),
                           'native_suites': sum(1 + ('candidate_native' in r) for r in rows),
                           'reference_passed': sum(r['reference_native']['label'] is True for r in rows),
                           'candidate_passed': sum(r.get('candidate_native', {}).get('label') is True for r in rows)}
    write(args.output / 'execution-summary.json', {'status': 'COMPLETE', 'studies': summary})
    print(json.dumps({'status': 'COMPLETE', 'studies': summary}), flush=True)


if __name__ == '__main__':
    main()
