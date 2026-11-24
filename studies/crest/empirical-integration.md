# CREST empirical extension: current received evidence

The current canonical studies are `accepted/reference` and `accepted/catalogue`.
The current published-program functional studies are `accepted/gpt4o` and
`accepted/qwen`. Generated-program validity uses the original mxeval prompt and
assertions with separate program and test namespace bindings. The original
entry object and its globals are retained, with no wrapper or value encoding.
The preceding typed observations are
retained under `contract-sensitivity/typed/gpt4o` and `contract-sensitivity/typed/qwen` as additional evidence, not
as the primary functional outcomes. Every number below is exported from the
current received records by `export_crest_tables.py`.

## Full attempted populations

`N` includes every scheduled input. `E=0` is a completed precheck rejection with
no output; it has zero operational output yield and no invented V/D label.
`Pass`, `Fail`, and `Unknown` describe emitted candidate suites. A joint output
is emitted, passes the original suite, and is detector-positive. The main
detector is the unchanged upstream random forest at its released operating point.

| Cohort | N | Input pass | Emitted | E=0 | Pass | Fail | Unknown | D+ | Joint count bounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Canonical, stock | 591 | 591 | 589 | 2 | 574 | 15 | 0 | 589 | [574, 574]/591 |
| Canonical, catalogue ablation | 591 | 591 | 589 | 2 | 589 | 0 | 0 | 456 | [456, 456]/591 |
| Published GPT-4o | 1138 | 948 | 1138 | 0 | 934 | 204 | 0 | 1138 | [934, 934]/1138 |
| Published Qwen | 1138 | 826 | 1020 | 118 | 761 | 258 | 1 | 1020 | [761, 762]/1138 |

## Preservation and usable output retention

Qualification uses only the original program's suite outcome. The table counts
all qualified inputs, including known no-output events. An emitted program
failure is a separate mechanism from failure to emit. Results for initially
failing programs remain in the full-population table and transition matrices.

| Cohort | Qualified originals | Qualified emitted | Retained | New suite failures | No output | Unknown | Joint retention bounds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Canonical, stock | 591 | 589 | 574 | 15 | 2 | 0 | ['574/591', '574/591'] |
| Canonical, catalogue ablation | 591 | 589 | 589 | 0 | 2 | 0 | ['152/197', '152/197'] |
| Published GPT-4o | 948 | 948 | 934 | 14 | 0 | 0 | ['467/474', '467/474'] |
| Published Qwen | 826 | 774 | 761 | 13 | 52 | 0 | ['761/826', '761/826'] |

## Corpus-specific outcomes

| Cohort | Corpus | N | Input pass | Output pass | New suite failures | Qualified no output | Output unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Canonical, stock | HumanEval | 164 | 164 | 159 | 5 | 0 | 0 |
| Canonical, stock | MBPP | 427 | 427 | 415 | 10 | 2 | 0 |
| Canonical, catalogue ablation | HumanEval | 164 | 164 | 164 | 0 | 0 | 0 |
| Canonical, catalogue ablation | MBPP | 427 | 427 | 425 | 0 | 2 | 0 |
| Published GPT-4o | HumanEval | 164 | 145 | 143 | 2 | 0 | 0 |
| Published GPT-4o | MBPP | 974 | 803 | 791 | 12 | 0 | 0 |
| Published Qwen | HumanEval | 164 | 130 | 104 | 1 | 25 | 0 |
| Published Qwen | MBPP | 974 | 696 | 657 | 12 | 27 | 1 |

## Causal diagnostics and catalogue tradeoff

All 15 stock failures on canonical inputs have three fresh, source-bound
interventions: the complete catalogue fails, removing the implicated rule
passes, and that rule alone fails. The 45 current native receipts are in
`accepted/causes/summary.json`. Default emissions reproduce the original
candidates exactly. Rule 46 accounts for 11 cases of invalid operand reordering;
rule 24 accounts for two API/name-binding cases; rule 20 removes a loop binding
used afterward; rule 38 captures a nested enumerate binding.

The catalogue ablation removes these four rule families only from embedding.
Detection still uses the complete upstream feature extractor and unchanged
classifiers. The ablation restores all 15 observed emitted-program failures,
while its RF-positive count falls from 589 to 456. This is a measured
post-diagnosis tradeoff, not a claim that the remaining rules are universally safe.

## Full-population audit comparisons

Both catalogues retain all 591 scheduled attempts, including their two known
no-output events. The emitted candidates form 739 actual source/contract groups;
439 groups occur in both catalogues. Identity includes original and candidate
text, the complete test contract, the observer, and the execution environment.
No terminal no-output event receives a fabricated behavioral group. Query
counts below come from retrospective disclosure of fresh measurements, not
native wall-time trials. All current shared C certificates use the paired
ratio envelope and its separate-interval fallback.

| Corpus | Head | J shared | J independent | C H-first | C independent | C adaptive |
| --- | --- | --- | --- | --- | --- | --- |
| HumanEval | rf | 9 | 128 | 52 | 3 | 3 |
| HumanEval | logreg_l1 | 1 | 120 | 46 | 2 | 2 |
| HumanEval | logreg_l2 | 1 | 120 | 46 | 2 | 2 |
| MBPP | rf | 16 | 336 | 117 | 2 | 2 |
| MBPP | logreg_l1 | 1 | 321 | 106 | 2 | 2 |
| MBPP | logreg_l2 | 1 | 321 | 106 | 2 | 2 |
| pooled | rf | 22 | 461 | 168 | 3 | 3 |
| pooled | logreg_l1 | 1 | 440 | 151 | 2 | 2 |
| pooled | logreg_l2 | 1 | 440 | 151 | 2 | 2 |

The H-first acquisition result remains visible as an ablation. The adaptive
rule uses only public interval structure: when either defined C interval is a
singleton, it selects the separate minimax query; otherwise it follows the
coefficient-difference policy. Stopping still requires positive denominators.
An independent Fraction implementation receives every paired certificate and
every query selection, without importing the production paired implementation.

## Execution and provenance

The generated-program study covers every published HumanEval and MBPP file for
both models: 164 + 974 per model, 2,276 inputs total. No syntax, source-quality,
output, or detector filtering changes the population. The original mxeval
assembly is `prompt + completion + newline + test + newline + check(entry_point)`.
The complete literal-assembly evaluation is retained under `contract-sensitivity/literal` as a
contract sensitivity study. The primary runner executes prompt plus completion
in program globals and binds the original entry object. It executes the
unchanged test in a shallow copy of those globals, then calls its check on the
original object. This separates namespace bindings while sharing imported
modules and original objects. Candidate globals are retained; arguments and
return values are never serialized. Resource limits are 10 CPU seconds, 15 wall seconds,
and 1 GiB address space; resource interruptions remain unavailable. Assertions
are enabled, hash seed and thread settings are fixed, and the worker environment
is probed with the same clean interpreter invocation used for every task.

NumPy and SymPy are available in the declared functional environment. Ten
small contract controls check recursive entry names, preserved program bindings,
native complex values, type objects, named tuples, Counters, numeric package
values, successful suites, witnessed failures, and
resource/harness unavailability. They are observer controls, not empirical
benchmark rows. Typed observations retain their original results and the two
explicit dependency amendments for auditability.

Input text uses UTF-8 decoding with Python universal-newline handling. All 974
GPT-4o MBPP archive files use CRLF and are submitted as LF text; the other 1,302
files already match the submitted UTF-8 bytes. No token-level repairs or
completion edits were applied. The provenance receiver checks archived bytes,
decoded input text, official test files, native requests, source files from the
retained generation stage, upstream implementation/model/threshold identities,
and the exact observer/environment of each original/candidate pair. Numerical
receiving independently validates native outcomes and every saved classifier
probability under the estimator's training-compatible library and class order.

Source feature extraction is additionally checked through the official CLI on
four selected original/candidate cases, including rejection and unmarked-positive
controls. This is a selected-pair conformance check, not an all-source independent
feature recomputation. The three released detector heads provide sensitivity
readings on the same programs, not three independent cohorts.

## Remaining unavailable observations

| Cohort | Task | Side | Interruption | Error |
| --- | --- | --- | --- | --- |
| Published Qwen | MBPP/747 | reference | -9 | null |
| Published Qwen | MBPP/747 | candidate | -9 | null |

## Evidence interpretation and source records

Four official MBPP entries (56, 349, 899, and 967) are named `check`; their test
texts also define `check(candidate)`. Literal assembly ends with `check(check)`.
All four official canonical solutions fail that assembly and pass the uniform
separate-bindings contract. The full two-model sensitivity study checks all
4,434 original/candidate observations: five input pairs (ten native labels)
change, all within these four entries, and original/candidate labels change
together. All other observations agree, including the Qwen timeout pair.
`contract-sensitivity/summary.json` records the complete difference set and all
eight model/task combinations. These execution-contract effects are not
classified as watermark-induced failures.

These public generated programs also appear in the original CREST classifier
data workflow. Available public assets do not establish that the complete
cohorts were held out from fitting. The fixed detector readings therefore
support utility and preservation analysis on these actual published programs;
they are not an independent held-out detector-generalization estimate. Input
detector controls likewise report observed numerators and available denominators,
not a population false-positive rate. Complete transitions, including initially
failing and unavailable originals, are in `empirical-tables.json`.

The functional claim is compliance with each original benchmark assertion
contract, not unrestricted semantic equivalence. The declared observer and
execution environment are part of every obligation's identity. The complete
pipeline requires no remote service or API token for embedding/detection.
ACW was inspected but its authenticated Sourcery dependency prevented a full
execution; it is not counted as an evaluated implementation.

Primary upstream implementation: https://github.com/niccap/crest . Its README
describes the associated work as submitted; no publication venue is inferred.
Official functional contracts and assembly: https://github.com/amazon-science/mxeval .
The retained mxeval license accompanies the contract files. No top-level CREST
license was present in the acquired repository; acquisition instructions should
preserve its provenance rather than assign a new license to vendor code/models.

The current deliverable should expose only the four current study directories
listed above as primary results. Retained generation records are provenance
inputs only; old standalone and typed behavioral labels do not compete with
the final functional outcomes. Source records and their acquisition instructions
must remain available for the provenance receiver. The paired comparison is
`accepted/comparison/summary.json`; the old comparison directory is historical.
