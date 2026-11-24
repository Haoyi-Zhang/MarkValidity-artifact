"""Recheck observed S4 failures with plain standalone Python assertion scripts.

This diagnostic imports neither the benchmark producer nor its observer. Every
original assertion runs in a new ordinary Python process. A second, diagnostic
evaluation prints the original comparison's left expression after the exact
assertion passes; it is not counted as a benchmark observation or budget query.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--results-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    tasks = {t['task_id']: t for t in json.loads(args.dataset.read_text())}
    root = args.results_root.resolve()
    factors = {v: {(r['task_id'], r['key_id']): r for r in json.loads((root / 'factors' / v / 'rows.json').read_text())}
               for v in ('stock', 's4_return_boundary')}
    failed = [r for r in factors['stock'].values() if r['validity_status'] == 'contradicted']
    assert len(failed) == 3
    args.out.mkdir(parents=True, exist_ok=False)
    scripts = args.out / 'standalone'; scripts.mkdir()
    sources = args.out / 'sources'; sources.mkdir()
    env = os.environ.copy(); env.pop('PYTHONPATH', None)
    env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1')
    records = []
    for before in failed:
        coordinate = (before['task_id'], before['key_id'])
        task = tasks[before['task_id']]
        after = factors['s4_return_boundary'][coordinate]
        stem = 'MBPP-%04d__%s' % coordinate
        source_map = {'reference': task['code'],
                      'stock': (root / 'factors/stock' / before['candidate_path']).read_text(),
                      's4_return_boundary': (root / 'factors/s4_return_boundary' / after['candidate_path']).read_text()}
        for version, source in source_map.items():
            (sources / (stem + '__' + version + '.py')).write_text(source)
            for index, original_assertion in enumerate(task['test_list']):
                parsed = ast.parse(original_assertion)
                assert len(parsed.body) == 1 and isinstance(parsed.body[0], ast.Assert)
                comparison = parsed.body[0].test
                assert isinstance(comparison, ast.Compare)
                expression = ast.get_source_segment(original_assertion, comparison.left)
                assert expression is not None
                standalone = '\n'.join(task['test_imports']) + '\n' + source + '\n' + original_assertion + '\n'
                standalone += 'print("RETURN_VALUE " + repr(' + expression + '))\n'
                path = scripts / (stem + '__' + version + '__assertion-%d.py' % index)
                path.write_text(standalone)
                process = subprocess.run([sys.executable, '-B', '-S', str(path.resolve())],
                                         capture_output=True, text=True, env=env, timeout=15,
                                         cwd=args.out.resolve())
                outcome = {'task_id': coordinate[0], 'key_id': coordinate[1], 'version': version,
                           'test_index': index, 'source_sha256': sha(source.encode()),
                           'original_assertion': original_assertion,
                           'original_assertion_sha256': sha(original_assertion.encode()),
                           'diagnostic_expression': expression,
                           'script_path': path.relative_to(args.out).as_posix(),
                           'script_sha256': sha(path.read_bytes()),
                           'returncode': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr}
                if version == 'stock':
                    assert process.returncode != 0 and 'NameError' in process.stderr and 'returnmax_length' in process.stderr
                else:
                    assert process.returncode == 0 and process.stdout.startswith('RETURN_VALUE ')
                records.append(outcome)
    for row in records:
        if row['version'] != 's4_return_boundary':
            continue
        reference = next(r for r in records if r['version'] == 'reference' and
                         all(r[k] == row[k] for k in ('task_id', 'key_id', 'test_index')))
        assert row['stdout'] == reference['stdout'], 'Repaired return differs from reference'
    report = {'status': 'PASS', 'scope': 'All three actually failing stock coordinates and paired S4 candidates, with their unchanged original assertions, reexecuted in plain standalone Python scripts. Independent diagnostic, not additional benchmark samples.',
              'python': sys.version, 'configurations': 3, 'unique_public_tasks': 2,
              'standalone_processes': len(records), 'stock_assertion_failures': sum(r['version'] == 'stock' and r['returncode'] != 0 for r in records),
              's4_original_assertions_passed': sum(r['version'] == 's4_return_boundary' and r['returncode'] == 0 for r in records),
              'reference_original_assertions_passed': sum(r['version'] == 'reference' and r['returncode'] == 0 for r in records),
              'script_sha256': sha(Path(__file__).read_bytes()), 'records': records}
    (args.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'records'}, indent=2))


if __name__ == '__main__':
    main()
