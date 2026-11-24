"""Public-information policies for separately tailored comparison baselines.

The independent policies choose their own queries. They use the same legitimate
source-contract cache and reference admissions as the coupled method. Neither
policy receives an oracle, saved candidate label, measured duration, or future
observation. The joint policy minimizes independent width at fixed unit budget;
the conditional policy greedily minimizes the worst one-response width. Neither
is asserted to minimize the first-certificate cost.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction


class IndependentPairState:
    """Two independent score envelopes with shared propagation of received labels."""
    def __init__(self, api, left, right, denominator):
        self.api = api
        self.denominator = denominator
        self.left, self.right = api.ScoreState(left), api.ScoreState(right)
        if denominator <= 0 or self.left.unknown_valid != denominator or self.right.unknown_valid != denominator:
            raise ValueError('the two versions need the declared equal workload')
        self.groups = set(self.left.coefficients) | set(self.right.coefficients)
        self.pairs = {g: (self.left.coefficients.get(g, (0, 0)),
                         self.right.coefficients.get(g, (0, 0))) for g in self.groups}
        self.attempted, self.admitted = set(), {}

    def reveal(self, group, label):
        if group not in self.groups or group in self.attempted:
            raise ValueError('a query must select a previously unqueried group')
        if label is not None and type(label) is not bool:
            raise ValueError('the oracle response must be Boolean or unavailable')
        self.attempted.add(group)
        if label is None:
            return
        self.admitted[group] = label
        self.left.reveal(group, label)
        self.right.reveal(group, label)


def hypothetical_conditional(score, group, value):
    """Read-only exact individual interval after one hypothetical Boolean reply."""
    if type(value) is not bool:
        raise ValueError('counterfactual response must be Boolean')
    a, b = score.coefficients.get(group, (0, 0))
    if group not in score.unknown:
        a = b = 0
    known_n, known_b = score.joint + value * a, score.valid + value * b
    affected_ratio = Fraction(a, b) if b else None

    def extreme(reverse):
        n, mass = known_n, known_b
        best = Fraction(n, mass) if mass else None
        ratios = reversed(score.sorted_ratios) if reverse else score.sorted_ratios
        for ratio in ratios:
            add_a, add_b = score.buckets[ratio]
            if ratio == affected_ratio:
                add_a, add_b = add_a - a, add_b - b
            if not add_b:
                continue
            n, mass = n + add_a, mass + add_b
            q = Fraction(n, mass)
            if best is None or (q > best if reverse else q < best):
                best = q
        return best

    return extreme(False), extreme(True)


class IndependentJointWidth:
    """Largest a_L + a_R first, excluding groups irrelevant to both J scores."""
    def __init__(self, state):
        remaining = (g for g in state.groups - state.attempted
                     if sum(pair[0] for pair in state.pairs[g]) > 0)
        self.order = sorted(remaining,
                            key=lambda g: (-sum(pair[0] for pair in state.pairs[g]), g))
        self.index = 0

    def next_group(self, state):
        if self.index == len(self.order):
            return None
        group = self.order[self.index]
        self.index += 1
        return group


class IndependentConditionalWidth:
    """Minimize max_v [width(C_L | v) + width(C_R | v)] for the next query.

Groups with identical public coefficient pairs have identical objective values;
only their lexicographically smallest unqueried identity needs evaluation.
Ties use that identity. Empty defined-score sets have span zero, while the
separate decision function always retains undefinedness and cannot certify an
unconditional comparison from such a state. Primary runs have qualified valid
reference mass on both sides, so every counterfactual denominator is positive.
"""
    def __init__(self, state):
        classes = defaultdict(list)
        for group in state.groups - state.attempted:
            classes[state.pairs[group]].append(group)
        self.classes = [sorted(groups, reverse=True) for groups in classes.values()]

    def next_group(self, state):
        choices = []
        for groups in self.classes:
            while groups and groups[-1] in state.attempted:
                groups.pop()
            if not groups:
                continue
            group = groups[-1]
            costs = []
            for response in (False, True):
                width = Fraction()
                for score in (state.left, state.right):
                    lower, upper = hypothetical_conditional(score, group, response)
                    if lower is not None:
                        width += upper - lower
                costs.append(width)
            choices.append((max(costs), group))
        return min(choices)[1] if choices else None


def policy_name(method, target):
    if method == 'independent':
        return ('independent_joint_width' if target == 'J'
                else 'independent_conditional_minimax_width')
    if method == 'coupled':
        return 'joint_width_per_suite' if target == 'J' else 'conditional_differences_first'
    raise ValueError('unknown comparison method')


def initialize(api, coefficients, initial, method, target):
    left, right, denominator, order = coefficients
    if method == 'independent':
        state = IndependentPairState(api, left, right, denominator)
    elif method == 'coupled':
        state = api.PairState(left, right, denominator)
    else:
        raise ValueError('unknown comparison method')
    for group, value in sorted(initial.items()):
        if group in state.groups:
            state.reveal(group, value)
    if method == 'independent':
        policy = IndependentJointWidth(state) if target == 'J' else IndependentConditionalWidth(state)
    else:
        policy = api.AuditPolicy(policy_name(method, target), state, order)
    return state, policy


def target_bounds(api, state, method, target):
    """Evaluate only the requested target; no unused competitor bounds are timed."""
    if target == 'J':
        if method == 'coupled':
            lower, upper = state.joint.lower, state.joint.upper
        else:
            lower = state.left.joint - state.right.joint - state.right.unknown_joint
            upper = state.left.joint + state.left.unknown_joint - state.right.joint
        return dict(lower=lower, upper=upper, units='joint_count_difference',
                    decision=api.relation(lower, upper), defined_all=True)
    if target != 'C':
        raise ValueError('target must be J or C')
    if method == 'coupled' and state.margin is not None:
        result = state.common_conditional()
        return dict(lower=result['lower'], upper=result['upper'],
                    units='conditional_cross_product_count_margin',
                    decision=result['decision'],
                    defined_all=state.left.valid > 0 and state.right.valid > 0)
    left, right = state.left.conditional(), state.right.conditional()
    result = api.independent_conditional(left, right)
    return dict(lower=result['lower'], upper=result['upper'], units='conditional_rate_difference',
                decision=result['decision'], defined_all=left['defined_all'] and right['defined_all'])
