# Result-only admission for the frozen Python carriers

The receiver selects one of the twelve trusted task definitions. The candidate
must parse and compile as exactly that ordinary function, with an additional
prefix of at most 24 statements. After deleting the prefix, its complete
module AST, including signature and every functional statement, must equal the
receiver reference AST. A marker is an actual immediately preceding comment
token; a string or a different site identifier cannot supply it.

The only admitted prefix statements are a fresh local integer-zero assignment,
an `if False` with a sole `pass`, or an empty-tuple `for` with a sole `pass` and
no else. The assignment/loop name is absent from every reference name and
argument, has the declared indexed spelling, and is not reused. Site indices
are distinct and increasing. The integer-zero check excludes Boolean constants.

## Erasure lemma

Under ordinary Python result-only execution of the trusted task on its declared
builtin-input domain, without frame/reflection observation or resource-failure
observations, an admitted candidate has the reference result and termination
behavior. No candidate program needs to execute to establish this relation.

Proof: a zero assignment terminates and changes only a fresh, unread local. Its
compile-time local binding cannot shadow a reference name. A false branch has
no executed body, and an empty tuple loop has no iterations; its target is also
fresh. Erasing the prefix therefore preserves the reference state on every
name it can observe. Induction over prefix length reaches the identical
remaining function body, whose execution starts with the same observable
state. The module/signature equality excludes altered defaults, decorators,
top-level effects and changed functional code. The same argument covers the
empty prefix and deletion of any subset of carrier sites.

The registry's lack of introspection and external frame observations is a
premise, not something proved for arbitrary Python by a name denylist. It was
checked for these twelve frozen references. The result does not promise equal
timing, memory, local-variable dictionaries, tracing events, code objects, or
arbitrary contextual equivalence. It does not apply to JavaScript or to external
watermark implementations.

A candidate outside the sufficient grammar has **unavailable** validity under
this proof rule. Rejection is not by itself a semantic counterexample. Parsing
or compilation failure, or a source-bound bounded-execution mismatch, instead
**contradicts** the semantic gate. Complete matching execution or successful
restricted erasure **supports** it. Malformed, stale, or source-inconsistent
evidence is refused before a semantic judgment is made.

## Decision linkage and fair comparison

Only after admission does the consumer read actual indexed syntax and use it
in the existing detector. Each rendered source is identified separately from
its indexed model; disagreement stops analysis. Exact repeated source bytes
under the same receiver task may reuse their AST admission, not an unrelated
semantic label. This gives source-bound proof-derived admission rather than
new executed validity labels. Historical 432 executed dense links and their
75,600 missing labels remain historical.

The original marker regex is only an extraction control, not an equally strong
semantic baseline. Inserting division by zero into a carrier assignment can
leave its extracted bits unchanged. The new gate rejects the statement. A
direct receiver applying the same AST-erasure contract has the same information
and can make the same decision without a certificate; no detection-accuracy,
runtime or information advantage over that receiver is claimed.

## Source-identity reuse

Validity belongs to the receiver reference, candidate source, input domain,
runtime, initialization rule and observation rule. Exact equality of this tuple permits a retained
label to be reused across configurations with different attack, payload or
carrier metadata. The origin of the label remains execution or proof; reuse
does not increase the execution count. Contradictory admitted labels in one
source-contract group invalidate the evidence join.

The current standalone execution receiver requires a fresh module instance
for each input and tagged observations that distinguish a returned JSON value
from an exception. Reusing one function across an ordered test batch does not
establish this pointwise contract: a program can read its call counter instead
of its input and nevertheless match that batch. The counterexample and its
regression checks accompany the artifact. A new observation identifier and
initialization identifier keep these records distinct from the archived
batch observations. The archived identifiers are not changed retroactively.

Fresh module initialization recreates the function, module namespace,
defaults and builtin mapping before each input. The execution harness is for
owned terminating programs without ambient external-state dependence; it
does not isolate arbitrary code from the host. Every accepted return or
exception is serialized before the next call. Full matching execution
establishes the finite relation when each guarded invocation completes;
finiteness of the input set alone does not decide arbitrary termination.

All source decisions must be read from the candidate text before a complete
source-joint bound is reported. Fair-bit detector calibration remains a
conditional null statement; the erasure proof does not establish a null model
for arbitrary source corpora or adaptively selected surviving sites.

## Sharp pairwise bounds with a shared source label

Let each configuration have a fixed nonnegative weight `lambda_si`, summing to
one within carrier `s`, and an actual-source detector decision `D_si`. For each
source-contract group `g`, accumulate

`c_sg = sum(lambda_si * D_si for i in group g)`.

Joint source-valid detection yield is `J_s = sum(c_sg * V_g)`, not detection
conditional on validity. For carriers A and B, put `delta_g = c_Ag - c_Bg`.
Known labels contribute `K = sum(delta_g * V_g for known groups)`. Unknown
groups contribute either zero or `delta_g`, giving exact endpoints

`lower = K + sum(min(0, delta_g) for unknown groups)`

`upper = K + sum(max(0, delta_g) for unknown groups)`.

Choosing each unknown label by the sign of its coefficient attains the
corresponding endpoint. Hence the bounds are sharp over binary completions
that preserve source identity and impose no additional cross-group constraints.
This does not assert realizability of every completion by executable programs.
Carrier A has a strict lead over every competitor for every allowed completion
exactly when each of its pairwise lower endpoints is positive.

Computing separate carrier intervals and subtracting them need not preserve
shared validity. If one unknown source contributes `0.4 * V_g` to both carriers,
that contribution cancels from their difference. Pairwise coefficient
accumulation preserves the cancellation. The implementation therefore groups
sources before applying signed completion bounds.
