#!/usr/bin/env python3
"""Independently receive every retrospective own-order trace and joint witness.

Only this retrospective receiver opens the frozen completed normalized ledgers.
Its arithmetic and next-query reconstruction use public coefficients and the
prefix already revealed. Realized full labels are used separately to validate
the explicitly hindsight-only minimum certificates.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from fractions import Fraction as F
import gzip
import hashlib
import io
import json
from pathlib import Path

from independent import (ANALYSIS, UnknownGroup, ScoreModel, conditional_bounds,
                         conditional_comparison, joint_comparison, coefficients,
                         require, relation, check_bounds)

CERTIFICATES = {'left_strict', 'right_strict', 'tie'}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReceiverState:
    """Public coefficient histogram independent of the producer's score state.

    Histograms coalesce only arithmetic. Attempted identities remain individual.
    Undefined conditional margins are expanded to individual identities so an
    endpoint requiring one positive group cannot be rounded up to a full class.
    """
    def __init__(self, left, right, initial):
        self.sides = (left, right)
        self.pairs = {g: (left.get(g, (0, 0)), right.get(g, (0, 0))) for g in set(left) | set(right)}
        self.histogram = Counter(self.pairs.values())
        self.known = [[0, 0], [0, 0]]
        self.admitted, self.attempted = {}, set()
        self.ids = sorted(self.pairs)
        self.different = {g for g, pair in self.pairs.items() if pair[0] != pair[1]}
        for group, label in initial.items():
            if group in self.pairs:
                self.reveal(group, label)

    def reveal(self, group, label):
        require(group in self.pairs and group not in self.attempted, 'duplicate or unknown disclosure')
        require(label is None or type(label) is bool, 'invalid disclosed label')
        self.attempted.add(group)
        if label is None:
            return
        self.admitted[group] = label
        pair = self.pairs[group]
        self.histogram[pair] -= 1
        for index in (0, 1):
            a, b = pair[index]
            self.known[index][0] += a * label
            self.known[index][1] += b * label

    def models(self, hypothetical=None, response=False, individual=False):
        if individual:
            unknown = [(g, pair, 1) for g, pair in self.pairs.items() if g not in self.admitted]
        else:
            unknown = [(repr(pair), pair, count) for pair, count in sorted(self.histogram.items()) if count]
        result = []
        for index in (0, 1):
            n, v = self.known[index]
            if hypothetical is not None:
                a, b = hypothetical[index]
                n, v = n + a * response, v + b * response
            terms = []
            for identifier, pair, count in unknown:
                count -= hypothetical is not None and hypothetical == pair
                if count:
                    a, b = pair[index]
                    terms.append(UnknownGroup(identifier, F(count * b), F(count * a)))
            result.append(ScoreModel(F(n), F(v), tuple(terms)))
        return result

    def bounds(self, method, target):
        if target == 'J':
            constant = self.known[0][0] - self.known[1][0]
            if method == 'coupled':
                lower = constant + sum(min(0, pair[0][0] - pair[1][0]) * n for pair, n in self.histogram.items())
                upper = constant + sum(max(0, pair[0][0] - pair[1][0]) * n for pair, n in self.histogram.items())
            else:
                lower = constant - sum(pair[1][0] * n for pair, n in self.histogram.items())
                upper = constant + sum(pair[0][0] * n for pair, n in self.histogram.items())
            return dict(lower=F(lower), upper=F(upper), units='joint_count_difference',
                        decision=relation(lower, upper), defined_all=True)
        models = self.models(individual=not all(k[1] > 0 for k in self.known))
        if method == 'coupled':
            interval = conditional_comparison(*models)
            if interval['route'] == 'exact_common_remainder':
                decision = interval['decision']
                if decision == 'undefined_everywhere':
                    decision = 'undefined_everywhere_for_at_least_one_side'
                return dict(lower=interval['margin_lower'], upper=interval['margin_upper'],
                            units='conditional_cross_product_count_margin', decision=decision,
                            defined_all=interval['defined_for_all_completions'])
        left, right = map(conditional_bounds, models)
        defined = left['defined_for_all_completions'] and right['defined_for_all_completions']
        if not left['defined_for_some_completion'] or not right['defined_for_some_completion']:
            return dict(lower=None, upper=None, units='conditional_rate_difference',
                        decision='undefined_everywhere_for_at_least_one_side', defined_all=False)
        lower, upper = left['lower'] - right['upper'], left['upper'] - right['lower']
        return dict(lower=lower, upper=upper, units='conditional_rate_difference',
                    decision=relation(lower, upper) if defined else 'undefined_possible', defined_all=defined)

    def next_query(self, method, target):
        remaining = [g for g in self.ids if g not in self.attempted]
        if not remaining:
            return None
        if target == 'J':
            if method == 'independent':
                priority = lambda g: sum(pair[0] for pair in self.pairs[g])
                remaining = [g for g in remaining if priority(g)]
            else:
                priority = lambda g: abs(self.pairs[g][0][0] - self.pairs[g][1][0])
            return min(remaining, key=lambda g: (-priority(g), g)) if remaining else None
        if method == 'coupled':
            pending = self.different - self.attempted
            if pending:
                return min(pending, key=lambda g: (-sum(abs(a - b) for a, b in zip(*self.pairs[g])), g))
            if self.different - set(self.admitted):
                return remaining[0]
            dn = self.known[0][0] - self.known[1][0]
            dv = self.known[1][1] - self.known[0][1]
            return min(remaining, key=lambda g: (-abs(dn * self.pairs[g][0][1] + dv * self.pairs[g][0][0]), g))
        representatives = {}
        for group in remaining:
            representatives.setdefault(self.pairs[group], group)
        choices = []
        for pair, group in representatives.items():
            widths = []
            for reply in (False, True):
                width = F()
                for model in self.models(hypothetical=pair, response=reply):
                    interval = conditional_bounds(model)
                    if interval['defined_for_some_completion']:
                        width += interval['upper'] - interval['lower']
                widths.append(width)
            choices.append((max(widths), group))
        return min(choices)[1]


def check_hindsight(record, left, right, initial, truth, method):
    state = ReceiverState(left, right, initial)
    full = sum(a * truth[g] for g, (a, b) in left.items()) - sum(a * truth[g] for g, (a, b) in right.items())
    direction = relation(full, full)
    require(record['available'] and record['decision'] == direction, 'wrong hindsight direction')
    remaining = set(state.pairs) - state.attempted
    if direction == 'tie':
        witness = sorted(g for g in remaining if
                         (sum(pair[0] for pair in state.pairs[g]) if method == 'independent'
                          else abs(state.pairs[g][0][0] - state.pairs[g][1][0])))
        require(record['witness'] == witness and record['minimum_queries'] == len(witness), 'wrong exact-tie minimum witness')
        return
    start = state.bounds(method, 'J')
    endpoint = start['lower'] if direction == 'left_strict' else -start['upper']
    gains = {}
    for group in remaining:
        (al, _), (ar, _) = state.pairs[group]
        value = truth[group]
        if method == 'independent':
            gain = al * value + ar * (1 - value) if direction == 'left_strict' else al * (1 - value) + ar * value
        else:
            c = al - ar
            gain = c * value - min(0, c) if direction == 'left_strict' else max(0, c) - c * value
        require(gain >= 0, 'a disclosure widened the true-direction joint endpoint')
        gains[group] = gain
    order = sorted(gains, key=lambda group: (-gains[group], group))
    total, witness = 0, []
    for group in order:
        if endpoint + total > 0:
            break
        witness.append(group)
        total += gains[group]
    previous = total - (gains[witness[-1]] if witness else 0)
    require(endpoint + total > 0 and (not witness or endpoint + previous <= 0), 'joint witness does not cross strictly at its minimum size')
    expected = {'witness': witness, 'minimum_queries': len(witness), 'initial_signed_endpoint': endpoint,
                'selected_gain': total, 'best_gain_with_one_fewer_query': previous,
                'strict_signed_endpoint': endpoint + total}
    require(all(record[key] == value for key, value in expected.items()), 'hindsight certificate/gain argument differs')


def receive(root, results, progress=False):
    cases, schedules, prefixes, disclosed, witness_count = 0, 0, 0, 0, 0
    inputs, reports = {}, []
    for folder, expected_initialization, original in (
            ('retrospective-primary', 'reference_identity_known', 'analysis-primary'),
            ('retrospective-all-withheld', 'all_withheld', 'analysis-all-withheld')):
        base = results / folder
        analysis = json.loads((base / 'analysis.json').read_text())
        inputs[folder + '/analysis.json'] = sha(base / 'analysis.json')
        require(analysis['status'] == 'COMPLETE' and analysis['initialization'] == expected_initialization
                and analysis['cases'] == 18 and analysis['schedules'] == 72, 'incomplete retrospective matrix')
        for name, path in {'analyze.py': Path(__file__).with_name('analyze.py'),
                           'policies.py': Path(__file__).with_name('policies.py'),
                           'natural_analysis.py': ANALYSIS / 'natural_analysis.py'}.items():
            require(sha(path) == analysis['source_sha256'][name], 'changed retrospective producer dependency')
        require(sha(root / 'results/revision-sew-natural' / original / 'comparisons.json') == analysis['original_comparisons_sha256'],
                'changed original coupled comparison')
        rows, truth, initial = [], {}, {}
        for relative, checksum in analysis['inputs'].items():
            path = (root / relative).resolve()
            require(path.is_relative_to(root) and sha(path) == checksum, 'changed frozen completed ledger')
            for row in json.loads(path.read_text()):
                group = row['source_contract_sha256']
                require(hashlib.sha256(canonical({key: row[key] for key in
                        ('reference_sha256', 'candidate_sha256', 'contract_sha256')})).hexdigest() == group,
                        'ledger source-contract identity is malformed')
                raw = row['validity_label']
                if raw == 'supported' or type(raw) is int and raw == 1:
                    label = True
                elif raw == 'contradicted' or type(raw) is int and raw == 0:
                    label = False
                else:
                    raise ValueError('these complete finite ledgers require a resolved admitted label')
                require(group not in truth or truth[group] is label, 'completed labels disagree within identity')
                truth[group] = label
                require(row['reference_status'] == 'passed' and row['suite_cost'] == 1, 'wrong reference qualification or suite unit')
                if expected_initialization == 'reference_identity_known' and row['reference_sha256'] == row['candidate_sha256']:
                    require(label, 'qualified reference identity cannot have contradictory label')
                    initial[group] = True
                rows.append(row)
        table = list(csv.DictReader((base / 'comparison_summary.csv').open(newline='')))
        require(len(table) == 72 and len({(r['case'], r['method'], r['target']) for r in table}) == 72,
                'retrospective table has duplicates or omissions')
        table_map = {(r['case'], r['method'], r['target']): r for r in table}
        for case, report in analysis['reports'].items():
            dataset = {'humaneval': 'HumanEval', 'mbpp': 'mbpp_sanitized', 'pooled': None}[report['scope']]
            left, right, denominator = coefficients(rows, dataset, report['left'], report['right'])
            require(report['denominator'] == denominator and report['case'] == case, 'changed case/denominator')
            for method in ('coupled', 'independent'):
                check_hindsight(report['hindsight_joint_witness'][method], left, right, initial, truth, method)
                witness_count += 1
                for target in ('J', 'C'):
                    run = report['runs'][method + '_' + target]
                    state = ReceiverState(left, right, initial)
                    path = base / 'traces' / run['trace_file']
                    require(path.resolve().is_relative_to(base.resolve()) and sha(path) == run['trace_sha256'], 'changed retrospective trace')
                    trace = list(csv.DictReader(io.StringIO(gzip.decompress(path.read_bytes()).decode())))
                    order = run['full_query_order']
                    require(len(trace) == len(order) + 1 and len(order) == run['full_retrospective_queries'], 'wrong full retrospective trace length')
                    first = None
                    for step, snapshot in enumerate(trace):
                        expected = state.bounds(method, target)
                        require(int(snapshot['step']) == step and int(snapshot['groups_admitted']) == len(state.admitted), 'wrong retrospective prefix identity')
                        for key in ('lower', 'upper'):
                            actual = None if snapshot[key] == '' else F(snapshot[key])
                            require(actual == expected[key], 'retrospective exact endpoint mismatch: ' + case + '/' + method + target + '/' + str(step))
                        require(snapshot['units'] == expected['units'] and snapshot['decision'] == expected['decision'], 'wrong retrospective endpoint units/decision')
                        if first is None and expected['decision'] in CERTIFICATES:
                            first = step
                            recorded = run['first_certificate']
                            require(recorded['suite_queries'] == step and recorded['decision'] == expected['decision'], 'first certificate was skipped or advanced')
                            require(recorded['query_prefix_sha256'] == hashlib.sha256(canonical(order[:step])).hexdigest(), 'changed first certificate prefix')
                            check_bounds(recorded['bounds'], expected)
                        selected = state.next_query(method, target)
                        prefixes += 1
                        if step == len(order):
                            require(selected is None, 'full retrospective schedule stopped early')
                            break
                        require(selected == order[step] and trace[step + 1]['group'] == selected, 'own-order policy selected a different public group')
                        # Only after checking the public choice do we disclose this saved real label.
                        label = truth[selected]
                        require(trace[step + 1]['received_label'] == str(int(label)), 'trace did not disclose its actual frozen label')
                        state.reveal(selected, label)
                        disclosed += 1
                    require(first is not None, 'retrospective trace lacks a finite certificate')
                    row = table_map[(case, method, target)]
                    require(int(row['candidate_suite_queries']) == first and int(row['denominator']) == denominator
                            and row['decision'] == run['first_certificate']['decision'] and row['policy'] == run['policy']
                            and row['initialization'] == expected_initialization
                            and row['trace_file'] == 'traces/' + run['trace_file'], 'retrospective summary table differs')
                    if target == 'J':
                        require(int(row['hindsight_minimum_J_queries']) == report['hindsight_joint_witness'][method]['minimum_queries'], 'table hindsight count differs')
                    schedules += 1
            cases += 1
            reports.append({'initialization': expected_initialization, 'case': case, 'schedules_received': 4})
            if progress:
                print(json.dumps({'event': 'case_received', **reports[-1]}), flush=True)
    return {'schema': 'markvalidity-independent-own-order-receiving-v1', 'status': 'PASS',
            'scope': 'Every saved own-order prefix and selection, including full plotting suffixes, reconstructed independently from public coefficients and the admitted prefix; each disclosed label checked against unchanged completed benchmark ledgers. The hindsight witnesses are received separately as label-informed diagnostics.',
            'case_initializations_received': cases, 'schedules_received': schedules,
            'prefixes_received': prefixes, 'historical_disclosures_received': disclosed,
            'joint_hindsight_minima_received': witness_count,
            'new_candidate_program_executions': 0, 'input_sha256': inputs,
            'source_sha256': {'verify_replay.py': sha(Path(__file__)), 'independent.py': sha(Path(__file__).with_name('independent.py'))},
            'reference_math_sha256': sha(ANALYSIS / 'conditional_bounds.py'), 'cases': reports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--progress', action='store_true')
    args = parser.parse_args()
    report = receive(args.artifact.resolve(), args.results.resolve(), args.progress)
    if args.out:
        require(not args.out.exists(), 'fresh receiving output required')
        args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ('cases', 'source_sha256', 'input_sha256')}, indent=2))


if __name__ == '__main__':
    main()
