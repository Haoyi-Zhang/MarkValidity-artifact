#!/usr/bin/env python3
"""Independent finite receiver: enumerate labels rather than signed formulas.

No producer interval routine is used to build the ground truth. Each individual
ratio range, relaxed (label, ratio) envelope, actual conditional difference, and
H-free common-margin comparison is computed by direct enumeration.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import itertools
import json
from pathlib import Path
from types import SimpleNamespace

from paired_conditional import certify, envelope
from exact_residual_conditional import compare as exact_residual, compare_classes


class DirectScore:
    def __init__(self, known, unknown):
        self.joint, self.valid = known
        self.unknown = unknown
        self.values = [(self.joint + sum(c[0] * v for c, v in zip(unknown, labels)),
                        self.valid + sum(c[1] * v for c, v in zip(unknown, labels)))
                       for labels in itertools.product((0, 1), repeat=len(unknown))]

    def conditional(self):
        values = [Fraction(n, d) for n, d in self.values if d]
        return {'lower': min(values) if values else None,
                'upper': max(values) if values else None,
                'defined_some': bool(values),
                'defined_all': all(d > 0 for n, d in self.values)}


def direct_relation(values):
    if min(values) > 0:
        return 'left_strict'
    if max(values) < 0:
        return 'right_strict'
    if min(values) == max(values) == 0:
        return 'tie'
    return 'unresolved'


def run_case(known_left, known_right, pairs, counts, witnesses):
    left = DirectScore(known_left, [pair[0] for pair in pairs])
    right = DirectScore(known_right, [pair[1] for pair in pairs])
    state = SimpleNamespace(left=left, right=right, admitted={},
                            pairs={str(i): pair for i, pair in enumerate(pairs)})
    actual = certify(state)
    counts['models'] += 1
    counts['label_completions'] += len(left.values)
    if known_left[1] + sum(p[0][1] for p in pairs) != known_right[1] + sum(p[1][1] for p in pairs):
        counts['asymmetric_total_mass_models'] += 1
    valid = [(nl, dl, nr, dr) for (nl, dl), (nr, dr) in zip(left.values, right.values)
             if dl > 0 and dr > 0]
    all_defined = len(valid) == len(left.values)
    if not all_defined:
        counts['undefined_possible_models'] += 1
        if actual['decision'] in ('left_strict', 'right_strict', 'tie'):
            raise AssertionError('an undefined completion was lost')
    gaps = [Fraction(nl, dl) - Fraction(nr, dr) for nl, dl, nr, dr in valid]
    truth = direct_relation(gaps) if gaps else None
    if actual['decision'] in ('left_strict', 'right_strict', 'tie'):
        counts['certified_models'] += 1
        if actual['decision'] != truth:
            raise AssertionError(('unsound comparison', known_left, known_right, pairs, actual, truth))
    exact = exact_residual(state)
    if all_defined:
        counts['exact_residual_models'] += 1
        cross = [nl * dr - nr * dl for nl, dl, nr, dr in valid]
        if not exact['evaluated'] or exact['lower'] != min(cross) or exact['upper'] != max(cross):
            raise AssertionError('bounded exact residual endpoints differ from exhaustive completion')
        if exact['decision'] != truth:
            raise AssertionError('exact residual sign differs from exhaustive completion')
    elif exact['evaluated'] or exact['decision'] in ('left_strict', 'right_strict', 'tie'):
        raise AssertionError('exact residual receiver erased undefinedness')
    class_result = compare_classes(state)
    if all_defined:
        if not class_result['exact_decision'] or class_result['decision'] != truth:
            raise AssertionError('class-compressed exact sign differs from exhaustive completion')
        if class_result['endpoints_complete']:
            if class_result['lower'] != min(cross) or class_result['upper'] != max(cross):
                raise AssertionError('complete class-compressed endpoints differ')
            counts['class_complete_endpoints'] += 1
        else:
            if any(value not in cross for value in class_result['witness_margin_interval']):
                raise AssertionError('early unresolved sign witness is not attained')
            counts['class_early_unresolved_decisions'] += 1
    elif class_result['exact_decision'] or class_result['decision'] in ('left_strict', 'right_strict', 'tie'):
        raise AssertionError('class-compressed solver erased undefinedness')
    for name, score in [('left', left), ('right', right)]:
        c = score.conditional()
        if not c['defined_some']:
            continue
        endpoints = (c['lower'], c['upper'])
        actual_envelope = envelope(state, endpoints)
        values = []
        for q in endpoints:
            for (nl, dl), (nr, dr) in zip(left.values, right.values):
                values.append(nl - nr - q * (dl - dr))
        if actual_envelope['lower'] != min(values) or actual_envelope['upper'] != max(values):
            raise AssertionError('producer envelope does not equal direct relaxed enumeration')
        counts['anchor_envelopes'] += 1
        counts['relaxed_endpoint_completions'] += len(values)
    different = any(l != r for l, r in pairs)
    if not different and all_defined:
        # Independently enumerate cross products rather than reusing the
        # producer's affine-margin formula.
        cross = [nl * dr - nr * dl for nl, dl, nr, dr in valid]
        exact = direct_relation(cross)
        if actual['decision'] != exact:
            raise AssertionError('H-free certificate loses the exact sign')
        counts['common_remainder_equivalences'] += 1
    lrange, rrange = left.conditional(), right.conditional()
    independent = None
    if all_defined:
        independent = direct_relation([lrange['lower'] - rrange['upper'],
                                       lrange['upper'] - rrange['lower']])
        if independent in ('left_strict', 'right_strict', 'tie') and actual['decision'] != independent:
            raise AssertionError('union certificate lost an existing separate certificate')
        if lrange['lower'] == lrange['upper'] or rrange['lower'] == rrange['upper']:
            if min(gaps) != lrange['lower'] - rrange['upper'] or max(gaps) != lrange['upper'] - rrange['lower']:
                raise AssertionError('singleton-score difference interval is not sharp')
            counts['singleton_exact_models'] += 1
    if different and actual['decision'] in ('left_strict', 'right_strict', 'tie') and independent == 'unresolved':
        counts['pre_H_certificates_beyond_separate'] += 1
        if len(witnesses['pre_H']) < 3:
            witnesses['pre_H'].append({'known_left': known_left, 'known_right': known_right,
                                      'pairs': pairs, 'decision': actual['decision'],
                                      'true_gap_endpoints': [str(min(gaps)), str(max(gaps))]})
    if all_defined and truth in ('left_strict', 'right_strict', 'tie') and actual['decision'] == 'unresolved':
        counts['sufficient_but_not_complete_models'] += 1
        if len(witnesses['not_complete']) < 1:
            witnesses['not_complete'].append({'known_left': known_left, 'known_right': known_right,
                                             'pairs': pairs, 'actual_decision': actual['decision'],
                                             'true_gap_endpoints': [str(min(gaps)), str(max(gaps))]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    names = ('models', 'label_completions', 'asymmetric_total_mass_models',
             'undefined_possible_models', 'certified_models', 'anchor_envelopes',
             'relaxed_endpoint_completions', 'common_remainder_equivalences',
             'pre_H_certificates_beyond_separate', 'sufficient_but_not_complete_models')
    counts = dict.fromkeys(names, 0)
    counts['exact_residual_models'] = 0
    counts['class_complete_endpoints'] = 0
    counts['class_early_unresolved_decisions'] = 0
    counts['singleton_exact_models'] = 0
    witnesses = {'pre_H': [], 'not_complete': []}
    known = [(a, b) for b in range(3) for a in range(b + 1)]
    # Complete enumeration of all three-state row incidences on up to 3 groups,
    # with both known numerator/denominator masses in 0 <= n <= m <= 2.
    coefficient = ((0, 0), (0, 1), (1, 1))
    choices = [p for p in itertools.product(coefficient, repeat=2) if p != ((0, 0), (0, 0))]
    for groups in range(4):
        for pairs in itertools.product(choices, repeat=groups):
            for lknown, rknown in itertools.product(known, repeat=2):
                run_case(lknown, rknown, pairs, counts, witnesses)
    # Cover non-unit group multiplicity with two groups and all numerator
    # counts through mass 2. Unit-only cases are already covered above.
    weighted = [(a, b) for b in range(3) for a in range(b + 1)]
    choices = [p for p in itertools.product(weighted, repeat=2) if p != ((0, 0), (0, 0))]
    for pairs in itertools.product(choices, repeat=2):
        if all(max(pair[0][1], pair[1][1]) <= 1 for pair in pairs):
            continue
        for lknown, rknown in itertools.product(known, repeat=2):
            run_case(lknown, rknown, pairs, counts, witnesses)
    # Test the solver cap independently of the small-model range.
    gate_state = SimpleNamespace(left=SimpleNamespace(joint=1, valid=2),
                                 right=SimpleNamespace(joint=1, valid=2), admitted={},
                                 pairs={str(i): ((1, 1), (0, 0)) for i in range(13)})
    capped = exact_residual(gate_state, 12)
    if capped['evaluated'] or capped['assignments_evaluated'] != 0 or capped['lower'] is not None:
        raise AssertionError('exact solver exceeded its declared inference cap')
    gate_state.admitted['0'] = False
    uncapped = exact_residual(gate_state, 12)
    if not uncapped['evaluated'] or uncapped['assignments_evaluated'] != 4096:
        raise AssertionError('exact solver did not enumerate the full eligible residual')
    try:
        exact_residual(gate_state, -1)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid enumeration cap was accepted')
    counts['exact_cap_controls'] = 3
    gate_state.admitted.clear()
    limited = compare_classes(gate_state, 1)
    if limited['exact_decision'] or limited['assignments_evaluated'] != 1:
        raise AssertionError('class comparator exceeded its inference budget')
    decisive = compare_classes(gate_state, 2)
    if not decisive['exact_decision'] or decisive['decision'] != 'unresolved' or decisive['coefficient_class_assignments'] != 14:
        raise AssertionError('class compression or early zero/nonzero witness is incorrect')
    counts['class_budget_controls'] = 2
    result = {'status': 'pass', 'counts': counts, 'witnesses': witnesses,
              'method': 'Independent direct Boolean-completion enumeration. No signed-coefficient formula or production score range routine is used to construct the reference results.',
              'meaning': 'Finite implementation checks support the accompanying all-size algebraic proof; these models are mathematical verification inputs, not program experiments.'}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
