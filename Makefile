.DEFAULT_GOAL := help
.PHONY: help verify verify-primary verify-supporting test publication artifact-smoke artifact-check artifact-paper
PYTHON ?= python3
# Optional: directory with the paper LaTeX sources (default ../paper); enables the paper-binding checks.
PAPER ?=
PAPER_ARG := $(if $(PAPER),--paper $(PAPER))
# Optional: previously acquired CREST upstream files (otherwise downloaded from GitHub).
CREST_CACHE ?=
CREST_ARG := $(if $(CREST_CACHE),--crest-upstream-cache $(CREST_CACHE))

help:
	@echo "make artifact-smoke   fast evidence receivers (+ paper bindings if the paper is present), ~2 min"
	@echo "make artifact-check   tests + primary + supporting receivers (see README for Node.js/CREST needs)"
	@echo "make artifact-paper   regenerate tables/figures and compile ../paper (submission package only)"
	@echo "make verify | verify-primary | verify-supporting | test | publication   individual check.py scopes"
	@echo "Add PAPER=DIR to point the paper-binding checks at the paper LaTeX sources."

# Every scope runs in a disposable copy that restores the recorded layout.
verify:
	$(PYTHON) -B -S check.py --keep-going $(PAPER_ARG) $(CREST_ARG)

verify-primary:
	$(PYTHON) -B -S check.py --scope primary --keep-going $(CREST_ARG)

verify-supporting:
	$(PYTHON) -B -S check.py --scope supporting --keep-going

test:
	$(PYTHON) -B -S check.py --scope tests --keep-going $(PAPER_ARG)

publication:
	$(PYTHON) -B -S check.py --scope publication $(PAPER_ARG)

artifact-smoke:
	$(PYTHON) tools/artifact_check.py smoke --python $(PYTHON) $(PAPER_ARG)

artifact-check:
	$(PYTHON) tools/artifact_check.py full --python $(PYTHON) $(PAPER_ARG) $(CREST_ARG)

artifact-paper:
	$(PYTHON) tools/artifact_check.py paper --python $(PYTHON)
