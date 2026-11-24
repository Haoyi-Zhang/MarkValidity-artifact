# Generation provenance

These records preserve the original source-to-candidate and detector evidence.
The receiving chain checks their exact bytes, the source files they name, the
upstream implementation/model/threshold identities, and the official inputs.
No behavioral label in this directory is admitted as a current functional
outcome. Current results are only in `../accepted`.

`generation-records/full-study` and `catalogue-ablation` describe the canonical
workload generation. `generated-gpt4o` and `generated-qwen` describe complete
published input populations and their emitted candidates. `context-gpt4o` and
`context-qwen` preserve the intermediate native-context stage that links to the
same generation records. Current original/candidate observations were obtained
by new executions under the protocols in `accepted`.

`causal-generation` retains the original intervention output record. The 45
current request-bound intervention observations are in `accepted/causes`.
