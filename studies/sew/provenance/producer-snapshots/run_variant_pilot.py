from pathlib import Path
import argparse
import collections
import datetime
import gzip
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ART = HERE.parents[2] / 'work/MarkValidity_TOSEM/artifact'
sys.path.insert(0, os.environ.get('SEW_PILOT_VENDOR', str(ART / 'external-studies/sew_aliasing/vendor')))
from sew import embed, detect, EXPERIMENT_KEY


def sha(value): return hashlib.sha256(value).hexdigest()

def execute(source, task):
    env = os.environ.copy(); env.pop('PYTHONPATH', None); env['PYTHONHASHSEED'] = '0'
    with tempfile.TemporaryDirectory(prefix='markvalidity-he-pilot-') as temporary:
        try:
            result = subprocess.run([sys.executable, '-B', '-S', str(HERE / 'native_runner.py')],
                cwd=temporary, env=env, input=json.dumps({'source': source, 'test': task['test'], 'entry_point': task['entry_point']}),
                text=True, capture_output=True, timeout=15)
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'error': {'phase': 'source_or_suite'}, 'observations': []}
    if result.returncode != 0:
        return {'status': 'process_error', 'returncode': result.returncode, 'stderr': result.stderr, 'observations': []}
    try: return json.loads(result.stdout)
    except ValueError: return {'status': 'invalid_output', 'stdout': result.stdout, 'stderr': result.stderr, 'observations': []}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, required=True); parser.add_argument('--keys', type=int, default=1)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=False); out = args.out
    (out / 'programs').mkdir(); (out / 'observations').mkdir()
    tasks = [json.loads(x) for x in gzip.decompress((HERE / 'data/HumanEval.jsonl.gz').read_bytes()).decode().splitlines()]
    assert len(tasks) == 164 and len({t['task_id'] for t in tasks}) == 164
    keys = [('upstream_default', EXPERIMENT_KEY)] + [('integer_' + str(i), i.to_bytes(16, 'big')) for i in range(args.keys - 1)]
    spec = {'schema': 'markvalidity-sew-humaneval-variant-pilot-v1', 'variant_vendor': os.environ.get('SEW_PILOT_VENDOR', 'stock'), 'dataset_commit': 'b9453e8f1865df0a0057a1383767caa400acfbcf',
            'dataset_sha256': sha((HERE / 'data/HumanEval.jsonl.gz').read_bytes()), 'tasks': [x['task_id'] for x in tasks],
            'selection': 'All 164 tasks in the official frozen HumanEval file, in dataset order, with no result-based exclusions.',
            'keys': [{'key_id': k, 'hex': v.hex()} for k, v in keys], 'python': platform.python_version(),
            'sew_commit': '3c873186a56033e73347391b7aedebce1f7f71d0', 'source': 'prompt + canonical_solution',
            'primary_obligation': 'Pass the unchanged original check(candidate) test suite, with random.seed(0) and PYTHONHASHSEED=0.',
            'observer_note': 'Instrumentation captures calls in original suite order and their return/exception and argument poststate. This pilot does not yet execute a separate fresh-per-input contract or prove equivalence.',
            'limits': 'HumanEval is a frozen hand-written benchmark, not a production-code population or LLM-output sample; upstream is marked deprecated/unmaintained. No model generation is claimed.',
            'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'producer_sha256': sha(Path(__file__).read_bytes()), 'native_runner_sha256': sha((HERE / 'native_runner.py').read_bytes())}
    (out / 'specification.json').write_text(json.dumps(spec, indent=2) + '\n')
    rows = []; refs = []; start = time.monotonic()
    for task in tasks:
        task_id = task['task_id']; name = task_id.replace('/', '-')
        source = task['prompt'] + task['canonical_solution']
        (out / 'programs' / (name + '__reference.py')).write_text(source)
        reference = execute(source, task); refs.append({'task_id': task_id, 'source_sha256': sha(source.encode()), 'result': reference})
        for key_id, key in keys:
            record = {'task_id': task_id, 'key_id': key_id, 'reference_sha256': sha(source.encode()),
                      'reference_status': reference['status'], 'reference_calls': len(reference['observations'])}
            try:
                embedded = embed(source, 'python', key); candidate = embedded.pop('code')
                relative = 'programs/' + name + '__' + key_id + '.py'; (out / relative).write_text(candidate)
                detection = detect(candidate, 'python', key); reference_detection = detect(source, 'python', key)
                observed = execute(candidate, task)
                obs_path = 'observations/' + name + '__' + key_id + '.json'
                (out / obs_path).write_text(json.dumps(observed, sort_keys=True) + '\n')
                record.update({'embedding': embedded, 'candidate_path': relative, 'candidate_sha256': sha(candidate.encode()),
                    'observations_path': obs_path, 'candidate_status': observed['status'], 'candidate_calls': len(observed['observations']),
                    'detector': detection, 'reference_detector': reference_detection, 'detected': detection['verdict'] == 'Watermark detected',
                    'test_supported': reference['status'] == observed['status'] == 'passed',
                    'joint': reference['status'] == observed['status'] == 'passed' and detection['verdict'] == 'Watermark detected',
                    'candidate_error': observed.get('error'), 'source_changed': candidate != source,
                    'all_observed_call_records_equal': observed['observations'] == reference['observations']})
            except BaseException as exc:
                record.update({'embedding_error': type(exc).__name__ + ': ' + str(exc), 'candidate_status': 'unavailable',
                    'detected': None, 'test_supported': False, 'joint': False, 'candidate_calls': 0})
            rows.append(record)
        if (len(refs) % 20) == 0: print(json.dumps({'tasks_finished': len(refs), 'seconds': round(time.monotonic() - start, 2)}), flush=True)
    with gzip.open(out / 'reference-observations.jsonl.gz', 'wt') as handle:
        for r in refs: handle.write(json.dumps(r, sort_keys=True) + '\n')
    (out / 'rows.json').write_text(json.dumps(rows, indent=2) + '\n')
    summary = {'status': 'COMPLETE', 'tasks': len(tasks), 'keys': len(keys), 'configurations': len(rows),
        'reference_statuses': dict(collections.Counter(r['result']['status'] for r in refs)),
        'candidate_statuses': dict(collections.Counter(r['candidate_status'] for r in rows)),
        'embedding_statuses': dict(collections.Counter(r.get('embedding', {}).get('status', 'error') for r in rows)),
        'test_supported': sum(r['test_supported'] for r in rows), 'detected': sum(r['detected'] is True for r in rows),
        'joint': sum(r['joint'] for r in rows), 'detected_test_failure': sum(r['detected'] is True and r['candidate_status'] == 'failed' for r in rows),
        'detection_unavailable': sum(r['detected'] is None for r in rows),
        'reference_invocations': sum(len(r['result']['observations']) for r in refs),
        'candidate_invocations': sum(r['candidate_calls'] for r in rows),
        'complete_observation_agreement': sum(r.get('all_observed_call_records_equal', False) for r in rows),
        'elapsed_seconds': round(time.monotonic() - start, 3),
        'failed_configurations': [{'task_id': r['task_id'], 'key_id': r['key_id'], 'status': r['candidate_status'], 'error': r.get('candidate_error'), 'detected': r['detected']} for r in rows if r['candidate_status'] != 'passed']}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__': main()
