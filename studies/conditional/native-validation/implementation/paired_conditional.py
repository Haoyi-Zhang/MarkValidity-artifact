"""Conditional sign certificates before coefficient differences are resolved.

This receiver uses public integer coefficients and already admitted labels only.
It neither receives an oracle nor reads future observations. Every unresolved
label stays shared between the two versions. Individual conditional intervals
provide an auxiliary ratio range; allowing that ratio to vary independently of
the labels is a safe relaxation. The result is a sufficient sign certificate,
not a claim of sharp numerical bounds on C_left - C_right.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction


def envelope(state, anchor_interval, difference_counts=None):
    """Exact extrema of delta_J(v) - q delta_A(v) on a relaxed product set.

The product set has independent unresolved Boolean labels and
q in anchor_interval. The actual ratio-to-label relation is not imposed. The
objective is affine in q; for either endpoint q=p/t, optimizing the labels is
the exact signed-coefficient calculation performed with integers below.
"""
    if anchor_interval[0] is None or anchor_interval[1] is None:
        return None
    if not 0 <= anchor_interval[0] <= anchor_interval[1] <= 1:
        raise ValueError('a conditional anchor interval must lie in [0, 1]')
    delta_n = state.left.joint - state.right.joint
    delta_m = state.left.valid - state.right.valid
    if difference_counts is None:
        difference_counts = Counter((al - ar, bl - br)
                                    for group, ((al, bl), (ar, br)) in state.pairs.items()
                                    if group not in state.admitted and (al, bl) != (ar, br))
    endpoints = []
    for q in dict.fromkeys(anchor_interval):
        p, t = q.numerator, q.denominator
        lower = upper = t * delta_n - p * delta_m
        for (c, d), count in difference_counts.items():
            term = count * (t * c - p * d)
            lower += min(0, term)
            upper += max(0, term)
        endpoints.append({'q': q, 'lower_numerator': lower,
                          'upper_numerator': upper, 'denominator': t})
    lower = min(Fraction(e['lower_numerator'], e['denominator']) for e in endpoints)
    upper = max(Fraction(e['upper_numerator'], e['denominator']) for e in endpoints)
    return {'lower': lower, 'upper': upper, 'endpoints': endpoints,
            'different_unknown_groups': sum(difference_counts.values())}


def sign(lower, upper):
    if lower > 0:
        return 'left_strict'
    if upper < 0:
        return 'right_strict'
    if lower == upper == 0:
        return 'tie'
    return 'unresolved'


def certify(state, difference_counts=None):
    """Use both exact single-version ratio ranges as possible anchors.

For q=C_right(v), the affine expression is A_left(v)*(C_left-C_right).
For q=C_left(v), it is A_right(v)*(C_left-C_right). Thus either envelope
certifies the comparison when both denominators are positive in every
completion. Undefinedness is returned otherwise even if the restricted
defined subset has a fixed sign.
"""
    left, right = state.left.conditional(), state.right.conditional()
    result = {'route': 'paired_ratio_envelope',
              'defined_all': left['defined_all'] and right['defined_all'],
              'anchors': {}, 'decision': 'unresolved', 'anchor': None,
              'decision_source': None}
    if not left['defined_some'] or not right['defined_some']:
        result['decision'] = 'undefined_everywhere_for_at_least_one_side'
        return result
    decisions = []
    for name, interval in [('left', left), ('right', right)]:
        bounds = envelope(state, (interval['lower'], interval['upper']), difference_counts)
        bounds['relation_on_relaxation'] = sign(bounds['lower'], bounds['upper'])
        result['anchors'][name] = bounds
        if bounds['relation_on_relaxation'] != 'unresolved':
            decisions.append((name, bounds['relation_on_relaxation']))
    if len({decision for _, decision in decisions}) > 1:
        raise ArithmeticError('two sound ratio anchors cannot disagree')
    if not result['defined_all']:
        result['decision'] = 'undefined_possible'
    elif decisions:
        result['anchor'], result['decision'] = decisions[0]
        result['decision_source'] = 'paired_ratio_envelope'
    else:
        # Retain the old separate-interval rule as well: the union of two
        # sufficient certificates cannot need more labels than either alone.
        separate_lower = left['lower'] - right['upper']
        separate_upper = left['upper'] - right['lower']
        separate_decision = sign(separate_lower, separate_upper)
        if separate_decision != 'unresolved':
            result['decision'] = separate_decision
            result['decision_source'] = 'separate_conditional_intervals'
            result['separate_interval'] = [separate_lower, separate_upper]
    return result


class PairedEnvelope:
    """A comparison state with an incrementally maintained coefficient histogram.

The histogram compresses arithmetic only. Each source-contract identity remains
a distinct label in the wrapped state, and each successful observation removes
exactly its own coefficient contribution. An unavailable response leaves it in
the histogram. Group selection and the existing state API pass through.
"""
    def __init__(self, state):
        self.state = state
        self.difference_counts = Counter((al - ar, bl - br)
                                         for group, ((al, bl), (ar, br)) in state.pairs.items()
                                         if group not in state.admitted and (al, bl) != (ar, br))

    def __getattr__(self, name):
        return getattr(self.state, name)

    def reveal(self, group, label):
        # Let the wrapped receiver validate before changing this derived index.
        self.state.reveal(group, label)
        if label is not None:
            (al, bl), (ar, br) = self.state.pairs[group]
            if (al, bl) != (ar, br):
                pair = al - ar, bl - br
                self.difference_counts[pair] -= 1
                if self.difference_counts[pair] == 0:
                    del self.difference_counts[pair]

    def certify(self):
        return certify(self.state, self.difference_counts)
