"""Independent reconstruction from public coefficients and admitted histories.

This receiver imports the exact Fraction reference, not production policy/state
code. Equal coefficient classes can be coalesced for extrema because all groups
in a class have the same ratio or linear margin coefficient. Selection still
uses individual identities and its declared deterministic tie rule.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path
import sys

ANALYSIS = Path(__file__).resolve().parents[1] / 'analysis'
sys.path.insert(0, str(ANALYSIS))
from conditional_bounds import UnknownGroup, ScoreModel, conditional_bounds, conditional_comparison, joint_comparison


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relation(lower, upper):
    return ('left_strict' if lower > 0 else 'right_strict' if upper < 0
            else 'tie' if lower == upper == 0 else 'unresolved')


def compact_pair(left, right, admitted):
    known = []
    for side in (left, right):
        known.append((sum(a * admitted[g] for g, (a, b) in side.items() if g in admitted),
                      sum(b * admitted[g] for g, (a, b) in side.items() if g in admitted)))
    remaining = (set(left) | set(right)) - set(admitted)
    counts = Counter((left.get(g, (0, 0)), right.get(g, (0, 0))) for g in remaining)
    models = []
    for index in (0, 1):
        unknown = []
        if all(value[1] > 0 for value in known):
            for pair, count in sorted(counts.items()):
                a, b = pair[index]
                unknown.append(UnknownGroup(repr(pair), F(b * count), F(a * count)))
        else:
            # An undefined common margin may attain an endpoint by selecting
            # only one positive group; do not round that up to a whole class.
            side = (left, right)[index]
            for group in sorted(remaining):
                a, b = side.get(group, (0, 0))
                unknown.append(UnknownGroup(group, F(b), F(a)))
        models.append(ScoreModel(F(known[index][0]), F(known[index][1]), tuple(unknown)))
    return models


def bounds(left, right, admitted, method, target):
    models = compact_pair(left, right, admitted)
    if target == 'J':
        if method == 'coupled':
            value = joint_comparison(*models)
            lower, upper = value['lower'], value['upper']
        else:
            lower = models[0].known_joint - models[1].known_joint - sum((g.detected_mass for g in models[1].unknown), F())
            upper = models[0].known_joint + sum((g.detected_mass for g in models[0].unknown), F()) - models[1].known_joint
        return dict(lower=lower, upper=upper, units='joint_count_difference',
                    decision=relation(lower, upper), defined_all=True)
    left_score, right_score = map(conditional_bounds, models)
    if method == 'coupled':
        pair = conditional_comparison(*models)
        if pair['route'] == 'exact_common_remainder':
            decision = pair['decision']
            if decision == 'undefined_everywhere':
                decision = 'undefined_everywhere_for_at_least_one_side'
            return dict(lower=pair['margin_lower'], upper=pair['margin_upper'],
                        units='conditional_cross_product_count_margin', decision=decision,
                        defined_all=pair['defined_for_all_completions'])
    defined = left_score['defined_for_all_completions'] and right_score['defined_for_all_completions']
    if not left_score['defined_for_some_completion'] or not right_score['defined_for_some_completion']:
        return dict(lower=None, upper=None, units='conditional_rate_difference',
                    decision='undefined_everywhere_for_at_least_one_side', defined_all=False)
    lower = left_score['lower'] - right_score['upper']
    upper = left_score['upper'] - right_score['lower']
    return dict(lower=lower, upper=upper, units='conditional_rate_difference',
                decision=relation(lower, upper) if defined else 'undefined_possible', defined_all=defined)


def check_bounds(record, expected):
    for key in ('decision', 'units', 'defined_all'):
        require(record.get(key) == expected[key], 'bound field disagrees: ' + key)
    for key in ('lower', 'upper'):
        value = None if record.get(key) is None else F(record[key])
        require(value == expected[key], 'exact reconstructed endpoint disagrees: ' + key)


def score_class_model(side, admitted, selected=None, response=False):
    known_n = sum(a * admitted[g] for g, (a, b) in side.items() if g in admitted)
    known_b = sum(b * admitted[g] for g, (a, b) in side.items() if g in admitted)
    unknown = Counter(tuple(coeff) for g, coeff in side.items() if g not in admitted)
    if selected is not None and selected in side and selected not in admitted:
        a, b = side[selected]
        unknown[(a, b)] -= 1
        known_n += a * response
        known_b += b * response
    return ScoreModel(F(known_n), F(known_b), tuple(
        UnknownGroup(repr(coefficient), F(coefficient[1] * count), F(coefficient[0] * count))
        for coefficient, count in sorted(unknown.items()) if count))


def next_query(left, right, admitted, attempted, method, target):
    universe = set(left) | set(right)
    remaining = universe - attempted
    if not remaining:
        return None
    pair = {g: (left.get(g, (0, 0)), right.get(g, (0, 0))) for g in universe}
    if method == 'independent' and target == 'J':
        useful = [g for g in remaining if pair[g][0][0] + pair[g][1][0] > 0]
        return min(useful, key=lambda g: (-(pair[g][0][0] + pair[g][1][0]), g)) if useful else None
    if method == 'coupled' and target == 'J':
        return min(remaining, key=lambda g: (-abs(pair[g][0][0] - pair[g][1][0]), g))
    if method == 'coupled':
        different = {g for g in universe if pair[g][0] != pair[g][1]}
        pending = different - attempted
        if pending:
            return min(pending, key=lambda g: (-sum(abs(a - b) for a, b in zip(*pair[g])), g))
        if different - set(admitted):
            return min(remaining)
        models = compact_pair(left, right, admitted)
        dn = models[0].known_joint - models[1].known_joint
        dm = models[1].known_valid - models[0].known_valid
        return min(remaining, key=lambda g: (-abs(dn * pair[g][0][1] + dm * pair[g][0][0]), g))
    representative = {}
    for g in sorted(remaining):
        representative.setdefault(pair[g], g)
    objective = []
    for g in representative.values():
        widths = []
        for response in (False, True):
            total = F()
            for side in (left, right):
                interval = conditional_bounds(score_class_model(side, admitted, g, response))
                if interval['defined_for_some_completion']:
                    total += interval['upper'] - interval['lower']
            widths.append(total)
        objective.append((max(widths), g))
    return min(objective)[1]


def coefficients(rows, dataset, left, right):
    result = {left: defaultdict(lambda: [0, 0]), right: defaultdict(lambda: [0, 0])}
    attempted = {left: set(), right: set()}
    for row in rows:
        if dataset is not None and row['dataset'] != dataset:
            continue
        variant = row['variant']
        variant = {'s1_literal_predecessor': 's1', 's4_return_boundary': 's4'}.get(variant, variant)
        if variant not in result:
            continue
        key = (row['dataset'], row['task_id'], row['key_id'], row['key_hex'])
        require(key not in attempted[variant], 'duplicate workload configuration')
        attempted[variant].add(key)
        require(type(row['detected']) is bool, 'detector decision is not observed')
        value = result[variant][row['source_contract_sha256']]
        value[0] += row['detected']
        value[1] += 1
    require(attempted[left] and attempted[left] == attempted[right], 'unequal comparison workloads')
    return ({g: tuple(pair) for g, pair in result[left].items()},
            {g: tuple(pair) for g, pair in result[right].items()}, len(attempted[left]))
