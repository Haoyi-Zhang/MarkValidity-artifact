"""Exact incomplete-evidence calculations for a source/contract ledger.

This module consumes already admitted identities and labels. It does not decide
whether two source contracts are equal or whether an execution supports a label.
Weights are exact Fractions. They may be normalized workload weights or counts;
cross-system joint comparisons require the same intended units and denominator.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Mapping

ZERO = Fraction(0)


@dataclass(frozen=True)
class UnknownGroup:
    identity: str
    mass: Fraction
    detected_mass: Fraction

    def __post_init__(self):
        if not isinstance(self.identity, str) or not self.identity:
            raise ValueError('a nonempty admitted source-contract identity is required')
        if type(self.mass) is not Fraction or type(self.detected_mass) is not Fraction:
            raise ValueError('exact Fraction weights are required')
        if not ZERO <= self.detected_mass <= self.mass:
            raise ValueError('group weights require 0 <= detected mass <= total mass')


@dataclass(frozen=True)
class ScoreModel:
    known_joint: Fraction
    known_valid: Fraction
    unknown: tuple[UnknownGroup, ...]

    def __post_init__(self):
        if type(self.known_joint) is not Fraction or type(self.known_valid) is not Fraction:
            raise ValueError('exact Fraction weights are required')
        if not ZERO <= self.known_joint <= self.known_valid:
            raise ValueError('known weights require 0 <= joint mass <= valid mass')
        identifiers = [g.identity for g in self.unknown]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError('merge repeated source-contract groups before calculation')

    def mapping(self):
        return {g.identity: g for g in self.unknown}


def _bits(labels: Mapping[str, bool], identifiers: Iterable[str]):
    for identity in identifiers:
        if identity not in labels or type(labels[identity]) is not bool:
            raise ValueError('every requested completion must supply a Boolean label')


def evaluate(model: ScoreModel, labels: Mapping[str, bool]):
    """Return (joint mass, valid mass, conditional detection or None)."""
    _bits(labels, (g.identity for g in model.unknown))
    numerator, denominator = model.known_joint, model.known_valid
    for group in model.unknown:
        if labels[group.identity]:
            numerator += group.detected_mass
            denominator += group.mass
    return numerator, denominator, numerator / denominator if denominator else None


def reveal(model: ScoreModel, identity: str, validity: bool):
    """Move one resolved source group into the known part without changing weights."""
    if type(validity) is not bool:
        raise ValueError('an admitted Boolean label is required')
    mapping = model.mapping()
    if identity not in mapping:
        return model
    group = mapping[identity]
    return ScoreModel(model.known_joint + group.detected_mass * validity,
                      model.known_valid + group.mass * validity,
                      tuple(g for g in model.unknown if g.identity != identity))


def conditional_bounds(model: ScoreModel):
    """Sharp C bounds over positive-valid-mass binary completions, O(G log G).

    The result separately states whether C is defined for every completion.
    An empty valid set is undefined, never assigned conditional score zero.
    Endpoint witnesses set every source group once, including zero-weight groups.
    """
    positive = [g for g in model.unknown if g.mass > 0]
    base_labels = {g.identity: False for g in model.unknown}
    defined_everywhere = model.known_valid > 0
    defined_somewhere = defined_everywhere or bool(positive)
    if not defined_somewhere:
        return dict(lower=None, upper=None, defined_for_all_completions=False,
                    defined_for_some_completion=False, undefined_possible=True,
                    lower_completion=None, upper_completion=None)

    def extremum(descending):
        ordered = sorted(positive, key=lambda g: (g.detected_mass / g.mass, g.identity),
                         reverse=descending)
        numerator, denominator = model.known_joint, model.known_valid
        best = numerator / denominator if denominator else None
        best_prefix = 0 if denominator else None
        for size, group in enumerate(ordered, start=1):
            numerator += group.detected_mass
            denominator += group.mass
            value = numerator / denominator
            if best is None or (value > best if descending else value < best):
                best, best_prefix = value, size
        witness = dict(base_labels)
        for group in ordered[:best_prefix]:
            witness[group.identity] = True
        return best, witness

    lower, lower_completion = extremum(False)
    upper, upper_completion = extremum(True)
    return dict(lower=lower, upper=upper,
                defined_for_all_completions=defined_everywhere,
                defined_for_some_completion=True,
                undefined_possible=not defined_everywhere,
                lower_completion=lower_completion, upper_completion=upper_completion)


def different_unknown_groups(left: ScoreModel, right: ScoreModel):
    """Groups to resolve to obtain an equal-coefficient common remainder.

    These groups depend only on declared weights, detector observations and
    source identities. Selecting them does not inspect unrevealed validity.
    A group absent from one side has zero coefficients on that side.
    """
    a, b = left.mapping(), right.mapping()
    def coefficients(mapping, key):
        g = mapping.get(key)
        return (g.mass, g.detected_mass) if g is not None else (ZERO, ZERO)
    return tuple(key for key in sorted(set(a) | set(b))
                 if coefficients(a, key) != coefficients(b, key))


def joint_comparison(left: ScoreModel, right: ScoreModel):
    """Sharp bound on left joint mass minus right joint mass."""
    a, b = left.mapping(), right.mapping()
    constant = left.known_joint - right.known_joint
    coefficients = {key: (a[key].detected_mass if key in a else ZERO)
                    - (b[key].detected_mass if key in b else ZERO)
                    for key in set(a) | set(b)}
    lo = {key: value < 0 for key, value in coefficients.items()}
    hi = {key: value > 0 for key, value in coefficients.items()}
    lower = constant + sum((value * lo[key] for key, value in coefficients.items()), ZERO)
    upper = constant + sum((value * hi[key] for key, value in coefficients.items()), ZERO)
    relation = ('left_strict' if lower > 0 else 'right_strict' if upper < 0
                else 'tie' if lower == upper == 0 else 'unresolved')
    return dict(lower=lower, upper=upper, relation=relation,
                lower_completion=lo, upper_completion=hi)


def common_remainder_comparison(left: ScoreModel, right: ScoreModel):
    """Sharp conditional-order certificate after all coefficient differences resolve.

    Remaining unknown groups must have the same valid/detected masses on both
    sides. The returned interval is the cross-product margin N_L A_R-N_R A_L,
    NOT an interval for C_L-C_R. Their signs agree wherever both C values exist.
    """
    different = different_unknown_groups(left, right)
    if different:
        raise ValueError('unresolved coefficient-different groups: ' + ','.join(different))
    maps = left.mapping(), right.mapping()
    identities = sorted(set(maps[0]) | set(maps[1]))
    common = [(maps[0].get(key) or maps[1][key]) for key in identities]
    positive = [g for g in common if g.mass > 0]
    defined_everywhere = left.known_valid > 0 and right.known_valid > 0
    defined_somewhere = defined_everywhere or bool(positive)
    if not defined_somewhere:
        return dict(margin_lower=None, margin_upper=None,
                    relation_on_defined_completions=None, decision='undefined_everywhere',
                    defined_for_all_completions=False, defined_for_some_completion=False,
                    can_stop_for_strict_ordering=False, can_stop_for_equal_scores=False,
                    lower_completion=None, upper_completion=None)

    constant = left.known_joint * right.known_valid - right.known_joint * left.known_valid
    coefficients = {g.identity:
                    (left.known_joint - right.known_joint) * g.mass
                    + (right.known_valid - left.known_valid) * g.detected_mass
                    for g in common}
    lower_bits = {key: coefficients[key] < 0 for key in identities}
    upper_bits = {key: coefficients[key] > 0 for key in identities}
    if not defined_everywhere:
        # Both denominators are positive exactly when some positive-mass common
        # group is valid. The all-zero choice must not supply a spurious endpoint.
        if not any(lower_bits[g.identity] for g in positive):
            lower_bits[min(positive, key=lambda g: (coefficients[g.identity], g.identity)).identity] = True
        if not any(upper_bits[g.identity] for g in positive):
            upper_bits[max(positive, key=lambda g: (coefficients[g.identity], g.identity)).identity] = True
    lower = constant + sum((coefficients[k] * lower_bits[k] for k in identities), ZERO)
    upper = constant + sum((coefficients[k] * upper_bits[k] for k in identities), ZERO)
    relation = ('left_strict' if lower > 0 else 'right_strict' if upper < 0
                else 'tie' if lower == upper == 0 else 'unresolved')
    decision = relation if defined_everywhere else 'undefined_possible'
    return dict(margin_lower=lower, margin_upper=upper,
                relation_on_defined_completions=relation, decision=decision,
                defined_for_all_completions=defined_everywhere,
                defined_for_some_completion=True,
                can_stop_for_strict_ordering=defined_everywhere and relation in ('left_strict', 'right_strict'),
                can_stop_for_equal_scores=defined_everywhere and relation == 'tie',
                lower_completion=lower_bits, upper_completion=upper_bits)


def conditional_comparison(left: ScoreModel, right: ScoreModel):
    """Safe generic comparison, with a sharp route for a common remainder.

    Outside the common-remainder condition, separated individual sharp score
    intervals suffice but are not asserted necessary. The returned audit plan
    names the unresolved coefficient differences that enable the exact route.
    """
    required = different_unknown_groups(left, right)
    if not required:
        return {'route': 'exact_common_remainder', 'audit_groups_to_common_remainder': (),
                **common_remainder_comparison(left, right)}
    lb, rb = conditional_bounds(left), conditional_bounds(right)
    if not lb['defined_for_some_completion'] or not rb['defined_for_some_completion']:
        decision = 'undefined_everywhere_for_at_least_one_side'
    elif not lb['defined_for_all_completions'] or not rb['defined_for_all_completions']:
        decision = 'undefined_possible'
    elif lb['lower'] > rb['upper']:
        decision = 'left_strict'
    elif rb['lower'] > lb['upper']:
        decision = 'right_strict'
    elif lb['lower'] == lb['upper'] == rb['lower'] == rb['upper']:
        decision = 'tie'
    else:
        decision = 'unresolved'
    return dict(route='individual_sharp_intervals_sufficient_only', decision=decision,
                left=lb, right=rb, audit_groups_to_common_remainder=required,
                can_stop_for_strict_ordering=decision in ('left_strict', 'right_strict'),
                can_stop_for_equal_scores=decision == 'tie')
