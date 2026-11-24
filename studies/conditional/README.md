# Paired conditional comparison

This directory contains the conditional comparison method, public query policy,
exact inference comparator, and the executable evidence used by the paper. The
behavioral group remains one emitted source under one reference and test
contract. Arithmetic classes accelerate inference without joining distinct
behavioral groups or sharing their labels.

## Method and evidence

`paired_conditional.py` computes the paired ratio envelope and keeps the separate
conditional interval certificate as a fallback. The two anchor envelopes are in
numerator count units, equal to the workload size times the normalized residual
function. They are not conditional rate differences. A strict ordering or an
exact tie is reported only when both denominators are positive for every
completion.

`adaptive_policy.py` uses the separate minimax query policy when either sharp
conditional interval is a point; otherwise it follows coefficient differences.
The selection rule uses public coefficients and admitted responses. The
point-interval test can guide acquisition before positivity is established,
while the stopping rule always checks positivity.

`operational_state.py` accounts for completed attempts that emit no candidate.
Such attempts have emission indicator zero and contribute known zero to usable
output and joint yield. They remain in the scheduled workload. Their behavioral
and detection labels are not applicable. An unaccounted or interrupted attempt
cannot be supplied as a completed no-output attempt.

`exact_residual_conditional.py`, through `compare_classes`, partitions unresolved
coefficient differences by their full left/right coefficient quadruple. It
enumerates the attainable valid-label count of each class and optimizes the
common remainder exactly. Attained incompatible signs can establish that the
comparison is unresolved before full endpoint enumeration. The output separates
an exact decision, complete endpoints, and an exhausted assignment budget.

The retained studies answer distinct questions:

| Evidence | Question answered |
| --- | --- |
| `paired-study/` | When do paired and common-remainder certificates first stop on the same actual response sequence? |
| `class-comparison-study/` | Can exact inference stop earlier than the inexpensive paired envelope on those recorded sequences? |
| `native-validation/` | Do fresh executions, raw records, and independent receiving agree with the intended selections and certificates? |
| `native-timing/` | What is the audit cost of the current policy and the separate minimax baseline under balanced serial execution? |
| `paper-materials/` | Which exact received endpoints and query counts generate the conditional figure and comparison table? |

The paired study contains 36 comparisons across two initializations. Paired
certificates stop earlier than the common-remainder ablation in 28 comparisons
and at the same prefix in the remaining eight. The current adaptive policy
selects the same queries as the coefficient-differences policy on these SEW
ledgers. The exact class comparator receives all 8,746 prefixes: 8,672 have an
exact comparison decision and 74 permit a zero denominator. It exhausts no
assignment budget, and its first certificates agree with the paired envelope in
all 36 comparisons. This is an earliest-prefix result for the recorded query
sequences, rather than an optimality claim about all query policies.

The four-run native validation contains 1,823 fresh candidate suite executions.
Its independent receiver checks every raw record, query, prefix, and first
certificate. Its durations are excluded from performance comparisons because
the runs were execution checks. Performance results use the separate balanced
block of 24 runs: two cases, two methods, and six repetitions, with each method
first three times and second three times within each case.

The balanced conditional block contains 10,938 fresh candidate suites and
10,962 received prefixes. HumanEval requires 154 suites with shared comparison
and 532 with separate comparison; the median audit times are 5.146 and 20.346
seconds. MBPP requires one and 1,136 suites, with medians of 0.042 and 47.877
seconds. Every run and phase remains in the native records. The paper reports
the six-run ranges alongside these medians.



## Reproduction

Run the commands below from the project root. The shared `artifact/run.py` entry point prepares an isolated working copy, resolves the clean input paths to their recorded locations, and saves new outputs outside the project. Choose a new output directory for each invocation.

Receive the retained balanced native experiment:

```sh
python3 artifact/run.py --output ../conditional-receiving \
  studies/conditional/verify_native_conditional.py -- \
  --artifact . --registry results/sew/public-registry.json \
  --native studies/conditional/native-timing --out '{output}'
```

The received JSON is saved as `results.json`, alongside `run.json` and `run.log`. The receiver checks the raw program observations, exact source and contract bindings, every selected query and prefix, denominator positivity, the first certificate, and the balanced execution order. For the four-run correctness study, use `--native studies/conditional/native-validation` with a different output directory.

Recompute the 36 comparison traces from the retained paired observations:

```sh
python3 artifact/run.py --output ../conditional-replay \
  studies/conditional/evaluate_paired_conditional.py -- \
  --artifact . --adaptive --out '{output}'
```

This command discloses already measured observations in the current public query order. It writes the new trace collection under `results/`. To inspect the exact comparator on the retained trace collection:

```sh
python3 artifact/run.py --output ../conditional-exact \
  studies/conditional/evaluate_class_comparison.py -- \
  --artifact . --study studies/conditional/paired-study/study.json \
  --assignment-budget 1000000 --out '{output}'
```

Acquire new native observations with the current policy and separate minimax baseline:

```sh
python3 artifact/run.py --output ../conditional-native \
  studies/conditional/run_native_conditional.py -- \
  --artifact . --registry results/sew/public-registry.json \
  --repeats 6 --out '{output}'
```

Run the timing producer serially, without concurrent experimental workloads. Each repetition executes its own candidate suites. The measured audit includes coefficient construction, query selection, comparison inference, native candidate execution, receipt admission and recording through the first certificate. Generation, detector evaluation and reference qualification precede the audit; common public registration is reported separately.

The main scientific check also runs the finite mathematical, indexed-update, adaptive-selection and emission-accounting controls. These validate inference and evidence admission. Program-preservation and timing results come from the separately retained execution records.
