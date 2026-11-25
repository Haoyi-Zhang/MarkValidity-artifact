# Null-calibration study (correlated, multi-query and repository-derived nulls)

Pre-declared protocol: `studies/null-calibration/protocol.json` (written before any detector was run on
the populations; its SHA-256 is recorded in every output file).

## Files

| File | Content |
| --- | --- |
| `controlled-correlated-null.json` | Part 1. Controlled 24-site detector (`src/covewm/benchmark.py`): acceptance threshold k*(n) for every surviving-site count n = 0..24 (confirmed by 325 detector calls); exact accept probabilities (fraction, 40-digit decimal, float) under the independent fair null, exchangeable beta-binomial nulls (rho grid), duplicated-site block nulls (n = 24); P(any of K accepts) for independent queries and the arbitrary-dependence bounds [p, min(1, Kp)]. |
| `sew-run.json` | Part 2 run record: environment, pinned stock SEW vendor hashes, the 1,003 declared keys (index order), row format, output-file hashes. |
| `sew-null-humaneval.jsonl.gz`, `sew-null-mbpp.jsonl.gz`, `sew-null-projects.jsonl.gz` | Part 2 raw results. One JSON line per unwatermarked source (164 HumanEval prompt+canonical solution, 427 sanitized MBPP references, 120 project modules of `corpus/transfer`): identity, availability, key-invariant structure (n_grades, n_syntax, n_sites), and `results[key_index] = [verdict, p, p_all, p_syntax, k_grades, k_syntax]` for every key (D = Watermark detected, N = No watermark evidence, I = Insufficient evidence, U = unavailable). |
| `crest-unmarked-programs.json` | Part 3. Retained CREST readings (`reference_detector`: RF, LogReg-L1, LogReg-L2 at the released fpr_1pct thresholds) on the unmodified programs of `studies/crest/accepted/{reference,gpt4o,qwen}/results.json`, bound by SHA-256. No model was re-run. |
| `summary.json` | All reported numbers: per-corpus/per-key false-positive counts and exact Clopper-Pearson intervals, any-key rates, 1,003-key distributions, p-value profile, agreement with the retained SEW `reference_detector` records, CREST per-head rates, and the Part 1 headline values. |

## Regenerate (from the artifact root)

```sh
python3 -B studies/null-calibration/exact_controlled_null.py --out results/null-calibration/controlled-correlated-null.json
# Python 3.12 with tree-sitter==0.23.2, tree-sitter-python==0.23.6 (POSIX; ~4 min with 16 workers)
python -B studies/null-calibration/run_sew_null.py --out results/null-calibration --workers 16
python3 -B -S studies/null-calibration/bind_crest_null.py --out results/null-calibration/crest-unmarked-programs.json
# needs scipy (Clopper-Pearson); e.g. the environment of studies/crest/requirements.txt
python -B studies/null-calibration/summarize_null_calibration.py --results results/null-calibration
```

`run_sew_null.py` refuses to overwrite existing raw files; regenerate into a new directory and compare.

## Verify (standard library only)

```sh
python3 -B -S studies/null-calibration/verify_null_calibration.py --results results/null-calibration
```

The receiver recomputes the Part 1 tables from first principles (exact fractions; Polya-urn recursion
for the beta-binomial; explicit block-word enumeration), re-derives the population identities, keys and
vendor hashes, recomputes every number of `summary.json` from the raw files, re-extracts the CREST
readings from the retained study files, and exits 1 on any mismatch.

## Scope

The SEW pairs of one source under different keys are not independent; per-key rates use sources as
units and the pooled 1,003-key rate is a point estimate only. The CREST GPT-4o/Qwen cohorts participate
in the upstream classifier data workflow, so their readings are not held-out false-positive estimates.
