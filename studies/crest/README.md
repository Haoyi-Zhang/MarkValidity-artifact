# CREST evidence and reproduction

`accepted` is the current result interface. It contains `reference`, `catalogue`,
`gpt4o`, `qwen`, `comparison`, and `causes`. Each program-study directory retains
the complete task table, original and candidate source files, all native
requests and responses in `results.json`, the operating-point observations,
the reporting summary, and separate numerical and provenance receiving records.

## Populations and outcomes

The canonical workload has 164 HumanEval and 427 sanitized MBPP programs. The
stock pipeline emits 589 candidates: 574 pass their original suites and 15 fail.
The two completed precheck rejections remain in the 591-attempt denominator.
The explicit post-diagnosis catalogue ablation emits the same 589 candidates
and all pass, while RF-positive outputs fall from 589 to 456.

The published-program study includes every HumanEval and MBPP file supplied for
both named models, 1,138 per model. GPT-4o has 948 passing originals and retains
934 passing outputs; Qwen has 826 passing originals and retains 761. Among
qualified originals, the measured losses are 14 emitted failures for GPT-4o,
and 13 emitted failures plus 52 completed no-output events for Qwen. One Qwen
task has unavailable original and candidate observations due to the wall budget.
Full-population outcomes and all before/after transitions are retained alongside
the qualification-conditioned preservation results.

The primary generated-program contract executes the exact official prompt and
completion in program globals, binds the original entry object, executes the
unchanged original test in a shallow copy of those globals, and passes the
original object to the test's `check`. This separates namespace bindings while
sharing imported modules and original objects. It preserves the candidate's
own globals and adds no value encoding or function wrapper.

## Audit and contract evidence

`accepted/comparison` contains the 45 complete audit traces over the full
591-attempt workload. Source-sharing identity includes both programs, the
complete contract, observer identity, and execution environment. Shared C
certificates use the paired ratio envelope with separate-interval fallback.
The RF pooled query counts are 22 versus 461 for J; for C they are 168 for the
H-first acquisition ablation, 3 for independent minimax, and 3 for the public
point-interval adaptive rule. Every prefix and query choice is independently
received. These are retrospective disclosure counts from fresh measurements.

`contract-sensitivity/summary.json` compares all 4,434 generated-program native
observations with literal mxeval executor assembly. Four official MBPP entries
are named `check`, which conflicts with the test function of that name. Five
model/task pairs change labels, original and candidate together; all changes
belong to these entries. Four official canonical-solution controls confirm the
collision. Literal assembly and preceding typed observations remain separately
available under `contract-sensitivity`; they are not the current functional
results. `accepted/causes` holds the 45 fresh rule interventions underlying the
15 canonical failures.



## Receive the delivered evidence

Run from the project root. The dependencies include the exact compatible scikit-learn model environment and libarchive bindings; the system libarchive library is also required. A separate Python environment can be used for these dependencies.

```sh
python3 -m pip install -r artifact/studies/crest/requirements.txt
python3 -B -S artifact/check.py --scope primary --output ../primary-receiving
```

The primary check acquires only the exact public upstream core, classifiers and thresholds specified by the original protocol, checks their recorded identities, and loads models only after this verification. Acquisition happens inside the temporary working tree. To acquire a reusable local cache first:

```sh
python3 artifact/studies/crest/acquire_crest_upstream.py --output ../crest-upstream
python3 -B -S artifact/check.py --scope primary \
  --crest-upstream-cache ../crest-upstream --output ../primary-receiving-cached
```

The receiver checks all four program populations, native requests, the source-to-task and generation chains, fixed detector scores, complete contract sensitivity, every causal intervention, and all 45 paired comparison traces. The top-level paper-data checks independently reconstruct the tables, transition matrices, macro values and plot coordinates. The clean directory names are restored to their originally recorded locations only inside isolated temporary work; retained evidence is not edited.

The raw inputs include the published archive and official mxeval contract files. Archive bytes and UTF-8 text with universal-newline decoding are verified separately; the 974 GPT-4o MBPP files undergo only CRLF-to-LF decoding.

## Fresh functional execution

Use the common producer entry from the project root and choose a new external result directory:

```sh
python3 artifact/run.py --output ../crest-functional \
  studies/crest/reexecute_crest_isolated_assertions.py -- \
  --source studies/crest/contract-sensitivity/typed \
  --output '{output}' --workers 4
```

The source study supplies the fixed generation and detector records. Every original and emitted candidate is executed afresh under the uniform separated-namespace contract. Resource limits, installed dependencies, assertion settings and submitted requests are recorded. The preceding typed labels do not determine the new outcomes. The common entry preserves partial results if execution fails and never overwrites supplied evidence. The ten native execution-contract controls are run separately by `artifact/check.py --scope tests`; they are implementation fixtures, not extra benchmark samples.

## Provenance

Upstream implementation and published programs: <https://github.com/niccap/crest>.
Official prompts and assertions: <https://github.com/amazon-science/mxeval>.
The upstream repository describes its associated manuscript as submitted.
The included mxeval license accompanies its original contract files. Upstream
CREST code and classifiers are acquired from their own repository; no project
license is assigned to them here.

`provenance/generation-records` retains the exact original generation records
required by the receiving chain. Their older behavioral fields are provenance
only and are never used as current outcomes. The two additional classifier heads
are sensitivity readings on the same programs. The released generated cohorts
also participate in the upstream classifier data workflow, so their detector
readings are not presented as independent held-out generalization estimates.
