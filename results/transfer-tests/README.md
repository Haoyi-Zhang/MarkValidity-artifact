# Transfer-tests study (project test suites as behavioral oracle)

Protocol (written before any baseline or variant run): `studies/transfer-tests/protocol.json`.
Deviations decided after the first baseline runs and before any variant run:
`studies/transfer-tests/deviations.json` (three harness repairs; anyio and urllib3 re-resolved with
their release date as dependency cutoff; jmespath test tree from its tag archive).

Question: when the three transfer-audit variants (inert trailing comment, syntax-aware local rename,
scope-blind identifier collapse) replace one frozen module inside its own project at the pinned
release, does the project's own test suite still pass every test that passed twice on unmodified code?

## Commands (Linux/WSL; needs uv, CPython 3.12.14, network for `fetch`/`setup`, `unshare`)

```sh
bash studies/transfer-tests/run.sh fetch      # pinned sdists / tag archives, SHA-256 recorded
bash studies/transfer-tests/run.sh setup      # one isolated venv per project
bash studies/transfer-tests/run.sh baseline   # two baseline runs per project
bash studies/transfer-tests/run.sh variants   # 360 cells (+ confirmation reruns, post controls)
bash studies/transfer-tests/run.sh export     # writes this directory
bash studies/transfer-tests/run.sh verify     # stdlib verifier (TT_PYTHON overrides the interpreter)
```

Total wall time on a 20-thread machine: about 1 h (most of it aiohttp, ~5 min per run).
The verifier (standard library only) recomputes everything from the raw records. `tokenize.untokenize`,
used to regenerate variants, produces different bytes for two modules on CPython 3.12.3 than on the
pinned 3.12.14; on another interpreter those four regenerated-variant checks are reported as SKIPPED
(their audited-hash checks still run) and every other check must pass.

## Files

| File | Content |
| --- | --- |
| `runs.jsonl` | 360 cells: project, module, intervention, variant SHA-256, attempts (counts, lost tests, messages, monitor data), outcome and reason, baseline exercise flags |
| `projects.jsonl` | 24 projects: source archive hashes, resolved environment, test command, eligibility, baseline counts, post-control drift |
| `baseline/<project>.json.gz` | baseline-passing and flaky-excluded test ids |
| `summary.json` | all reported counts |

## Results

23 of 24 projects eligible (asn1crypto: its test package imports `imp`, removed in Python 3.12, so no
test is collected). 62,887 baseline-passing tests; the suites exercise 109 of 115 eligible modules and
the renamed function in 106. 475 variant runs.

| Intervention | Preserved (exercised) | Contradicted | Preserved, not exercised | Unavailable |
| --- | --- | --- | --- | --- |
| inert trailing comment | 106 | 0 | 6 | 8 (5 ineligible, 3 non-reproducing failures) |
| syntax-aware local rename | 94 | 13 | 6 | 7 (5 ineligible, 1 non-reproducing, 1 timeout) |
| scope-blind identifier collapse | 0 | 113 | 2 | 5 (ineligible) |

The rename parses and compiles on all 120 modules (`results/controlled/raw/project_transfer.csv`)
but is contradicted by the project tests on 13 modules (1 to 373 lost tests): 4 NameError on the
original parameter name, 2 keyword callers, 1 missing positional argument, 1 ResourceWarning under a
strict warning filter, 5 without a recorded message. Post-control drift: at most 2 tests (requests),
1 (anyio, urllib3), 0 elsewhere.

Scope: execution inside subprocesses spawned by tests is not observed by the monitor; "preserved"
means the project's baseline tests pass, not behavioral equivalence.
