#!/usr/bin/env python3
"""Independent finite-completion controls for the new disclosure policies.

These are mathematical and interface controls, not empirical program trials.
Expected score endpoints are computed from all Boolean completions directly.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path

from analyze import joint_witness_optimum, load_api, sha
from policies import IndependentConditionalWidth, IndependentPairState, hypothetical_conditional, initialize, target_bounds


def require(value, message):
    if not value:
        raise ValueError(message)


def direct_values(coefficients, admitted):
    unknown = sorted(set(coefficients) - set(admitted))
    values, total = [], 0
    for bits in product((False, True), repeat=len(unknown)):
        labels = dict(admitted, **dict(zip(unknown, bits)))
        joint = sum(a * labels[g] for g, (a, b) in coefficients.items())
        valid = sum(b * labels[g] for g, (a, b) in coefficients.items())
        values.append((joint, valid, Fraction(joint, valid) if valid else None))
        total += 1
    return values, total


def direct_conditional(coefficients, admitted):
    values, total = direct_values(coefficients, admitted)
    defined = [x[2] for x in values if x[2] is not None]
    return (min(defined), max(defined)) if defined else (None, None)


def direct_joint_interval(left, right, admitted, method):
    if method == 'independent':
        lv, _ = direct_values(left, admitted)
        rv, _ = direct_values(right, admitted)
        return min(x[0] for x in lv) - max(x[0] for x in rv), max(x[0] for x in lv) - min(x[0] for x in rv)
    remaining = sorted((set(left) | set(right)) - set(admitted))
    gaps = []
    for bits in product((False, True), repeat=len(remaining)):
        labels = dict(admitted, **dict(zip(remaining, bits)))
        gaps.append(sum(a * labels[g] for g, (a, b) in left.items())
                    - sum(a * labels[g] for g, (a, b) in right.items()))
    return min(gaps), max(gaps)


def controls(api):
    left = {'g0': (1, 1), 'g1': (1, 1), 'g3': (0, 1), 'g4': (0, 1), 'g5': (1, 1)}
    right = {'g0': (1, 1), 'g2': (0, 1), 'g3': (1, 1), 'g4': (0, 1), 'g5': (1, 1)}
    groups = sorted(set(left) | set(right))
    coefficients = (left, right, 5, groups)
    counters = {'hidden_assignments': 0, 'policy_prefixes': 0, 'hypothetical_endpoint_checks': 0,
                'complete_candidate_greedy_checks': 0, 'joint_hindsight_minima': 0,
                'joint_witness_subsets': 0, 'matching_history_choices': 0}
    histories = {}
    for initialization in ('all_withheld', 'reference_identity_known'):
        for bits in product((False, True), repeat=len(groups)):
            truth = dict(zip(groups, bits))
            if initialization == 'reference_identity_known' and not truth['g0']:
                continue
            counters['hidden_assignments'] += 1
            initial = {'g0': True} if initialization == 'reference_identity_known' else {}
            for target in ('J', 'C'):
                state, policy = initialize(api, coefficients, initial, 'independent', target)
                history = []
                while True:
                    counters['policy_prefixes'] += 1
                    if target == 'J':
                        expected = direct_joint_interval(left, right, state.admitted, 'independent')
                        got = target_bounds(api, state, 'independent', target)
                        require(expected == (got['lower'], got['upper']), 'independent J envelope differs from direct completion')
                    remaining = sorted(state.groups - state.attempted)
                    choices = []
                    for candidate in remaining:
                        losses = []
                        for reply in (False, True):
                            hypothetical = dict(state.admitted, **{candidate: reply})
                            width = Fraction()
                            for score, coefficients_one in ((state.left, left), (state.right, right)):
                                expected = direct_conditional(coefficients_one, hypothetical)
                                got = hypothetical_conditional(score, candidate, reply)
                                require(got == expected, 'one-response conditional endpoint differs from complete Boolean oracle')
                                counters['hypothetical_endpoint_checks'] += 1
                                if expected[0] is not None:
                                    width += expected[1] - expected[0]
                            losses.append(width)
                        choices.append((max(losses), candidate))
                    selected = policy.next_group(state)
                    if target == 'C':
                        expected = min(choices)[1] if choices else None
                        require(selected == expected, 'coefficient-class shortcut changed the full candidate greedy choice')
                        counters['complete_candidate_greedy_checks'] += 1
                    else:
                        influential = [g for g in remaining if left.get(g, (0, 0))[0] + right.get(g, (0, 0))[0] > 0]
                        expected = min(influential, key=lambda g: (-(left.get(g, (0, 0))[0] + right.get(g, (0, 0))[0]), g)) if influential else None
                        require(selected == expected, 'independent J ordering includes zero width or uses the wrong coefficient')
                    history_key = (initialization, target, tuple(history))
                    if history_key in histories:
                        require(histories[history_key] == selected, 'hidden labels changed a query before disclosure')
                        counters['matching_history_choices'] += 1
                    histories[history_key] = selected
                    if selected is None:
                        break
                    state.reveal(selected, truth[selected])
                    history.append((selected, truth[selected]))
            remaining = sorted(set(groups) - set(initial))
            for method in ('independent', 'coupled'):
                optimum = joint_witness_optimum(api, coefficients, initial, truth, method)
                full_gap = sum(a * truth[g] for g, (a, b) in left.items()) - sum(a * truth[g] for g, (a, b) in right.items())
                wanted = api.relation(full_gap, full_gap)
                direct_minimum = None
                for size in range(len(remaining) + 1):
                    for subset in combinations(remaining, size):
                        disclosed = dict(initial, **{g: truth[g] for g in subset})
                        lower, upper = direct_joint_interval(left, right, disclosed, method)
                        counters['joint_witness_subsets'] += 1
                        if api.relation(lower, upper) == wanted:
                            direct_minimum = size
                            break
                    if direct_minimum is not None:
                        break
                require(optimum['minimum_queries'] == direct_minimum, 'hindsight gain prefix does not give exact minimum certificate size')
                counters['joint_hindsight_minima'] += 1
    state = IndependentPairState(api, left, right, 5)
    before = target_bounds(api, state, 'independent', 'J')
    state.reveal('g0', None)
    require(before == target_bounds(api, state, 'independent', 'J') and 'g0' not in state.admitted,
            'unavailable reply tightened a baseline interval')
    try:
        state.reveal('g0', True)
    except ValueError:
        pass
    else:
        raise ValueError('baseline accepted a repeated unit-cost disclosure')
    return {'status': 'PASS', 'scope': 'Finite mathematical controls, independent direct Boolean completion; no empirical candidate execution.',
            **counters, 'unavailable_and_duplicate_controls': 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    api, api_path = load_api(args.artifact.resolve())
    result = controls(api)
    result['source_sha256'] = {name: sha(Path(__file__).with_name(name)) for name in ('policies.py', 'analyze.py', 'verify_policies.py')}
    result['natural_analysis_sha256'] = sha(api_path)
    content = json.dumps(result, indent=2) + '\n'
    if args.out:
        if args.out.exists():
            raise ValueError('fresh control output required')
        args.out.write_text(content)
    print(content, end='')


if __name__ == '__main__':
    main()
