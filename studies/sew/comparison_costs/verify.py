#!/usr/bin/env python3
"""Read-only receiving for all new comparison baselines and actual audit costs.

The command writes only its stdout. It does not rerun candidate programs,
refresh historical analysis outputs, or rewrite observations and timing files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import admission
from analyze import load_api
import independent
from independent import require
import summarize
import verify_native
import verify_policies
import verify_replay


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_receiver_boundary():
    # An undefined common margin can require one, not all, members of a
    # coefficient class. This checks the receiver's aggregation boundary.
    left = {'known': (1, 1), 'u1': (0, 1), 'u2': (0, 1)}
    right = {'u1': (0, 1), 'u2': (0, 1)}
    admitted = {'known': True}
    expected = dict(lower=1, upper=2, units='conditional_cross_product_count_margin',
                    decision='undefined_possible', defined_all=False)
    require(independent.bounds(left, right, admitted, 'coupled', 'C') == expected,
            'independent native receiver merged a required one-group witness')
    require(verify_replay.ReceiverState(left, right, admitted).bounds('coupled', 'C') == expected,
            'independent replay receiver merged a required one-group witness')
    # The independent receiver must also reject corrupted completed evidence;
    # these cases may not be silently rewritten to unavailable labels.
    compile_ok = {'event': 'source_compile', 'status': 'passed', 'error': None}
    failed = {'event': 'test_result', 'test_index': 0, 'status': 'failed',
              'error': {'phase': 'original_assertion', 'type': 'builtins.AssertionError'}}
    duplicate = '\n'.join(json.dumps(event) for event in (compile_ok, failed, failed))
    for stdout, dataset, tests in [('broken', 'HumanEval', None), (duplicate, 'mbpp_sanitized', 2)]:
        try:
            verify_native.native_record(stdout, dataset, tests, 0, None)
        except (ValueError, AssertionError):
            pass
        else:
            raise ValueError('independent receiver hid malformed completed evidence as unavailable')
    return {'status': 'PASS', 'receiver_undefined_class_controls': 2,
            'receiver_malformed_completion_controls': 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--results', type=Path, required=True)
    args = parser.parse_args()
    root, results = args.artifact.resolve(), args.results.resolve()

    def stored(relative):
        return json.loads((results / relative).read_text())

    controls = admission.controls()
    controls['admission_sha256'] = sha(Path(admission.__file__))
    require(controls == stored('admission-controls.json'), 'strict admission controls or source binding changed')
    api, path = load_api(root)
    policy = verify_policies.controls(api)
    policy['source_sha256'] = {name: sha(Path(__file__).with_name(name))
                               for name in ('policies.py', 'analyze.py', 'verify_policies.py')}
    policy['natural_analysis_sha256'] = sha(path)
    require(policy == stored('policy-controls.json'), 'finite policy controls or source binding changed')
    boundary = verify_receiver_boundary()
    print(json.dumps({'event': 'controls_received', 'admission_cases': controls['checked'],
                      'hypothetical_endpoint_checks': policy['hypothetical_endpoint_checks'],
                      **boundary}), flush=True)
    replay = verify_replay.receive(root, results)
    require(replay == stored('retrospective-receiving.json'), 'independent retrospective receiving report differs')
    print(json.dumps({'event': 'retrospective_received', 'schedules': replay['schedules_received'],
                      'prefixes': replay['prefixes_received']}), flush=True)
    native = verify_native.receive(root, root / 'results/revision-sew-natural/public-registry.json', results / 'native-timing')
    require(native == stored('native-receiving.json'), 'independent native receiving report differs')
    reverse_native = verify_native.receive(root, root / 'results/revision-sew-natural/public-registry.json', results / 'native-timing-reverse')
    require(reverse_native == stored('native-receiving-reverse.json'), 'independent complementary native receiving report differs')
    summary = summarize.derive(root, results)
    expected = {'summary.json': json.dumps(summary, indent=2) + '\n', **summarize.table_bytes(summary)}
    for relative, text in expected.items():
        with (results / relative).open(newline='') as stream:
            require(stream.read() == text, 'derived publication summary/table is stale: ' + relative)
    output = {'status': 'PASS', 'mode': 'read-only',
              'retrospective_schedules': replay['schedules_received'],
              'retrospective_prefixes': replay['prefixes_received'],
              'native_runs': native['runs_received'] + reverse_native['runs_received'],
              'native_candidate_suite_records': native['candidate_suite_records_received'] + reverse_native['candidate_suite_records_received'],
              'native_prefixes': native['prefixes_received'] + reverse_native['prefixes_received'],
              'native_source_snapshots_received': native['source_snapshots_received'] + reverse_native['source_snapshots_received'],
              'native_order_balance': summary['native_timing']['counterbalance'],
              'hindsight_joint_minima': replay['joint_hindsight_minima_received'],
              'finite_policy_endpoint_controls': policy['hypothetical_endpoint_checks'],
              'admission_controls': controls['checked'],
              'receiver_boundary_controls': boundary['receiver_undefined_class_controls'] + boundary['receiver_malformed_completion_controls'],
              'candidate_programs_executed': 0, 'artifact_files_written': 0,
              'summary_sha256': sha(results / 'summary.json')}
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
