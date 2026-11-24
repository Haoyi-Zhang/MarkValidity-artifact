# HumanEval external study: completed evidence and integration notes

## What the experiment establishes

The unselected HumanEval corpus supplies a real, independently authored benchmark on which the original SEW implementation preserves all observed original test suites. Its value to MarkValidity is a reproducible natural-code control and a nontrivial source-sharing comparison. It supplies no observed instance of a detected, behaviorally invalid output under the original-suite contract.

All 164 reference implementations were evaluated with three explicitly fixed keys: the upstream key (`76` repeated 16 bytes), the 128-bit integer zero, and the 128-bit integer one. Every source is the exact `prompt + canonical_solution` from the frozen official file. Four variants were run on the same task/key grid. No task, key, abstention, exception, or timeout was selected away.

| Variant | Configurations | Original-suite support | Detected | Joint | Exact original-call record agreement |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stock SEW | 492 | 492 | 368 | 368 | 492 |
| Conservative S1 guard policy | 492 | 492 | 365 | 365 | 492 |
| S4 return-token boundary repair | 492 | 492 | 368 | 368 | 492 |
| S1 policy and S4 repair | 492 | 492 | 365 | 365 | 492 |

All embedding calls returned `ok`. All 164 reference suites passed in every factor run. There were no unavailable detector results. For each variant, the candidate suites made 4,602 observed entry-point invocations, while the 164 reference suites made 1,534. The four-factor candidate total is 1,968 whole-suite executions and 18,408 observed function-entry invocations. These are distinct cost units.

The stock detections by key are 122, 122, and 124; the S1-policy detections are 118, 123, and 124, in the key order above. S4 alone leaves every paired HumanEval output byte-identical to stock; combined S1/S4 leaves every output byte-identical to S1. S1 changes 80 of 492 paired output texts. Five paired detector decisions change: four detections disappear and one appears. These observations show a real restriction-versus-detection tradeoff, rather than universal improvement from a stronger local premise.

## Data and provenance

The source is the official [OpenAI HumanEval repository](https://github.com/openai/human-eval), commit `b9453e8f1865df0a0057a1383767caa400acfbcf`. The complete gzip file has SHA-256 `b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef` and contains all 164 tasks. The MIT license, pinned README, and official execution source are retained. The pinned README describes the repository as deprecated and unmaintained; this is a fixed historical benchmark of hand-written reference programs.

Expanded inputs come from the complete official [HumanEvalPlus v0.1.10 release](https://github.com/evalplus/humanevalplus_release/releases/tag/v0.1.10), asset `HumanEvalPlus.jsonl.gz`. Its SHA-256 is `272720b90ac375502c8ed23cd791c2a93dfb22a911641a494da74a426c09f101`. The release contains 1,570 base-input tuples and 122,683 additional tuples over the same 164 tasks. The release repository supplies Apache-2.0 terms with an explicit note retaining MIT compliance for the HumanEval-derived data. Neither Mini nor NoExtreme was substituted for the full asset.

Stock SEW is the existing vendored upstream commit `3c873186a56033e73347391b7aedebce1f7f71d0`. The runtime was CPython 3.12.14 on Linux, with task-local `tree-sitter==0.23.2` and `tree-sitter-python==0.23.6`. Full URLs, byte counts, file fingerprints, environment details, and license locations are recorded in `provenance-humaneval.json`. No model generation or global dependency installation was needed.

## The primary observation contract

The primary oracle is completion of the unchanged original `check(candidate)` suite, conditional on the reference suite passing. Calls are wrapped to record typed arguments before execution, return or exception, and argument values after execution; the wrapper returns the actual result unchanged to the original assertions. Trace agreement is a separately reported differential observation, not an additional hidden requirement in the primary validity label.

Each whole suite runs in a fresh process and module namespace with `random.seed(0)`, `PYTHONHASHSEED=0`, active assertions, a fresh temporary working directory, no inherited `PYTHONPATH`, a 10-second CPU limit, a 15-second parent wall limit, and a 1 GiB address-space limit. State persists between the original suite's calls, as in its test body. The normalized task contract includes the exact test body and hash, entry point, reference hash, observer hash, interpreter identity, seeds, and limits.

The accepted primary observer is `native_runner_v3.py`. It separates copying and value encoding from program exceptions, preserves unavailable evidence even if the original suite catches `BaseException`, and retains the earlier normal value representation. Uncaught `MemoryError`, OS `ENOMEM`, and `KeyboardInterrupt` are unavailable; ordinary program exceptions remain subject to the unchanged original assertions. Twenty-four primary native controls pass. All 1,968 task/key/version candidates and all 656 per-factor reference suites were rerun. Emitted bytes, embedding and full detector records, and all normal semantic observations match v2 exactly, while every contract identity changes. The full earlier primary packages remain in `history/humaneval-primary-v1/` and `history/humaneval-primary-v2/` under the natural results directory.

The original 1,534 reference invocations contain no keyword arguments. A static scan also found no direct `candidate(...)` call with keywords and no direct call passing the same simple variable name in multiple argument positions. Twenty-three calls change argument values: eight in HumanEval/70, nine in /120, and six in /149. Those poststate observations agree for all four variants. The value-tree encoder records builtin structure and type, not the complete heap identity or alias graph. Thus this corpus is not evidence that arbitrary alias-sensitive or keyword-facing APIs are covered.

## The two local interventions

The S1 policy adds an independent, conservative pre-state condition to the existing guard. The immediately preceding statement in the same basic block must be a single-name assignment to an exact builtin integer or float literal; the updated target must be the same local name in a function scope, and declarations of that name as global or nonlocal are rejected. Existing S1 operator and precedence checks still apply. Annotation-based inference and inference from the augmented-assignment right-hand side are not accepted as substitutes for this condition. Twelve admission controls pass, including module/class/global scope, nonadjacency, list aliasing, and same-branch cases.

SEW uses `discover` from both `embed` and `detect`, and `discover` calls each rule's guard. Consequently S1 changes admission in both the embedder and detector. The stock detector's calibration table and threshold are retained; this is a shared-discovery guard-policy variant, not solely a writer edit or a newly calibrated watermarking algorithm. Its observed detection change combines changed output text with changed eligible evidence.

The S4 intervention is supplied by the MBPP study. It adds one separating space when removing tuple parentheses would join the `return` keyword to the first emitted identifier-like character. Its match and guard stay byte-identical. The independent 19-case lexical controls and the natural MBPP results belong to that study; they must not be counted as additional HumanEval tasks. The S4 policy makes no claim of whole-system semantic preservation.

The prior targeted aliasing grid also ran under S1 with the original six diagnostic programs, 17 fixed keys, and 33 input values. Stock had 85 valid, 90 detected, and 75 joint configurations out of 102; S1 has 102 valid, 69 detected, and 69 joint. These are controlled mechanism cases, separate from the natural-code denominators. They show removal of the observed aliasing failures together with a detection cost.

## Exact detector event

The experiment invokes the unmodified public `detect` API with default `calibrate=True`. It aggregates sites by grade identifier, takes majority votes with ties mapped to one, and uses the retained per-rule table to assign null-hit probabilities `q` or `1-q` according to the key's target bit. It computes Poisson-binomial upper tails for all grades and for the subset excluding format-rule grades. The reported value is

`p = min(1, 2 * min(p_all, p_syntax))`.

Detection requires at least five all-grade evidence units and strictly `p < 0.01`. Fewer grades yield `Insufficient evidence`. This is the recorded upstream decision rule; the fixed benchmark/key pool is not a calibration experiment. Stock detects none of the 492 unembedded reference/key pairs. That negative control is descriptive and supplies no calibrated false-positive guarantee.

## A distinct expanded-input contract

The accepted expanded-input run is `artifact/results/revision-sew-natural/enhanced-humaneval/`. It uses stock/default-key output, the original HumanEval reference source, and all 124,253 frozen input tuples. Each reference/candidate invocation gets a fresh namespace, freshly copied positional arguments, and a reset random state. The relation compares exact typed return-or-invocation-exception envelopes. Argument poststate and stdout/stderr are checked separately. This is an input-domain differential contract, not the official EvalPlus task score: corrected EvalPlus reference implementations, tolerance rules, and special oracles are not substituted into this relation.

Every input pair has a retained log record. Of 124,253 pairs, 124,158 have comparable outcomes and all agree; 95 pairs contain an unavailable observation under the fixed 500 ms per-invocation budget. There are no recorded return, poststate, or stream differences. Nine tasks therefore remain unavailable and 155 have complete support. All nine unavailable tasks are detected, so the joint numerator is bounded by 113 and 122 out of 164. Reporting 122/164 as fully established joint success would erase the incomplete observations.

Eight pairs contain matching genuine program exceptions: seven `OverflowError` outcomes in HumanEval/32 and one `IndexError` in /64. These are observational matches, not task-correctness evidence or watermark failures. Eleven unavailable pairs reach the limit during return encoding on both sides; the other unavailable observations occur during the invocation. Availability under a wall-time budget depends on execution conditions, so these counts are records of this execution rather than a reproducibility promise for exact timeout counts on another machine.

The exploratory v1 enhanced observer placed return encoding inside the program-exception handler, misclassifying 78 large integer values when decimal conversion hit CPython's digit limit; it also emitted observations only at batch completion. V2 corrected the encoding and per-pair retention. V3 additionally makes uncaught memory exhaustion, OS `ENOMEM`, interruption, and elapsed observation guards unavailable. It preserves normal returned-value encoding. All 21 expanded-input controls pass, including true CPU/wall termination with an earlier pair retained. The full v3 run contains every declared input. Across v2 and v3, all 124,154 jointly comparable pairs and 248,312 jointly observed individual sides agree exactly. Four previously unavailable pairs become comparable and one previously comparable pair becomes unavailable. The new timing results are retained as measured. The complete v2 package, including the v1 summary, remains in `history/humaneval-expanded-v2/`.

## Source sharing and audit cost

The four-factor primary ledger has 1,968 rows but only 546 distinct candidate-source/contract pairs. A source group is identified by SHA-256 of canonical UTF-8 JSON containing `reference_sha256`, `candidate_sha256`, and `contract_sha256`, with `ensure_ascii=False`, sorted keys, and compact separators. The contract is independent of method and key. Before pooling, all repeated source/contract observations were checked for identical suite status, errors, call records, streams, and invocation counts.

For stock minus S1, both methods have 492 configurations. With all validity labels deliberately withheld, 151 source groups have nonzero difference coefficients: 77 positive and 74 negative; 395 groups have zero coefficient. The source-coupled interval is `[-74/492, 77/492]`, of width `151/492`. Separately bounding the scores gives `[-365/492, 368/492]`, of width `733/492`. The fully observed difference is `3/492 = 1/164`.

One full candidate-suite query per unique source/contract costs 546 queries; querying only the 151 nonzero groups determines this difference. The corresponding measured HumanEval entry-point counts are 5,160 and 1,559, compared with 9,204 if all 984 stock/S1 rows are executed separately. These are exact reconstructions from retained observations under deliberate withholding. They are not measurements of an online adaptive audit that was executed during data collection.

Stock versus S4 has zero difference coefficients because every corresponding source and detection result is identical. This is a useful natural zero-gap control. Its equality can be decided without spending a validity query, while absolute validity of either method remains a separate question.

## Reproduction and delivery

`artifact/external-studies/sew_natural/scripts/humaneval/` contains the supported command-line entry points. `run_humaneval.py` accepts explicit `--data`, `--vendor`, `--runner`, `--out`, and `--keys`. The enhanced runner accepts `--data`, `--plus-data`, `--candidate-run`, `--runner`, and `--out`; it selects stock/default-key rows from either raw or normalized input. Both normalizers use explicit paths and retain precise contract identities. Current entry points contain no QA workspace path defaults.

The v3 primary producer completed all 164 tasks, three keys, and four variants, with isolated native subprocesses. `primary-v2-v3-comparison.json` records matching source bytes, embedding records, complete detector records, and all normal semantic observations across the observer correction. The read-only `verify_humaneval.py` receiver reopens the 1,968 primary labels and all 124,253 expanded input pairs. Its current receipt is `results/revision-sew-natural/humaneval/receiving-current.json`; receiving executes no scientific program. The expanded v3 execution took 199.977 seconds in this environment. This duration is not an algorithmic speed comparison.

`HUMANEVAL_README.md` gives the explicit current commands. Accepted results are `artifact/results/revision-sew-natural/humaneval/` (primary v3) and `artifact/results/revision-sew-natural/enhanced-humaneval/` (expanded v3). The four-factor comparison analyses and fresh native comparison replays use the current primary ledger. Earlier observation packages are marked as history and never pooled with current observations. The diagnostic S1 policy that merely removed a right-hand-side bypass is also historical; the selected S1 intervention uses the conservative immediate-predecessor condition stated above.
