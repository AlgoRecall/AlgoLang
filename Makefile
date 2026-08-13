.DEFAULT_GOAL := help

PYTHON ?= python3
PIPX ?= pipx
ALGO ?= algo
EXAMPLE ?= examples/arithmetic.algo
WATCH ?=

.PHONY: help setup install hooks test test-lexer run check ast dryrun

help:
	@printf '%s\n' \
		'Usage: make <target> [EXAMPLE=path] [WATCH=name1,name2]' \
		'' \
		'Targets:' \
		'  setup       Install AlgoLang with pipx and enable Git hooks' \
		'  install     Install the editable AlgoLang CLI with pipx' \
		'  hooks       Enable the version-controlled Git hooks' \
		'  test        Run the complete test suite' \
		'  test-lexer  Run only lexer tests' \
		'  run         Run EXAMPLE' \
		'  check       Type-check EXAMPLE' \
		'  ast         Print the AST for EXAMPLE' \
		'  dryrun      Dry-run EXAMPLE, optionally watching WATCH variables'

setup: install hooks

install:
	$(PIPX) install --editable . --force

hooks:
	./scripts/setup-git-hooks.sh

test:
	$(PYTHON) -B -m unittest discover -s tests -v

test-lexer:
	$(PYTHON) -B -m unittest discover -s tests/lexer -v

run:
	$(ALGO) run $(EXAMPLE)

check:
	$(ALGO) check $(EXAMPLE)

ast:
	$(ALGO) ast $(EXAMPLE)

dryrun:
	$(ALGO) dryrun $(EXAMPLE) $(if $(WATCH),--watch $(WATCH),)
