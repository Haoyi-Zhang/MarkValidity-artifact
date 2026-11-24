"""Exact linear bounds with one shared validity label per source identity."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from typing import Hashable, Iterable


@dataclass(frozen=True)
class SourceGroupBounds:
    lower: Fraction
    upper: Fraction
    groups: int
    unknown_groups: int
    lower_completion: dict
    upper_completion: dict


def source_group_bounds(observations: Iterable[tuple[Hashable, Fraction, bool | None]]) -> SourceGroupBounds:
    """Bound sum_g c_g V_g after merging equal source/contract identities.

    Contributions may be signed, as in a difference between carrier yields.
    Repeated observations share V_g. A known label on any exact source closes
    its group; inconsistent labels are an evidence error, not a voting rule.
    """
    coefficients, labels = {}, {}
    for group, coefficient, validity in observations:
        if not isinstance(coefficient, Fraction):
            raise ValueError('exact Fraction coefficient required')
        if validity is not None and type(validity) is not bool:
            raise ValueError('known validity must be a Boolean')
        coefficients[group] = coefficients.get(group, Fraction()) + coefficient
        previous = labels.get(group)
        if previous is not None and validity is not None and previous != validity:
            raise ValueError('conflicting validity labels for the same source and contract')
        labels[group] = previous if validity is None else validity
    lower = upper = Fraction()
    lower_completion, upper_completion = {}, {}
    for group, coefficient in coefficients.items():
        label = labels[group]
        if label is None:
            lo, hi = coefficient < 0, coefficient > 0
            lower_completion[group], upper_completion[group] = lo, hi
            lower += coefficient * lo
            upper += coefficient * hi
        else:
            lower += coefficient * label
            upper += coefficient * label
    return SourceGroupBounds(lower, upper, len(coefficients),
        sum(label is None for label in labels.values()), lower_completion, upper_completion)
