# MarkValidity artifact

Artifact for the ACM TOSEM submission *Sound Comparison of Code Watermarks with
Contract-Bound Behavioral Evidence*. It contains the implementation of the
shared-evidence comparison method, the two public watermark studies (SEW and
CREST), exact controls, the retained native observations, and independent
"receivers" (verification scripts) that re-derive the numbers reported in the
paper from those observations.

- SEW: 591 canonical tasks (HumanEval + sanitized MBPP), three keys, four treatments.
- CREST: 591 canonical tasks and all 2,276 programs of the two published cohorts.

Every original program remains in the recorded population; qualification,
candidate behavior, emission and detector output are separate fields.

## Repository layout

| Study / evidence | Retained data | Implementation |
| --- | --- | --- |
| HumanEval and sanitized MBPP transformations | `results/sew/` | `studies/sew/` |
| Independent policies, joint native timing, common-remainder ablation | `results/comparisons/` | `studies/sew/comparison_costs/` |
| Expanded HumanEval inputs | `results/sew/enhanced-humaneval/` | `studies/sew/scripts/humaneval/` |
| Aliasing counterexamples | `results/aliasing/` | `studies/aliasing/` |
| Controlled Python and JavaScript programs | `results/controlled/`, `results/python/`, `results/javascript/` | `src/`, `js/` |
| Source evidence and query budgets | `results/source-evidence/`, `results/audit-budget/` | top-level `verify_*.py` / `audit_*.py` |
| Project invocation contracts | `results/project-contracts/` | `check_project_contracts.py`, `corpus/` |
| Exact detector-null enumeration | `results/detector-null/` | `scripts/exact_detector_null.py` |
| Paired conditional certificates, exact inference, native costs | `studies/conditional/` | `studies/conditional/` |
| CREST canonical/published outcomes, causal diagnosis, comparison replay | `studies/crest/accepted/` | `studies/crest/` |
| Detector decisions on unwatermarked programs (SEW 1,003 keys, CREST heads), correlated nulls | `results/null-calibration/` | `studies/null-calibration/` |
| Source distortion vs. executed validity on real SEW/CREST edits | `results/edit-similarity/` | `studies/edit-similarity/` |
| Controlled carriers: matched realized effort, render-attack-extract validation | `results/controlled-validation/` | `studies/controlled-validation/` |
| Project test suites on the 120 transfer-audit modules | `results/transfer-tests/` | `studies/transfer-tests/` |

Other directories:

| Path | Content |
| --- | --- |
| `check.py`, `tools/artifact_check.py`, `Makefile` | entry points (see below) |
| `internal/` | machine-readable check configuration: `verification-plan.json` (all components), `layout.json` (recorded-path map), `scientific.make` (original study Makefile) |
| `tests/`, `regressions/` | unit/rejection-path tests; paper-table reconciliation tests |
| `reporting/` | SHA-256 index of the paper files bound by the regression tests |
| `citations/`, `citation-evidence/` | citation audit and per-source reading records |
| `proofs/`, `external-baselines/`, `figure_data/`, `supporting-figure-data/`, `test-data/` | proof checks, baseline protocols, figure inputs, test fixtures |
| `docs/ARTIFACT.md` | what is executed locally vs. retained provenance |

## Requirements

- Linux x86-64 (tested: Ubuntu 24.04 under WSL2, glibc 2.39, Python 3.12.3) or
  macOS. Windows works for most receivers (see notes below); the CREST execution
  controls need POSIX. `make` is used for the entry points.
- Python >= 3.11. The core receivers use only the standard library.
- Node.js >= 18 on `PATH` for the JavaScript controls (4 of the 127 unit tests;
  tested with the official Node.js v24.22.3 linux-x64 build, the version
  recorded in `results/javascript/registration.json`). Without root access:
  ```sh
  curl -LO https://nodejs.org/dist/v24.22.3/node-v24.22.3-linux-x64.tar.xz
  mkdir -p ~/opt/node && tar -xJf node-v24.22.3-linux-x64.tar.xz -C ~/opt/node --strip-components=1
  export PATH=~/opt/node/bin:$PATH
  ```
- CREST numerical receivers: the pinned packages in `studies/crest/requirements.txt`
  (scikit-learn 1.7.2, numpy 2.3.5, libarchive-c, ...) and the system libarchive
  library (`libarchive13` on Debian/Ubuntu, `brew install libarchive` on macOS),
  plus network access to fetch 17 CREST model/source files from GitHub
  (or a cache, see `CREST_CACHE` below).
- Hardware: any recent CPU, 4 GB RAM, about 2 GB free disk (the repository is
  ~830 MB; each check makes a temporary copy in `$TMPDIR`). No GPU.
- Only for `make artifact-paper` (submission package): the paper's
  `paper/requirements.txt` (matplotlib 3.10.8, PyMuPDF, reportlab, Pillow),
  TeX Live 2024 with `pdflatex`/`bibtex` and the acmart dependencies (e.g. the
  `scheme-small` installer plus `collection-latexrecommended`,
  `collection-latexextra`, `collection-fontsrecommended`, `collection-pictures`,
  `libertine`, `newtx`, `inconsolata`), and the URW base35 *Nimbus Roman* OTF
  fonts (`fonts-urw-base35` on Debian/Ubuntu, or the `NimbusRoman-*.otf` files of
  github.com/ArtifexSoftware/urw-base35-fonts tag 20200910 copied to
  `~/.local/share/fonts`). Remove `~/.cache/matplotlib/fontlist-*.json` if the
  fonts were installed after matplotlib was first used.

## Installation

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r studies/crest/requirements.txt   # only for the CREST numerical receivers
python -m pip install -r studies/aliasing/requirements.txt  # only for the fresh aliasing run (run.py example below)
python -m pip install -r ../paper/requirements.txt        # submission package only, for make artifact-paper
```

Run all commands below inside this activated environment (the Makefile calls
`python3`).

`requirements.txt` at the root lists no packages on purpose: everything except
the CREST receivers runs on the standard library.

## Quick check (~1-2 min)

```sh
make artifact-smoke          # = python3 tools/artifact_check.py smoke
```

Runs a fast subset of the evidence receivers (SEW comparison arithmetic,
matched disclosure, paired-certificate mathematics and index, detector-null
enumeration, source query budgets). Expected output ends with

```
source-query-budgets: PASS (...)
paired-conditional-mathematics: PASS (...)
paired-conditional-index: PASS (...)
Overall: PASS
[passed] fast evidence receivers ...
```

### Paper-binding checks (optional)

Two components, `paper-data-consistency` (every table/macro value in the paper
is reconstructed from raw observations) and `citation-source-bindings`, read the
paper's LaTeX sources, which are not part of this repository. They run
automatically when the sources sit in `../paper`, or with `PAPER=DIR`:

```sh
make artifact-smoke PAPER=/path/to/paper    # also runs the two paper-binding components
```

Without the paper they are reported as `SKIPPED`, never as `PASS`.

## Full reproduction (~5-10 min)

```sh
make artifact-check          # = python3 tools/artifact_check.py full
make artifact-check CREST_CACHE=/path/to/crest-cache   # same, without downloading CREST files
```

Runs three stages (all components of `internal/verification-plan.json`):
implementation tests, primary receivers, supporting receivers. A stage that
cannot run a component because a prerequisite is missing reports it as
`SKIPPED` with the reason; the remaining components still run. Logs and a JSON
summary are printed; `tools/artifact_check.py` also writes
`.worktree/artifact-full.json`.

| Paper claim / evidence | Component(s) | Retained data checked | Runtime |
| --- | --- | --- | --- |
| SEW HumanEval/MBPP observations, comparison arithmetic, matched disclosure (primary and all-withheld) | `humaneval-observations`, `mbpp-observations`, `comparison-arithmetic`, `matched-disclosure-*`, `conditional-bounds`, `algorithm-branches` | `results/sew/` | ~40 s |
| Independent query policies, native stopping records | `independent-query-policies`, `native-stopping-records`, `native-and-ledger-agreement` | `results/comparisons/`, `results/sew/native-audit/` | ~90 s |
| Paired conditional certificates, adaptive policy, emission accounting, native validation/timing | `paired-*`, `emission-accounting`, `conditional-native-*` | `studies/conditional/` | ~25 s |
| CREST outcomes, contract sensitivity, causal diagnosis, paired comparison | `crest-*` | `studies/crest/accepted/` | ~35 s + download |
| Controlled Python/JavaScript evidence, detector null, query budgets, aliasing, project contracts | supporting scope | `results/python/`, `results/javascript/`, `results/audit-budget/`, `results/aliasing/`, `results/project-contracts/`, `results/detector-null/` | ~45 s |
| Implementation and rejection-path tests (127 tests) | `implementation-tests`, `crest-execution-contract-controls` | `tests/` | ~60 s |
| Paper tables/macros and citation bindings | `paper-data-consistency`, `citation-source-bindings` | paper sources (optional, see above) | ~15 s |

Individual scopes and components:

```sh
python3 -B -S check.py --scope primary|supporting|tests|publication|all [--keep-going]
python3 -B -S check.py --component source-query-budgets --output /tmp/mv-logs
make verify-primary CREST_CACHE=/path/to/crest-cache   # reuse acquired CREST files
```

Each run copies the repository into a disposable temporary directory that
restores the original recording paths (`internal/layout.json`), so the supplied
observations are never modified. With `--output DIR` (outside the repository)
per-component logs and an `input-files.json` hash index of all scientific
inputs are kept.

A CREST cache can be created once with
`python3 studies/crest/acquire_crest_upstream.py --output DIR` (downloads 17
files of the pinned upstream commit and checks their SHA-256 values).

## Follow-up studies (pre-declared protocols)

Four studies answer reviewer questions on an earlier draft. Each has a protocol written before any
outcome was computed (`studies/<name>/protocol.json`), raw results, a standard-library verifier and a
README in `results/<name>/`. Their receivers read the clean repository layout and run as the last
stages of `make artifact-check` (the first two also in `make artifact-smoke`):

| Study | Paper | Verifier runtime | Notes |
| --- | --- | --- | --- |
| `null-calibration` | RQ1, Fig. 6; supplement proxy checks and null section | ~6 s | producer needs tree-sitter (SEW) and scipy |
| `edit-similarity` | RQ1, Fig. 7; supplement proxy checks | ~10 min | recomputes every metric from the sources |
| `controlled-validation` | supplement matched effort (supplement Fig. 1), source-level validation | ~20 s | JavaScript syntax check needs Node.js, otherwise reported SKIPPED |
| `transfer-tests` | supplement transfer audit .5; threats | ~5 s | producer needs uv, CPython 3.12.14, `unshare`, ~1 h; on CPython other than 3.12.14 four tokenize-sensitive regeneration checks are reported SKIPPED |

## Fresh executions

`run.py` runs a selected scientific script in an isolated copy and saves its new
output and log outside the repository. The `--output` directory must not exist
yet and must lie outside the directory that contains `artifact/` (e.g. under
`/tmp`). Pass the script's result argument as `{output}`; for example, rerun the
aliasing study with actual watermark generation and program execution:

```sh
python3 run.py --output /tmp/markvalidity-aliasing-run studies/aliasing/run_study.py -- --out '{output}'
```

Historical hosted-model generation calls and released detector outputs are
retained inputs and are not re-issued (see `docs/ARTIFACT.md`).

## Known limitations and verification status

Reviewer-style run of a clean copy on Ubuntu 24.04 (WSL2, glibc 2.39, Intel
Core i7-12700KF), Python 3.12.3 in a fresh venv with the packages from
`studies/crest/requirements.txt`, Node.js v24.22.3: every documented command
exits 0 with no FAIL (standalone and with `../paper`), as listed here. The
`run.py` aliasing example reproduces the retained `results/aliasing/` rows and
summary exactly (only per-run `elapsed_seconds` differ).

- `make artifact-smoke`: PASS (6 components, ~1 min on a native filesystem; the
  staging copy dominates the runtime when the repository sits on a Windows
  drive mounted into WSL, about 9 min on the test host); with the paper present
  (`../paper` or `PAPER=...`) the two paper-binding components also PASS.
- `make artifact-check`: PASS (tests 127/127 incl. the 4 Node.js tests; primary
  and supporting scopes all PASS; ~35 min on the test host, most of it staging
  the copy). Standalone, the report is `PASS_WITH_SKIPS` because only the two
  paper-binding components of the tests scope are skipped; with `../paper`
  beside the artifact the same command is `PASS` and both components pass
  (`paper-data-consistency`, `citation-source-bindings`).
- The four follow-up study receivers (`null-calibration`,
  `controlled-validation`, `edit-similarity`, `transfer-tests`) run as the last
  stages of both levels and PASS. On the test host (CPython 3.12.3) the
  transfer-tests receiver reports four tokenize-sensitive regeneration checks as
  SKIPPED, as documented below.
- `make artifact-paper` (submission package): PASS; the regenerated tables,
  macros, figure data, all nine figure stems (`natural-overview`,
  `natural-joint-budget`, `natural-conditional`, `crest-outcomes`,
  `detector-null`, `edit-similarity`, `certificate-costs`, `native-timing`,
  `matched-effort`; PDF, SVG and PNG) and the figure atlas are byte-identical to
  `../paper` (regenerated on the test host with Python 3.13.18 and matplotlib
  3.11.2, beyond the pinned 3.10.8, without changing a byte). The compiled
  article has 39 pages with seven statistical figures (Figs. 4 to 10) and three
  conceptual-figure placeholders (Figs. 1 to 3); the online supplement has 48 pages and the supplement figure
  `matched-effort`.
- CREST classifier scores (`crest-native-model-*`): the saved LogReg
  probabilities were computed on an x86-64 CPU with AVX-512 (recorded platform:
  Linux 6.18, glibc 2.41, Python 3.12.14), where the OpenBLAS 0.3.30 bundled with
  numpy 2.3.5 uses its SkylakeX `ddot` kernel. CPUs without AVX-512 (e.g. Intel
  Alder Lake desktop CPUs, as in the test host) use the Haswell kernel, whose
  different summation order changes up to 183 of the 3,534-6,828 LogReg scores per
  study by at most 1.6e-16; neither glibc nor the Python build matters (Python
  3.12.14 and glibc 2.39 give the same values). A pure-Python emulation of the
  two kernels reproduces all saved scores bitwise with the SkylakeX order and all
  locally computed scores with the Haswell order. The receiver therefore accepts
  bitwise-equal scores, or scores within an absolute tolerance of 1e-15
  (reported as `probabilities_within_tolerance_not_bitwise` and
  `max_abs_probability_difference`), and always requires every detector decision,
  threshold and operating point to be identical. Random Forest scores match
  bitwise everywhere.
- `crest-execution-contract-controls`: PASS (POSIX only).
- On Windows, `crest-paired-comparison` fails only because a recorded source
  path is compared with `\` separators; set `PYTHONUTF8=1` and point `TEMP`/`TMP`
  at a short directory (restored paths reach ~200 characters).
- `results/audit-budget/checkpoints.csv` was missing from an earlier upload; it
  is a deterministic projection of the retained traces and was restored
  byte-identically (SHA-256 recorded in `results/audit-budget/summary.json`).
  `python3 tools/rebuild_audit_checkpoints.py results/audit-budget OUT.csv`
  regenerates it.
- Regenerating the paper's figures and PDFs (`make artifact-paper`) needs the
  paper sources and their build requirements and only works inside the
  submission package (`../paper`); all generated tables, macros, figure data
  and figures were checked to be identical to those in the paper. The hash index
  of the bound paper files is `reporting/paper/manifest.json`; the generator,
  input and output hashes of the publication material are recorded in
  `../paper/figdata/publication-bindings.json`. The citation audit
  (`citations/`) binds every citing paragraph of the current main text and
  supplement (66 references, 95 citation positions).

## License

Code: MIT, see `LICENSE`. Retained results and observations produced for this
work: CC BY 4.0, see `LICENSE-DATA`. Third-party benchmark data, CREST/MxEval
records and vendored code keep their own licenses (`corpus/licenses/`,
`studies/sew/data/LICENSE`, `studies/aliasing/vendor/LICENSE`,
`studies/sew/variants/*/LICENSE`).
