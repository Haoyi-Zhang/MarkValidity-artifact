# MBPP data license and attribution

The **Mostly Basic Python Problems (MBPP)** dataset is attributed to **Google Research** and **Jacob Austin et al.**, released with *Program Synthesis with Large Language Models* (2021), arXiv:2108.07732.

The official Google Research MBPP dataset card declares the dataset license as **Creative Commons Attribution 4.0 International (CC BY 4.0)**. The license URL is https://creativecommons.org/licenses/by/4.0/ and its legal code is https://creativecommons.org/licenses/by/4.0/legalcode.en . Retain this attribution, the license link, and the indication of changes when redistributing these data or derived candidate programs. The original creators do not endorse this study.

## Source and exact copy

- Official dataset card, pinned revision: https://huggingface.co/datasets/google-research-datasets/mbpp/blob/4bb6404fdc6cacfda99d4ac4205087b89d32030c/README.md
- Dataset repository: https://github.com/google-research/google-research/tree/f82046ba5aabbbb427dbfd38a254d26bff08b533/mbpp
- Exact distributed file: `sanitized-mbpp.json` from that Google Research commit.
- File SHA256: `ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9`.
- Git blob SHA1: `a999d25df7e489e4c183cadfa5c0ecf557a702b6`.
- Publication: https://arxiv.org/abs/2108.07732 .

The complete original JSON bytes, all 427 reference programs, and all declared imports/assertions are preserved without edits. Emitted candidate `.py` files in the results are modified versions created by the pinned SEW tool and the named local patches. Their reference identity, key, method identity, and candidate-source digest are recorded in the corresponding ledger. The S1/S4 modifications and the execution protocol are described in `README.md`; original test statements were not rewritten for the primary evaluation. Standalone diagnostic scripts additionally print a return value after the unchanged assertion passes, and are marked as diagnostics.

## Distinct software licenses

`REPOSITORY_LICENSE` preserves the **Apache License 2.0** file from the Google Research repository. It records the repository's general software license; it is not used to relabel the MBPP data as Apache-only or MIT. The dataset-specific CC BY 4.0 notice above is retained separately.

The SEW implementation and copied local variants keep their **MIT** license files under `../variants/{stock,s1,s4,s1_s4}/LICENSE`. The evaluation scripts authored for this artifact follow the artifact's MIT license at `../../../LICENSE`. These software notices do not replace the data attribution.
