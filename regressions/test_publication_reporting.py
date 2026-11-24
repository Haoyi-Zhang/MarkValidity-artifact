"""Receive the current article's tables, plotted data and native timing records.

This module reads the original records directly. It does not import a producer,
watermark implementation, inference implementation or publication generator.
"""
from collections import Counter
from fractions import Fraction
import itertools
import json
import math
import re
import statistics
import unittest

from test_natural_reporting import (
    ROOT, NATURAL, current_reporting_text, digest, expanded_current_main,
    json_file, mbpp_observed_label, observed_rows, source_contract,
)

PAPER = ROOT.parent / 'paper'
CONDITIONAL = ROOT / 'studies/conditional'
COMPARISONS = ROOT / 'results/revision-sew-comparison-costs'
CREST = ROOT / 'studies/crest/accepted'
PHASES = ('register_seconds', 'select_seconds', 'bounds_seconds',
          'worker_seconds', 'receive_seconds', 'record_seconds')
VERSION_NAMES = {'stock': 'Stock', 's1': 'S1', 's4': 'S4', 's1_s4': 'S1+S4'}
CORPUS_NAMES = {'humaneval': 'HumanEval', 'mbpp': 'Sanitized MBPP', 'pooled': 'Pooled'}


def count(value):
    return format(value, ',').replace(',', r'\,')


def cells(line):
    return [cell.rstrip().removesuffix(chr(92) * 2).strip() for cell in line.split('&')]


def macros(name):
    text = current_reporting_text('figdata/' + name)
    pairs = re.findall(r'\\newcommand\{\\([A-Za-z]+)\}\{([^{}]*)\}', text)
    if len(pairs) != len(dict(pairs)):
        raise ValueError('Duplicate current macro')
    return dict(pairs)


def summary(values):
    return {'median': statistics.median(values), 'minimum': min(values),
            'maximum': max(values), 'values_in_repeat_order': values}


def label(record):
    """Read the actual worker result without relying on the row's validity field."""
    if record.get('evidence_rejected') or record.get('interruption') or record.get('returncode') != 0:
        actual = None
    else:
        try:
            worker = json.loads(record['stdout'])
        except json.JSONDecodeError:
            events = [json.loads(line) for line in record['stdout'].splitlines() if line.strip()]
            value = mbpp_observed_label({'events': events, 'returncode': record['returncode']},
                                        len(record['execution_request']['test_list']))
            actual = None if value is None else bool(value)
        else:
            actual = {'passed': True, 'failed': False, 'unknown': None,
                      'unavailable': None}[worker['status']]
            if actual is True and (worker.get('error') is not None or worker.get('check_finished', True) is not True):
                raise ValueError('Incomplete or contradictory suite success')
    if actual is not record['label']:
        raise ValueError('Declared native label differs from the worker receipt')
    return actual


def emission(row):
    if row.get('emission'):
        return row['emission']
    if row.get('candidate_source') and row['embedding']['status'] == 'completed':
        return 'emitted'
    if row['embedding']['status'] == 'error' and not row.get('candidate_source'):
        return 'rejected'
    return 'unknown'


def crest_counts(rows, model):
    transition = {before: {after: 0 for after in ('passed', 'failed', 'not_emitted', 'unavailable')}
                  for before in ('passed', 'failed', 'unavailable')}
    actual = Counter()
    observed = []
    for row in rows:
        e = emission(row)
        before = label(row['reference_native'])
        after = label(row['candidate_native']) if e == 'emitted' else None
        detected = row.get('candidate_detector', {}).get('classifiers', {}).get(model, {}).get('detected')
        actual['attempts'] += 1
        actual['input_passed' if before is True else 'input_failed' if before is False else 'input_unknown'] += 1
        actual['emitted' if e == 'emitted' else 'rejected' if e == 'rejected' else 'emission_unknown'] += 1
        before_name = 'passed' if before is True else 'failed' if before is False else 'unavailable'
        after_name = ('not_emitted' if e == 'rejected' else 'passed' if after is True
                      else 'failed' if after is False else 'unavailable')
        transition[before_name][after_name] += 1
        # A completed no-output event is a known zero, not an unknown program.
        usable = False if e == 'rejected' else after
        joint = False if e == 'rejected' or after is False or detected is False else (
            True if e == 'emitted' and after is True and detected is True else None)
        actual['passed'] += usable is True
        actual['failed_emitted'] += e == 'emitted' and after is False
        actual['output_unknown'] += usable is None
        actual['detected'] += e == 'emitted' and detected is True
        actual['joint'] += joint is True
        actual['joint_unknown'] += joint is None
        actual['detected_failed'] += e == 'emitted' and detected is True and after is False
        observed.append((before, after, e, detected))
    return actual, transition, observed


class CurrentPublicationTests(unittest.TestCase):
    def test_current_figure_sources_and_rendered_coordinates_are_bound(self):
        binding = json.loads(current_reporting_text('figdata/publication-bindings.json'))
        self.assertTrue(binding['inputs'] and binding['generators'] and binding['outputs'])
        for section in ('inputs', 'generators'):
            for name, expected in binding[section].items():
                self.assertEqual(digest((ROOT.parent / name).read_bytes()), expected, name)
        for name, expected in binding['outputs'].items():
            self.assertEqual(digest((PAPER / name).read_bytes()), expected, name)
        self.assertIn('artifact/studies/conditional/native-timing/receipt.json', binding['inputs'])
        for study in ('reference', 'catalogue', 'gpt4o', 'qwen'):
            self.assertIn('artifact/studies/crest/accepted/' + study + '/reporting-summary.json', binding['inputs'])

        # The SEW ledger remains joined to exact original native contracts.
        manifest = json_file(NATURAL / 'analysis-primary/manifest.json')
        rows = observed_rows()
        self.assertEqual(manifest['total_rows'], len(rows))
        self.assertEqual(manifest['total_source_contract_groups'], len({source_contract(r) for r in rows}))
        for entry in manifest['inputs']:
            self.assertEqual(digest((ROOT / entry['rows_path']).read_bytes()), entry['rows_sha256'])
            self.assertEqual(len(json_file(ROOT / entry['rows_path'])), entry['rows'])

        data = json.loads(current_reporting_text('figdata/paired-conditional-figure-data.json'))
        self.assertEqual(data, json_file(CONDITIONAL / 'paper-materials/paired-conditional-figure-data.json'))
        plot = json.loads(current_reporting_text('figures/natural-conditional.json'))
        self.assertEqual(plot['units'], data['envelope_units'])
        self.assertEqual(plot['source'], 'paired-conditional-figure-data.json')
        self.assertEqual({p['case'] for p in plot['depicted_cases']}, {'humaneval', 'mbpp'})
        for shown in plot['depicted_cases']:
            case = data['cases'][shown['case']]
            first = next(p for p in case['prefixes'] if p['decision'] != 'unresolved')
            self.assertEqual(shown['native_prefix'], first)
            self.assertEqual(shown['suites'], case['native_first_suites'])
            self.assertEqual(shown['unresolved_differences'], first['unresolved_differences'])
            self.assertEqual(shown['full_envelope'], first['left_anchor_count_envelope'])
            endpoint = 0 if first['decision'] == 'left_strict' else 1
            self.assertEqual(shown['displayed_extremum'], shown['full_envelope'][endpoint])
            gap = list(map(Fraction, first['independent_gap']))
            self.assertLessEqual(gap[0], 0)
            self.assertGreaterEqual(gap[1], 0)

        joint = json.loads(current_reporting_text('figures/natural-joint-budget.json'))
        for name, expected in joint['input_sha256'].items():
            self.assertEqual(digest((ROOT / name).read_bytes()), expected)
        self.assertEqual([next(iter(item.values())) for item in joint['first_certificates']],
                         [[146, 429, 541], [1, 811, 1136]])

    def test_current_comparison_tables_use_paired_certificates_and_own_orders(self):
        comparisons = json_file(NATURAL / 'analysis-primary/comparisons.json')
        baseline = json_file(COMPARISONS / 'retrospective-primary/analysis.json')['reports']
        withheld = json_file(COMPARISONS / 'retrospective-all-withheld/analysis.json')['reports']
        paired = json_file(CONDITIONAL / 'paired-study/study.json')
        self.assertEqual(paired['case_count'], 36)
        shown = json.loads(current_reporting_text('figdata/paired-costs.json'))
        self.assertEqual(len(shown), 18)
        self.assertEqual({r['case'] for r in shown}, set(comparisons))
        tables = {False: current_reporting_text('figdata/paired-costs.tex'),
                  True: current_reporting_text('figdata/natural-pooled.tex')}
        self.assertIn(tables[False], expanded_current_main())
        sensitivity = current_reporting_text('figdata/natural-baseline-sensitivity.tex')
        for row in shown:
            case = row['case']; c = comparisons[case]; b = baseline[case]['runs']
            p = paired['results']['reference_identity_known/' + case]
            first = p['paired_first']
            self.assertEqual(first['certificate']['decision'], p['complete_decision'])
            self.assertEqual(p['denominator'], c['denominator'])
            expected = {'case': case, 'rows': c['full_row_suites_after_reference'],
                        'unique': c['full_unique_group_suites_after_reference'],
                        'joint_separate': b['independent_J']['first_certificate']['suite_queries'],
                        'joint_shared': b['coupled_J']['first_certificate']['suite_queries'],
                        'conditional_separate': b['independent_C']['first_certificate']['suite_queries'],
                        'conditional_shared': first['queries']}
            self.assertEqual(row, expected)
            title = VERSION_NAMES[c['left']] + ' / ' + VERSION_NAMES[c['right']]
            values = [title, count(row['rows']), count(row['unique']), count(c['J_gap_influential_groups']),
                      count(c['C_coefficient_different_groups']),
                      count(row['joint_separate']) + ' / ' + count(row['joint_shared']),
                      count(row['conditional_separate']) + ' / ' + count(row['conditional_shared'])]
            self.assertEqual(tables[c['scope'] == 'pooled'].count(' & '.join(values) + r'\\'), 1)
            w = withheld[case]['runs']; p = paired['results']['all_withheld/' + case]
            values = [CORPUS_NAMES[c['scope']], title]
            for target, policy in [('J', 'joint_width_per_suite'), ('C', 'conditional_differences_first')]:
                values.append(count(c['schedules'][policy]['first_certificates']['independent_' + target]['suite_queries']))
            values += [count(w['independent_J']['first_certificate']['suite_queries']) + ' / ' +
                       count(w['coupled_J']['first_certificate']['suite_queries']),
                       count(w['independent_C']['first_certificate']['suite_queries']) + ' / ' + count(p['paired_first']['queries'])]
            self.assertEqual(sensitivity.count(' & '.join(values) + r'\\'), 1)
        values = {r['case']: r['conditional_shared'] for r in shown}
        self.assertEqual(values['humaneval__stock__s1'], 154)
        self.assertEqual(values['mbpp__stock__s4'], 1)

    def test_current_runtime_is_reconstructed_from_all_balanced_native_runs(self):
        report = json.loads(current_reporting_text('figdata/current-runtime.json'))
        runs = report['raw_run_summaries']
        self.assertEqual((report['runs'], len(runs)), (48, 48))
        self.assertEqual(sum(r['candidate_suite_queries'] for r in runs), 19260)
        self.assertEqual(report['candidate_suite_executions'], 19260)
        self.assertEqual(Counter((r['scope'], r['target'], r['method'], r['position']) for r in runs),
                         Counter({key: 3 for key in itertools.product(('humaneval', 'mbpp'), ('J', 'C'),
                                                                     ('shared', 'separate'), ('first', 'second'))}))
        self.assertEqual((report['joint_runs'], report['conditional_runs'], report['joint_suites'], report['conditional_suites']),
                         (24, 24, 8322, 10938))
        allowed_sources = set()
        old = json_file(COMPARISONS / 'summary.json')
        self.assertEqual(old['receiving']['status'], 'PASS')
        self.assertEqual(old['native_timing']['counterbalance']['status'], 'PASS')
        for row in old['native_timing']['rows']:
            if row['target'] == 'J':
                allowed_sources.update(('retained_joint_blocks', p + '/receipt.json') for p in row['run_directories'])
        current = json_file(CONDITIONAL / 'native-timing/receipt.json')
        for row in current['runs']:
            allowed_sources.add(('current_conditional_block', row['directory'] + '/receipt.json'))
        self.assertEqual({(r['origin'], r['native_record']) for r in runs}, allowed_sources)
        for run in runs:
            origin = COMPARISONS if run['target'] == 'J' else CONDITIONAL / 'native-timing'
            native = json_file(origin / run['native_record'])
            self.assertEqual(native['target'], run['target'])
            self.assertEqual(native['scope'], run['scope'])
            self.assertEqual({'coupled': 'shared', 'paired': 'shared', 'independent': 'separate'}[native['method']], run['method'])
            for key in ('candidate_suite_queries', 'audit_total_seconds', 'phase_seconds', 'unallocated_loop_seconds'):
                self.assertEqual(native[key], run[key])
            self.assertTrue(all(math.isfinite(x) and x >= 0 for x in native['phase_seconds'].values()))
            self.assertGreaterEqual(native['audit_total_seconds'], sum(native['phase_seconds'].values()))
        receiving = json_file(CONDITIONAL / 'native-timing-receiving.json')
        self.assertEqual((receiving['status'], receiving['runs_received'], receiving['candidate_suite_records_received'], receiving['prefixes_received']),
                         ('pass', 24, 10938, 10962))
        table = current_reporting_text('figdata/current-runtime.tex')
        phase_table = current_reporting_text('figdata/current-runtime-phases.tex')
        self.assertIn(table, expanded_current_main())
        shown = [cells(line) for line in table.splitlines() if cells(line)[0] in ('$J$', '$C$')]
        shown_phases = [cells(line) for line in phase_table.splitlines() if cells(line)[0] in ('$J$', '$C$')]
        self.assertEqual((len(report['rows']), len(shown), len(shown_phases)), (8, 8, 8))
        runtime_macros = macros('current-runtime-macros.tex')
        for row, displayed, phase_displayed in zip(report['rows'], shown, shown_phases):
            selected = sorted((r for r in runs if (r['scope'], r['target'], r['method']) ==
                               (row['scope'], row['target'], row['method'])), key=lambda r: r['repeat'])
            self.assertEqual([r['repeat'] for r in selected], list(range(1, 7)))
            self.assertEqual(row['repetitions'], 6)
            self.assertEqual(row['audit_seconds'], summary([r['audit_total_seconds'] for r in selected]))
            self.assertEqual(row['phases'], {key: summary([r['phase_seconds'][key] for r in selected]) for key in PHASES})
            self.assertEqual({r['candidate_suite_queries'] for r in selected}, {row['candidate_suite_queries']})
            t = row['audit_seconds']; phases = row['phases']
            self.assertEqual(displayed, [f"${row['target']}$", row['method'].capitalize(), count(row['candidate_suite_queries']),
                                        f"{1000*phases['select_seconds']['median']:.3f}", f"{phases['worker_seconds']['median']:.3f}",
                                        f"{t['median']:.3f} [{t['minimum']:.3f}, {t['maximum']:.3f}]"])
            self.assertEqual(phase_displayed, displayed[:2] + [f"{1000*phases[key]['median']:.3f}" for key in PHASES if key != 'worker_seconds'])
            prefix = 'Current' + ('HE' if row['scope'] == 'humaneval' else 'MB') + row['target'] + row['method'].capitalize()
            self.assertEqual(runtime_macros[prefix + 'Suites'], count(row['candidate_suite_queries']))
            self.assertEqual(runtime_macros[prefix + 'Seconds'], f"{t['median']:.3f}")

        validation = report['execution_validation']; validation_table = current_reporting_text('figdata/current-native-validation.tex')
        self.assertEqual((validation['runs'], validation['suites'], validation['prefixes']), (4, 1823, 1827))
        for row in validation['rows']:
            native = json_file(CONDITIONAL / 'native-validation' / row['native_directory'] / 'receipt.json')
            self.assertEqual(len(native['queries']), row['suites'])
            entries = 0
            for query in native['queries']:
                receipt = json_file(CONDITIONAL / 'native-validation' / query['evidence_file'])
                if row['scope'] == 'humaneval':
                    entries += len(json.loads(receipt['stdout'])['observations'])
                else:
                    entries += sum(e.get('event') == 'test_result' and e.get('assertion_reached') is True
                                   for e in map(json.loads, filter(str.strip, receipt['stdout'].splitlines())))
            self.assertEqual(row['entries'], entries)
            title = 'HumanEval: stock / S1' if row['scope'] == 'humaneval' else 'MBPP: stock / S4'
            self.assertIn(' & '.join([title, row['method'].capitalize(), count(row['suites']), count(entries), row['entry_unit']]) + r'\\', validation_table)
        for key, value in {'CurrentTimingRuns': 48, 'CurrentTimingRepeats': 6, 'CurrentTimingSuites': 19260,
                           'CurrentJointTimingRuns': 24, 'CurrentConditionalTimingRuns': 24,
                           'CurrentJointTimingSuites': 8322, 'CurrentConditionalTimingSuites': 10938,
                           'CurrentValidationRuns': 4, 'CurrentValidationSuites': 1823, 'CurrentValidationPrefixes': 1827}.items():
            self.assertEqual(runtime_macros[key], count(value))

    def test_crest_complete_populations_tables_matrices_and_macros_agree(self):
        report = json.loads(current_reporting_text('figdata/crest-report-data.json'))
        chart = json.loads(current_reporting_text('figdata/crest-figure-data.json'))
        plot = json.loads(current_reporting_text('figures/crest-outcomes.json'))
        values = macros('crest-macros.tex')
        tables = {name: current_reporting_text('figdata/crest-' + name + '.tex')
                  for name in ('reference-outcomes', 'generated-outcomes', 'heads', 'comparisons')}
        self.assertEqual(set(report), {'reference', 'catalogue', 'gpt4o', 'qwen'})
        pooled = {}
        for study in report:
            source = json_file(CREST / study / 'results.json')
            saved = json_file(CREST / study / 'reporting-summary.json')
            self.assertEqual(report[study], saved['reports'])
            self.assertEqual(saved['status'], 'COMPLETE')
            self.assertEqual(json_file(CREST / study / 'verification.json')['status'], 'PASS')
            self.assertEqual(json_file(CREST / study / 'provenance-verification.json')['status'], 'PASS')
            self.assertEqual(len(source), 591 if study in ('reference', 'catalogue') else 1138)
            self.assertEqual(len({r['task_id'] for r in source}), len(source))
            self.assertEqual(Counter(r['dataset'] for r in source),
                             {'HumanEval': 164, 'MBPP': 427 if study in ('reference', 'catalogue') else 974})
            self.assertEqual(chart['source_summaries'][study], 'artifact/studies/crest/accepted/' + study + '/reporting-summary.json')
            self.assertEqual({(r['dataset'], r['classifier']) for r in report[study]},
                             set(itertools.product(('HumanEval', 'MBPP', 'pooled'), ('rf', 'logreg_l1', 'logreg_l2'))))
            for row in report[study]:
                selected = [r for r in source if row['dataset'] == 'pooled' or r['dataset'] == row['dataset']]
                actual, transitions, observations = crest_counts(selected, row['classifier'])
                self.assertEqual(row['before_after_transition_matrix'], transitions)
                for shown, raw in [('scheduled_attempts', 'attempts'), ('input_suite_passed', 'input_passed'),
                                   ('input_suite_failed', 'input_failed'), ('input_suite_unavailable', 'input_unknown'),
                                   ('emitted_candidates', 'emitted'), ('known_emission_rejections', 'rejected'),
                                   ('candidate_suite_passed_all_inputs', 'passed'), ('candidate_suite_failed_all_inputs', 'failed_emitted'),
                                   ('detector_positive_all_inputs', 'detected')]:
                    self.assertEqual(row[shown], actual[raw], (study, row['dataset'], row['classifier'], shown))
                utility = row['overall_task_utility']
                for shown, raw in [('usable_outputs', 'passed'), ('output_utility_unknown', 'output_unknown'),
                                   ('joint_outputs', 'joint'), ('joint_output_unknown', 'joint_unknown'),
                                   ('detected_but_suite_failed', 'detected_failed')]:
                    self.assertEqual(utility[shown], actual[raw])
                self.assertEqual(utility['joint_output_rate_bounds'],
                                 [str(Fraction(actual['joint'], actual['attempts'])),
                                  str(Fraction(actual['joint'] + actual['joint_unknown'], actual['attempts']))])
                if row['classifier'] != 'rf':
                    continue
                corpus = 'Pooled' if row['dataset'] == 'pooled' else row['dataset']
                if study in ('gpt4o', 'qwen'):
                    title = 'GPT-4o' if study == 'gpt4o' else 'Qwen'
                    expected = [title, corpus, count(actual['attempts']), count(actual['input_passed']),
                                count(transitions['passed']['passed']), count(transitions['passed']['failed']),
                                count(transitions['passed']['not_emitted']), count(actual['output_unknown'])]
                    self.assertIn(' & '.join(expected) + r'\\', tables['generated-outcomes'])
                elif row['dataset'] != 'pooled':
                    title = 'Full catalogue' if study == 'reference' else 'Four rules omitted'
                    expected = [title, count(actual['emitted']), count(actual['passed']),
                                count(actual['detected']), count(actual['detected_failed']), count(actual['joint'])]
                    self.assertIn(' & '.join(expected) + r'\\', tables['reference-outcomes'])
                    expected_chart = {'corpus': corpus, 'catalogue': title, 'attempts': actual['attempts'],
                                      'pass_detected': actual['joint'], 'pass_undetected': actual['passed'] - actual['joint'],
                                      'failed_detected': actual['detected_failed'],
                                      'failed_undetected': actual['failed_emitted'] - actual['detected_failed'],
                                      'no_output': actual['rejected'], 'unknown': actual['joint_unknown']}
                    self.assertIn(expected_chart, chart['reference_outcomes'])
                if row['dataset'] == 'pooled':
                    pooled[study] = actual, transitions
            if study == 'catalogue':
                for row in report[study]:
                    title = {'rf': 'Random forest', 'logreg_l1': r'Logistic $L_1$', 'logreg_l2': r'Logistic $L_2$'}[row['classifier']]
                    expected = ['Pooled' if row['dataset'] == 'pooled' else row['dataset'], title,
                                count(row['scheduled_attempts']), count(row['overall_task_utility']['usable_outputs']),
                                count(row['overall_task_utility']['joint_outputs'])]
                    self.assertIn(' & '.join(expected) + r'\\', tables['heads'])
        for study, title, prefix in [('gpt4o', 'GPT-4o', 'GPT'), ('qwen', 'Qwen', 'Qwen')]:
            actual, transitions = pooled[study]
            matrix = [[transitions[r][c] for c in ('passed', 'failed', 'not_emitted', 'unavailable')]
                      for r in ('passed', 'failed', 'unavailable')]
            shown = next(p for p in chart['generated_transitions'] if p['cohort'] == title)
            plotted = next(p for p in plot['panels'] if p['cohort'] == title)
            self.assertEqual(shown['matrix'], matrix)
            self.assertEqual(plotted['counts'], matrix)
            self.assertEqual(plotted['row_totals'], list(map(sum, matrix)))
            for suffix, n in {'Attempts': actual['attempts'], 'Qualified': actual['input_passed'],
                              'Retained': transitions['passed']['passed'], 'NewFailures': transitions['passed']['failed'],
                              'NoOutputQualified': transitions['passed']['not_emitted'], 'NoOutput': actual['rejected'],
                              'InputUnknown': actual['input_unknown'], 'OutputUnknown': actual['joint_unknown'],
                              'Joint': actual['joint']}.items():
                self.assertEqual(values[prefix + suffix], count(n))
            low, high, n = actual['joint'], actual['joint'] + actual['joint_unknown'], actual['attempts']
            expected = 'J=' + count(low) + '/' + count(n) if low == high else r'J\in[' + count(low) + ',' + count(high) + ']/' + count(n)
            self.assertEqual(values[prefix + 'JointExpression'], expected)
        comparison = json_file(CREST / 'comparison/summary.json')
        self.assertEqual(comparison['status'], 'PASS')
        self.assertEqual(len(comparison['reports']), 45)
        self.assertEqual(len(chart['comparison_costs']), 9)
        for row in chart['comparison_costs']:
            selected = [r for r in comparison['reports'] if r['scope'] == row['scope'] and r['classifier'] == row['model']]
            self.assertEqual(len(selected), 5)
            for item in selected:
                self.assertEqual(item['first_certificate']['decision'], 'left_strict')
                key = ('j_shared' if item['method'] == 'coupled' else 'j_separate') if item['target'] == 'J' else (
                    'c_separate' if item['method'] == 'independent' else 'c_adaptive' if ('adaptive' in item['policy'] or 'point' in item['policy']) else 'c_h_first')
                self.assertEqual(row[key], item['first_certificate']['suite_queries'])
            title = {'rf': 'Random forest', 'logreg_l1': r'Logistic $L_1$', 'logreg_l2': r'Logistic $L_2$'}[row['model']]
            expected = ['Pooled' if row['scope'] == 'pooled' else row['scope'], title] + [
                count(row[k]) for k in ('j_separate', 'j_shared', 'c_separate', 'c_h_first', 'c_adaptive')]
            self.assertIn(' & '.join(expected) + r'\\', tables['comparisons'])
            if row['scope'] == 'pooled' and row['model'] == 'rf':
                for key, name in [('j_separate', 'CRESTJointSeparate'), ('j_shared', 'CRESTJointShared'),
                                  ('c_separate', 'CRESTConditionalSeparate'), ('c_h_first', 'CRESTConditionalHFirst'),
                                  ('c_adaptive', 'CRESTConditionalAdaptive')]:
                    self.assertEqual(values[name], count(row[key]))


if __name__ == '__main__':
    unittest.main()
