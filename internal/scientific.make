# Run from this artifact root. Default checks receive current retained evidence.
.DEFAULT_GOAL := verify
.PHONY: all verify verify-natural verify-supporting verify-humaneval verify-mbpp \
	verify-comparisons verify-native-audit verify-python verify-javascript verify-budget verify-sew \
	verify-project-contracts verify-history verify-sew-upstream parity-delivered \
	test reproduce-fresh fresh-python fresh-javascript fresh-budget \
	fresh-project-contracts fresh-sew legacy-reproduce recheck clean-results

PYTHON ?= python3
RESULTS ?= results/revision-reproduction
EVIDENCE ?= results/revision-source-joint
FRESH_PYTHON ?= results/revision-python-fresh
FRESH_NATIVE ?= results/revision-native-completion
FRESH_BUDGET ?= results/revision-audit-budget
SEW_RESULTS ?= results/revision-sew-aliasing
PROJECT_RESULTS ?= results/revision-project-contracts
NATURAL := external-studies/sew_natural
NATURAL_RESULTS := results/revision-sew-natural

# Keep generated native inputs within this artifact root: budget registration
# binds their paths relative to this root. Generation requires new output trees.
FRESH_ROOT ?= .reproduction-v2
PYTHON_OUT ?= $(FRESH_ROOT)/python-fresh
NATIVE_OUT ?= $(FRESH_ROOT)/native-completion
BUDGET_OUT ?= $(FRESH_ROOT)/audit-budget
PROJECT_OUT ?= $(FRESH_ROOT)/project-contracts
SEW_OUT ?= $(FRESH_ROOT)/sew
WORKERS ?= 2
LEGACY_OUT ?= .reproduction-v1/results

all: verify

verify: verify-natural verify-supporting

verify-natural: verify-humaneval verify-mbpp verify-comparisons verify-native-audit

verify-supporting: verify-python verify-javascript verify-budget verify-sew verify-project-contracts

verify-humaneval:
	$(PYTHON) -B -S $(NATURAL)/scripts/humaneval/verify_humaneval.py \
		--main-results $(NATURAL_RESULTS)/humaneval \
		--enhanced-results $(NATURAL_RESULTS)/enhanced-humaneval \
		--data $(NATURAL)/data/HumanEval.jsonl.gz \
		--plus-data $(NATURAL)/data/HumanEvalPlus-v0.1.10.jsonl.gz \
		--primary-runner $(NATURAL)/scripts/humaneval/native_runner_v3.py \
		--enhanced-runner $(NATURAL)/scripts/humaneval/native_pairs_v3.py \
		--variants-root $(NATURAL)/variants

verify-mbpp:
	$(PYTHON) -B -S $(NATURAL)/mbpp/scripts/verify_normalized.py --results-root $(NATURAL_RESULTS)/mbpp

verify-comparisons:
	$(PYTHON) -B -S scripts/check_algorithm_branches.py
	$(PYTHON) -B -S $(NATURAL)/analysis/verify_conditional_bounds.py
	$(PYTHON) -B -S $(NATURAL)/analysis/verify_natural_analysis.py
	$(PYTHON) -B -S $(NATURAL)/analysis/verify_natural_results.py --analysis $(NATURAL_RESULTS)/analysis-primary
	$(PYTHON) -B -S $(NATURAL)/analysis/verify_natural_results.py --analysis $(NATURAL_RESULTS)/analysis-all-withheld
	$(PYTHON) -B -S $(NATURAL)/comparison_costs/verify.py --artifact . \
		--results results/revision-sew-comparison-costs

verify-native-audit:
	$(PYTHON) -B -S $(NATURAL)/analysis/verify_native_audit.py --artifact . \
		--registry $(NATURAL_RESULTS)/public-registry.json --audit $(NATURAL_RESULTS)/native-audit
	$(PYTHON) -B -S $(NATURAL)/analysis/compare_native_retrospective.py \
		--audit $(NATURAL_RESULTS)/native-audit \
		--analysis $(NATURAL_RESULTS)/analysis-primary

verify-python:
	$(PYTHON) -B -S verify_python_fresh.py --fresh "$(FRESH_PYTHON)" --results "$(RESULTS)" --evidence "$(EVIDENCE)"
	$(PYTHON) -B -S scripts/exact_detector_null.py --verify results/revision-exact-null/full-word-enumeration.json

verify-javascript:
	$(PYTHON) -B -S verify_javascript_completion.py --out "$(FRESH_NATIVE)" --retained "$(RESULTS)" --evidence "$(EVIDENCE)"

verify-budget:
	$(PYTHON) -B -S verify_source_budget.py --out "$(FRESH_BUDGET)" --native "$(FRESH_NATIVE)" --retained "$(RESULTS)" --evidence "$(EVIDENCE)"

verify-sew:
	$(PYTHON) -B -S external-studies/sew_aliasing/verify_study.py --results "$(SEW_RESULTS)"

verify-project-contracts:
	$(PYTHON) -B -S check_project_contracts.py --out "$(PROJECT_RESULTS)" --verify

verify-history:
	$(PYTHON) -B -S verify_historical_source_joint.py --results "$(RESULTS)" --evidence "$(EVIDENCE)"

# Optional upstream replay requires the parser versions in the SEW requirements.
verify-sew-upstream:
	$(PYTHON) -B external-studies/sew_aliasing/verify_study.py --results "$(SEW_RESULTS)" --replay-upstream

# Fixed delivered paths; rewrites two deterministic derived outputs.
parity-delivered:
	$(PYTHON) -B -S verify_fresh_cross_language.py

test:
	PYTHONPATH=src $(PYTHON) -B -S -m unittest discover -s tests -p 'test*.py' -v
	$(PYTHON) -B -S -m unittest discover -s regressions -p 'test*.py' -v

# Sequential submakes even with make -j: budget needs the new native receipt.
reproduce-fresh:
	$(MAKE) fresh-python
	$(MAKE) fresh-javascript
	$(MAKE) fresh-budget

fresh-python:
	@test ! -e "$(PYTHON_OUT)" || (echo "Choose a fresh PYTHON_OUT; existing results will not be overwritten." >&2; exit 2)
	$(PYTHON) -B -S recheck_python_fresh.py --out "$(PYTHON_OUT)" --results "$(RESULTS)" --evidence "$(EVIDENCE)"
	$(PYTHON) -B -S verify_python_fresh.py --fresh "$(PYTHON_OUT)" --results "$(RESULTS)" --evidence "$(EVIDENCE)" > "$(PYTHON_OUT)/verification.json"

fresh-javascript:
	@test ! -e "$(NATIVE_OUT)" || (echo "Choose a fresh NATIVE_OUT; existing results will not be overwritten." >&2; exit 2)
	$(PYTHON) -B -S complete_javascript_sources.py --out "$(NATIVE_OUT)" --workers "$(WORKERS)" --retained "$(RESULTS)" --evidence "$(EVIDENCE)"
	$(PYTHON) -B -S verify_javascript_completion.py --out "$(NATIVE_OUT)" --retained "$(RESULTS)" --evidence "$(EVIDENCE)" > "$(NATIVE_OUT)/verification.json"

fresh-budget:
	@test ! -e "$(BUDGET_OUT)" || (echo "Choose a fresh BUDGET_OUT; existing results will not be overwritten." >&2; exit 2)
	$(PYTHON) -B -S audit_source_budget.py --out "$(BUDGET_OUT)" --native "$(NATIVE_OUT)" --retained "$(RESULTS)" --evidence "$(EVIDENCE)"
	$(PYTHON) -B -S verify_source_budget.py --out "$(BUDGET_OUT)" --native "$(NATIVE_OUT)" --retained "$(RESULTS)" --evidence "$(EVIDENCE)" > "$(BUDGET_OUT)/verification.json"

fresh-project-contracts:
	@test ! -e "$(PROJECT_OUT)" || (echo "Choose a fresh PROJECT_OUT; existing results will not be overwritten." >&2; exit 2)
	$(PYTHON) -B -S check_project_contracts.py --out "$(PROJECT_OUT)"
	$(PYTHON) -B -S check_project_contracts.py --out "$(PROJECT_OUT)" --verify > "$(PROJECT_OUT)/receiving-check.json"

fresh-sew:
	@test ! -e "$(SEW_OUT)" || (echo "Choose a fresh SEW_OUT; existing results will not be overwritten." >&2; exit 2)
	$(PYTHON) -B external-studies/sew_aliasing/run_study.py --out "$(SEW_OUT)"
	$(PYTHON) -B external-studies/sew_aliasing/verify_study.py --results "$(SEW_OUT)" --replay-upstream > "$(SEW_OUT)/receiving-check.json"

# Original benchmark keeps its v1 observation and initialization semantics.
legacy-reproduce:
	@test ! -e "$(LEGACY_OUT)" || (echo "Choose a fresh LEGACY_OUT; existing results will not be overwritten." >&2; exit 2)
	$(PYTHON) -B run_all.py --out "$(LEGACY_OUT)"
	$(PYTHON) -B recheck.py --results "$(LEGACY_OUT)"

recheck:
	@test -n "$(OUT_RECHECK)" || (echo "Set OUT_RECHECK to a disposable result copy; recheck updates its manifest." >&2; exit 2)
	$(PYTHON) -B recheck.py --results "$(OUT_RECHECK)"

clean-results:
	@echo "Retained results are not a clean target. Remove only your own disposable output explicitly." >&2
	@exit 2
