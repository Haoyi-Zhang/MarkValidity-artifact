"""Shared evidence state with explicit completed no-output attempts.

The behavioral coefficient maps contain emitted candidates only. Terminal
E=0 attempts remain in the workload denominator and contribute known zero to
both operational valid mass and joint yield. They have no behavioral label.
"""
from __future__ import annotations


class OperationalPairState:
    """Reuse the tested algebra while allowing unequal emitted-row totals.

Both sides must account for the entire scheduled workload through emitted
coefficient mass plus explicitly counted completed no-output attempts. Missing
or interrupted emission records must not be passed as terminal zeros.
"""
    def __init__(self, api, left, right, denominator, *, left_terminal_zero, right_terminal_zero):
        if type(denominator) is not int or denominator <= 0:
            raise ValueError('scheduled workload must be a positive integer')
        if any(type(value) is not int or value < 0 for value in (left_terminal_zero, right_terminal_zero)):
            raise ValueError('terminal no-output counts must be nonnegative integers')
        self._api = api
        self.denominator = denominator
        self.terminal_zero = {'left': left_terminal_zero, 'right': right_terminal_zero}
        self.left, self.right = api.ScoreState(left), api.ScoreState(right)
        if self.left.unknown_valid + left_terminal_zero != denominator:
            raise ValueError('left emitted and completed no-output attempts do not cover the workload')
        if self.right.unknown_valid + right_terminal_zero != denominator:
            raise ValueError('right emitted and completed no-output attempts do not cover the workload')
        self.groups = set(self.left.coefficients) | set(self.right.coefficients)
        self.pairs = {g: (self.left.coefficients.get(g, (0, 0)),
                          self.right.coefficients.get(g, (0, 0))) for g in self.groups}
        self.joint = api.LinearState({g: l[0] - r[0] for g, (l, r) in self.pairs.items()})
        self.behavior = api.LinearState({g: l[1] - r[1] for g, (l, r) in self.pairs.items()})
        self.different = {g for g, (l, r) in self.pairs.items() if l != r}
        self.attempted, self.admitted, self.margin = set(), {}, None
        self._initialize_common_remainder()

    def _initialize_common_remainder(self):
        return self._api.PairState._initialize_common_remainder(self)

    def reveal(self, group, label):
        return self._api.PairState.reveal(self, group, label)

    def common_conditional(self):
        return self._api.PairState.common_conditional(self)

    def snapshot(self):
        return self._api.PairState.snapshot(self)
