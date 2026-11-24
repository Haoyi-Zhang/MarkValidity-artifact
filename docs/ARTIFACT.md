# Artifact evaluation

This repository separates three questions that should not be conflated during review.

1. `make artifact-smoke` stages the immutable evidence in a disposable copy and runs a fast subset of the evidence receivers; when the paper sources are available (`../paper` or `PAPER=DIR`) it also verifies the bindings between the paper, data, and cited sources. It is the recommended first command.
2. `make artifact-check` runs implementation tests, rejection paths, and all scientific evidence receivers used by the paper's principal claims.
3. `make artifact-paper` regenerates the publication figures and compiles the manuscript and supplement from the checked evidence (submission package with `../paper` only).

Each command prints a stage before running it, reports the elapsed time and exit status, and writes a machine-readable report under `.worktree/`. Components whose prerequisites are missing (paper sources, CREST packages) are reported as `SKIPPED`, never as passed; a failed component makes its stage and the command fail.

## What is executed locally

The local checks execute the behavior-suite receivers, exact comparison logic, conflict and unavailable-evidence paths, paper-data consistency checks, figure generation, and LaTeX build. The retained program outputs, detector decisions, and native execution receipts are bound to the inputs used by these checks.

## What remains retained provenance

Historical hosted-model generation calls and released detector outputs are retained inputs. They are not presented as fresh API calls. The paper's comparison and behavior claims can be checked locally from the supplied evidence; recreating the original hosted services is outside the deterministic artifact path.

## Expected outcomes

A successful smoke check establishes that the repository is complete enough to inspect and that the paper refers to the supplied evidence. A successful full check establishes that the implementation, rejection paths, comparison certificates, and retained observations agree. A successful paper check establishes that the figures and PDFs can be rebuilt from the checked evidence and the paper sources.

These outcomes are evidence for artifact quality. Formal ACM badges, if requested, remain decisions of the journal's artifact-review process.

## Validation-host timings

On the reference host used to prepare this package, `artifact-smoke` took about 1 minute, the non-CREST part of `artifact-check` about 6 minutes, and figure regeneration under a minute (each run includes about 50 s for staging the disposable copy). These are observations rather than time limits; hardware and filesystem performance will change them. Each command reports its own stages so a reviewer can identify the active receiver.
