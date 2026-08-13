# AlgoLang

AlgoLang is an executable notation for learning and explaining algorithms. This
repository currently contains Milestones 1–7: expressions, control flow,
functions, algorithm collections, static type checking, structured execution
events, watched-variable dry runs, replay, call trees, an AST printer, and
educational diagnostics.

```algo
x = 10
y = 20
result = x + y * 2
print(result)
```

AlgoLang requires Python 3.11 or newer, `pipx`, and Make. Set up an editable
installation, enable the Git hooks, run the tests, and try an example:

```sh
make setup
make test
make run
```

The setup target uses `pipx install --editable .` to expose the `algo` command
from an isolated environment while keeping source changes immediately visible.
Run `make help` to see the available development commands.

Examples of common commands:

```sh
make ast EXAMPLE=examples/arithmetic.algo
make check EXAMPLE=examples/dijkstra.algo
make dryrun EXAMPLE=examples/binary_search.algo WATCH=left,right,mid
```

See [docs/language-design.md](docs/language-design.md) for syntax, semantics,
architecture, and deliberate limitations.

Tracing is available as a presentation-neutral Python API:

```python
from algolang import trace_source

environment, trace = trace_source("x = 1\nx = x + 1")
print(len(trace.events))
```

Use `ExecutionReplay(trace)` for programmatic forward, backward, and random-access
replay of a collected execution.

## VS Code

A small dependency-free extension lives in [vscode-extension](vscode-extension).
It recognizes and highlights `.algo` files and adds editor buttons for Run and
Dry Run, plus Check and AST commands. Errors appear in VS Code's Problems view.

Open this repository in VS Code, select **Run AlgoLang Extension** in **Run and
Debug**, and press `F5`. See [the extension guide](vscode-extension/README.md)
for settings and VSIX packaging instructions.

## Algorithm examples

| Example | Demonstrates |
|---|---|
| [dynamic_programming.algo](examples/dynamic_programming.algo) | Bottom-up coin change and DP-table updates |
| [dijkstra.algo](examples/dijkstra.algo) | Weighted shortest paths with `minheap<[int]>` priority entries |
| [floyd_warshall.algo](examples/floyd_warshall.algo) | Matrix DP with three nested loops |
| [bfs.algo](examples/bfs.algo) | Graph traversal with a queue and visited set |
| [heap.algo](examples/heap.algo) | Min/max heaps and lexicographic priority pairs |

Run or inspect any example:

```sh
make run EXAMPLE=examples/dijkstra.algo
make dryrun EXAMPLE=examples/bfs.algo WATCH=node,pending,order
```

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for project
setup, branch naming, Conventional Commits, testing expectations, and the
pull/merge request standard. Run `make setup` once after cloning to install the
editable CLI and enable the branch-name and commit-message checks.
