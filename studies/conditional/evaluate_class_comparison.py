#!/usr/bin/env python3
"""Evaluate exact class-count conditional decisions on every actual audit prefix."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

from exact_residual_conditional import compare_classes
from paired_conditional import PairedEnvelope


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact', type=Path, required=True)
    p.add_argument('--study', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--assignment-budget', type=int, default=1_000_000)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    source = args.artifact / 'external-studies/sew_natural/analysis/natural_analysis.py'
    spec = importlib.util.spec_from_file_location('class_model', source)
    api = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = api
    spec.loader.exec_module(api)
    study = json.loads(args.study.read_text())
    manifest = json.loads((args.artifact / 'results/revision-sew-natural/analysis-primary/manifest.json').read_text())
    ledger, labels = api.load_ledgers((args.artifact / i['rows_path'], args.artifact / i['asset_root']) for i in manifest['inputs'])
    initial = {g: True for g, info in ledger.groups.items() if info['candidate_sha256'] == info['reference_sha256']}
    timing = {'exact_cpu_ns': [], 'envelope_cpu_ns': []}
    counts = {'prefixes': 0, 'exact_decisions': 0, 'full_endpoints': 0, 'early_unresolved_witnesses': 0,
              'budget_exhaustions': 0, 'undefined_prefixes': 0, 'count_assignments_evaluated': 0,
              'max_unresolved_differences': 0, 'max_full_count_space': 0,
              'max_assignments_evaluated_at_one_prefix': 0}
    results = {}
    for name, case in study['results'].items():
        scope, left, right = case['case'].split('__')
        corpus = {'humaneval': 'HumanEval', 'mbpp': 'mbpp_sanitized', 'pooled': None}[scope]
        lc, rc, denominator, order = api.pair_coefficients(ledger.scope(corpus), left, right)
        state = api.PairState(lc, rc, denominator)
        if case['initialization'] == 'reference_identity_known':
            for group, label in sorted(initial.items()):
                if group in state.groups:
                    state.reveal(group, label)
        state = PairedEnvelope(state)
        first, prefixes, all_previous_exact_or_undefined = None, [], True
        full_nl, full_ml, full_nr, full_mr = case['paired_result']
        complete_margin = full_nl * full_mr - full_nr * full_ml
        for step in range(len(case['query_order']) + 1):
            functions = [('exact_cpu_ns', lambda: compare_classes(state, args.assignment_budget)),
                         ('envelope_cpu_ns', state.certify)]
            if step % 2:
                functions.reverse()
            values = {}
            for key, function in functions:
                tick = time.process_time_ns()
                values[key] = function()
                timing[key].append(time.process_time_ns() - tick)
            exact, cheap = values['exact_cpu_ns'], values['envelope_cpu_ns']
            counts['prefixes'] += 1
            counts['count_assignments_evaluated'] += exact['assignments_evaluated']
            counts['max_unresolved_differences'] = max(counts['max_unresolved_differences'], exact['different_groups'])
            counts['max_full_count_space'] = max(counts['max_full_count_space'], exact['coefficient_class_assignments'])
            counts['max_assignments_evaluated_at_one_prefix'] = max(counts['max_assignments_evaluated_at_one_prefix'], exact['assignments_evaluated'])
            if not exact['defined_all']:
                counts['undefined_prefixes'] += 1
            elif not exact['exact_decision']:
                counts['budget_exhaustions'] += 1
                all_previous_exact_or_undefined = False
            else:
                counts['exact_decisions'] += 1
                if exact['endpoints_complete']:
                    counts['full_endpoints'] += 1
                    if not exact['lower'] <= complete_margin <= exact['upper']:
                        raise AssertionError('class endpoints lose the completed ledger margin')
                else:
                    counts['early_unresolved_witnesses'] += 1
                if cheap['decision'] in api.CERTIFICATES and exact['decision'] != cheap['decision']:
                    raise AssertionError('exact inference loses a sound envelope certificate')
                if exact['decision'] in api.CERTIFICATES:
                    if exact['decision'] != case['complete_decision']:
                        raise AssertionError('exact inference disagrees with the actual complete comparison')
                    if first is None:
                        first = {'queries': step, 'all_earlier_prefixes_resolved': all_previous_exact_or_undefined,
                                 'certificate': exact}
            prefixes.append(dict(step=step, envelope_decision=cheap['decision'], **exact))
            if step < len(case['query_order']):
                group = case['query_order'][step]
                state.reveal(group, labels[group])
        if first is None:
            raise AssertionError('the complete existing certificate should be reached')
        results[name] = {'case': case['case'], 'initialization': case['initialization'],
                         'envelope_queries': case['paired_first']['queries'], 'exact_first': first,
                         'common_queries': case['legacy_first']['queries'], 'prefixes': prefixes}
        print(name, 'envelope', case['paired_first']['queries'], 'exact', first['queries'],
              'all-earlier-decided', first['all_earlier_prefixes_resolved'], flush=True)
    report = {'status': 'complete', 'assignment_budget_per_prefix': args.assignment_budget,
              'design': 'Same actual paired observations and public query sequence. Exact comparison groups unresolved differing obligations by the full coefficient quadruple; any valid-label count in each class is allowed. Early attainable sign witnesses can prove unresolvedness without completing the endpoint search.',
              'counts': counts,
              'cases_earlier_than_envelope': sum(r['exact_first']['queries'] < r['envelope_queries'] for r in results.values()),
              'cases_same_as_envelope': sum(r['exact_first']['queries'] == r['envelope_queries'] for r in results.values()),
              'cases_with_global_first_certificate_established': sum(r['exact_first']['all_earlier_prefixes_resolved'] for r in results.values()),
              'timing': {name: {'calls': len(values), 'total_cpu_seconds': sum(values) / 1e9,
                                'median_cpu_microseconds': statistics.median(values) / 1e3,
                                'min_cpu_microseconds': min(values) / 1e3, 'max_cpu_microseconds': max(values) / 1e3}
                         for name, values in timing.items()},
              'results': results}
    (args.out / 'study.json').write_text(json.dumps(report, indent=2) + '\n')
    with (args.out / 'summary.csv').open('w', newline='') as stream:
        w = csv.writer(stream)
        w.writerow(['case', 'initialization', 'envelope_queries', 'exact_queries', 'all_previous_prefixes_decided', 'common_queries'])
        for r in results.values():
            w.writerow([r['case'], r['initialization'], r['envelope_queries'], r['exact_first']['queries'],
                        r['exact_first']['all_earlier_prefixes_resolved'], r['common_queries']])
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}, indent=2))


if __name__ == '__main__':
    main()
