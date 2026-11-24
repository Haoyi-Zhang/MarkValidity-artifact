"""Exact conditional sign over a bounded number of differing unknown groups.

This is an inference comparator. It observes no new program labels. Enumerating
the differing groups leaves a common remainder whose cross-product margin is
linear. Every returned endpoint is attained in the Boolean completion model.
"""
from __future__ import annotations

from collections import Counter
import itertools
import math


def compare(state, max_differences=12):
    if type(max_differences) is not int or max_differences < 0:
        raise ValueError('the enumeration cap must be a nonnegative integer')
    remaining = [(group, pair) for group, pair in state.pairs.items()
                 if group not in state.admitted]
    different = sorted((g, p) for g, p in remaining if p[0] != p[1])
    shared = Counter(p[0] for g, p in remaining if p[0] == p[1])
    result = {'route': 'exact_differing_group_completion', 'different_groups': len(different),
              'enumeration_cap': max_differences, 'defined_all': state.left.valid > 0 and state.right.valid > 0,
              'evaluated': False, 'decision': 'unresolved', 'assignments_evaluated': 0,
              'lower': None, 'upper': None, 'units': 'conditional_cross_product_count_margin'}
    if not result['defined_all']:
        result['decision'] = 'undefined_possible'
        result['reason'] = 'No unconditional conditional comparison while a zero denominator remains possible.'
        return result
    if len(different) > max_differences:
        result['reason'] = 'Differing unknown groups exceed the declared inference cap.'
        return result
    best_lower = best_upper = None
    lower_bits = upper_bits = None
    for bits in itertools.product((0, 1), repeat=len(different)):
        nl, ml = state.left.joint, state.left.valid
        nr, mr = state.right.joint, state.right.valid
        for value, (_, ((al, bl), (ar, br))) in zip(bits, different):
            nl += al * value
            ml += bl * value
            nr += ar * value
            mr += br * value
        low = high = nl * mr - nr * ml
        for (a, b), count in shared.items():
            coefficient = ((nl - nr) * b + (mr - ml) * a) * count
            low += min(0, coefficient)
            high += max(0, coefficient)
        if best_lower is None or low < best_lower:
            best_lower, lower_bits = low, bits
        if best_upper is None or high > best_upper:
            best_upper, upper_bits = high, bits
        result['assignments_evaluated'] += 1
    result.update(evaluated=True, lower=best_lower, upper=best_upper,
                  lower_different_assignment=list(lower_bits), upper_different_assignment=list(upper_bits),
                  different_identity_order=[g for g, pair in different])
    result['decision'] = ('left_strict' if best_lower > 0 else 'right_strict' if best_upper < 0
                          else 'tie' if best_lower == best_upper == 0 else 'unresolved')
    return result


def compare_classes(state, max_assignments=1_000_000):
    """Exact sign decisions by coefficient-quadruple counts, within an effort budget.

Equal quadruples compress arithmetic, not evidence: any count from zero through
their multiplicity is reachable by independent Boolean labels. Simple public
corner probes can prove that a strict direction/exact tie is unresolved without
computing every margin endpoint. Such a result explicitly omits full endpoints.
An exhausted budget without that proof remains a distinct unresolved result.
"""
    if type(max_assignments) is not int or max_assignments < 0:
        raise ValueError('the assignment budget must be a nonnegative integer')
    unknown = [(group, pair) for group, pair in state.pairs.items() if group not in state.admitted]
    classes = Counter(pair for group, pair in unknown if pair[0] != pair[1])
    shared = Counter(pair[0] for group, pair in unknown if pair[0] == pair[1])
    ordered = sorted(classes)
    maxima = tuple(classes[pair] for pair in ordered)
    count_space = math.prod(c + 1 for c in maxima)
    result = {'route': 'exact_coefficient_class_comparison',
              'different_groups': sum(maxima), 'different_classes': len(ordered),
              'coefficient_class_assignments': count_space, 'assignment_budget': max_assignments,
              'defined_all': state.left.valid > 0 and state.right.valid > 0,
              'exact_decision': False, 'endpoints_complete': False, 'decision': 'unresolved',
              'assignments_evaluated': 0, 'lower': None, 'upper': None,
              'units': 'conditional_cross_product_count_margin'}
    if not result['defined_all']:
        result.update(decision='undefined_possible', reason='A zero denominator remains possible.')
        return result

    def bounds_at(counts):
        nl, ml = state.left.joint, state.left.valid
        nr, mr = state.right.joint, state.right.valid
        for count, ((al, bl), (ar, br)) in zip(counts, ordered):
            nl += al * count
            ml += bl * count
            nr += ar * count
            mr += br * count
        low = high = nl * mr - nr * ml
        for (a, b), count in shared.items():
            coefficient = ((nl - nr) * b + (mr - ml) * a) * count
            low += min(0, coefficient)
            high += max(0, coefficient)
        return low, high

    zero = (0,) * len(ordered)
    probes = [zero, maxima]
    for index, maximum in enumerate(maxima):
        one = list(zero)
        one[index] = maximum
        probes.append(tuple(one))
        all_but_one = list(maxima)
        all_but_one[index] = 0
        probes.append(tuple(all_but_one))
    probes = list(dict.fromkeys(probes))
    probe_set = set(probes)
    best_lower = best_upper = None
    lower_counts = upper_counts = None
    for phase, assignments in [('probe', iter(probes)),
                               ('complete', itertools.product(*(range(c + 1) for c in maxima)))]:
        for counts in assignments:
            if phase == 'complete' and counts in probe_set:
                continue
            if result['assignments_evaluated'] == max_assignments:
                result['reason'] = 'The inference budget was exhausted before a complete decision.'
                return result
            low, high = bounds_at(counts)
            result['assignments_evaluated'] += 1
            if best_lower is None or low < best_lower:
                best_lower, lower_counts = low, counts
            if best_upper is None or high > best_upper:
                best_upper, upper_counts = high, counts
            if best_lower <= 0 <= best_upper and (best_lower != 0 or best_upper != 0):
                result.update(exact_decision=True, decision='unresolved',
                              reason='Attainable margins rule out both strict directions and an exact tie.',
                              witness_margin_interval=[best_lower, best_upper],
                              lower_class_counts=list(lower_counts), upper_class_counts=list(upper_counts))
                return result
    result.update(exact_decision=True, endpoints_complete=True, lower=best_lower, upper=best_upper,
                  lower_class_counts=list(lower_counts), upper_class_counts=list(upper_counts))
    result['decision'] = ('left_strict' if best_lower > 0 else 'right_strict' if best_upper < 0
                          else 'tie' if best_lower == best_upper == 0 else 'unresolved')
    return result
