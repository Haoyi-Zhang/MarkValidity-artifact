# Edit similarity on real watermark edits

**Question.** On the candidates that real watermark pipelines (CREST rewrite catalogue, SEW keyed style
watermark) actually emitted, does source distortion between the qualified reference and the candidate
separate behaviorally invalid (contradicted) candidates from valid (supported) ones? This answers the
concern that the controlled contrast (large no-op edits vs. small mutants) is constructed.

**Protocol.** `studies/edit-similarity/protocol.json` (status `PRE_DECLARED`, declared 2026-11-25T09:38:00Z,
SHA-256 `4690e1b5b2c3d248db9575d91addf3abdad2ae875fd63e1541f91918168649da`). It fixes the populations, label
and exclusion rules, the instrument (`covewm.metrics.source_metrics`, distortion = 1 - similarity), the
statistics (AUROC, medians, task-cluster bootstrap with 2,000 replicates and seed 20261125) and the
interpretation rule: AUROC in [0.4, 0.6] means distortion does not separate validity, > 0.6 means
distortion is associated with invalidity, < 0.4 means an inverse association.

## Commands (from the artifact root)

```
python3 -B -S studies/edit-similarity/run_edit_similarity.py --out results/edit-similarity
python3 -B -S studies/edit-similarity/verify_edit_similarity.py --out results/edit-similarity   # prints PASS
```

## Files

| File | Content |
|---|---|
| `studies/edit-similarity/protocol.json` | Pre-declared protocol |
| `studies/edit-similarity/run_edit_similarity.py` | Producer (stdlib + `artifact/src/covewm/metrics.py`) |
| `studies/edit-similarity/verify_edit_similarity.py` | Independent verifier: recomputes records from the raw sources and every summary number from `records.csv` |
| `records.csv` | 9,403 units: population, task, variant/key or cohort, source paths and SHA-256s, label, identical flag, seven distortions |
| `summary.json` | All statistics, counts, exclusions by reason, input and protocol SHA-256s |

## Headline results

Units (valid / invalid): CREST reference 574 / 15; CREST GPT-4o 934 / 14; CREST Qwen 761 / 13; CREST pooled
2,269 / 42 (32 invalid task clusters); SEW HumanEval 1,968 / 0; SEW MBPP 5,118 / 6 (2 tasks: MBPP/290 and MBPP/393).

AUROC of distortion for predicting invalidity, with a 95% task-cluster bootstrap interval:

| Instrument | CREST ref | CREST GPT-4o | CREST Qwen | CREST pooled | SEW (HE+MBPP) |
|---|---|---|---|---|---|
| character | 0.564 [0.404, 0.714] | 0.670 [0.548, 0.776] | 0.735 [0.633, 0.824] | 0.655 [0.565, 0.734] | 0.525 [0.486, 0.553] |
| token | 0.617 [0.484, 0.753] | 0.789 [0.722, 0.853] | 0.759 [0.676, 0.840] | 0.730 [0.666, 0.791] | 0.870 [0.845, 0.891] |
| identifier-normalized | 0.616 [0.476, 0.756] | 0.773 [0.664, 0.859] | 0.744 [0.626, 0.846] | 0.719 [0.642, 0.788] | 0.802 [0.770, 0.826] |
| AST type | 0.496 [0.336, 0.666] | 0.580 [0.469, 0.694] | 0.506 [0.377, 0.654] | 0.533 [0.447, 0.621] | 0.825 [0.801, 0.848] |
| control profile | 0.463 [0.424, 0.532] | 0.478 [0.437, 0.553] | 0.472 [0.424, 0.563] | 0.471 [0.438, 0.512] | 1.000 [1.000, 1.000] |
| identifier multiset | 0.538 [0.394, 0.692] | 0.490 [0.391, 0.601] | 0.505 [0.386, 0.640] | 0.524 [0.434, 0.609] | 0.989 [0.982, 0.994] |
| identifier style | 0.532 [0.375, 0.691] | 0.515 [0.411, 0.641] | 0.537 [0.413, 0.676] | 0.540 [0.455, 0.625] | 0.440 [0.430, 0.449] |

Under the pre-declared rule, pooled CREST shows distortion associated with invalidity for character,
token and identifier-normalized distortion, and no separation for the four profile and identifier
instruments. Character distortion of the pooled CREST invalid units: 2 of 42 lie below the 10th percentile
of valid units ("small faulty edits"); 176 of 2,269 valid units lie above the 90th percentile of invalid
units ("large harmless edits"). SEW has 6 invalid units from 2 tasks. Its AUROCs and intervals are therefore
unstable: 271 of 2,000 bootstrap replicates were skipped, and the intervals of the replicates that were kept
condition on both invalid tasks being drawn. Medians, per-population counts and SEW sub-populations are in
`summary.json`.

## Scope and limitations

- Labels are finite-suite contracts: "valid" means the candidate passed the task's retained suite, not
  that it is semantically equivalent to the reference.
- The populations contain only the edits these two pipelines emit on HumanEval and sanitized MBPP. Invalid
  units are few: 42 for pooled CREST and 6 for SEW.
- The CREST cohorts took part in upstream detector development. That does not affect the behavior labels
  used here, which come from executed native receipts.
- CREST rows carry no source hash. Integrity is checked by requiring each archived source file to equal,
  or be a suffix of, the program text in the native execution request that produced the label. SEW sources
  are checked against the SHA-256 values recorded in their rows.
