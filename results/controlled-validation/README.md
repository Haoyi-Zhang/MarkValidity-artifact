# Controlled-validation study (reviewer comments R2 and R6)

Protocol (written and frozen before any result was computed):
`studies/controlled-validation/protocol.json`. Code: `studies/controlled-validation/`.

```sh
# from artifact/ ; Node.js on PATH (or $NODE) only for the compile-only JavaScript syntax check
python3 -B studies/controlled-validation/run_study.py --out results/controlled-validation      # ~40 s
python3 -B -S studies/controlled-validation/verify_controlled_validation.py --results results/controlled-validation  # ~45 s
```

The verifier (stdlib only) recomputes every number in `summary.json` and every
derived CSV from the per-configuration records and
`results/controlled/raw/robustness.csv`, re-runs all 51,840 text-level attacks
and extractions (Python and JavaScript sources are transformed and extracted in
pure Python), re-checks Python syntax with `compile()`, and re-checks JavaScript
syntax with Node when available. Without Node it prints an explicit `SKIPPED`
line for that one check (`--require-node` makes this a failure). It exits 1 on
any mismatch. No program is executed in either part.

## Files

| File | Content |
| --- | --- |
| `effort_records.csv` | the 76,032 retained rows with E1 realized edits, E2 requested-operation bin, E3 attempted operations |
| `matched_effort_curves.csv` | tidy figure table: effort_measure, relation (eq / le), attack, carrier, effort, n, detected, rate, rate_exact |
| `matched_effort_rankings.csv` | per effort cell: n and rate per carrier, supported carriers (n >= 30), common support, winner set |
| `matched_effort_family_scores.csv` | direct-standardized family rates over three-way and pairwise common support, with coverage |
| `matched_effort_mixture_scores.csv` | balanced / rename-heavy / structure-heavy scores and winners per effort measure |
| `source_validation_records.csv` | 34,560 primary source-level configurations (source vs state fields, agreement flags, op log, source SHA-256, syntax) |
| `source_variant_records.csv` | 17,280 secondary sensitivity configurations |
| `source_disagreements.csv` | every configuration with a primary or per-site disagreement (all from the secondary variants) |
| `source_agreement_strata.csv` | agreement counts per declared stratum |
| `summary.json` | all summary numbers, hashes of protocol, inputs and producers |

## A. Matched effort (R2)

Nominal-severity comparator (reproduces `results/controlled/derived/mixture_scores.csv`):
balanced lexical 0.395739 > structural 0.395076 > hybrid 0.302746; rename-heavy
structural 0.665540 wins; structure-heavy lexical 0.665080 wins.

Exact structural fact (all 76,032 rows): the detector decision is a function of
(realized bit changes c, deletions d) alone; 241 distinct (c, d) pairs, 0
conflicts. Among observed pairs, detection holds exactly for c = 0 with
d <= 10, c = 1 with d <= 6, and c = 2 with d <= 2 (`detecting_pairs` in
`summary.json`). Consequently, at
matched realized edits the carriers can differ only through the flip/deletion
composition of those edits.

At matched realized edits (E1, relation eq, three-way common support):

* rename, flip, strip: rates of the three carriers are identical in every
  common-support cell (rename 1/1, flip 25/25, strip 25/25 cells).
* normalize: 1/1 cell identical.
* mixed: 20 of 25 cells identical; unique winners lexical 2, structural 2, hybrid 1.
* rename and normalize have three-way common support only at 0 edits: the
  targeted attack never realizes an edit on the other single-channel carrier
  (structural rows under rename and lexical rows under normalize all have 0
  edits). Coverage of the attacked carrier in that support: lexical/rename
  0.118, hybrid/rename 0.161, structural/normalize 0.122, hybrid/normalize 0.165.
  Pairwise lexical-vs-hybrid (rename, 11 values) and structural-vs-hybrid
  (normalize, 10 values) standardized rates are identical (0.355609 and 0.374842).
* Standardized mixture scores (E1): balanced hybrid 0.547333 > lexical 0.547257
  > structural 0.546817; rename-heavy and structure-heavy: exact three-way tie
  0.665346.

Pre-declared decision: the reversal does **not** persist at matched realized
edits (E1); also not under E3 attempted operations (same ties; balanced hybrid
0.547409 > lexical 0.547106 > structural 0.546896) and not under E2
requested-operation bins (structural is the unique winner of all three
mixtures, margins <= 0.0005 over lexical). Under the cumulative budget view
(E1, relation le, budget b >= 3) structural is the unique winner for rename in
18 of 21 common-support budgets and lexical for normalize in 18 of 21, because
the budget never binds for the carrier that the targeted attack cannot touch.
Interpretation: the nominal reversal is produced by eligibility (which carrier
an attack can modify at all) and by the carrier-specific multipliers, not by a
difference in detection per realized edit.

## B. Source-level validation (R6)

Primary sample: 3 carriers x 6 attacks x severities {0.2, 0.4, 0.5, 0.6, 0.8}
x 12 tasks x 2 languages x payloads 0..15 = 34,560 configurations. The
unattacked marked program is rendered, the attack is applied to the source
text (`source_attacks.py`, which never calls `attacked_states`), and the
existing extractor and detector are run.

* Agreement of surviving_sites, match_count and detected: 34,560 / 34,560;
  every one of the 180 carrier x attack x severity x language cells: 192 / 192.
  Also realized_bit_changes, deletions and p_value: 34,560 / 34,560; per-site
  observations: 829,440 / 829,440. Detections: 13,539 in both.
* Byte identity of the source-attacked program with the rendering of the
  predicted state (non-format attacks): 28,758 / 28,800. The 42 differences
  are strip configurations in which all 24 carriers are deleted: the text
  attack removes the carrier lines, the state rendering leaves one empty line
  where the empty carrier block was substituted. Detection fields agree.
* Syntax: Python 17,280 / 17,280 compile; JavaScript 17,280 / 17,280 compile (Node v24.22.3).
* No disagreements in the primary sample; the declared rule is met (validated on this sample).

Secondary sensitivity variants (declared in advance as probes of the
extractor's syntax assumptions; compared with the base-attack row):

| Variant | Agree (3 fields) | State detections | Source detections | Cause |
| --- | --- | --- | --- | --- |
| format_whitespace | 3,860 / 5,760 (Python 2,880/2,880; JavaScript 980/2,880) | 5,760 | 5,125 | 1,900 extractor_does_not_recognize_transformed_form |
| strip_statement_only | 60 / 5,760 | 1,912 | 815 (1,146 lost, 49 gained) | 5,700 marker_statement_attribution_shift |
| rename_no_digit_split | 2,035 / 5,760 | 2,745 | 5,450 (2,705 gained) | 3,725 extractor_does_not_recognize_transformed_form |

* format_whitespace: JavaScript `if(false){}` / `for(const ...)` are not
  recognized (the extractor requires `if (false)` and `for `); structural
  JavaScript 1/960 agree, hybrid JavaScript 19/960, lexical JavaScript and all
  Python 960/960.
* strip_statement_only: a remaining `WM_SITE` comment makes the extractor read
  the next carrier's statement for the stripped index.
* rename_no_digit_split: `wm_bit07` matches neither identifier pattern, so the
  site is treated as missing rather than mismatched, which raises detection.
  Structural carriers are unaffected (960/960 per language).

## Scope and limitations

* Only the detection side is validated. Behavioral preservation of the
  source-attacked programs is not checked (the paper's behavioral labels come
  from separate execution of retained programs); programs are compiled, never run.
* The text attacks are white-box: they locate carriers through the `WM_SITE`
  comments and use the declared site-selection rule, so the comparison tests the
  render/extract correspondence, not an attacker's ability to find carriers.
* The extractor is the marker-assisted regex extractor of the artifact, used
  for both languages; it is not a language parser. The primary agreement holds
  for the declared text forms; the secondary variants show that other
  semantically neutral spellings break the extractor's assumptions.
* Part A uses the deterministic grid; the rates are descriptive of that grid.
  Common support is thin for the targeted attacks (one value), so matched-effort
  statements about rename/normalize rest on the pairwise comparisons and on the
  exact (c, d) invariance.
