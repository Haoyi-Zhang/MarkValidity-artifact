"""Replay the retained constructed MBPP v2 boundary controls.

Runs the real producer's execute adapter to cover interrupted-stream admission,
but does not embed a candidate or treat these controls as benchmark samples.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--controls', type=Path, required=True)
    parser.add_argument('--producer', type=Path, required=True)
    parser.add_argument('--vendor', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    producer = args.producer.resolve()
    old_argv = sys.argv
    sys.argv = [str(producer), '--variant', 'stock', '--vendor', str(args.vendor.resolve())]
    try:
        spec = importlib.util.spec_from_file_location('mbpp_v2_boundary_adapter', producer)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
    finally:
        sys.argv = old_argv
    baseline = json.loads((args.controls / 'report.json').read_text())
    args.out.mkdir(parents=True, exist_ok=False)
    results = []
    for case in baseline['records']:
        request = json.loads((args.controls / (case['case'] + '-request.json')).read_text())
        task = {k: request[k] for k in ('test_imports', 'test_list')}
        observation = adapter.execute(request['source'], task)
        if observation['status'] != case['expected']:
            raise ValueError('Boundary-control status differs: ' + case['case'])
        (args.out / (case['case'] + '-result.json')).write_text(json.dumps(observation, indent=2) + '\n')
        results.append({'case': case['case'], 'status': observation['status']})
    report = {'status': 'PASS', 'scope': 'Constructed controls, not additional public-benchmark samples.',
              'cases': len(results), 'producer_sha256': hashlib.sha256(producer.read_bytes()).hexdigest(),
              'results': results}
    (args.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
