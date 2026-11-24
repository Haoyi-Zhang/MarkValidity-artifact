# Fixed-budget width reduction for one source-group contrast

Fix one carrier pair, one workload, and its already accumulated coefficients
`c_g`. Let `U` be the unknown source-contract groups. Their binary labels are
otherwise unrestricted, so the comparison interval has width

`W = sum(abs(c_g) for g in U)`.

A query costs one unit and supplies the correct Boolean validity label of one
whole source-contract group. Assume queries always resolve their selected
group, the budget `b` is a nonnegative integer, and no additional cross-group
semantic constraints are introduced by an answer.

## Proposition

After querying a set `S` of at most `b` groups, the residual interval width is

`W(S) = W - sum(abs(c_g) for g in S)`

for every possible set of returned labels. Therefore querying the
`min(b, len(U))` groups with largest `abs(c_g)` minimizes residual width for
every outcome. No adaptive policy with the same budget can achieve a smaller
width on any outcome than this fixed selection.

## Proof

Before a query, the contribution of group `g` ranges between `min(0,c_g)` and
`max(0,c_g)`, a width of `abs(c_g)`. After a correct answer, it is the constant
`c_g * V_g`, of width zero. Other group labels remain unrestricted. The exact
groupwise endpoint formula therefore subtracts precisely `abs(c_g)` from
the interval width, regardless of the answer's value.

Summing over the queried set proves the displayed identity. On each realized
answer path, any adaptive policy selects a set of at most `b` groups. Its sum
of absolute coefficients is at most the sum of the largest `b` absolute
coefficients. The fixed largest-coefficient selection attains that sum on
every path, proving the claim.

If `b=0`, the width stays `W`. If `b >= len(U)`, the width becomes zero. A group
with coefficient zero never changes this contrast, even when its validity
is unknown. Equal-magnitude ties may be resolved arbitrarily. Already known
groups are not part of `U`.

## What this objective does not establish

The proposition concerns one fixed contrast and a fixed query budget. It
does not minimize the number of queries needed to certify a winner. For
example, take known gap `K=1/10`, unknown coefficients `c_1=3/5` and
`c_2=-2/5`, and actual labels `V_1=V_2=0`. Initially the interval is
`[-3/10,7/10]`. Querying the larger coefficient first leaves
`[-3/10,1/10]`, whereas querying group 2 first yields `[1/10,7/10]` and
immediately certifies a positive gap. The first query removes more width,
but the second removes the uncertainty relevant to this certificate.

For several carrier pairs, each pair has its own coefficients and width;
one ranking need not optimize them simultaneously. Heterogeneous query
costs, queries that can remain unavailable, and cross-group restrictions
also change the optimization problem. This priority is an audit-design
rule, not a probability sample of programs.
