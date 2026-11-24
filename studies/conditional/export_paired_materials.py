#!/usr/bin/env python3
"""Export paper data from received native traces and the complete paired study."""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study', type=Path, required=True)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--receiving', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    study = json.loads(args.study.read_text())
    native = json.loads((args.native / 'receipt.json').read_text())
    protocol = json.loads((args.native / 'protocol.json').read_text())
    receiving = json.loads(args.receiving.read_text())
    if receiving['status'] != 'pass' or receiving['runs_received'] != len(native['runs']):
        raise ValueError('native traces must have an independent receiving record')
    source_description = ('Received execution-validation block; durations are excluded from runtime comparisons.'
                          if protocol['design'] == 'execution_validation' else
                          'First received repetition of each paired comparison in the balanced native block.')
    plot = {'description': 'Exact endpoints at every fresh native paired-conditional prefix. ' + source_description,
            'rate_units': 'fractions', 'envelope_units': 'count units N*F; not conditional-rate differences',
            'cases': {}}
    entry_counts = []
    for row in native['runs']:
        if row['method'] != 'paired':
            continue
        scope = row['scope']
        if scope in plot['cases']:
            continue
        case = f"{scope}__{row['left']}__{row['right']}"
        expected = study['results']['reference_identity_known/' + case]
        if row['candidate_suite_queries'] != expected['paired_first']['queries']:
            raise ValueError('native and retained-ledger stopping counts differ')
        if row['final_certificate'] != expected['paired_first']['certificate']:
            raise ValueError('native and retained-ledger first certificates differ')
        run = json.loads((args.native / row['directory'] / 'receipt.json').read_text())
        entries = 0
        for query in run['queries']:
            observation = json.loads((args.native / query['evidence_file']).read_text())
            if scope == 'humaneval':
                entries += len(json.loads(observation['stdout'])['observations'])
            else:
                events = [json.loads(line) for line in observation['stdout'].splitlines() if line.strip()]
                entries += sum(event.get('event') == 'test_result' and event.get('assertion_reached') is True
                               for event in events)
        entry_counts.append({'scope': scope, 'method': 'paired', 'target': 'C',
                             'suites': row['candidate_suite_queries'], 'entries': entries,
                             'entry_unit': 'function entries' if scope == 'humaneval' else 'assertion entries',
                             'native_run': row['directory']})
        values = []
        for prefix in json.loads((args.native / row['directory'] / 'trace.json').read_text()):
            b = prefix['bounds']
            ranges = {side: [str(min(Fraction(e['q']) for e in b['anchors'][side]['endpoints'])),
                             str(max(Fraction(e['q']) for e in b['anchors'][side]['endpoints']))]
                      for side in ('left', 'right')}
            independent = [str(Fraction(ranges['left'][0]) - Fraction(ranges['right'][1])),
                           str(Fraction(ranges['left'][1]) - Fraction(ranges['right'][0]))]
            values.append({'suites': prefix['step'], 'decision': b['decision'],
                           'left_conditional': ranges['left'], 'right_conditional': ranges['right'],
                           'independent_gap': independent,
                           'left_anchor_count_envelope': [b['anchors']['left']['lower'], b['anchors']['left']['upper']],
                           'right_anchor_count_envelope': [b['anchors']['right']['lower'], b['anchors']['right']['upper']],
                           'unresolved_differences': b['anchors']['left']['different_unknown_groups']})
        plot['cases'][scope] = {'left': row['left'], 'right': row['right'], 'denominator': row['denominator'],
                                'native_first_suites': row['candidate_suite_queries'],
                                'common_remainder_suites': expected['legacy_first']['queries'],
                                'independent_suites': next(r['candidate_suite_queries'] for r in native['runs']
                                                           if r['scope'] == scope and r['method'] == 'independent'),
                                'prefixes': values}
    (args.out / 'paired-conditional-figure-data.json').write_text(json.dumps(plot, indent=2) + '\n')
    rows = list(study['results'].values())
    names = {'humaneval': 'HumanEval', 'mbpp': 'MBPP', 'pooled': 'Pooled',
             'stock': 'stock', 's1': 'S1', 's4': 'S4', 's1_s4': 'both'}
    lines = [r'\begin{table}[t]', r'\centering',
             r'\caption{Conditional suite queries under the same public order.}',
             r'\label{tab:paired-all-comparisons}', r'\small',
             r'\begin{tabular}{@{}llrrrr@{}}', r'\toprule',
             r' & & \multicolumn{2}{c}{Reference identity known} & \multicolumn{2}{c}{All withheld} \\',
             r'Corpus & Pair & Paired & Common & Paired & Common \\', r'\midrule']
    for case in dict.fromkeys(r['case'] for r in rows):
        known = study['results']['reference_identity_known/' + case]
        withheld = study['results']['all_withheld/' + case]
        scope, left, right = case.split('__')
        lines.append(f"{names[scope]} & {names[left]} / {names[right]} & "
                     f"{known['paired_first']['queries']} & {known['legacy_first']['queries']} & "
                     f"{withheld['paired_first']['queries']} & {withheld['legacy_first']['queries']} \\\\")
    lines += [r'\bottomrule', r'\end{tabular}',
              r'\par\smallskip\begin{minipage}{\linewidth}\footnotesize Paired: the ratio-envelope certificate with the separate-interval fallback. Common: the common-remainder certificate enabled after coefficient differences are resolved, with the same separate-interval fallback. Both receive the same public query sequence.\end{minipage}',
              r'\end{table}']
    (args.out / 'paired-comparison-table.tex').write_text('\n'.join(lines) + '\n')
    macros = {'HECPaired': plot['cases']['humaneval']['native_first_suites'],
              'MBCPaired': plot['cases']['mbpp']['native_first_suites'],
              'PairedCasesImproved': study['cases_with_fewer_queries'],
              'PairedCasesTotal': study['case_count']}
    balanced = protocol['design'] == 'balanced_native_timing'
    if balanced:
        for row in native['summaries']:
            prefix = ('HEC' if row['scope'] == 'humaneval' else 'MBC') + ('Paired' if row['method'] == 'paired' else 'Separate')
            for field, suffix in [('median_seconds', 'MedianSeconds'), ('minimum_seconds', 'MinimumSeconds'),
                                  ('maximum_seconds', 'MaximumSeconds')]:
                macros[prefix + suffix] = format(row[field], '.3f')
    for row in entry_counts:
        macros[('HEC' if row['scope'] == 'humaneval' else 'MBC') + 'PairedEntries'] = row['entries']
    (args.out / 'paired-macros.tex').write_text(''.join('\\newcommand{\\' + key + '}{' + str(value) + '}\n'
                                                    for key, value in macros.items()))
    timing = {'design': protocol['design'], 'performance_comparison_permitted': balanced,
              'timing_scope': protocol['timing_scope'],
              'common_preparation_seconds': native['common_preparation_seconds'],
              'summaries': native['summaries'] if balanced else [],
              'entry_counts_first_paired_repetition': entry_counts,
              'receiving': {key: receiving[key] for key in ('status', 'runs_received',
                            'candidate_suite_records_received', 'prefixes_received', 'historical_candidate_observations_read')},
              'runs': [{key: row[key] for key in ('scope', 'method', 'repeat', 'directory', 'candidate_suite_queries',
                       'audit_total_seconds', 'phase_seconds', 'unallocated_loop_seconds')} for row in native['runs']] if balanced else []}
    (args.out / 'paired-native-summary.json').write_text(json.dumps(timing, indent=2) + '\n')
    print(json.dumps({'status': 'complete', 'native_prefixes_exported': sum(len(v['prefixes']) for v in plot['cases'].values()),
                      'table_case_rows': len(rows) // 2, 'files': 4}))


if __name__ == '__main__':
    main()
