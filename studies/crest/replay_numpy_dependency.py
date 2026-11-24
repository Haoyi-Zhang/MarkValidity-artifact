#!/usr/bin/env python3
"""Reexecute the declared NumPy contract with a scalar-preserving observer.

Only observation encoding changes. The original returned object continues to
the original test, and unsupported values remain unavailable evidence.
"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT.parents[2] / 'work/MarkValidity_TOSEM/artifact'
OUT = ROOT / 'dependency-contracts'
RUNNER = OUT / 'native_runner_numpy.py'
sys.path.insert(0, str(ARTIFACT / 'external-studies/sew_natural/comparison_costs'))
import admission


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def execute(request):
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONOPTIMIZE', None)
    env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='crest-numpy-') as tmp:
        result = subprocess.run([sys.executable, '-B', str(RUNNER)], cwd=tmp,
                                env=env, input=json.dumps(request), text=True,
                                capture_output=True, timeout=15)
    label = admission.humaneval(result.stdout, result.returncode, None)
    return dict(label=label, evidence_rejected=None, stdout=result.stdout,
                stderr=result.stderr, returncode=result.returncode,
                interruption=None, elapsed_seconds=time.monotonic() - start)


def main():
    base = ARTIFACT / 'external-studies/sew_natural/scripts/humaneval/native_runner_v3.py'
    protocol = {
        'status': 'FIXED_BEFORE_EXECUTION',
        'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'task': {'cohort': 'qwen', 'dataset': 'HumanEval', 'task_id': 'HumanEval/32'},
        'base_observer': str(base.relative_to(ARTIFACT)),
        'base_observer_sha256': hashlib.sha256(base.read_bytes()).hexdigest(),
        'observer_file': str(RUNNER.relative_to(ROOT)),
        'observer_source_sha256': hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
        'producer_file': Path(__file__).name,
        'producer_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'amendment': 'Extend only observation encoding for numeric NumPy scalars to dtype with explicit byte order and exact raw bytes. Return the original scalar unchanged to the original tests. Unsupported values remain observer-unavailable; no program, prompt, test or watermark changes.'}
    write(OUT / 'numpy-observer-protocol.json', protocol)
    spec = importlib.util.spec_from_file_location('numeric_observer', RUNNER)
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    import numpy as np
    values = [np.float64(-0.0), np.float64(1.25), np.float64(float('inf')),
              np.float64(float('-inf')), np.float64(float('nan')),
              np.float32(-12.5), np.int64(-17), np.complex128(1+2j), np.bool_(True)]
    for value in values:
        encoded = observer.encode(value)
        restored = np.frombuffer(bytes.fromhex(encoded[2]), dtype=encoded[1])[0]
        assert restored.tobytes() == value.tobytes() and type(restored) is type(value)
    for value in [np.str_('x'), np.array((object(),), dtype=[('item', object)])[()]]:
        try:
            observer.encode(value)
        except TypeError:
            pass
        else:
            raise ValueError('Unsupported nonnumeric object was admitted')
    controls = []
    for expression, test, expected in [
        ('np.float64(-0.0)', 'assert type(candidate()) is np.float64\n    assert np.signbit(candidate())', True),
        ('np.float64(float("nan"))', 'assert type(candidate()) is np.float64\n    assert np.isnan(candidate())', True),
        ('np.str_("x")', 'assert candidate() == "x"', None)]:
        request = {'source': 'import numpy as np\ndef f():\n    return ' + expression,
                   'test': 'def check(candidate):\n    ' + test, 'entry_point': 'f'}
        result = execute(request)
        assert result['label'] is expected
        if expected is None:
            assert json.loads(result['stdout'])['error']['reason'] == 'observer_error'
        controls.append({'request': request, 'expected_label': expected, 'receipt': result})
    write(OUT / 'numpy-scalar-controls.json', {'status': 'PASS', 'numeric_byte_round_trips': 9,
          'rejected_nonnumeric_encodings': 2, 'native_controls': controls,
          'scope': 'Observer controls only, not additional empirical task observations.'})
    output = []
    for row in json.loads((OUT / 'receipts.json').read_text()):
        if row['cohort'] != 'qwen':
            continue
        native = dict(row['native'], **execute(row['native']['execution_request']))
        native.update(observer_file=protocol['observer_file'], observer_root='empirical',
                      observer_source_sha256=protocol['observer_source_sha256'])
        output.append(dict(row, native=native))
        print(json.dumps({'side': row['side'], 'label': native['label'],
                          'error': json.loads(native['stdout']).get('error')}))
    write(OUT / 'numpy-receipts.json', output)


if __name__ == '__main__':
    main()
