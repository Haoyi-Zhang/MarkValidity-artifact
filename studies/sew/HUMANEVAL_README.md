# HumanEval: receiving and reproducing the accepted v3 study

Run the commands below from `artifact/`. The accepted primary and expanded-input ledgers use distinct behavioral contracts. Each frozen result binds its exact source, reference, interpreter, observer, seed, and resource policy.

## Receive the delivered evidence without executing programs

This standard-library command reopens every retained source and contract, all 1,968 primary configurations, and all 124,253 expanded-input records:

```sh
python3 -B external-studies/sew_natural/scripts/humaneval/verify_humaneval.py \
  --main-results results/revision-sew-natural/humaneval \
  --enhanced-results results/revision-sew-natural/enhanced-humaneval \
  --data external-studies/sew_natural/data/HumanEval.jsonl.gz \
  --plus-data external-studies/sew_natural/data/HumanEvalPlus-v0.1.10.jsonl.gz \
  --variants-root external-studies/sew_natural/variants
```

Success prints a JSON receipt with `status: PASS` and `mode: read-only receiving; no source execution`. The saved receipt is `results/revision-sew-natural/humaneval/receiving-current.json`. The receiver checks retained-byte bindings, detector-statistic consistency, labels, and aggregation. It does not execute candidates, references, watermarkers, detectors, or normalizers, or attest that an external producer performed an execution.

The primary data contain 492 supported configurations per variant. Detected/joint counts are 368 for stock and S4, and 365 for S1 and combined. Expanded inputs produce 124,158 comparable pairs and 95 unavailable pairs. At task level, 155 contracts are supported and nine unavailable; the joint numerator lies between 113 and 122 out of 164.

## Reexecute the original suites

The recorded runtime is CPython 3.12.14. Use an isolated environment with the dependencies in `scripts/humaneval/requirements-pilot.txt`: Tree-sitter 0.23.2 and its Python grammar 0.23.6. The current worker is **`native_runner_v3.py`**. Each producer requires a fresh output directory.

```sh
for sew_variant in stock s1 s4 s1_s4; do
  python3 -B external-studies/sew_natural/scripts/humaneval/run_humaneval.py \
    --data external-studies/sew_natural/data/HumanEval.jsonl.gz \
    --vendor "external-studies/sew_natural/variants/$sew_variant" \
    --runner external-studies/sew_natural/scripts/humaneval/native_runner_v3.py \
    --out "reproduction/humaneval-v3/$sew_variant" \
    --keys 3
done

python3 -B external-studies/sew_natural/scripts/humaneval/normalize_humaneval_v3.py \
  --data external-studies/sew_natural/data/HumanEval.jsonl.gz \
  --license external-studies/sew_natural/data/LICENSE \
  --runner external-studies/sew_natural/scripts/humaneval/native_runner_v3.py \
  --variant stock:reproduction/humaneval-v3/stock \
  --variant s1:reproduction/humaneval-v3/s1 \
  --variant s4:reproduction/humaneval-v3/s4 \
  --variant s1_s4:reproduction/humaneval-v3/s1_s4 \
  --vendor stock:external-studies/sew_natural/variants/stock \
  --vendor s1:external-studies/sew_natural/variants/s1 \
  --vendor s4:external-studies/sew_natural/variants/s4 \
  --vendor s1_s4:external-studies/sew_natural/variants/s1_s4 \
  --out reproduction/humaneval-normalized-v3
```

The original assertions define the primary label. Argument and return traces are separate differential observations. Uncaught `MemoryError`, `OSError(errno=ENOMEM)`, `KeyboardInterrupt`, resource termination, and observer copying/encoding failures leave evidence unavailable. Ordinary program exceptions and assertion failures remain failures when uncaught by the original suite. A suite cannot turn a caught observer failure into support.

## Run the observation-boundary controls

The matrix includes 24 primary controls and 21 expanded-input controls. It covers normal returns, exception-shaped returned values, ordinary program errors, malformed source/tests, actual address-space exhaustion, interruptions, CPU/wall limits, copying/encoding failures, and caught observer events. The CPU/wall controls retain native process outcomes. The callback-catching control explicitly delivers the callback synchronously; actual timer expiry is tested separately.

```sh
python3 -B external-studies/sew_natural/scripts/humaneval/check_observer_boundaries_v3.py \
  --primary-runner external-studies/sew_natural/scripts/humaneval/native_runner_v3.py \
  --enhanced-runner external-studies/sew_natural/scripts/humaneval/native_pairs_v3.py \
  --out reproduction/observer-boundaries-v3-controls.json
```

The delivered matrix is `results/revision-sew-natural/observer-boundaries-v3-controls.json`. Its two family subsets accompany the primary and expanded-input result packages. These constructed diagnostics do not add natural benchmark samples.

## Reexecute the distinct expanded-input contract

The producer takes stock/default-key sources from either raw or normalized primary rows. This command uses the frozen delivered primary sources, the original HumanEval references, and every tuple in the full HumanEval+ release:

```sh
python3 -B external-studies/sew_natural/scripts/humaneval/run_humaneval_plus_v3.py \
  --data external-studies/sew_natural/data/HumanEval.jsonl.gz \
  --plus-data external-studies/sew_natural/data/HumanEvalPlus-v0.1.10.jsonl.gz \
  --candidate-run results/revision-sew-natural/humaneval \
  --runner external-studies/sew_natural/scripts/humaneval/native_pairs_v3.py \
  --out reproduction/humaneval-expanded-v3

python3 -B external-studies/sew_natural/scripts/humaneval/normalize_humaneval_plus_v3.py \
  --data external-studies/sew_natural/data/HumanEval.jsonl.gz \
  --plus-data external-studies/sew_natural/data/HumanEvalPlus-v0.1.10.jsonl.gz \
  --candidate-run results/revision-sew-natural/humaneval \
  --enhanced-run reproduction/humaneval-expanded-v3 \
  --runner external-studies/sew_natural/scripts/humaneval/native_pairs_v3.py \
  --controls reproduction/observer-boundaries-v3-controls.json \
  --out reproduction/humaneval-expanded-normalized-v3
```

Each side starts from a fresh namespace and independently copied positional arguments. Random state resets once before that side's source initialization. The relation compares typed return or ordinary invocation-exception envelopes; argument post-state and streams are additional observations. The per-side 500 ms budget covers initialization, invocation, and observation. Resource and interruption events remain unavailable, and a caught elapsed guard cannot become support. This is not the official EvalPlus scoring protocol.

Use the receiver again with the two reproduction result paths to check a new run. Timeout counts may vary with execution conditions; retain the new observations and their identities instead of replacing them with the delivered counts.

## History and version identity

Earlier primary packages are retained under `results/revision-sew-natural/history/humaneval-primary-v1/` and `humaneval-primary-v2/`. The full expanded-v2 package is in `history/humaneval-expanded-v2/`; it also retains the superseded expanded-v1 summary and correction reason. The current contracts use the v3 observer fingerprints. History does not contribute extra samples to any current denominator.

`primary-v2-v3-comparison.json` establishes that all 1,968 primary source/detector/normal semantic records remained unchanged after the boundary repair. `v2-v3-observation-comparison.json` checks every expanded input across versions and records changed availability at the time boundary. The current primary and expanded ledgers are the sole inputs to current findings.
