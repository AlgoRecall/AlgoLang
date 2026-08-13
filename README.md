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

Run directly from the checkout:

```sh
python -m algolang run examples/arithmetic.algo
python -m algolang ast examples/arithmetic.algo
python -m algolang check examples/arithmetic.algo
python -m algolang dryrun examples/binary_search.algo --watch left,right,mid
python3 -m unittest discover -s tests -v
```

Install with `pip install -e .` to make the equivalent `algo` command available.
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
python3 -m algolang run examples/dijkstra.algo
python3 -m algolang dryrun examples/bfs.algo --watch node,pending,order
```

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for project
setup, branch naming, Conventional Commits, testing expectations, and the
pull/merge request standard. Run `./scripts/setup-git-hooks.sh` once after
cloning to enable the branch-name and commit-message checks.
