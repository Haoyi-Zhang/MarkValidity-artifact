#!/usr/bin/env python3
"""Receive the retained SEW grid and independently re-execute its source bytes.

The default verification uses Python's standard library and does not import the
study producer or the watermark implementation. --replay-upstream additionally
repeats the stock embed/detect calls; that part shares the upstream code and is
reported separately from the native receiver.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


NATIVE_RECEIVER = r'''
import json, sys
job = json.load(sys.stdin)
answer = []
for number in job['domain']:
    try:
        module = {'__name__': '__received_source__'}
        exec(compile(job['program'], '<received-source>', 'exec'), module)
        value = module['solve'](number)
        observed = dict(kind='return', value=value)
    except BaseException as problem:
        observed = dict(kind='exception', type=type(problem).__module__ + '.' + type(problem).__qualname__, message=str(problem))
    answer.append(dict(input=number, observation=observed))
sys.stdout.write(json.dumps(answer, sort_keys=True, separators=(',', ':')))
'''


def native(source: str, domain: list[int]) -> list[dict]:
    run = subprocess.run(
        [sys.executable, '-I', '-B', '-c', NATIVE_RECEIVER],
        input=json.dumps({'program': source, 'domain': domain}),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        timeout=10, check=True,
    )
    assert not run.stderr
    return json.loads(run.stdout)


def reference_value(case: dict, n: int):
    if case['kind'] == 'aliased_integer':
        return n
    values = list(range(n))
    if case['kind'] == 'unaliased_list' or case['original_form'] == 'augmented':
        return values + values
    return values


def main():
    if not __debug__:
        raise RuntimeError('Verification must run without Python optimization; assertions are required.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=ARTIFACT / 'results/revision-sew-aliasing')
    parser.add_argument('--replay-upstream', action='store_true')
    args = parser.parse_args()
    out = args.results.resolve()
    start = time.monotonic()
    spec_bytes = (HERE / 'study-spec.json').read_bytes()
    spec = json.loads(spec_bytes)
    summary = json.loads((out / 'summary.json').read_text())
    assert sha(spec_bytes) == summary['study_spec_sha256']
    assert sha((HERE / 'run_study.py').read_bytes()) == summary['runner_sha256']
    assert summary['status'] == 'PASS'
    upstream = json.loads((HERE / 'upstream.json').read_text())
    assert upstream['commit'] == spec['upstream_commit'] == summary['upstream_commit']
    for rel, expected in upstream['files_sha256'].items():
        assert sha((HERE / 'vendor' / rel).read_bytes()) == expected, rel
    for rel, expected in summary['files_sha256'].items():
        assert sha((out / rel).read_bytes()) == expected, rel
    rows = json.loads((out / 'rows.json').read_text())
    with gzip.open(out / 'native-observations.jsonl.gz', 'rt') as f:
        observations = [json.loads(line) for line in f]
    archive = {r['record_id']: r for r in observations}
    assert len(archive) == len(observations) == 108
    cases = {c['case_id']: c for c in spec['cases']}
    keys = {k['key_id']: k for k in spec['keys']}
    domain = spec['input_domain']
    assert domain == list(range(33)) and len(cases) == 6 and len(keys) == 17
    expected_grid = {(c, k) for c in cases for k in keys}
    assert {(r['case_id'], r['key_id']) for r in rows} == expected_grid
    assert len(rows) == len(expected_grid) == 102
    received = {}
    for name, record in archive.items():
        path = out / record['source_path']
        source = path.read_text()
        assert sha(path.read_bytes()) == record['source_sha256']
        assert record['domain_sha256'] == sha(encode(domain))
        assert record['compile_status'] == 'ok' and not record['stderr']
        assert [x['input'] for x in record['observations']] == domain
        actual = native(source, domain)
        assert actual == record['observations'], name
        received[name] = actual
    for name, case in cases.items():
        record = archive[name + '__reference']
        assert (out / record['source_path']).read_text() == case['source']
        assert record['source_sha256'] == case['source_sha256']
        assert received[name + '__reference'] == [
            {'input': n, 'observation': {'kind': 'return', 'value': reference_value(case, n)}}
            for n in domain
        ], name
    totals = Counter()
    grouped = defaultdict(Counter)
    for row in rows:
        case = cases[row['case_id']]
        assert row['key_hex'] == keys[row['key_id']]['hex']
        assert row['kind'] == case['kind'] and row['original_form'] == case['original_form']
        before_id = row['case_id'] + '__reference'
        after_id = row['case_id'] + '__' + row['key_id']
        before, after = received[before_id], received[after_id]
        assert row['reference_path'] == archive[before_id]['source_path']
        assert row['candidate_path'] == archive[after_id]['source_path']
        assert row['reference_sha256'] == archive[before_id]['source_sha256']
        assert row['candidate_sha256'] == archive[after_id]['source_sha256']
        assert row['domain_sha256'] == sha(encode(domain))
        assert row['reference_observations_sha256'] == sha(encode(before))
        assert row['candidate_observations_sha256'] == sha(encode(after))
        differing = [
            {'input': a['input'], 'reference': a['observation'], 'candidate': b['observation']}
            for a, b in zip(before, after) if a['observation'] != b['observation']
        ]
        assert row['inputs_compared'] == 33
        assert row['mismatch_count'] == len(differing)
        assert row['first_mismatch'] == (differing[0] if differing else None)
        valid = not differing
        assert row['behavior_valid'] is valid
        assert row['validity'] == ('supported' if valid else 'contradicted')
        detector = row['detector_after']
        assert math.isclose(detector['p'], min(1.0, 2 * min(detector['p_all'], detector['p_syntax'])), abs_tol=1e-15)
        detected = detector['n_grades'] >= 5 and detector['p'] < 0.01
        expected_verdict = 'Insufficient evidence' if detector['n_grades'] < 5 else 'Watermark detected' if detected else 'No watermark evidence'
        assert detector['verdict'] == expected_verdict
        assert row['detected'] is detected and row['joint_success'] is (valid and detected)
        assert row['embedding']['status'] == 'ok'
        for counts in [totals, grouped[row['case_id']]]:
            counts['configurations'] += 1
            counts['behavior_valid'] += valid
            counts['detected'] += detected
            counts['joint_success'] += valid and detected
            counts['input_mismatches'] += len(differing)
        totals['detected_but_invalid'] += detected and not valid
    for name, counts in grouped.items():
        assert dict(counts) == summary['case_summaries'][name]
    for field, stat in [('candidate_configurations', 'configurations'), ('behavior_valid_configurations', 'behavior_valid'), ('detected_configurations', 'detected'), ('joint_success_configurations', 'joint_success'), ('detected_but_invalid_configurations', 'detected_but_invalid')]:
        assert summary[field] == totals[stat], field
    with (out / 'rows.csv').open(newline='') as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == len(rows)
    for csv_row, row in zip(csv_rows, rows):
        for name in ['case_id', 'key_id', 'candidate_sha256']:
            assert csv_row[name] == row[name]
        for name in ['behavior_valid', 'detected', 'joint_success', 'mismatch_count']:
            assert int(csv_row[name]) == row[name]
        assert csv_row['embedding_status'] == row['embedding']['status']
        assert float(csv_row['p_before']) == row['detector_before']['p']
        assert float(csv_row['p_after']) == row['detector_after']['p']
        assert int(csv_row['n_groups_after']) == row['detector_after']['n_grades']
    replayed = 0
    if args.replay_upstream:
        sys.path.insert(0, str(HERE / 'vendor'))
        from sew import embed, detect
        for row in rows:
            source = cases[row['case_id']]['source']
            key = bytes.fromhex(row['key_hex'])
            embedded = embed(source, 'python', key)
            assert embedded['code'].encode() == (out / row['candidate_path']).read_bytes()
            assert {k: v for k, v in embedded.items() if k != 'code'} == row['embedding']
            assert detect(source, 'python', key) == row['detector_before']
            assert detect(embedded['code'], 'python', key) == row['detector_after']
            replayed += 1
    report = {
        'status': 'PASS', 'receiver_sha256': sha(Path(__file__).read_bytes()),
        'study_spec_sha256': sha(spec_bytes), 'summary_sha256': sha((out / 'summary.json').read_bytes()),
        'native_source_runs': len(received), 'native_input_evaluations': sum(len(x) for x in received.values()),
        'case_key_pairs': len(rows), 'paired_input_comparisons': len(rows) * len(domain),
        'reference_cases_checked_against_independent_closed_form': len(cases),
        'upstream_embedding_detection_pairs_replayed': replayed,
        'detector_replay_independence': 'Uses upstream code when requested; the native receiver and closed-form reference checks do not import it or the producer.',
        'summary_counts': dict(totals), 'elapsed_seconds': round(time.monotonic() - start, 6),
    }
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
