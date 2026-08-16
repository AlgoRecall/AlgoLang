# AlgoLang

AlgoLang is a small, Python-based programming language for learning,
practising, and explaining algorithms. It combines familiar pseudocode with an
executable interpreter, static type checking, educational diagnostics, and
step-by-step execution tools.

The project is designed for learners who want to understand not only whether
an algorithm works, but also how its variables and data structures change over
time.

> **Project status:** AlgoLang is experimental and under active development.
> Syntax and APIs may change as the language evolves.

## Why AlgoLang?

Traditional pseudocode is readable but cannot be executed. General-purpose
languages are executable but can introduce details that distract from the
algorithm itself. AlgoLang aims for the space between them:

- concise enough to read like structured pseudocode;
- strict enough to catch common mistakes before execution;
- executable enough to test real algorithm implementations; and
- observable enough to explain each step of an algorithm.

## Features

- Expressions, variables, conditions, loops, and typed functions
- Primitive types and type inference
- Arrays, maps, sets, stacks, queues, deques, and min/max heaps
- Static semantic and type checking
- Source-aware lexical, parse, semantic, type, and runtime diagnostics
- Execution tracing with structured events
- Watched-variable dry runs and trace replay
- Call-tree reconstruction and AST inspection
- Algorithm examples including BFS, Dijkstra, dynamic programming, heaps, and
  Floyd–Warshall
- A VS Code extension with syntax highlighting, snippets, editor commands, and
  diagnostics

## A first AlgoLang program

```algo
fn binary_search(values: [int], target: int) -> int {
    left = 0
    right = len(values) - 1

    while left <= right {
        mid = (left + right) / 2
        if values[mid] == target {
            return mid
        }
        if values[mid] < target {
            left = mid + 1
        } else {
            right = mid - 1
        }
    }

    return -1
}

result = binary_search([1, 3, 5, 7, 9], 7)
print(result)
```

## Quick start

### Requirements

- Python 3.11 or newer
- [pipx](https://pipx.pypa.io/)
- Make

Clone the repository and prepare an editable development installation:

```sh
git clone https://github.com/AlgoRecall/AlgoLang.git
cd AlgoLang
make setup
```

`make setup` installs the `algo` command in an isolated pipx environment and
enables the repository's Git hooks. Because the installation is editable,
changes in the checkout are immediately reflected in the CLI.

Run an example and the complete test suite:

```sh
make run
make test
```

Run `make help` to list all development commands.

## CLI usage

After setup, use the `algo` command directly:

```sh
algo run examples/arithmetic.algo
algo check examples/dijkstra.algo
algo ast examples/arithmetic.algo
algo dryrun examples/binary_search.algo --watch left,right,mid
```

The equivalent Make targets are useful during development:

```sh
make run EXAMPLE=examples/dijkstra.algo
make check EXAMPLE=examples/dijkstra.algo
make ast EXAMPLE=examples/arithmetic.algo
make dryrun EXAMPLE=examples/bfs.algo WATCH=node,pending,order
```

## Learning with dry runs

Dry runs collect execution events and render the changing values of selected
variables. For example:

```sh
algo dryrun examples/binary_search.algo --watch left,right,mid
```

Tracing is also available through a presentation-neutral Python API:

```python
from algolang import trace_source

environment, trace = trace_source("x = 1\nx = x + 1")
print(len(trace.events))
```

Use `ExecutionReplay(trace)` for forward, backward, and random-access replay of
a collected execution.

## Algorithm examples

| Example | Demonstrates |
|---|---|
| [binary_search.algo](examples/binary_search.algo) | Search bounds and watched-variable dry runs |
| [two_sum.algo](examples/two_sum.algo) | Map-based lookup |
| [dynamic_programming.algo](examples/dynamic_programming.algo) | Bottom-up coin change and DP-table updates |
| [dijkstra.algo](examples/dijkstra.algo) | Weighted shortest paths with a priority heap |
| [floyd_warshall.algo](examples/floyd_warshall.algo) | Matrix dynamic programming with nested loops |
| [bfs.algo](examples/bfs.algo) | Graph traversal with a queue and visited set |
| [heap.algo](examples/heap.algo) | Min/max heaps and lexicographic priority pairs |
| [collections.algo](examples/collections.algo) | AlgoLang's built-in collection types |

## How the interpreter works

```text
source code
    -> lexer
    -> parser and AST
    -> semantic analysis
    -> static type checking
    -> interpreter
    -> output and optional execution trace
```

The main implementation lives in `algolang/`:

| Area | Responsibility |
|---|---|
| `lexer/` | Converts source text into location-aware tokens |
| `parser.py` | Builds the abstract syntax tree |
| `semantic.py` | Validates declarations and control-flow rules |
| `type_checker.py` | Checks and infers static types |
| `interpreter.py` | Executes validated programs |
| `tracing.py` and `dryrun.py` | Records and presents execution state |
| `cli.py` | Provides the `algo` command-line interface |

See [the language design document](docs/language-design.md) for grammar,
semantics, architecture, tracing, and deliberate limitations.

## VS Code extension

The extension in [vscode-extension/](vscode-extension) provides:

- syntax highlighting for `.algo` files;
- snippets for functions, conditions, and loops;
- Run, Check, Show AST, and Dry Run commands;
- editor buttons for Run and Dry Run; and
- errors in VS Code's Problems view.

Open this repository in VS Code, select **Run AlgoLang Extension** in **Run and
Debug**, and press `F5`. See the [extension guide](vscode-extension/README.md)
for usage, settings, development, and packaging instructions.

## Development

Common commands are:

```sh
make quality           # Run lint, tests, and coverage checks
make test              # Run the complete test suite
make test-lexer        # Run focused lexer tests
make check EXAMPLE=examples/dijkstra.algo
make dryrun EXAMPLE=examples/bfs.algo WATCH=node,pending,order
```

Tests use Python's standard `unittest` framework and require no third-party
runtime dependencies. The GitHub Actions pipeline runs the suite across the
supported Python versions, checks Python code with Ruff, and enforces at least
85% branch coverage. Run `make quality` before opening a pull/merge request to
reproduce those checks locally; pipx provides the quality tools in isolated
environments.

## Contributing

Contributions to the interpreter, language design, tests, examples,
documentation, and editor tooling are welcome.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before starting. It describes project
setup, branch naming, Conventional Commits, testing expectations, language
change proposals, and the pull/merge request standard.

For significant syntax, semantic, or public API changes, open an issue before
implementation so the design can be discussed first.

## Roadmap

Potential future work includes:

- expanding educational diagnostics and algorithm visualizations;
- richer editor intelligence and language-server support;
- additional standard algorithms and teaching examples;
- broader language and CLI documentation; and
- stable packaging and releases.

Roadmap items are directions rather than release commitments. Issues and design
discussions should define their final scope.

## License

This repository does not currently include an open-source license. Until a
license is selected and added, the source is publicly visible but should not be
treated as licensed for reuse or redistribution. Adding a `LICENSE` file is
required before presenting AlgoLang as an open-source project.
