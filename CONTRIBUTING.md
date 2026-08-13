# Contributing to AlgoLang

Thank you for helping make AlgoLang a better language for learning and
practising algorithms. Contributions of code, tests, examples, documentation,
bug reports, and design ideas are welcome.

## Before you start

For a small bug fix or documentation improvement, you can open a pull request
(PR) or merge request (MR) directly. For a new language feature or a change to
syntax, semantics, or public APIs, open an issue first. This lets contributors
agree on the behaviour before implementation begins.

Keep each contribution focused on one problem. Small, reviewable changes are
easier to test, discuss, and merge.

## Set up the project

AlgoLang requires Python 3.11 or newer, `pipx`, and Make. It has no runtime
dependencies. Install the CLI in an isolated, editable environment so changes
in the checkout are immediately available to the `algo` command:

```sh
git clone <your-fork-url>
cd AlgoLang
make setup
make test
```

Run an example to confirm the interpreter works:

```sh
make run EXAMPLE=examples/binary_search.algo
```

`make setup` runs `pipx install --editable . --force` and enables the Git hooks.
Use `make help` for all available commands. Contributors without Make can run
the commands shown by the relevant Makefile targets directly.

### Enable the Git hooks

Enable AlgoLang's version-controlled Git hooks once after cloning:

```sh
make hooks
```

The `pre-commit` hook checks the current branch name, and the `commit-msg` hook
checks the Conventional Commit subject. The hooks have no third-party
dependencies. Git hooks are local to each clone, so every contributor must run
the setup command for their own checkout.

## Branch workflow

The `main` branch should always be releasable. Do not develop directly on it.

1. Fork the repository and clone your fork.
2. Add the upstream repository if you need to keep a fork in sync:

   ```sh
   git remote add upstream <upstream-repository-url>
   git fetch upstream
   ```

3. Create a short-lived branch from the latest `main`:

   ```sh
   git switch main
   git pull --ff-only upstream main
   git switch -c feat/add-merge-sort-example
   ```

4. Make and test your changes, then push the branch to your fork:

   ```sh
   git push -u origin feat/add-merge-sort-example
   ```

5. Open a PR/MR into `main`. Delete the branch after it is merged.

If you work directly from the main repository rather than a fork, update
`main` from `origin` instead of `upstream`.

### Branch names

Use lowercase words separated by hyphens, with a prefix that describes the
kind of work:

| Prefix | Use for | Example |
|---|---|---|
| `feat/` | New behaviour or capabilities | `feat/add-graph-type` |
| `fix/` | Bug fixes | `fix/parser-empty-block` |
| `docs/` | Documentation only | `docs/explain-type-checking` |
| `test/` | Test-only changes | `test/lexer-edge-cases` |
| `refactor/` | Internal changes without new behaviour | `refactor/token-stream` |
| `perf/` | Performance improvements | `perf/cache-type-lookups` |
| `build/` | Packaging, dependencies, or build tooling | `build/update-setuptools` |
| `ci/` | Continuous integration | `ci/test-python-versions` |
| `chore/` | Maintenance not covered above | `chore/clean-generated-files` |

Keep names brief but specific. Include an issue number when useful, for example
`fix/42-parser-empty-block`.

## Commit standard

AlgoLang uses [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(optional-scope): <short description>
```

Use an imperative, lowercase description without a trailing period. Keep the
first line concise. Add a body when the reason for the change is not obvious,
and reference related issues in the footer.

Common types are:

- `feat`: a new user-visible capability
- `fix`: a bug fix
- `docs`: documentation only
- `test`: adding or correcting tests
- `refactor`: code changes that neither fix a bug nor add a feature
- `perf`: a performance improvement
- `build`: build system, packaging, or dependency changes
- `ci`: continuous-integration changes
- `chore`: other maintenance
- `revert`: reverting an earlier commit

Useful scopes include `lexer`, `parser`, `types`, `interpreter`, `cli`,
`tracing`, `examples`, `docs`, and `vscode`.

Examples:

```text
feat(parser): support break statements
fix(types): reject mixed heap element types
docs(language): explain function return rules
test(interpreter): cover nested loop control flow
```

For a breaking change, add `!` before the colon and explain the migration in a
`BREAKING CHANGE:` footer:

```text
feat(parser)!: require braces around function bodies

BREAKING CHANGE: Function bodies without braces are no longer accepted.
```

Each commit should be a coherent, working step. Before requesting review,
squash noisy work-in-progress or typo-fix commits when doing so will make the
history easier to understand. Do not squash distinct changes that are useful
to review separately.

The commit-message hook enforces a maximum subject length of 100 characters.
Merge commits, Git revert subjects, and `fixup!`/`squash!` commits are accepted
so standard Git maintenance and interactive-rebase workflows continue to work.
Use `git commit --no-verify` only for an exceptional local recovery; a PR/MR
title and its final commits must still follow the project standards.

## Development standards

- Match the style and type annotations of the surrounding Python code.
- Add or update tests for every behaviour change and bug fix.
- Add an `.algo` example when it improves the language's teaching value.
- Update `docs/language-design.md` when syntax, semantics, types, diagnostics,
  or architecture changes.
- Update the VS Code extension when language syntax or editor behaviour changes.
- Keep generated files and local virtual environments out of commits.
- Avoid unrelated formatting or refactoring in a focused change.

Run the full test suite before pushing:

```sh
make test
```

You can also exercise the parts relevant to your change:

```sh
make check EXAMPLE=examples/dijkstra.algo
make ast EXAMPLE=examples/arithmetic.algo
make dryrun EXAMPLE=examples/bfs.algo WATCH=node,pending,order
```

## Pull/merge request standard

A PR/MR should:

- have a clear title in Conventional Commit form;
- address one feature, fix, or maintenance concern;
- explain what changed, why it changed, and any design trade-offs;
- link the related issue with `Closes #123` when applicable;
- include tests and documentation appropriate to the change;
- pass the complete test suite;
- contain no secrets, credentials, generated caches, or unrelated changes;
- be rebased or otherwise brought up to date if conflicts appear; and
- be marked as a draft while it is not ready for review.

Use the repository template when opening a PR. Reviewers may request changes to
correctness, language consistency, test coverage, maintainability, or teaching
clarity. Resolve conversations only after the concern has been addressed or an
agreement has been recorded.

Maintainers normally use squash merging so the PR/MR title becomes the commit
on `main`. Ensure that title follows the commit standard. Larger contributions
with a deliberately structured history may be merged without squashing at a
maintainer's discretion.

## Reporting bugs

Include the AlgoLang version or commit, Python version, operating system, a
minimal `.algo` program that reproduces the problem, the command you ran, the
actual output, and the expected output. Never include private data or secrets.

## Proposing language changes

Language changes need extra care because they can affect the lexer, parser,
AST, type checker, interpreter, diagnostics, tracing, examples, documentation,
and editor support. In the issue or PR/MR, describe:

- the learning problem the feature solves;
- the proposed syntax and semantics;
- at least one valid and one invalid example;
- compatibility or migration concerns; and
- which interpreter layers are affected.

Be respectful and constructive in all project discussions. Assume good intent,
focus feedback on the contribution, and help keep AlgoLang welcoming to learners
of every experience level.
