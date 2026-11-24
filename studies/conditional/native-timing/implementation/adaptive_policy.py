"""Conditional query selection from public score structure and admitted labels."""
from __future__ import annotations


class AdaptiveConditionalPolicy:
    """Use separate minimax acquisition when either defined C range is a point.

The singleton test can guide acquisition before positivity is established.
Stopping remains the responsibility of the denominator-aware certificate. Both
supplied policies receive only the public comparison state, never an oracle.
"""
    def __init__(self, state, difference_policy, independent_policy):
        self.difference_policy = difference_policy
        self.independent_policy = independent_policy
        self.branch_counts = {'point_interval_minimax': 0, 'coefficient_differences': 0}
        self.last_branch = None

    def next_group(self, state):
        intervals = [state.left.conditional(), state.right.conditional()]
        singleton = any(interval['defined_some'] and interval['lower'] == interval['upper']
                        for interval in intervals)
        branch = 'point_interval_minimax' if singleton else 'coefficient_differences'
        policy = self.independent_policy if singleton else self.difference_policy
        selected = policy.next_group(state)
        # The static H-first schedule can contain identities already selected
        # by the other branch. Its remaining fixed order is preserved.
        while selected is not None and selected in state.attempted:
            selected = policy.next_group(state)
        self.last_branch = branch
        if selected is not None:
            self.branch_counts[branch] += 1
        return selected
