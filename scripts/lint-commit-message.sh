#!/bin/sh

set -eu

if [ "$#" -ne 1 ] || [ ! -r "$1" ]; then
    printf 'Usage: %s <commit-message-file>\n' "$0" >&2
    exit 2
fi

subject=$(sed -n '1p' "$1")

# These subjects are created or interpreted by Git and should remain intact.
case "$subject" in
    Merge\ *|Revert\ \"*|fixup!\ *|squash!\ *)
        exit 0
        ;;
esac

subject_length=$(printf '%s' "$subject" | LC_ALL=C wc -c | tr -d ' ')
if [ "$subject_length" -gt 100 ]; then
    printf 'Commit lint failed: subject is %s characters; maximum is 100.\n' \
        "$subject_length" >&2
    exit 1
fi

if ! printf '%s\n' "$subject" \
    | grep -Eq '^(feat|fix|docs|test|refactor|perf|build|ci|chore|revert)(\([a-z0-9][a-z0-9-]*\))?!?: [a-z0-9].+$'; then
    printf 'Commit lint failed: subject must follow Conventional Commits.\n' >&2
    printf 'Expected: <type>(optional-scope): <lowercase description>\n' >&2
    printf 'Example: feat(parser): support break statements\n' >&2
    printf 'Types: feat, fix, docs, test, refactor, perf, build, ci, chore, revert\n' >&2
    exit 1
fi

case "$subject" in
    *.)
        printf 'Commit lint failed: subject must not end with a period.\n' >&2
        exit 1
        ;;
esac
