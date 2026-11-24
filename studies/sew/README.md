# Paired SEW study

This study transforms the 164 HumanEval and 427 sanitized MBPP reference programs under three fixed keys and four SEW treatments: the released emitter and detector, a numeric-assignment eligibility guard, a return-token boundary repair, and their combination. The original assertion suites define the primary behavioral labels. Expanded HumanEval inputs use a separate paired observation contract.

The complete source trees and licenses are in `variants/`. Inputs are in `data/`; observers and producers are in `scripts/humaneval/` and `mbpp/scripts/`. The paired observations are in `../../results/sew/`. The current paper's supplementary protocol describes the intervention rules, initialization, assertion semantics, resource handling, and denominators.

From the project root, `python3 -B -S artifact/check.py --scope primary` independently receives these records and the comparison analyses. To execute a producer, use `artifact/run.py` as described in the [artifact guide](../../README.md). This entry restores the original recording paths in a temporary copy and saves new outputs separately.
