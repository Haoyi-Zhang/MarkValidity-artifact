"""Export public query prefixes for independently reexecuted receiving cases."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from natural_analysis import canonical_bytes, digest


def export(analysis_root, destination):
    manifest = json.loads((analysis_root / 'manifest.json').read_text())
    if manifest['initialization'] != 'reference_identity_known':
        raise ValueError('online cases use the reference-identity initialization')
    reports = json.loads((analysis_root / 'comparisons.json').read_text())
    groups = json.loads((analysis_root / 'group_index.json').read_text())
    input_base = (analysis_root / manifest.get('input_path_base_from_analysis', '.')).resolve()
    input_rows = []
    for item in manifest['inputs']:
        path = Path(item['rows_path'])
        if not path.is_absolute(): path = input_base / path
        if digest(path.read_bytes()) != item['rows_sha256']:
            raise ValueError('input ledger changed after inference analysis')
        input_rows.append(json.loads(path.read_text()))
    public_fields = ('dataset', 'task_id', 'key_id', 'key_hex', 'variant',
                     'reference_sha256', 'candidate_sha256', 'contract_sha256',
                     'source_contract_sha256', 'source_path', 'reference_path',
                     'contract_path', 'native_contract_path', 'native_contract_sha256',
                     'suite_cost')
    selected = [('humaneval__stock__s1', 'J', 'joint_width_per_suite'),
                ('humaneval__stock__s1', 'C', 'conditional_differences_first'),
                ('mbpp__stock__s4', 'J', 'joint_width_per_suite'),
                ('mbpp__stock__s4', 'C', 'conditional_differences_first')]
    cases = []
    for case, metric, policy in selected:
        report = reports[case]
        run = report['schedules'][policy]
        certificate = run['first_certificates'][f'coupled_{metric}']
        prefix = run['schedule'][:certificate['suite_queries']]
        if digest(canonical_bytes(prefix)) != certificate['schedule_prefix_sha256']:
            raise ValueError('stored prefix digest mismatch')
        queries = []
        for step, group_index in enumerate(prefix, 1):
            info = groups[group_index]
            row = input_rows[info['input_index']][info['representative_row_index']]
            public = {key: row[key] for key in public_fields if key in row}
            for key in ('source_path', 'reference_path', 'contract_path'):
                public.setdefault(key, info[key])
            queries.append(dict(step=step, group_index=group_index,
                                input_index=info['input_index'], public_row=public))
        cases.append(dict(case=case, scope=report['scope'], left=report['left'], right=report['right'],
                          metric=metric, policy=policy, denominator=report['denominator'],
                          free_reference_groups=report['reference_identity_known_groups'],
                          target_decision=certificate['decision'], expected_suite_queries=len(prefix),
                          schedule_prefix_sha256=certificate['schedule_prefix_sha256'], queries=queries,
                          expected_certificate=certificate))
    result = dict(schema='markvalidity-independent-online-case-plan-v1',
                  declaration='Case/policy choices frozen before independent native replay. The source ledgers are already observed; this is an independent receiving replication, not a blinded new-corpus study.',
                  initialization='Admit candidate=reference groups from the already qualified exact reference contract at zero additional candidate-suite cost.',
                  stopping='Recompute PairState from public coefficients and newly received labels after each selected suite. Stop at the first strict/tie certificate for the target metric; do not assume the saved target or prefix length is correct.',
                  cost='Count actual candidate suite invocations and measure elapsed separately. Reference qualification is shared setup; candidate function calls and MBPP assertion entries are distinct optional measures.',
                  inputs=manifest['inputs'], input_path_base_from_analysis=manifest.get('input_path_base_from_analysis'),
                  analysis_path=str(analysis_root), cases=cases,
                  analysis_manifest_sha256=digest((analysis_root / 'manifest.json').read_bytes()),
                  comparisons_sha256=digest((analysis_root / 'comparisons.json').read_bytes()),
                  export_source_sha256=digest(Path(__file__).read_bytes()))
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({c['case'] + ':' + c['metric']: c['expected_suite_queries'] for c in cases}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    export(args.analysis, args.output)
