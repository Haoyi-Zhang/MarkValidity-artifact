# Complete JavaScript execution under the fresh-input contract

This directory completes the behavioral labels of **every JavaScript source
identity** in the saved source inventory. It preserves the earlier
`revision-source-joint` result as a partial-evidence policy and adds measured
labels under an explicit new observation contract.

## What ran

The producer read the saved source text and executed 22,095 candidate identities
on their complete frozen input domains: **60,758,192 candidate input calls**.
Every candidate matched its reference on that domain. Twelve separately
executed references account for 33,013 further calls; 36 owned JavaScript
mutants account for 99,039 further calls. The references and mutants also ran
on 244 nominal inputs in total. All 36 mutants differ on the full domain;
three still pass their nominal inputs. These controls are counted separately
from the 22,095 candidate sources.

For every input, a previously compiled source factory is invoked to create a
new function/module instance. Return observations use
`{"kind":"return","value":...}`; exceptions use
`{"kind":"exception","type":...,"message":...}`. This distinguishes a
returned exception-shaped object from a thrown exception. The exact IDs are
`covewm-tagged-return-or-exception-type-and-message-canonical-json-v2` and
`covewm-fresh-module-instance-per-input-v1`.

The runner is for trusted owned code. Before execution, the producer requires
the complete frozen reference body and an exact finite grammar of local prefix
statements. It rejects added top-level code, changed reference bodies and
ambient writes in that prefix. Inputs are immutable primitive strings and
safe integers; standard builtins are trusted. The source gate is an execution
isolation restriction. Every reported behavioral label still comes from the
complete native calls, not from a JavaScript equivalence claim or the state
model.

## Retained evidence

- `registration.json`: source/data/producer hashes, the new contract, runtime
  fingerprint, selection and resource limits.
- `reference-domains.json.gz`: exact reference programs, full input lists,
  nominal inputs and the registered mutant programs.
- `raw/<task>.jsonl.gz`: the native stream. Every source has its own measured
  record. Full typed observation vectors are retained once per identical
  vector **after execution and elementwise comparison**. The 48 vectors contain
  132,052 stored observations; candidate records point to their measured
  vectors. This storage deduplication does not reduce the recorded call count.
- `execution.json`: actual Node task start/finish records and measured task
  wall times, including Node resource-usage counters.
- `source_labels.csv`: the 22,095 exact source labels, reference/domain/output
  bindings and per-source domain-call costs.
- `completed_rows.csv.gz`: the full 76,032-configuration joint target. JavaScript
  labels use this fresh execution; Python labels use the restricted erasure
  proof. The fresh-compatible Python proofs are rechecked for all 22,054 saved
  Python identities in the separate `revision-audit-budget` study.
- `family_scores.csv`, `mixture_scores.csv`, `pairwise_gaps.csv`: exact completed
  values and comparison with the earlier partial-evidence endpoints.
- `previous_execution_links.csv`: all 252 original JavaScript audit rows bind
  to source identities executed here. The old behavioral flags are retained
  as history and do not provide the new labels.
- `verification.json`: independent receiving and numerical reconstruction.
- `fresh_cross_language_parity.csv` and `.json`: value-by-value equality of the
  new Python and JavaScript reference observations on 33,013 domain inputs
  and 61 nominal inputs, using the separately executed Python study.

The completed full-grid joint yield is **4471/9504 = 0.470433501684**. This is the
former upper endpoint because every remaining candidate was measured valid.
All 27 completed mixture values and all 27 pairwise gaps fall inside the earlier
intervals. The balanced combined comparison now identifies lexical over
structural by **7/10560 = 0.000662878788**. The two targeted workload winners
remain structural and lexical, respectively. The supplied three-workload
comparison excludes the formatting control; the full-grid yield includes all
six attack families.

These observations establish fresh-contract results for these frozen sources.
They do not assert that arbitrary stateful programs retain their old labels
when initialization or observation rules change.

## Reproduce and verify

From `artifact/`, choose a new output directory:

```sh
python3 -B -S complete_javascript_sources.py --out /absolute/fresh/native-completion --workers 2
python3 -B -S verify_javascript_completion.py --out /absolute/fresh/native-completion
```

To verify the delivered data without executing task programs:

```sh
python3 -B -S verify_javascript_completion.py
python3 -B -S -m unittest discover -s tests -p 'test_javascript_completion.py' -v
```

The saved-data receiver imports neither the native producer nor its
renderer. It reopens stored observation vectors, checks complete source/input
coverage and contract bindings, reconstructs behavioral labels, and recomputes
the joint scores. The AST proof rule is used elsewhere explicitly; the native
producer is trusted to have performed its recorded calls. Hashes identify the
records and inputs and are not remote execution attestation.

The recorded `summary.wall_seconds` of 77.270838 seconds covers the measured
producer phase beginning after source inventory/gate validation and runtime
fingerprinting and ending after aggregation, with two Node workers. It is not
a stopwatch around the whole Python command. Per-task measurements are in
`execution.json`; exact input-call counts are the primary portable cost measure.
