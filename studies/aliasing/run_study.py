#!/usr/bin/env python3
"""Run stock SEW on a fixed, targeted aliasing grid and execute its output.

Install requirements.txt first. This invokes the vendored unmodified embedding
and detection implementations. It does not run SEW's original benchmark,
train models, change its rules, or infer the prevalence of these cases.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import gzip
import hashlib
from importlib.metadata import version
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parents[1]
sys.path.insert(0, str(HERE / 'vendor'))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


RUNNER = r'''
import json, sys
request = json.load(sys.stdin)
try:
    code = compile(request['source'], '<source-bound-candidate>', 'exec')
except (SyntaxError, ValueError) as exc:
    print(json.dumps({'compile_status': 'error', 'exception_type': type(exc).__name__, 'observations': []}))
    raise SystemExit(0)
observations = []
for n in request['inputs']:
    namespace = {}
    try:
        exec(code, namespace)
        value = namespace['solve'](n)
        observation = {'kind': 'return', 'value': value}
    except BaseException as exc:
        observation = {'kind': 'exception', 'type': type(exc).__module__ + '.' + type(exc).__qualname__, 'message': str(exc)}
    observations.append({'input': n, 'observation': observation})
print(json.dumps({'compile_status': 'ok', 'observations': observations}, sort_keys=True, separators=(',', ':')))
'''


def execute(source: str, inputs: list[int], timeout: int) -> dict:
    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, '-B', '-I', '-c', RUNNER],
        input=json.dumps({'source': source, 'inputs': inputs}),
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=True,
    )
    response = json.loads(result.stdout)
    response['elapsed_seconds'] = round(time.monotonic() - start, 6)
    response['stderr'] = result.stderr
    response['source_sha256'] = digest(source.encode())
    response['domain_sha256'] = digest(canonical(inputs))
    return response


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ARTIFACT / 'results/revision-sew-aliasing')
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error('Output directory must be new or empty; retained results are never overwritten.')
    out = args.out.resolve()
    (out / 'programs').mkdir(parents=True)
    spec = json.loads((HERE / 'study-spec.json').read_text())
    upstream = json.loads((HERE / 'upstream.json').read_text())
    for name, expected in upstream['files_sha256'].items():
        if digest((HERE / 'vendor' / name).read_bytes()) != expected:
            raise ValueError('Upstream bytes changed: ' + name)
    from sew import embed, detect
    from sew import config
    if config.ALPHA != 0.01 or config.MIN_EVIDENCE != 5:
        raise ValueError('Unexpected upstream detector configuration')
    for name, expected in [('tree-sitter', '0.23.2'), ('tree-sitter-python', '0.23.6')]:
        if version(name) != expected:
            raise ValueError(f'{name}: expected {expected}, got {version(name)}')
    inputs = spec['input_domain']
    start = time.monotonic()
    records, rows = [], []
    for case in spec['cases']:
        before = case['source']
        if digest(before.encode()) != case['source_sha256']:
            raise ValueError('Reference source mismatch')
        reference_path = 'programs/' + case['case_id'] + '__reference.py'
        (out / reference_path).write_text(before)
        reference = execute(before, inputs, spec['native_contract']['batch_timeout_seconds'])
        if reference['compile_status'] != 'ok' or len(reference['observations']) != len(inputs):
            raise ValueError('Incomplete reference execution')
        reference_record = {'record_id': case['case_id'] + '__reference', 'role': 'reference', 'source_path': reference_path, **reference}
        records.append(reference_record)
        for key in spec['keys']:
            key_bytes = bytes.fromhex(key['hex'])
            embedded = embed(before, 'python', key_bytes)
            after = embedded['code']
            candidate_path = 'programs/' + case['case_id'] + '__' + key['key_id'] + '.py'
            (out / candidate_path).write_text(after)
            before_detect = detect(before, 'python', key_bytes)
            after_detect = detect(after, 'python', key_bytes)
            candidate = execute(after, inputs, spec['native_contract']['batch_timeout_seconds'])
            candidate_record = {'record_id': case['case_id'] + '__' + key['key_id'], 'role': 'candidate', 'source_path': candidate_path, **candidate}
            records.append(candidate_record)
            if candidate['compile_status'] == 'ok':
                if [x['input'] for x in candidate['observations']] != inputs:
                    raise ValueError('Incomplete or reordered candidate observations')
                mismatches = [
                    {'input': a['input'], 'reference': a['observation'], 'candidate': b['observation']}
                    for a, b in zip(reference['observations'], candidate['observations'])
                    if a['observation'] != b['observation']
                ]
                valid = not mismatches
            else:
                mismatches, valid = [], False
            detected = after_detect['verdict'] == 'Watermark detected'
            rows.append({
                'case_id': case['case_id'], 'kind': case['kind'], 'original_form': case['original_form'],
                'key_id': key['key_id'], 'key_hex': key['hex'],
                'reference_path': reference_path, 'candidate_path': candidate_path,
                'reference_sha256': digest(before.encode()), 'candidate_sha256': digest(after.encode()),
                'domain_sha256': digest(canonical(inputs)),
                'reference_observations_sha256': digest(canonical(reference['observations'])),
                'candidate_observations_sha256': digest(canonical(candidate['observations'])),
                'embedding': {k: v for k, v in embedded.items() if k != 'code'},
                'detector_before': before_detect, 'detector_after': after_detect,
                'validity': 'supported' if valid else 'contradicted',
                'behavior_valid': valid, 'detected': detected, 'joint_success': valid and detected,
                'inputs_compared': len(inputs) if candidate['compile_status'] == 'ok' else 0,
                'mismatch_count': len(mismatches), 'first_mismatch': mismatches[0] if mismatches else None,
            })
    assert len(rows) == spec['configurations']
    assert sum(r['inputs_compared'] for r in rows) == spec['input_comparisons']
    (out / 'rows.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n')
    with (out / 'native-observations.jsonl.gz').open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as zipped:
            for record in records:
                zipped.write(canonical(record) + b'\n')
    fields = ['case_id', 'key_id', 'embedding_status', 'behavior_valid', 'detected', 'joint_success', 'mismatch_count', 'p_before', 'p_after', 'n_groups_after', 'candidate_sha256']
    with (out / 'rows.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({
                'case_id': row['case_id'], 'key_id': row['key_id'], 'embedding_status': row['embedding']['status'],
                'behavior_valid': int(row['behavior_valid']), 'detected': int(row['detected']),
                'joint_success': int(row['joint_success']), 'mismatch_count': row['mismatch_count'],
                'p_before': row['detector_before']['p'], 'p_after': row['detector_after']['p'],
                'n_groups_after': row['detector_after']['n_grades'], 'candidate_sha256': row['candidate_sha256'],
            })
    group = defaultdict(list)
    for row in rows:
        group[row['case_id']].append(row)
    summary = {
        'status': 'PASS', 'schema': 'markvalidity-stock-sew-aliasing-v1',
        'meaning_of_pass': 'All fixed grid configurations were embedded, detected, executed and recorded completely; PASS does not mean all transformed programs preserved behavior.',
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': round(time.monotonic() - start, 6),
        'upstream_commit': upstream['commit'], 'study_spec_sha256': digest((HERE / 'study-spec.json').read_bytes()),
        'runner_sha256': digest(Path(__file__).read_bytes()), 'native_runner_sha256': digest(RUNNER.encode()),
        'environment': {'python': platform.python_version(), 'implementation': platform.python_implementation(), 'platform': platform.platform(), 'tree-sitter': version('tree-sitter'), 'tree-sitter-python': version('tree-sitter-python')},
        'upstream_python_environment_note': 'Upstream environment.yaml declares Python 3.10; this run uses the recorded Python version with its pinned parser dependencies.',
        'cases': len(spec['cases']), 'keys': len(spec['keys']), 'inputs_per_source': len(inputs),
        'candidate_configurations': len(rows), 'native_source_runs_including_references': len(records),
        'native_input_evaluations_including_references': sum(len(r['observations']) for r in records),
        'paired_input_comparisons': sum(r['inputs_compared'] for r in rows),
        'distinct_candidate_source_bytes': len({r['candidate_sha256'] for r in rows}),
        'embedding_statuses': dict(Counter(r['embedding']['status'] for r in rows)),
        'behavior_valid_configurations': sum(r['behavior_valid'] for r in rows),
        'detected_configurations': sum(r['detected'] for r in rows),
        'joint_success_configurations': sum(r['joint_success'] for r in rows),
        'detected_but_invalid_configurations': sum(r['detected'] and not r['behavior_valid'] for r in rows),
        'case_summaries': {name: {'configurations': len(values), 'behavior_valid': sum(r['behavior_valid'] for r in values), 'detected': sum(r['detected'] for r in values), 'joint_success': sum(r['joint_success'] for r in values), 'input_mismatches': sum(r['mismatch_count'] for r in values)} for name, values in group.items()},
        'scope': 'Targeted constructed counterexamples and controls under fixed keys and finite builtin input domains. This is not an estimate of SEW benchmark failure prevalence, a calibrated false-positive study, or a reproduction of its training or full evaluation.',
        'files_sha256': {name: digest((out / name).read_bytes()) for name in ['rows.json', 'rows.csv', 'native-observations.jsonl.gz']},
    }
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
