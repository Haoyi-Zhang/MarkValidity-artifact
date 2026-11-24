"""Frozen, complete MBPP sanitized population through stock SEW.

No task is filtered by reference or candidate result. Source and original test
contracts are retained; all assertion cases run even after another assertion
fails. Each native source is evaluated in a fresh guarded subprocess.
"""
from pathlib import Path
import argparse
import collections
import concurrent.futures
import datetime
import hashlib
import importlib.metadata
import json
import os
import platform
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]
ART = BASE / 'work/MarkValidity_TOSEM/artifact'
VENDOR = ART / 'external-studies/sew_aliasing/vendor'
sys.path.insert(0, str(VENDOR))
from sew import embed, detect, EXPERIMENT_KEY


def sha(value): return hashlib.sha256(value).hexdigest()

def canonical(value): return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def execute(source, task):
    env = os.environ.copy(); env.pop('PYTHONPATH', None)
    env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    request = {'source': source, 'test_imports': task['test_imports'], 'test_list': task['test_list']}
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='markvalidity-mbpp-pilot-') as temporary:
        try:
            proc = subprocess.run([sys.executable, '-B', '-S', str(HERE / 'native_runner.py')], cwd=temporary,
                                  env=env, input=json.dumps(request), text=True, capture_output=True, timeout=15)
            stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
            stopped = None
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ''; stderr = exc.stderr or ''
            if isinstance(stdout, bytes): stdout = stdout.decode(errors='replace')
            if isinstance(stderr, bytes): stderr = stderr.decode(errors='replace')
            returncode, stopped = None, 'timeout'
    events = []
    try:
        for line in stdout.splitlines():
            if line.strip(): events.append(json.loads(line))
    except ValueError:
        stopped = 'invalid_output'
    complete = [x for x in events if x.get('event') == 'complete']
    if stopped: status = stopped
    elif returncode != 0: status = 'process_error'
    elif len(complete) != 1: status = 'incomplete_output'
    else: status = complete[0]['status']
    return {'status': status, 'returncode': returncode, 'stderr': stderr, 'events': events,
            'raw_stdout': stdout if stopped == 'invalid_output' else None,
            'elapsed_seconds': round(time.monotonic() - started, 6)}


def guarded_call(function, *args):
    def stop(signum, frame): raise TimeoutError('SEW operation exceeded 15 seconds')
    old = signal.signal(signal.SIGALRM, stop); signal.setitimer(signal.ITIMER_REAL, 15)
    try: return function(*args)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, old)


def process_task(job):
    index, task, keys, out_s = job
    out = Path(out_s); source = task['code']; name = 'MBPP-%04d' % task['task_id']
    contract = {'dataset': 'google-research/sanitized-mbpp', 'task_id': task['task_id'],
                'test_imports': task['test_imports'], 'test_list': task['test_list'],
                'initialization': 'fresh namespace and builtin map per original test_list entry; test imports before source initialization',
                'process': 'fresh subprocess per source; deterministic random seed and hash seed zero',
                'runtime': 'CPython ' + platform.python_version(), 'oracle': 'unchanged original assert statements'}
    contract_sha = sha(canonical(contract)); source_sha = sha(source.encode())
    write(out / 'contracts' / (name + '.json'), contract)
    ref_path = 'programs/' + name + '__reference.py'; (out / ref_path).write_text(source)
    ref = execute(source, task); ref_obs = 'observations/' + name + '__reference.json'; write(out / ref_obs, ref)
    reference = {'task_id': task['task_id'], 'dataset_index': index, 'source_sha256': source_sha,
                 'source_path': ref_path, 'contract_sha256': contract_sha, 'status': ref['status'],
                 'observation_path': ref_obs, 'tests': len(task['test_list'])}
    rows = []
    for key_id, key_hex in keys:
        key = bytes.fromhex(key_hex)
        row = {'task_id': task['task_id'], 'dataset_index': index, 'key_id': key_id, 'key_hex': key_hex,
               'reference_sha256': source_sha, 'reference_path': ref_path, 'contract_sha256': contract_sha,
               'reference_status': ref['status'], 'tests': len(task['test_list']), 'variant': 'stock'}
        try:
            original_detection = guarded_call(detect, source, 'python', key)
            row['reference_detector'] = original_detection
        except Exception as exc:
            row['reference_detection_error'] = {'type': type(exc).__name__, 'message': str(exc)}
        try:
            embedded = guarded_call(embed, source, 'python', key)
            candidate = embedded['code']; meta = {k: v for k, v in embedded.items() if k != 'code'}
            rel = 'programs/' + name + '__' + key_id + '.py'; (out / rel).write_text(candidate)
            row.update(embedding=meta, candidate_path=rel, candidate_sha256=sha(candidate.encode()), source_changed=candidate != source)
        except Exception as exc:
            row.update(embedding_error={'type': type(exc).__name__, 'message': str(exc)}, candidate_status='unavailable',
                       detected=None, candidate_suite_pass=None, validity_status='unavailable', joint_supported=False)
            rows.append(row); continue
        try:
            detection = guarded_call(detect, candidate, 'python', key)
            row.update(detector=detection, detected=detection['verdict'] == 'Watermark detected')
        except Exception as exc:
            row.update(detection_error={'type': type(exc).__name__, 'message': str(exc)}, detected=None)
        result = execute(candidate, task)
        obs = 'observations/' + name + '__' + key_id + '.json'; write(out / obs, result)
        compile_events = [x for x in result['events'] if x['event'] == 'source_compile']
        row.update(candidate_status=result['status'], candidate_compile_status=compile_events[0]['status'] if compile_events else 'unavailable',
                   candidate_suite_pass=result['status'] == 'passed', observations_path=obs,
                   failed_test_indices=[x['test_index'] for x in result['events'] if x['event'] == 'test_result' and x['status'] == 'failed'])
        if ref['status'] != 'passed' or result['status'] not in ('passed', 'failed'): validity = 'unavailable'
        else: validity = 'supported' if result['status'] == 'passed' else 'contradicted'
        row['validity_status'] = validity; row['joint_supported'] = validity == 'supported' and row['detected'] is True
        rows.append(row)
    return index, reference, rows


def summarize(rows, refs, elapsed):
    admitted = [r for r in rows if r['reference_status'] == 'passed']
    def counts(pop):
        return {'attempts': len(pop), 'candidate_statuses': dict(collections.Counter(r['candidate_status'] for r in pop)),
                'embedding_statuses': dict(collections.Counter(r.get('embedding', {}).get('status', 'error') for r in pop)),
                'validity_statuses': dict(collections.Counter(r['validity_status'] for r in pop)),
                'detected': sum(r['detected'] is True for r in pop), 'detection_unavailable': sum(r['detected'] is None for r in pop),
                'candidate_suite_pass': sum(r.get('candidate_suite_pass') is True for r in pop),
                'joint_supported': sum(r['joint_supported'] for r in pop),
                'detected_contradicted': sum(r['detected'] is True and r['validity_status'] == 'contradicted' for r in pop),
                'source_changed': sum(r.get('source_changed', False) for r in pop),
                'distinct_candidate_bytes': len({r['candidate_sha256'] for r in pop if 'candidate_sha256' in r})}
    return {'status': 'COMPLETE', 'scope': 'All frozen sanitized MBPP tasks and predefined keys; original assertion-suite contract, not complete-domain equivalence or a population failure estimate.',
            'tasks': len(refs), 'keys': len({r['key_id'] for r in rows}), 'original_test_list_entries': sum(r['tests'] for r in refs),
            'reference_statuses': dict(collections.Counter(r['status'] for r in refs)),
            'all_scheduled_attempts': counts(rows), 'reference_passing_subset': counts(admitted),
            'reference_failed_tasks': [r for r in refs if r['status'] != 'passed'],
            'contradicted_task_key_pairs': [{'task_id': r['task_id'], 'key_id': r['key_id'], 'detected': r['detected'],
                'candidate_status': r['candidate_status'], 'candidate_compile_status': r.get('candidate_compile_status'),
                'failed_test_indices': r.get('failed_test_indices')} for r in rows if r['validity_status'] == 'contradicted'],
            'per_key': {k: counts([r for r in rows if r['key_id'] == k]) for k in dict.fromkeys(r['key_id'] for r in rows)},
            'elapsed_seconds': round(elapsed, 3)}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--keys', type=int, default=1); parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    if args.keys < 1: raise ValueError('At least the upstream default key is required')
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    for n in ('programs', 'observations', 'contracts'): (out / n).mkdir()
    data_path = HERE.parent / 'sanitized-mbpp.json'; raw = data_path.read_bytes(); tasks = json.loads(raw)
    assert len(tasks) == 427 and len({x['task_id'] for x in tasks}) == 427
    keys = [('upstream_default', EXPERIMENT_KEY.hex())] + [('integer_' + str(i), i.to_bytes(16, 'big').hex()) for i in range(args.keys - 1)]
    spec = {'schema': 'markvalidity-sew-mbpp-pilot-v1', 'dataset_commit': 'f82046ba5aabbbb427dbfd38a254d26bff08b533',
        'dataset_sha256': sha(raw), 'task_ids_in_frozen_order': [x['task_id'] for x in tasks], 'selection': 'All 427 sanitized records, no exclusions based on outcomes.',
        'keys': [{'key_id':k, 'hex':v}for k,v in keys], 'sew_commit': '3c873186a56033e73347391b7aedebce1f7f71d0',
        'python': platform.python_version(), 'implementation': platform.python_implementation(),
        'tree_sitter': importlib.metadata.version('tree-sitter'), 'tree_sitter_python': importlib.metadata.version('tree-sitter-python'),
        'native_contract': 'Every exact test_list entry executes independently after exact test_imports and source initialization in a new globals dictionary and builtin map. Every candidate source uses a fresh subprocess. Tests continue after earlier failures.',
        'observation': 'Per-test original-assertion pass/failure, exact exception and phase, stdout/stderr. No source instrumentation and no input-domain equivalence claim.',
        'resource_guard': {'per_source_cpu_seconds': 10, 'per_source_wall_seconds': 15, 'address_space_bytes': 1073741824, 'timeout_validity': 'unavailable'},
        'reference_failure_policy': 'Keep all attempts; separately summarize reference-passing tasks. Candidate failures under a failing reference are not attributed to SEW.',
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'workers': args.workers,
        'producer_sha256': sha(Path(__file__).read_bytes()), 'native_runner_sha256': sha((HERE / 'native_runner.py').read_bytes())}
    write(out / 'specification.json', spec)
    start = time.monotonic(); received = []
    jobs = [(i,t,keys,str(out))for i,t in enumerate(tasks)]
    with (out / 'completed-task-records.jsonl').open('w') as stream:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(process_task, job)for job in jobs]
            for future in concurrent.futures.as_completed(futures):
                result = future.result(); received.append(result)
                stream.write(json.dumps({'dataset_index': result[0], 'reference': result[1], 'rows': result[2]}, sort_keys=True) + '\n');stream.flush()
                if len(received) % 40 == 0: print(json.dumps({'tasks_complete': len(received), 'elapsed_seconds': round(time.monotonic() - start, 2)}), flush=True)
    received.sort(key=lambda x: x[0]); refs = [x[1]for x in received]; rows = [r for x in received for r in x[2]]
    write(out / 'references.json', refs); write(out / 'rows.json', rows)
    summary = summarize(rows, refs, time.monotonic() - start); write(out / 'summary.json', summary)
    manifest = {p.relative_to(out).as_posix(): sha(p.read_bytes())for p in sorted(out.rglob('*'))if p.is_file()}
    write(out / 'files-sha256.json', manifest)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__': main()
