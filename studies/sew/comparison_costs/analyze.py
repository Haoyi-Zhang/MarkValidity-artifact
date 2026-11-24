#!/usr/bin/env python3
"""Compare method-specific public policies on unchanged complete natural ledgers.

This is retrospective disclosure of actual saved observations. It performs no
new candidate execution. The full suffix is retained for plots, while first
certificates report what an online execution would request. The label-informed
joint witness optimum is an explicitly post hoc diagnostic, never a policy.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time

from policies import initialize, policy_name, target_bounds


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_api(artifact):
    source = artifact / 'external-studies/sew_natural/analysis/natural_analysis.py'
    spec = importlib.util.spec_from_file_location('comparison_costs_analysis', source)
    api = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = api
    spec.loader.exec_module(api)
    return api, source


def joint_witness_optimum(api, coefficients, initial, labels, method):
    """Exact hindsight minimum number of unit-cost queries for this certificate.

For a strict left win, each disclosed group improves the independent lower
endpoint by a_L*v+a_R*(1-v); for a strict right win, it reduces the upper endpoint
by a_L*(1-v)+a_R*v. The coupled endpoint has the analogous signed coefficient.
The largest actual gains therefore yield an exact minimum-size witness. This
uses hidden outcomes and cannot be used by an executable selection policy.
"""
    state, _ = initialize(api, coefficients, initial, method, 'J')
    start = target_bounds(api, state, method, 'J')
    remaining = state.groups - state.attempted
    if any(type(labels[g]) is not bool for g in remaining):
        return {'available': False, 'reason': 'not all finite reference labels are resolved'}
    full = (sum(a * labels[g] for g, (a, b) in state.left.coefficients.items())
            - sum(a * labels[g] for g, (a, b) in state.right.coefficients.items()))
    direction = api.relation(full, full)
    if direction == 'tie':
        relevant = [g for g in remaining if
                    (sum(pair[0] for pair in state.pairs[g]) if method == 'independent'
                     else abs(state.pairs[g][0][0] - state.pairs[g][1][0]))]
        return {'available': True, 'decision': direction, 'minimum_queries': len(relevant),
                'witness': sorted(relevant), 'proof': 'Exact tie requires zero remaining interval width.'}
    gain = {}
    for g in remaining:
        (al, _), (ar, _) = state.pairs[g]
        value = labels[g]
        if method == 'independent':
            gain[g] = al * value + ar * (1 - value) if direction == 'left_strict' else al * (1 - value) + ar * value
        else:
            c = al - ar
            gain[g] = c * value - min(0, c) if direction == 'left_strict' else max(0, c) - c * value
    endpoint = start['lower'] if direction == 'left_strict' else -start['upper']
    ordered = sorted(remaining, key=lambda g: (-gain[g], g))
    witness, total_gain = [], 0
    for g in ordered:
        if endpoint + total_gain > 0:
            break
        witness.append(g)
        total_gain += gain[g]
    if endpoint + total_gain <= 0:
        raise ValueError('complete labels must establish their strict joint direction')
    previous = total_gain - (gain[witness[-1]] if witness else 0)
    if witness and endpoint + previous > 0:
        raise ValueError('hindsight witness is not minimal')
    return {'available': True, 'decision': direction, 'minimum_queries': len(witness),
            'initial_signed_endpoint': endpoint, 'selected_gain': total_gain,
            'best_gain_with_one_fewer_query': previous,
            'strict_signed_endpoint': endpoint + total_gain, 'witness': witness,
            'proof': 'Any smaller subset has at most the sum of that many largest nonnegative realized endpoint gains.'}


def run(api, coefficients, initial, labels, method, target, output):
    state, policy = initialize(api, coefficients, initial, method, target)
    oracle = api.SealedOracle(labels)
    first = None
    queries = []
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ['step', 'group', 'received_label', 'lower', 'upper', 'units', 'decision', 'groups_admitted']
    with gzip.GzipFile(filename=str(output), mode='wb', mtime=0) as raw:
        with io.TextIOWrapper(raw, encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            selected, label = '', ''
            while True:
                bounds = target_bounds(api, state, method, target)
                writer.writerow({'step': len(queries), 'group': selected, 'received_label': label,
                                 'lower': '' if bounds['lower'] is None else str(bounds['lower']),
                                 'upper': '' if bounds['upper'] is None else str(bounds['upper']),
                                 'units': bounds['units'], 'decision': bounds['decision'],
                                 'groups_admitted': len(state.admitted)})
                if first is None and bounds['decision'] in api.CERTIFICATES:
                    first = {'suite_queries': len(queries), 'decision': bounds['decision'],
                             'bounds': api.serial(bounds),
                             'query_prefix_sha256': hashlib.sha256(api.canonical_bytes(queries)).hexdigest()}
                selected = policy.next_group(state)
                if selected is None:
                    break
                value = oracle.query(selected)
                state.reveal(selected, value)
                queries.append(selected)
                label = '?' if value is None else int(value)
    return {'method': method, 'target': target, 'policy': policy_name(method, target),
            'first_certificate': first, 'full_retrospective_queries': len(queries),
            'full_query_order': queries, 'trace_file': output.name, 'trace_sha256': sha(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--initialization', choices=('reference_identity_known', 'all_withheld'), default='reference_identity_known')
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('fresh output directory required')
    root = args.artifact.resolve()
    api, module_path = load_api(root)
    original = 'analysis-primary' if args.initialization == 'reference_identity_known' else 'analysis-all-withheld'
    base = root / 'results/revision-sew-natural' / original
    original_manifest = json.loads((base / 'manifest.json').read_text())
    comparisons = json.loads((base / 'comparisons.json').read_text())
    ledger, labels = api.load_ledgers((root / item['rows_path'], root / item['asset_root'])
                                     for item in original_manifest['inputs'])
    initial = ({g: True for g, info in ledger.groups.items() if info['reference_sha256'] == info['candidate_sha256']}
               if args.initialization == 'reference_identity_known' else {})
    args.out.mkdir(parents=True)
    reports, summary = {}, []
    indices = {g: index for index, g in enumerate(sorted(ledger.groups))}
    for case, prior in comparisons.items():
        dataset = {'humaneval': 'HumanEval', 'mbpp': 'mbpp_sanitized', 'pooled': None}[prior['scope']]
        coefficients = api.pair_coefficients(ledger.scope(dataset), prior['left'], prior['right'])
        record = {'case': case, 'denominator': coefficients[2], 'scope': prior['scope'],
                  'left': prior['left'], 'right': prior['right'], 'runs': {}, 'hindsight_joint_witness': {}}
        for method in ('coupled', 'independent'):
            record['hindsight_joint_witness'][method] = joint_witness_optimum(api, coefficients, initial, labels, method)
            for target in ('J', 'C'):
                result = run(api, coefficients, initial, labels, method, target,
                             args.out / 'traces' / f'{case}__{method}__{target}.csv.gz')
                if result['first_certificate'] is None:
                    raise ValueError('complete finite ledgers must identify this declared comparison')
                if method == 'coupled':
                    old = prior['schedules'][policy_name(method, target)]['first_certificates']['coupled_' + target]
                    if result['first_certificate']['suite_queries'] != old['suite_queries']:
                        raise ValueError('the existing coupled policy changed its stopping cost')
                    prefix = result['full_query_order'][:old['suite_queries']]
                    if hashlib.sha256(api.canonical_bytes([indices[g] for g in prefix])).hexdigest() != old['schedule_prefix_sha256']:
                        raise ValueError('the existing coupled policy changed its selected prefix')
                key = method + '_' + target
                record['runs'][key] = result
                summary.append({'case': case, 'scope': prior['scope'], 'initialization': args.initialization,
                                'method': method, 'target': target, 'policy': result['policy'],
                                'denominator': coefficients[2], 'candidate_suite_queries': result['first_certificate']['suite_queries'],
                                'decision': result['first_certificate']['decision'],
                                'hindsight_minimum_J_queries': record['hindsight_joint_witness'][method]['minimum_queries'] if target == 'J' else '',
                                'trace_file': 'traces/' + result['trace_file']})
        reports[case] = record
        print(case, {key: value['first_certificate']['suite_queries'] for key, value in record['runs'].items()},
              {key: value['minimum_queries'] for key, value in record['hindsight_joint_witness'].items()}, flush=True)
    manifest = {'schema': 'markvalidity-method-specific-policy-replay-v1', 'status': 'COMPLETE',
                'initialization': args.initialization,
                'scope': 'Retrospective disclosure of fixed actual benchmark observations; no program execution by this script. Full suffixes are for matched-budget plots; first-certificate prefixes are the executable selection costs.',
                'cost_unit': 'one additional full candidate source-contract suite after qualified reference-identity admission',
                'inputs': {item['rows_path']: sha(root / item['rows_path']) for item in original_manifest['inputs']},
                'original_comparisons_sha256': sha(base / 'comparisons.json'),
                'source_sha256': {'analyze.py': sha(Path(__file__)), 'policies.py': sha(Path(__file__).with_name('policies.py')),
                                  'natural_analysis.py': sha(module_path)},
                'cases': len(reports), 'schedules': len(summary),
                'policy_information': 'Public coefficients, identities, fixed suite cost and previously disclosed labels. Hypothetical 0/1 replies are evaluated symmetrically; no future reply is observed during selection.',
                'hindsight_diagnostic': 'Exact minimum-size joint endpoint certificate on the completed finite ledger. Its realized-label gains are not available to a runnable policy and are not counted as an executable baseline.',
                'reports': reports}
    (args.out / 'analysis.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    with (args.out / 'comparison_summary.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)


if __name__ == '__main__':
    main()
