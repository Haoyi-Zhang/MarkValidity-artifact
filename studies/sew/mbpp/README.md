# Sanitized MBPP observation contract

The study includes all 427 tasks in the retained sanitized MBPP file. Each candidate is evaluated with the task's original imports and assertion list. The observer records compilation, assertion outcomes, and terminal counters. An independently received assertion failure supplies a behavioral counterexample; incomplete or unavailable observation does not supply a success label.

`scripts/` contains the producer, observer, normalization, and receiving code. The original data and upstream attribution accompany the study. Complete observations and normalized paired rows are in `../../../results/sew/mbpp/`. Source and contract identities join each detector decision to the candidate that was actually checked.

The primary artifact check independently reconstructs all paired outcomes. Fresh producer runs use the common `artifact/run.py` entry point and a new result directory. The supplementary protocol states the full execution environment and observation policy.
