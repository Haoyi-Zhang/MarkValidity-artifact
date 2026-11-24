#!/usr/bin/env python3
"""Fresh full-corpus study of the unchanged released CREST pipeline.

The published default RF model is primary. The two other released classifiers
are recorded at their own upstream-selected thresholds, without local fitting.
All original benchmark tasks remain in the output, including unavailable runs.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import datetime
import gzip
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback
import warnings

HERE = Path(__file__).resolve().parent
MODELS = ('rf', 'logreg_l1', 'logreg_l2')
STATE = {}


class OperationDeadline(BaseException):
    """Not swallowed by upstream transformation helpers' except Exception."""
    pass


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initialize(upstream, artifact, output):
    upstream, artifact, output = map(Path, (upstream, artifact, output))
    for sub in ('transformations', 'embedding', 'detection'):
        sys.path.insert(0, str(upstream / 'crest' / sub))
    sys.path.insert(0, str(artifact / 'external-studies/sew_natural/comparison_costs'))
    import admission
    import load_classifier
    import watermark_detection
    import watermark_embedding
    models, thresholds, model_warnings = {}, {}, []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for name in MODELS:
            models[name], error = load_classifier.load_model(str(upstream / 'crest/models'), name)
            if error:
                raise ValueError(error)
            threshold, constraint, error = load_classifier.load_threshold(str(upstream / 'crest/models'), name)
            if error:
                raise ValueError(error)
            thresholds[name] = {'threshold': threshold, 'constraint': constraint}
        model_warnings = sorted(set(str(w.message) for w in caught))
    STATE.update(upstream=upstream, artifact=artifact, output=output, models=models,
                 thresholds=thresholds, model_warnings=model_warnings,
                 load_classifier=load_classifier, detection=watermark_detection,
                 embedding=watermark_embedding, admission=admission)


def guarded(operation, seconds):
    def stop(signum, frame):
        raise OperationDeadline('Declared operation wall budget exhausted')
    previous = signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return operation()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def native(task, source):
    root = STATE['artifact'] / 'external-studies/sew_natural'
    if task['dataset'] == 'HumanEval':
        runner = root / 'scripts/humaneval/native_runner_v3.py'
        request = {'source': source, 'test': task['test'], 'entry_point': task['entry_point']}
    else:
        runner = root / 'mbpp/scripts/native_runner_v2.py'
        request = {'source': source, 'test_imports': task['test_imports'], 'test_list': task['test_list']}
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONOPTIMIZE', None)
    env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    start = time.monotonic()
    interruption = None
    with tempfile.TemporaryDirectory(prefix='crest-original-tests-') as folder:
        try:
            result = subprocess.run([sys.executable, '-B', '-S', str(runner)], input=json.dumps(request),
                                    text=True, capture_output=True, cwd=folder, env=env, timeout=15)
            stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, returncode = exc.stdout or '', exc.stderr or '', None
            stdout = stdout.decode(errors='replace') if isinstance(stdout, bytes) else stdout
            stderr = stderr.decode(errors='replace') if isinstance(stderr, bytes) else stderr
            interruption = 'wall_timeout'
    try:
        if task['dataset'] == 'HumanEval':
            label = STATE['admission'].humaneval(stdout, returncode, interruption)
        else:
            label = STATE['admission'].mbpp(stdout, len(task['test_list']), returncode, interruption)
        rejected = None
    except STATE['admission'].EvidenceRejected as exc:
        label, rejected = None, str(exc)
    return {'label': label, 'evidence_rejected': rejected, 'stdout': stdout, 'stderr': stderr,
            'returncode': returncode, 'interruption': interruption,
            'elapsed_seconds': time.monotonic() - start}


def detect(path):
    features, error = guarded(lambda: STATE['detection'].detect_features(str(path)), 120)
    if error:
        return {'status': 'error', 'error': error, 'features': features, 'classifiers': {}}
    if len(features) != 49 or any(type(value) is not int or value not in (0, 1) for value in features):
        raise ValueError('Upstream did not return its 49 binary features')
    classifiers = {}
    for name in MODELS:
        probability = float(STATE['load_classifier'].predict_probability(STATE['models'][name], features))
        threshold = STATE['thresholds'][name]
        classifiers[name] = {**threshold, 'probability': probability,
                             'detected': bool(probability >= threshold['threshold'])}
    return {'status': 'completed', 'features': features, 'classifiers': classifiers}


def process(task):
    name = task['dataset'].lower() + '-' + str(task['task_id']).replace('/', '-')
    result = {'dataset': task['dataset'], 'dataset_index': task['dataset_index'],
              'task_id': task['task_id'], 'model_load_warnings': STATE['model_warnings']}
    output = STATE['output']
    ref_relative = 'sources/' + name + '-reference.py'
    candidate_relative = 'sources/' + name + '-candidate.py'
    (output / ref_relative).write_text(task['source'])
    result['reference_source'] = ref_relative
    result['reference_native'] = native(task, task['source'])
    stdout, stderr = io.StringIO(), io.StringIO()
    old_cwd = Path.cwd()
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='crest-upstream-') as tmp:
        tmp = Path(tmp)
        os.chdir(tmp)
        source, candidate = tmp / 'reference.py', tmp / 'candidate.py'
        source.write_text(task['source'])
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                error = guarded(lambda: STATE['embedding'].embed_to_file(str(source), str(candidate)), 120)
                if error:
                    result['embedding'] = {'status': 'error', 'error': error}
                else:
                    result['embedding'] = {'status': 'completed'}
                if candidate.exists():
                    content = candidate.read_text()
                    (output / candidate_relative).write_text(content)
                    result['candidate_source'] = candidate_relative
                    result['source_changed'] = content != task['source']
                    result['candidate_native'] = native(task, content)
                if result['embedding']['status'] == 'completed' and candidate.exists():
                    try:
                        result['candidate_detector'] = detect(candidate)
                    except BaseException as exc:
                        result['candidate_detector'] = {'status': 'error', 'error': repr(exc),
                                                        'traceback': traceback.format_exc()}
            except BaseException as exc:
                result['embedding'] = {'status': 'error', 'error': repr(exc), 'traceback': traceback.format_exc()}
            try:
                result['reference_detector'] = detect(source)
            except BaseException as exc:
                result['reference_detector'] = {'status': 'error', 'error': repr(exc), 'traceback': traceback.format_exc()}
        os.chdir(old_cwd)
    result['upstream_log'] = stdout.getvalue()
    result['upstream_stderr'] = stderr.getvalue()
    result['observed_seconds'] = time.monotonic() - start
    # Full truth table. Unknown candidate validity or detector output is retained,
    # never converted into negative evidence or dropped from the population.
    result['qualified_reference'] = result['reference_native']['label'] is True
    result['validity'] = result.get('candidate_native', {}).get('label') if result['qualified_reference'] else None
    result['classifiers'] = {}
    for model in MODELS:
        detector = result.get('candidate_detector', {}).get('classifiers', {}).get(model, {})
        detected = detector.get('detected')
        validity = result['validity']
        joint = None if validity is None or detected is None else bool(validity and detected)
        if validity is False or detected is False:
            joint = False
        result['classifiers'][model] = {'detected': detected, 'joint': joint}
    write(output / 'records' / (name + '.json'), result)
    return result


def load_tasks(artifact):
    root = artifact / 'external-studies/sew_natural'
    with gzip.open(root / 'data/HumanEval.jsonl.gz', 'rt') as handle:
        he = [json.loads(line) for line in handle if line.strip()]
    mb = json.loads((root / 'mbpp/sanitized-mbpp.json').read_text())
    tasks = []
    for i, task in enumerate(he):
        tasks.append({'dataset': 'HumanEval', 'dataset_index': i, 'task_id': task['task_id'],
                      'source': task['prompt'] + task['canonical_solution'],
                      'test': task['test'], 'entry_point': task['entry_point']})
    for i, task in enumerate(mb):
        tasks.append({'dataset': 'MBPP', 'dataset_index': i, 'task_id': task['task_id'],
                      'source': task['code'], 'test_imports': task['test_imports'], 'test_list': task['test_list']})
    assert len(he) == 164 and len(mb) == 427
    return tasks


def summarize(results):
    summaries = []
    for dataset in ('HumanEval', 'MBPP', 'pooled'):
        rows = [r for r in results if dataset == 'pooled' or r['dataset'] == dataset]
        for model in MODELS:
            d = [r['classifiers'][model]['detected'] for r in rows]
            j = [r['classifiers'][model]['joint'] for r in rows]
            v = [r['validity'] for r in rows]
            reference_d = [r.get('reference_detector', {}).get('classifiers', {}).get(model, {}).get('detected') for r in rows]
            supported = v.count(True)
            joint_count = j.count(True)
            summaries.append({'dataset': dataset, 'classifier': model, 'attempts': len(rows),
                              'reference_supported': sum(r['qualified_reference'] for r in rows),
                              'changed_sources': sum(r.get('source_changed') is True for r in rows),
                              'embedding_errors': sum(r['embedding']['status'] != 'completed' for r in rows),
                              'V': supported, 'V_failed': v.count(False), 'V_unknown': v.count(None),
                              'D': d.count(True), 'D_unknown': d.count(None),
                              'J': joint_count, 'J_unknown': j.count(None),
                              'D_positive_invalid': sum(x is False and y is True for x, y in zip(v, d)),
                              'C_numerator': joint_count, 'C_denominator': supported,
                              'C': joint_count / supported if supported else None,
                              'input_D': reference_d.count(True), 'input_D_unknown': reference_d.count(None)})
    return summaries


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact', type=Path, required=True)
    p.add_argument('--upstream', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--limit', type=int)
    args = p.parse_args()
    artifact, upstream, output = map(Path.resolve, (args.artifact, args.upstream, args.output))
    if output.exists():
        raise ValueError('Use a new output directory; observations cannot be overwritten')
    tasks = load_tasks(artifact)
    if args.limit:
        tasks = tasks[:args.limit]
    output.mkdir(parents=True)
    (output / 'sources').mkdir()
    (output / 'records').mkdir()
    protocol = {
        'status': 'FIXED_BEFORE_EXECUTION',
        'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source': 'https://github.com/niccap/crest',
        'upstream_commit': subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip(),
        'upstream_files': {str(path.relative_to(upstream)): digest(path) for path in sorted((upstream / 'crest').rglob('*')) if path.is_file()},
        'producer_file': digest(Path(__file__)),
        'datasets': {'HumanEval': digest(artifact / 'external-studies/sew_natural/data/HumanEval.jsonl.gz'),
                     'MBPP': digest(artifact / 'external-studies/sew_natural/mbpp/sanitized-mbpp.json')},
        'population': [{k: task[k] for k in ('dataset', 'dataset_index', 'task_id')} for task in tasks],
        'primary_classifier': 'rf', 'additional_classifiers': ['logreg_l1', 'logreg_l2'],
        'threshold_policy': 'Unchanged upstream load_threshold: fpr_1pct, then fpr_5pct, then default. No local fitting or calibration.',
        'source_policy': 'Exact HumanEval prompt + canonical_solution; exact sanitized MBPP code. All 591 original tasks, no output-based selection.',
        'reference_control': 'Fresh unchanged-suite execution and upstream detection of every original source.',
        'candidate_control': 'Fresh unchanged-suite execution; default upstream embed_to_file and detect_features. No transformation selection or implementation edits.',
        'timeouts_seconds': {'embedding': 120, 'detection_per_source': 120, 'native_suite': 15},
        'native_cpu_seconds': 10, 'native_address_space_bytes': 1073741824,
        'workers': args.workers, 'timing_claim': 'No speed comparison; parallel run wall durations retained only as execution metadata.',
        'environment': {'python': sys.version, 'platform': platform.platform(),
                        'dependencies': {name: importlib.metadata.version(name) for name in ['libcst', 'autopep8', 'chardet', 'numpy', 'scipy', 'scikit-learn', 'joblib']}},
        'pilot': bool(args.limit),
    }
    write(output / 'protocol.json', protocol)
    write(output / 'tasks.json', tasks)
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers, initializer=initialize,
                                                initargs=(str(upstream), str(artifact), str(output))) as pool:
        futures = {pool.submit(process, task): task for task in tasks}
        with (output / 'completed.jsonl').open('w') as stream:
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                stream.write(json.dumps(result, ensure_ascii=False) + '\n')
                stream.flush()
                print(json.dumps({'completed': len(results), 'total': len(tasks), 'dataset': result['dataset'],
                                  'task_id': result['task_id'], 'validity': result['validity'],
                                  'rf': result['classifiers']['rf']}), flush=True)
    results.sort(key=lambda r: (r['dataset'] != 'HumanEval', r['dataset_index']))
    write(output / 'results.json', results)
    write(output / 'summary.json', {'status': 'COMPLETE', 'rows': len(results), 'summaries': summarize(results)})
    print(json.dumps({'status': 'COMPLETE', 'rows': len(results), 'output': str(output)}))


if __name__ == '__main__':
    main()
