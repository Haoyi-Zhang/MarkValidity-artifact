#!/usr/bin/env python3
"""Export current joint/conditional timing tables from received native blocks."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics


PHASES = ('register_seconds', 'select_seconds', 'bounds_seconds',
          'worker_seconds', 'receive_seconds', 'record_seconds')
SCOPE_NAMES = {'humaneval': 'HumanEval: stock / S1', 'mbpp': 'MBPP: stock / S4'}
METHODS = {'coupled': 'shared', 'paired': 'shared', 'independent': 'separate'}


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summary(values):
    return {'median': statistics.median(values), 'minimum': min(values),
            'maximum': max(values), 'values_in_repeat_order': values}


def count(value):
    return format(value, ',').replace(',', r'\,')


def source_run(row, origin, path, repeat, position):
    require(all(math.isfinite(row['phase_seconds'][key]) and row['phase_seconds'][key] >= 0
                for key in PHASES), 'invalid phase duration')
    require(math.isfinite(row['audit_total_seconds']) and
            row['audit_total_seconds'] >= sum(row['phase_seconds'].values()), 'invalid total duration')
    return {'scope': row['scope'], 'target': row['target'], 'method': METHODS[row['method']],
            'repeat': repeat, 'position': position, 'origin': origin, 'native_record': path,
            'candidate_suite_queries': row['candidate_suite_queries'],
            'audit_total_seconds': row['audit_total_seconds'],
            'phase_seconds': row['phase_seconds'],
            'unallocated_loop_seconds': row['unallocated_loop_seconds']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--joint-summary', type=Path, required=True)
    parser.add_argument('--conditional-native', type=Path, required=True)
    parser.add_argument('--conditional-receiving', type=Path, required=True)
    parser.add_argument('--validation-native', type=Path, required=True)
    parser.add_argument('--validation-receiving', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    retained = read(args.joint_summary)
    fresh = read(args.conditional_native / 'receipt.json')
    fresh_protocol = read(args.conditional_native / 'protocol.json')
    fresh_received = read(args.conditional_receiving)
    validation = read(args.validation_native / 'receipt.json')
    validation_protocol = read(args.validation_native / 'protocol.json')
    validation_received = read(args.validation_receiving)
    require(retained['status'] == 'COMPLETE' and retained['receiving']['status'] == 'PASS',
            'retained joint data were not completely received')
    require(retained['native_timing']['counterbalance']['status'] == 'PASS', 'retained order is unbalanced')
    require(fresh['status'] == 'complete' and fresh_protocol['design'] == 'balanced_native_timing'
            and fresh_received['status'] == 'pass' and fresh_received['runs_received'] == 24,
            'conditional timing requires the received balanced block')
    require(validation['status'] == 'complete' and validation_protocol['design'] == 'execution_validation'
            and validation_received['status'] == 'pass' and validation_received['runs_received'] == 4,
            'execution validation requires its separate receiving record')
    runs = []
    joint_rows = [row for row in retained['native_timing']['rows'] if row['target'] == 'J']
    require(len(joint_rows) == 4, 'expected four joint case/method summaries')
    for row in joint_rows:
        require(len(row['run_directories']) == row['repeats'] == 6, 'incomplete joint repetitions')
        exact_runs = []
        for index, (directory, position) in enumerate(zip(row['run_directories'], row['measurement_order']), 1):
            require(position['run_path'] == directory, 'joint order/source binding differs')
            record = read(args.joint_summary.parent / directory / 'receipt.json')
            require(record['target'] == 'J' and record['scope'] == row['scope']
                    and record['method'] == row['method'], 'joint source row differs')
            exact_runs.append(record)
            runs.append(source_run(record, 'retained_joint_blocks', directory + '/receipt.json',
                                   index, position['within_case_position']))
        require(summary([x['audit_total_seconds'] for x in exact_runs]) == row['additional_audit_seconds'],
                'retained joint summary does not reproduce from native records')
        require(all(summary([x['phase_seconds'][key] for x in exact_runs]) == row['phase_seconds'][key]
                    for key in PHASES), 'retained phase summary does not reproduce')
        require({x['candidate_suite_queries'] for x in exact_runs} == {row['candidate_suite_queries']},
                'joint query counts vary or summary differs')
    for index, row in enumerate(fresh['runs']):
        require(row['target'] == 'C', 'conditional source includes another target')
        record = read(args.conditional_native / row['directory'] / 'receipt.json')
        require({key: value for key, value in record.items() if key != 'queries'} == row,
                'conditional per-run and aggregate records differ')
        runs.append(source_run(record, 'current_conditional_block', row['directory'] + '/receipt.json',
                               row['repeat'], 'first' if index % 2 == 0 else 'second'))
    require(len(runs) == 48, 'current target/method matrix must have 48 runs')
    order = Counter((r['scope'], r['target'], r['method'], r['position']) for r in runs)
    require(len(order) == 16 and set(order.values()) == {3}, 'current method positions are unbalanced')
    rows = []
    for scope in SCOPE_NAMES:
        for target in ('J', 'C'):
            for method in ('shared', 'separate'):
                selected = [r for r in runs if (r['scope'], r['target'], r['method']) == (scope, target, method)]
                require(len(selected) == 6 and len({r['candidate_suite_queries'] for r in selected}) == 1,
                        'six consistent repetitions required')
                selected.sort(key=lambda r: r['repeat'])
                rows.append({'scope': scope, 'target': target, 'method': method, 'repetitions': 6,
                             'candidate_suite_queries': selected[0]['candidate_suite_queries'],
                             'audit_seconds': summary([r['audit_total_seconds'] for r in selected]),
                             'phases': {key: summary([r['phase_seconds'][key] for r in selected]) for key in PHASES},
                             'origin': selected[0]['origin']})
    validation_rows = []
    for row in validation['runs']:
        record = read(args.validation_native / row['directory'] / 'receipt.json')
        require({key: value for key, value in record.items() if key != 'queries'} == row,
                'validation per-run and aggregate records differ')
        entries = 0
        for query in record['queries']:
            observation = read(args.validation_native / query['evidence_file'])
            if row['scope'] == 'humaneval':
                entries += len(json.loads(observation['stdout'])['observations'])
            else:
                events = [json.loads(line) for line in observation['stdout'].splitlines() if line.strip()]
                entries += sum(event.get('event') == 'test_result' and event.get('assertion_reached') is True
                               for event in events)
        matching = next(x for x in rows if (x['scope'], x['target'], x['method']) ==
                        (row['scope'], 'C', METHODS[row['method']]))
        require(row['candidate_suite_queries'] == matching['candidate_suite_queries'],
                'validation and timing query counts disagree')
        validation_rows.append({'scope': row['scope'], 'method': METHODS[row['method']],
                                'suites': row['candidate_suite_queries'], 'entries': entries,
                                'entry_unit': 'function entries' if row['scope'] == 'humaneval' else 'assertion entries',
                                'certificate': row['decision'], 'native_directory': row['directory']})
    total_suites = sum(r['candidate_suite_queries'] for r in runs)
    report = {'status': 'complete', 'runs': len(runs), 'candidate_suite_executions': total_suites,
              'repetitions_per_case_method': 6,
              'design': 'Joint timings use retained complementary matched blocks. Conditional timings use a separate fresh balanced serial block. Each case/target/method has six observations, three in each within-pair position. These are separate collections, not one execution batch.',
              'timing_scope': fresh_protocol['timing_scope'],
              'joint_runs': sum(r['target'] == 'J' for r in runs),
              'conditional_runs': sum(r['target'] == 'C' for r in runs),
              'joint_suites': sum(r['candidate_suite_queries'] for r in runs if r['target'] == 'J'),
              'conditional_suites': sum(r['candidate_suite_queries'] for r in runs if r['target'] == 'C'),
              'common_registration': {'joint_blocks': retained['native_timing']['common_preparations'],
                                      'conditional_block_seconds': fresh['common_preparation_seconds']},
              'excluded_from_current_timing': 'All common-remainder conditional observations in the retained joint source; all four execution-validation durations.',
              'rows': rows, 'raw_run_summaries': runs,
              'execution_validation': {'runs': len(validation_rows), 'suites': sum(r['suites'] for r in validation_rows),
                                        'prefixes': validation_received['prefixes_received'], 'rows': validation_rows}}
    (args.out / 'current-runtime.json').write_text(json.dumps(report, indent=2) + '\n')
    runtime = [r'\begin{table}[t]', r'\caption{Measured audit time through first certification.}',
               r'\label{tab:natural-runtime}', r'\centering\small', r'\begin{tabular}{@{}llrrrr@{}}',
               r'\toprule', r'Target & Method & Suites & Select (ms) & Worker (s) & Audit (s): median [range]\\', r'\midrule']
    phases = [r'\begin{table}[htbp]', r'\caption{Nonworker audit phases: median milliseconds over six executions.}',
              r'\label{tab:natural-runtime-phases}', r'\centering\small', r'\begin{tabular}{@{}llrrrrr@{}}',
              r'\toprule', r'Target & Method & Register & Select & Bounds & Receive & Record\\', r'\midrule']
    for scope in SCOPE_NAMES:
        if scope != 'humaneval':
            runtime.append(r'\addlinespace'); phases.append(r'\addlinespace')
        runtime.append(r'\multicolumn{6}{@{}l}{\textit{' + SCOPE_NAMES[scope] + r'}}\\')
        phases.append(r'\multicolumn{7}{@{}l}{\textit{' + SCOPE_NAMES[scope] + r'}}\\')
        for row in [x for x in rows if x['scope'] == scope]:
            values = [f"${row['target']}$", row['method'].capitalize(), count(row['candidate_suite_queries']),
                      f"{1000*row['phases']['select_seconds']['median']:.3f}",
                      f"{row['phases']['worker_seconds']['median']:.3f}",
                      f"{row['audit_seconds']['median']:.3f} [{row['audit_seconds']['minimum']:.3f}, {row['audit_seconds']['maximum']:.3f}]"]
            runtime.append(' & '.join(values) + r'\\')
            values = [f"${row['target']}$", row['method'].capitalize()] + [
                f"{1000*row['phases'][key]['median']:.3f}" for key in PHASES if key != 'worker_seconds']
            phases.append(' & '.join(values) + r'\\')
    ending = [r'\bottomrule\end{tabular}',
              r'\par\smallskip\begin{minipage}{\linewidth}\footnotesize $J$ uses retained matched blocks; $C$ uses a separate balanced serial block. Each method occupies the first and second position three times per comparison.\end{minipage}',
              r'\end{table}']
    (args.out / 'current-runtime.tex').write_text('\n'.join(runtime + ending) + '\n')
    (args.out / 'current-runtime-phases.tex').write_text('\n'.join(phases + ending) + '\n')
    validation_tex = [r'\begin{table}[htbp]', r'\caption{Fresh conditional execution validation.}',
                      r'\label{tab:current-native-validation}', r'\centering\small',
                      r'\begin{tabular}{@{}llrrl@{}}', r'\toprule',
                      r'Comparison & Method & Suites & Entries & Entry unit\\\midrule']
    for row in validation_rows:
        validation_tex.append(' & '.join([SCOPE_NAMES[row['scope']], row['method'].capitalize(),
                              count(row['suites']), count(row['entries']), row['entry_unit']]) + r'\\')
    validation_tex.extend([r'\bottomrule\end{tabular}',
                           r'\par\smallskip\begin{minipage}{\linewidth}\footnotesize The four runs validate native records and first certificates. Their durations are excluded from the timing comparison.\end{minipage}',
                           r'\end{table}'])
    (args.out / 'current-native-validation.tex').write_text('\n'.join(validation_tex) + '\n')
    macros = {'CurrentTimingRuns': len(runs), 'CurrentTimingRepeats': 6,
              'CurrentTimingSuites': count(total_suites), 'CurrentJointTimingRuns': report['joint_runs'],
              'CurrentConditionalTimingRuns': report['conditional_runs'],
              'CurrentJointTimingSuites': count(report['joint_suites']),
              'CurrentConditionalTimingSuites': count(report['conditional_suites']),
              'CurrentConditionalSetupSeconds': f"{fresh['common_preparation_seconds']:.3f}",
              'CurrentValidationRuns': len(validation_rows),
              'CurrentValidationSuites': count(report['execution_validation']['suites']),
              'CurrentValidationPrefixes': count(report['execution_validation']['prefixes'])}
    for row in rows:
        prefix = 'Current' + ('HE' if row['scope'] == 'humaneval' else 'MB') + row['target'] + row['method'].capitalize()
        macros[prefix + 'Suites'] = count(row['candidate_suite_queries'])
        macros[prefix + 'Seconds'] = f"{row['audit_seconds']['median']:.3f}"
    (args.out / 'current-runtime-macros.tex').write_text(''.join('\\newcommand{\\' + key + '}{' + str(value) + '}\n'
                                                             for key, value in macros.items()))
    print(json.dumps({key: report[key] for key in ('status', 'runs', 'candidate_suite_executions', 'joint_suites', 'conditional_suites')}, indent=2))


if __name__ == '__main__':
    main()
