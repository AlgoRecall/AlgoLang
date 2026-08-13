#!/bin/sh

set -eu

if [ "$#" -gt 0 ]; then
    branch_name=$1
else
    branch_name=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)
fi

# Detached HEADs occur during rebases and other Git-managed operations.
if [ -z "$branch_name" ]; then
    exit 0
fi

case "$branch_name" in
    main|master)
        printf 'Branch lint failed: do not commit directly to "%s".\n' "$branch_name" >&2
        printf 'Create a branch such as "feat/add-merge-sort-example".\n' >&2
        exit 1
        ;;
esac

if ! printf '%s\n' "$branch_name" \
    | grep -Eq '^(feat|fix|docs|test|refactor|perf|build|ci|chore)/([0-9]+-)?[a-z0-9]+(-[a-z0-9]+)*$'; then
    printf 'Branch lint failed: "%s" is not a valid branch name.\n' "$branch_name" >&2
    printf 'Expected: <type>/<short-name> or <type>/<issue>-<short-name>\n' >&2
    printf 'Types: feat, fix, docs, test, refactor, perf, build, ci, chore\n' >&2
    exit 1
fi
