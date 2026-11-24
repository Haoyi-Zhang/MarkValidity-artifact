# Conditional targets and version-comparison certificates

The source-contract ledger supports joint yield and detection conditional on
validity. The following constructions make the conditional target and its
cross-version comparison executable before every group label is available.

## 1. Define the target before comparing versions

For a fixed attempted configuration universe with nonnegative weights, record
validity `V`, detection `D`, and the source/contract identity to which `V` applies.
For version `s`, let `J_s = sum_i w_si V_i D_i` and
`A_s = sum_i w_si V_i`. The conditional target is `C_s = J_s / A_s` when
`A_s > 0`. Joint yield measures valid detected outputs per attempt; conditional
detection measures detected outputs among valid ones. A repair can increase
valid mass and alter either rate, so the choice between these targets belongs
to the stated evaluation question.

Every source/contract group has one Boolean label. After all admitted labels
are accumulated, write

\[
 N_s(v)=n_s+\sum_{g\in U}a_{sg}v_g,\qquad
 B_s(v)=b_s+\sum_{g\in U}b_{sg}v_g,
 \quad 0\le a_{sg}\le b_{sg}.
\]

Here `n_s` and `b_s` are known joint and valid masses. Unknown-group valid mass
`b_sg` includes every weighted occurrence of the source, and detected mass
`a_sg` includes its detected occurrences. A group can contain configurations
with different keys and detector outcomes. Counting one validity obligation
does not remove repeated configurations from their intended denominator.

The implementation accepts exact rational coefficients. It assumes that the
upstream receiver has established group identity and admitted known labels;
it does not infer reference or contract equality from a candidate hash alone.

## 2. Sharp conditional bounds require the common labels

For a single version, order positive-mass unknown groups by
`r_g = a_sg / b_sg`. Scan the empty set (if `b_s > 0`) and successive prefixes
in increasing order. The smallest resulting ratio is the sharp lower endpoint.
Scanning in decreasing order gives the sharp upper endpoint. Zero-mass groups
have no effect. The two sorts and scans use `O(|U| log |U|)` rational comparisons.

**Proof.** A minimum exists among the finitely many completions with a positive
denominator. Let its ratio be `q`. An excluded group with `r_g < q` could be
added to lower the ratio, contradicting minimality. An included group with
`r_g > q` could be removed to lower it; removing the last positive-mass group
cannot be such a case because its ratio would then equal `q`. Thus an optimum
includes every group below its own ratio and excludes every group above it.
Groups equal to the ratio can be added or removed without changing the score.
An increasing-order prefix therefore attains the minimum. Reversing the
inequalities proves the maximum. The implementation returns complete Boolean
endpoint witnesses, not only endpoint values.

When no known valid mass is present, the empty completion makes `C_s`
undefined. Endpoints over positive-mass completions may still exist, but the
receiver must report this possible undefinedness. If neither known nor unknown
positive valid mass is available, there is no conditional score or interval.
In particular, `0/0` is never assigned zero.

These are sharp endpoints over the declared independent binary group-label
completion set. Additional semantic constraints can make that completion set
smaller. Independent numerator and denominator endpoint division does not use
the shared labels and generally fails to give the sharp conditional interval.

## 3. Audit differences, then retain a common unresolved remainder

Consider two versions `L` and `R` evaluated on the same intended workload.
Define the coefficient-disagreement set

\[
 H=\{g\in U:(a_{Lg},b_{Lg})\ne(a_{Rg},b_{Rg})\}.
\]

Group absence on one side means zero coefficients on that side. `H` depends on
source identities, observed detector outcomes and declared weights, not on
unrevealed validity labels. Resolving groups in `H` to admitted Boolean labels removes
them from both unknown sets. An unavailable response leaves the group unresolved. Remaining unknown groups then have common coefficients
`(a_g,b_g)`. A changed source that is used repeatedly still creates one
validity obligation under one reference and test contract.

The joint difference immediately becomes the known constant `n_L - n_R`.
For conditional detection, put `X = sum_g b_g v_g` and
`Y = sum_g a_g v_g`. Cross multiplication gives

\[
 C_L(v)-C_R(v)
 =\frac{M(v)}{(b_L+X)(b_R+X)},
\]
\[
 M(v)=n_Lb_R-n_Rb_L
       +\sum_{g\in U}\big[(n_L-n_R)b_g+(b_R-b_L)a_g\big]v_g.
\]

The quadratic common terms cancel. If both `b_L` and `b_R` are positive, every
completion has positive denominators. Writing the bracketed coefficients as
`h_g` and the constant as `k`, the sharp margin endpoints are

\[
 M_{\min}=k+\sum_g\min(0,h_g),\qquad
 M_{\max}=k+\sum_g\max(0,h_g).
\]

`M_min > 0` is necessary and sufficient for a strict left-over-right ordering
throughout the completion set; `M_max < 0` gives the reverse. Both endpoints
zero establish equality throughout. Any other case retains an unresolved
strict comparison. These endpoints bound the **cross-product margin**, not the
numerical difference between conditional rates.

**Proof.** Expanding `(n_L+Y)(b_R+X)-(n_R+Y)(b_L+X)` cancels the `XY` terms and
gives the displayed affine expression. Independent endpoint choices attain
the minimum and maximum. The two conditional-score denominators are positive,
so their difference has exactly the margin's sign. A nonpositive minimum
supplies an attainable tie or reversal; hence the strict-order criterion is
also necessary under this completion model.

If either known valid mass is zero, both ratios exist precisely when at least
one positive-mass common group is valid. The implementation optimizes the
margin over this nonempty completion set: when the unrestricted minimizing
choice selects no positive-mass group, choose a single group with smallest
`h_g`; apply the symmetric largest-coefficient rule for the maximum. It still
records that an undefined completion remains possible. A strict ordering only
on the defined subset is not returned as an unconditional winner.

## 4. An executable stopping procedure

1. Receive source/contract identities, detector outcomes, declared weights and
   sound labels; keep unavailable labels as unknown.
2. Compute joint comparison bounds and single-version sharp conditional bounds.
   If `H` is already empty, also compute the common-remainder margin. A
   certificate can therefore be returned before any additional query.
3. If a conditional comparison remains unresolved, identify `H`. Acquire the
   declared evidence for its groups, updating both versions after each label.
   Stop early if the current evidence already certifies the requested target.
4. When every label in `H` is resolved, apply the common-remainder certificate. Return a
   strict direction, equality, unresolved comparison, or possible undefinedness.
   Additional common groups follow the declared margin-coefficient order.
   Stop unresolved when the budget or unqueried-group queue is exhausted.

No validity guesses determine `H`. No optimal-cost claim is made for this
audit plan. It provides a sufficient way to reach an exact comparison rule
and can save tests when the two versions share many source obligations. The
number of saved program runs, the size of `H`, and actual early stopping are
empirical outcomes to measure on the natural-code ledger.

## 5. Two small examples establish what the extension adds

**Intervals overlap although the conditional order is fixed.** Let known
`(n_L,b_L)=(4,5)`, `(n_R,b_R)=(3,5)` and one common unknown group have
`(a,b)=(0,5)`. Individual sharp conditional intervals are `[2/5,4/5]` and
`[3/10,3/5]`, whose separately subtracted interval is `[-1/5,1/2]`. The shared
completion gives conditional gaps `1/5` or `1/10`, both positive. Its margin
is `5+5v`, so the comparison is certified without learning the common label.

**Joint and conditional conclusions answer different questions.** Let known
parts be `(2,8)` and `(1,5)`, with common unknown `(a,b)=(2,2)`. The joint
numerator difference is always one. For an invalid common group, conditional
scores are `1/4` and `1/5`, favoring the left. For a valid group they are `2/5`
and `3/7`, favoring the right. The common group's coefficient is
`(2-1)*2+(5-8)*2=-4`, so the exact margin is `2-4v`, producing values `2` and
`-2`. The completion evidence therefore supports a joint ordering while
leaving the conditional ordering unresolved.

The examples are mathematical controls, not added empirical program trials.
`examples.json` records their exact models and endpoint witnesses.

## 6. Verification

`conditional_bounds.py` supplies the calculation and receiving primitives.
`verify_conditional_bounds.py` checks the formulas against independent complete
Boolean enumeration, including exact endpoint witnesses and undefined scores.
`verification.json` records the actual counts and source hashes.

The optimized natural-ledger implementation is `natural_analysis.py`. Its
independent completion and policy controls are in `verify_natural_analysis.py`.
The natural-result receiver rebuilds each certificate prefix from raw row
coefficients and checks it with this Fraction implementation. File names, cost
units, trace fields and reproduction commands are specified in `README.md`.
