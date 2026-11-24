# Reference and claim review

The current manuscript contains **66 bibliography entries**, cites **66 distinct keys** at **66 citation positions**, and leaves no bibliography entry unused. The local audit reports no duplicate keys, undefined citations, missing required metadata, malformed DOI strings, or missing source locators.

Claim-level source review is deliberately reported at two different strengths:

- **30 cited clauses** were reopened after the Round 5 reorganization and checked against the source scope already recorded in this project. Their status is `RECHECKED_AGAINST_RECORDED_SOURCE_SCOPE`.
- **36 cited clauses** retain bibliographic identity and a source locator but were not freshly reopened for claim-entailment review in this round. Their status is `NOT_AUTOMATICALLY_ASSESSED`; the manuscript uses them for narrow background or category placement, but this status is not a whole-paper reading claim.

The review therefore does **not** claim that all 66 works were read in full. It distinguishes selected body passages, abstracts, official repositories or project pages, retained source records, and local primary data. No citation count is used as a substitute for support.

## What was checked

For the 30 rechecked clauses, source access is recorded at the level actually inspected: selected body passages or scanned pages, abstracts, repository and executor files, author project pages, and publisher overviews. These records support the attributed clauses; they do not claim complete-work readings. Bibliographic identity, the cited source's substantive claim, and this paper's own empirical result remain separate.

The public input inventories were checked against their retained primary files: 164 HumanEval tasks, 427 sanitized MBPP tasks, and 164 HumanEval+ records with 1,570 base and 122,683 additional input tuples. The generated-program study joins every released program to the original mxeval prompt, tests, and entry point. Dataset inventory is not attributed to publication abstracts.

## Resolved attribution and metadata questions

- CREST is cited as released software. Its repository describes the associated manuscript as submitted; the bibliography does not invent a publication.
- The mxeval citation supplies benchmark infrastructure and task context. The isolated-namespace assertion contract is explicitly this study's declared contract, and the literal executor comparison remains a separate study.
- Ma et al.'s TOSEM article is cited for uncertainty-based selection aimed at misclassification discovery and retraining. Final publisher identity and author-preprint technical support are recorded separately.
- Metric-validation sources retain distinct contributions: Fenton on representation, Kitchenham on measurement models, and Meneely on intended use.
- The prior coefficient-order result is restricted to linear thresholds with uniform independent bits and unit costs. Conditional-ratio comparison is this paper's separate target.
- Regression-test selection is scoped to an existing suite. General fractional programming and partial identification supply background; the local Boolean endpoint and comparison proofs remain explicitly derived in the paper.
- Kitchenham's page range is 929--944. Meneely's publication year is distinguished from the journal issue date using the first-author bibliographic record.
- STONE, SrcMarker, and Mark My Words use verified final publication metadata, irrespective of internal citation-key spelling.
- The current Mark My Words title/year differ from an older retained receipt because the official SaTML 2025 record supersedes the preprint metadata; the audit records that reconciliation explicitly.

## Access ledger for the 30 rechecked clauses

| Reference key | Inspected source level | Occurrences | Inspected scope |
| --- | --- | ---: | --- |
| `acw2026` | FRESH_SELECTED_BODY_AUTHOR_PREPRINT | 2 | Sections IV-D and IV-E: utility evaluation and post-attack Pass Rate alongside TPR/FPR. |
| `athiwaratkun2022mxeval` | FRESH_PRIMARY_EXECUTOR_DATA_AND_CITATION | 1 | Official repository README, supplied bibliography, frozen HumanEval/MBPP task fields, and execution.py check_correctness: prompt, completion, unchanged test and final entry-point call. The isolated program/test namespaces are this study's declared contract, not a property attributed to the official executor. |
| `austin2021mbpp` | FRESH_SELECTED_BODY_AND_FROZEN_PRIMARY_DATA | 2 | Section 2.1 on short Python tasks, reference solutions and tests; local frozen sanitized file and provenance reopened. |
| `barr2015` | FRESH_SELECTED_BODY_AUTHOR_MANUSCRIPT | 1 | Abstract and Sections 2.2–2.3, especially Definition 2.4 on oracle information and observed activities. |
| `chen2021humaneval` | FRESH_SELECTED_BODY_AND_FROZEN_PRIMARY_DATA | 2 | Introduction on the 164 unit-tested benchmark tasks; frozen records, canonical solutions, tests and provenance reopened. |
| `crest2026` | FRESH_PRIMARY_REPOSITORY_AND_EXECUTED_SOURCE | 3 | Public repository README: source-transform catalogue, embedding/detection CLI, default random forest and two logistic heads, released thresholds and data archive. Executed emitter/detector source and archive acquisition are retained in the empirical study. |
| `deshpande2014sbfe` | FRESH_SELECTED_BODY_AUTHOR_PREPRINT | 1 | Introduction and Section 2, PDF page index 2: product distribution, costs, certificates, linear-function ranking and the restricted coefficient-ordering result. |
| `dinkelbach1967` | FRESH_PUBLISHER_ABSTRACT | 1 | Complete publisher abstract and bibliographic header; no body theorem attributed. |
| `fenton1994` | FRESH_SELECTED_BODY_AUTHOR_POSTED_PAPER | 1 | Printed pages 199–200, Sections II-A and II-B: attributes, empirical relations, and numerical representation. |
| `guan2024` | FRESH_SELECTED_BODY_FINAL_PAPER | 1 | Section 4.3, printed page 9248: CodeBLEU and the absence of test cases in the CodeSearchNet evaluation. |
| `kim2025` | FRESH_SELECTED_BODY_FINAL_PAPER | 1 | Section 3.2, printed pages 3992–3993: STEM and weights over functional correctness, detectability and imperceptibility. |
| `kitchenham1995` | FRESH_PUBLISHER_INDEXED_ABSTRACT | 1 | Complete IEEE-indexed abstract on measurement structure, attributes, protocols and population models; publisher page range. |
| `kossen2021active` | FRESH_SELECTED_BODY_FINAL_PAPER | 1 | Abstract, introduction and Section 2.2: costly test labels, model-risk estimates and acquisition-bias correction. |
| `le2014emi` | FRESH_SELECTED_BODY_AUTHOR_MANUSCRIPT | 1 | Introduction and Section 3.1.1: equivalence quantified over a specified set of program inputs. |
| `lee2024` | FRESH_SELECTED_BODY_AUTHOR_PREPRINT | 1 | Section 4.1: pass@k, AUROC, and TPR at an explicit FPR operating point. |
| `liang2025waterpark` | FRESH_SELECTED_BODY_FINAL_PAPER | 2 | Section 3.2 evaluation metrics and Section 4.2.5 attack-quality assessment. |
| `liu2023evalplus` | FRESH_PUBLISHER_ABSTRACT_AND_FROZEN_PRIMARY_DATA | 2 | Complete publisher abstract and metadata; local v0.1.10 input inventory and provenance reopened. |
| `ma2021selection` | FRESH_SELECTED_BODY_AUTHOR_PREPRINT | 1 | Author preprint abstract, introduction and objectives distinguish selection for finding misclassifications from selection for retraining. Final bibliographic metadata verified against the University of Luxembourg repository record. |
| `manski2003` | FRESH_PUBLISHER_OVERVIEW_AND_METADATA | 1 | Publisher About this book: identification regions under assumptions of varying strength. |
| `meneely2013` | FRESH_SELECTED_BODY_AUTHOR_MANUSCRIPT | 1 | Section 7 and opening of Section 7.1, manuscript pages 26–27, on selecting validation criteria by intended use; first-author publication/BibTeX entry. |
| `necula2000` | FRESH_SELECTED_BODY_AUTHOR_MANUSCRIPT | 1 | Section 2, PDF page 2: source/target relation over calls, returns and memory state. |
| `pan2024markllm` | FRESH_SELECTED_BODY_FINAL_PAPER | 2 | Appendix A.1, printed page 70: detection, robustness and text-quality evaluation pipelines. |
| `piet2024markmywords` | FRESH_AUTHOR_PROJECT_AND_CONFERENCE_ABSTRACT | 2 | Author project Abstract and Metrics sections; official 2025 conference entry. |
| `rothermel1997` | FRESH_FINAL_PAPER_ABSTRACT | 1 | Complete abstract and first-page publication information, with introduction context. |
| `sew2026` | FRESH_SELECTED_BODY_AUTHOR_PREPRINT | 2 | Sections 3.1–3.3 and Appendix I: keyed style rules, structural context, eligibility and type/effect checks. |
| `sjoberg2023` | FRESH_SELECTED_BODY_AUTHOR_POSTED_MANUSCRIPT | 1 | Manuscript page 2, Sections 2.1–2.2 on operationalization and validation evidence. |
| `sjoberg2023reporting` | FRESH_SELECTED_BODY_AUTHOR_PREPRINT | 1 | Sections 3.2–3.4 on clear constructs, consistent operationalization and specific validity threats. |
| `weyuker1982` | FRESH_SELECTED_SCANNED_PAGES | 1 | Actual page images of printed pages 465–466, including the oracle problem and partial/pseudo-oracles. |
| `yang2011compiler` | FRESH_SELECTED_BODY_AUTHOR_HOSTED_PAPER | 1 | Introduction and Section 2.1: compile/run/output comparison and generated programs with a unique interpretation. |
| `yang2023` | FRESH_SELECTED_BODY_AUTHOR_PREPRINT | 1 | Sections IV-B and IV-C: correctness checks using supplied unit tests and bit/message recovery; official 2024 program title/byline. |

## Clauses not freshly reopened in this round

The following 36 keys have current locators and valid bibliography metadata but remain `NOT_AUTOMATICALLY_ASSESSED` for claim-entailment in this revision:

```
basili1986 cadar2008 cassano2023multiple chen2018metamorphic collberg1997 collberg2002 demillo1978 engstrom2010 fraser2011 godefroid2005 golovin2011 hendrycks2021apps jia2011 just2014 kitchenham2002 leroy2009 li2022alphacode lopes2015 mckeeman1998 mcminn2004 monden2000 nagra2004 pacheco2007 pnueli1998 rothermel1998 rothermel2001 runeson2009 segura2016metamorphic settles2009 shamshiri2015 stern2000 tristan2011 venkatesan2001 wohlin2012 wohlin2014 yoo2012
```

This is not a missing-key or missing-locator error. It is an explicit review boundary. Any future edit that makes one of these sources carry a claim-critical premise must reopen the exact source and replace this status with a paragraph-bound assessment.

## Checking the current files

`artifact/citation-current/claim-reviews.json` records the 30 current paragraph-bound reassessments. `artifact/citation-current/verified-sources.json` records source access, usable support, limits, and bibliographic identity. `artifact/citation-current/citation-positions.csv` maps the assessments to the current TeX source. `artifact/citation-current/audit.json` traverses the complete main and supplement input graph and records all 66 cited keys, including the 36 explicitly unassessed clauses.

The canonical packaged copies under `artifact/citations/` mirror the current audit inputs. From the project root, run:

```sh
python3 -B -S artifact/check.py --scope publication
```

Publication receiving restores the recorded paths in an isolated copy and checks the current manuscript, record identities, and source bindings. A changed cited clause must be assessed against its source before its paragraph hash and review status are updated.
