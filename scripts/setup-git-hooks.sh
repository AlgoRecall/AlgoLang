#!/bin/sh

set -eu

repository_root=$(git rev-parse --show-toplevel)
cd "$repository_root"

chmod +x \
    .githooks/pre-commit \
    .githooks/commit-msg \
    scripts/lint-branch-name.sh \
    scripts/lint-commit-message.sh \
    scripts/setup-git-hooks.sh

git config --local core.hooksPath .githooks

printf 'AlgoLang Git hooks enabled for this checkout.\n'
printf 'Branch names and commit messages will be checked before each commit.\n'
