PYTHON ?= python3
DEV = $(PYTHON) tools/development/check.py

.PHONY: setup check check-ci check-go check-workflows test-tools test-toolchain test-race check-vuln

setup:
	$(DEV) setup $(SETUP_ARGS)

check:
	$(DEV) check

check-ci:
	$(DEV) ci $(PUBLICATION_ARGS)

check-go:
	$(DEV) go

check-workflows:
	$(DEV) workflows

test-tools:
	$(DEV) tooling

test-toolchain:
	$(DEV) toolchain

test-race:
	$(DEV) race

check-vuln:
	$(DEV) vuln
