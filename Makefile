.DEFAULT_GOAL := help

PYTHON ?= python3
PIPX ?= pipx
NPX ?= npx
ALGO ?= algo
EXAMPLE ?= examples/arithmetic.algo
WATCH ?=
EXTENSION_OUTPUT ?= build/algolang.vsix

.PHONY: help setup install hooks test test-lexer extension-check build-extension run check ast dryrun

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
		'  extension-check  Validate the VS Code extension JavaScript' \
		'  build-extension  Package the VS Code extension as a VSIX' \
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

extension-check:
	cd vscode-extension && npm run check

build-extension: extension-check
	mkdir -p $(dir $(EXTENSION_OUTPUT))
	cd vscode-extension && $(NPX) --yes @vscode/vsce package --out ../$(EXTENSION_OUTPUT)

run:
	$(ALGO) run $(EXAMPLE)

check:
	$(ALGO) check $(EXAMPLE)

ast:
	$(ALGO) ast $(EXAMPLE)

dryrun:
	$(ALGO) dryrun $(EXAMPLE) $(if $(WATCH),--watch $(WATCH),)
