#!/usr/bin/env python3
"""Evaluate the extra certificate on fixed observations, without new execution."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

from paired_conditional import PairedEnvelope
from adaptive_policy import AdaptiveConditionalPolicy


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--adaptive', action='store_true')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    api = load_module('natural_api', args.artifact / 'external-studies/sew_natural/analysis/natural_analysis.py')
    sys.path.insert(0, str(args.artifact / 'external-studies/sew_natural/comparison_costs'))
    from policies import target_bounds, IndependentConditionalWidth
    base = args.artifact / 'results/revision-sew-natural/analysis-primary'
    manifest = json.loads((base / 'manifest.json').read_text())
    comparisons = json.loads((base / 'comparisons.json').read_text())
    ledger, labels = api.load_ledgers((args.artifact / i['rows_path'], args.artifact / i['asset_root'])
                                    for i in manifest['inputs'])
    starts = {'reference_identity_known': {g: True for g, info in ledger.groups.items()
                                         if info['reference_sha256'] == info['candidate_sha256']},
              'all_withheld': {}}
    complete = {}
    timings = {'paired': [], 'legacy': []}
    for initialization, initial in starts.items():
        for case, prior in comparisons.items():
            dataset = {'humaneval': 'HumanEval', 'mbpp': 'mbpp_sanitized', 'pooled': None}[prior['scope']]
            left, right, denominator, order = api.pair_coefficients(ledger.scope(dataset), prior['left'], prior['right'])
            state = api.PairState(left, right, denominator)
            for group, label in sorted(initial.items()):
                if group in state.groups:
                    state.reveal(group, label)
            state = PairedEnvelope(state)
            policy = api.AuditPolicy('conditional_differences_first', state, order)
            if args.adaptive:
                policy = AdaptiveConditionalPolicy(state, policy, IndependentConditionalWidth(state))
            query_order, trace = [], []
            paired_first = legacy_first = None
            while True:
                # Reverse the measurement order at alternating prefixes.
                measures = [('paired', lambda: state.certify()),
                            ('legacy', lambda: target_bounds(api, state, 'coupled', 'C'))]
                if len(query_order) % 2:
                    measures.reverse()
                results = {}
                for name, action in measures:
                    start = time.perf_counter_ns()
                    results[name] = action()
                    timings[name].append(time.perf_counter_ns() - start)
                new, old = results['paired'], results['legacy']
                trace.append({'step': len(query_order), 'unknown_differences': len(state.different),
                              'paired_decision': new['decision'], 'legacy_decision': old['decision']})
                if paired_first is None and new['decision'] in api.CERTIFICATES:
                    paired_first = {'queries': len(query_order), 'certificate': api.serial(new),
                                    'unknown_differences': len(state.different)}
                if legacy_first is None and old['decision'] in api.CERTIFICATES:
                    legacy_first = {'queries': len(query_order), 'certificate': api.serial(old)}
                if paired_first is not None and legacy_first is not None:
                    break
                group = policy.next_group(state)
                if group is None:
                    raise RuntimeError('complete original study must certify this comparison')
                state.reveal(group, labels[group])
                query_order.append(group)
            # Retrospective complete labels are used only to validate certificates.
            def score(coefficients):
                n = sum(a * labels[g] for g, (a, b) in coefficients.items())
                d = sum(b * labels[g] for g, (a, b) in coefficients.items())
                return n, d
            nl, dl = score(left)
            nr, dr = score(right)
            truth = api.relation(nl * dr - nr * dl, nl * dr - nr * dl)
            if paired_first['certificate']['decision'] != truth or legacy_first['certificate']['decision'] != truth:
                raise AssertionError('certificate disagrees with the complete paired observation ledger')
            record = {'case': case, 'initialization': initialization, 'denominator': denominator,
                      'paired_first': paired_first, 'legacy_first': legacy_first,
                      'query_order': query_order, 'trace': trace, 'complete_decision': truth,
                      'paired_result': [nl, dl, nr, dr]}
            if args.adaptive:
                record['selection_branches'] = dict(policy.branch_counts)
            complete[initialization + '/' + case] = record
            print(initialization, case, paired_first['queries'], legacy_first['queries'],
                  paired_first['unknown_differences'], flush=True)
    report = {'status': 'complete',
              'design': ('Public singleton-interval minimax switch with H-first fallback.' if args.adaptive else 'Same public H-first query policy; add paired ratio-envelope stopping test.') + ' Actual retained labels are disclosed only after query selection. No new program executions in this analysis.',
              'adaptive_selection': args.adaptive,
              'case_count': len(complete),
              'cases_with_fewer_queries': sum(r['paired_first']['queries'] < r['legacy_first']['queries'] for r in complete.values()),
              'cases_with_more_queries': sum(r['paired_first']['queries'] > r['legacy_first']['queries'] for r in complete.values()),
              'prefixes_checked': len(timings['paired']),
              'timing': {name: {'calls': len(values), 'total_seconds': sum(values) / 1e9,
                                'median_microseconds': statistics.median(values) / 1e3,
                                'minimum_microseconds': min(values) / 1e3,
                                'maximum_microseconds': max(values) / 1e3}
                         for name, values in timings.items()},
              'results': complete}
    (args.out / 'study.json').write_text(json.dumps(report, indent=2) + '\n')
    with (args.out / 'summary.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['case', 'initialization', 'paired_queries', 'legacy_queries', 'remaining_differences', 'decision'])
        for record in complete.values():
            writer.writerow([record['case'], record['initialization'], record['paired_first']['queries'],
                             record['legacy_first']['queries'], record['paired_first']['unknown_differences'],
                             record['complete_decision']])
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}, indent=2))


if __name__ == '__main__':
    main()
