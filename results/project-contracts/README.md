# Call contracts on frozen project modules

This extension executes three targets already present in the 120-module
parse/compile audit. It asks whether the same parameter rename preserves both
positional and keyword calls. The selected complete modules require only
builtins or the standard library, so their retained bytes can be executed
without replacing third-party dependencies.

| Frozen module | Project version | Target | Input-value domain |
| --- | --- | --- | --- |
| `attrs-01` | attrs 26.1.0 | `set_run_validators` | Both Boolean values; the existing getter observes the resulting setting |
| `idna-02` | idna 3.17 | `intranges_from_list` | All 781 lists of lengths zero through four over integers zero through four |
| `jmespath-01` | jmespath 1.1.0 | `comparator` | Six comparator names and all nine pairs of three explicit AST-node values, giving 54 cases |

The 837 argument vectors are each invoked positionally and by the original
keyword names. The reference, a trailing comment, the existing syntax-aware
parameter rename, and a repair that preserves the signature while introducing
a fresh internal alias give 6,696 actual native invocations. Every invocation
initializes a fresh module namespace and receives a deep copy of its arguments.
Return and exception observations have disjoint tags. Builtin return types are
retained, and the attrs setter also exposes its state through its own getter.

All four variants parse and compile. The parameter rename preserves all 837
positional observations and fails all 837 keyword observations with an
unexpected-keyword `TypeError`. Both the comment control and the signature-
preserving alias preserve both calling conventions. This is a counterexample
to transferring a positional-only result to a keyword-call contract. It is not
an estimate of failures in these projects or a claim about whole-project tests.

`contracts.json` specifies the sources, hashes, inputs, observation contract,
runtime, and edits. `observations.csv.gz` retains every result; `sources/`
contains the exact executed modules. The input modules and original licenses
remain in `../../corpus/transfer/` and `../../corpus/licenses/`. These derived
copies retain the corresponding upstream license terms; the project license
does not replace them. The source identities are checked against the existing
transfer manifest before generation.

From the artifact directory, generate a new result directory:

```sh
python3 -B -S check_project_contracts.py --out /absolute/new/project-contracts
```

Receive the saved sources without regenerating any edit:

```sh
python3 -B -S check_project_contracts.py --verify
```

The receiving mode actually reexecutes all 6,696 calls, checks each saved
observation and reconstructs the summary. It shares the declared observation
routine with the producer; it is not represented as an independently designed
Python interpreter or a general-purpose sandbox. `receiving-check.json`
records the completed receiving run.
