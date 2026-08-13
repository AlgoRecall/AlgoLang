# AlgoLang language design — Milestones 1–7

AlgoLang is an executable notation for learning data structures and algorithms.
It favors short LeetCode-style programs, predictable static types, explicit AST
nodes, educational diagnostics, and extension points for tracing and analysis.

## Architecture

```text
source
  -> Lexer -> located tokens
  -> Parser -> immutable AST
  -> SemanticAnalyzer -> context validation
  -> TypeChecker -> scoped symbols and inferred/static types
  -> Interpreter -> runtime environments and values -> output
                   \-> structured EventSink -> TraceCollector
```

The phases are separate modules. AST nodes carry syntax and `SourceSpan` only;
they never contain runtime values, environments, inferred types, or UI strings.
Compile-time `SymbolTable` and runtime `Environment` are separate scope trees.
The AST's visitor interface supports visualization, optimization, and
complexity-analysis passes without changing the parser. Runtime tracing is an
observer of execution rather than AST or presentation state.

`algo ast` stops after parsing so malformed semantics can still be inspected.
`algo check` runs through static type checking. `algo run` checks before executing.
`algo dryrun` executes into a trace and renders that trace afterward.

## Grammar

This is compact EBNF; newlines or `;` separate statements:

```ebnf
program       = separators, { statement, separators }, EOF ;
statement     = function | if | while | for | break | continue | return | print
              | typed-assignment | expression, [ "=", expression ] ;
function      = "fn", IDENT, "(", [ parameters ], ")", "->", type, block ;
parameters    = parameter, { ",", parameter } ;
parameter     = IDENT, ":", type ;
if            = "if", expression, block, [ "else", (if | block) ] ;
while         = "while", expression, block ;
for           = "for", IDENT, [ ",", IDENT ], "in", expression, block ;
break         = "break" ;
continue      = "continue" ;
return        = "return", [ expression ] ;
print         = "print", "(", expression, ")" ;
typed-assignment = IDENT, ":", type, "=", expression ;
block         = "{", separators, { statement, separators }, "}" ;

type          = "int" | "float" | "bool" | "string" | "null"
              | "[", type, "]"
              | IDENT, "<", type, { ",", type }, ">" ;

expression    = or ;
or            = and, { "or", and } ;
and           = equality, { "and", equality } ;
equality      = comparison, { ("==" | "!="), comparison } ;
comparison    = term, { ("<" | "<=" | ">" | ">=" | "in"), term } ;
term          = factor, { ("+" | "-"), factor } ;
factor        = unary, { ("*" | "/" | "%"), unary } ;
unary         = ("-" | "not"), unary | postfix ;
postfix       = primary, { call | index | member } ;
call          = "(", [ arguments ], ")" ;
index         = "[", expression, "]" ;
member        = ".", IDENT ;
primary       = literal | IDENT | array | constructor | "(", expression, ")" ;
array         = "[", [ arguments ], "]" ;
constructor   = COLLECTION, "<", type, { ",", type }, ">", "(", ")" ;
```

Recursive descent remains a good fit because the fixed precedence layers map
directly to readable parser functions. Postfix parsing handles calls, indexing,
and members at a higher precedence than unary and binary operators.

## Control flow and scopes

Blocks introduce lexical scopes. Assignment updates the nearest enclosing name;
if none exists it defines a name in the current scope. A typed assignment always
declares in the current scope. Names first created inside a block do not escape.

```algo
total = 0
for index, value in [3, 5, 7] {
    if value == 5 { continue }
    total = total + value
}
```

`for value in iterable` visits values. `for index, value in iterable` also binds
a zero-based iteration index. Arrays, strings, map keys, sets, stacks, queues,
deques, and heaps are iterable. `break` and `continue` are statically restricted
to loops.

## Functions

Functions are top-level, lexically scoped, recursively callable, and require
parameter and return annotations:

```algo
fn add(a: int, b: int) -> int {
    return a + b
}
```

Calls are checked for arity and argument types. Non-`null` functions must
definitely return on all statically recognizable paths. Nested functions and
closures are intentionally deferred, although runtime call frames already use
enclosing environments.

## Collections

| Type | Construction | Operations |
|---|---|---|
| Array | `[1, 2]` | indexing, indexed assignment, `push`, `pop`, `len` |
| Map | `map<int,string>()` | indexing, indexed assignment, `in`, `len` |
| Set | `set<int>()` | `add`, `remove`, `in`, `len` |
| Stack | `stack<int>()` | `push`, `pop`, `peek`, `len` |
| Queue | `queue<int>()` | `enqueue`, `dequeue`, `front`, `len` |
| Deque | `deque<int>()` | `push_front`, `push_back`, `pop_front`, `pop_back`, `front`, `back`, `len` |
| Min/max heap | `minheap<int>()`, `maxheap<int>()` | `push`, `pop`, `peek`, `len` |

`len(value)` works for strings and every collection. `range(stop)`,
`range(start, stop)`, and `range(start, stop, step)` produce `[int]`.
Nested arrays represent matrices.

Heap elements may be numbers, strings, or recursively comparable arrays.
Arrays compare lexicographically, making `[priority, node]` a concise substitute
for a tuple until a dedicated tuple/product type is added. This supports
Dijkstra-style priority queues as `minheap<[int]>` while retaining static checks.

## Static type semantics

- Primitive types are `int`, `float`, `bool`, `string`, and `null`.
- First assignment infers and fixes a variable's type: `x = 10` infers `int`.
- Typed declarations use `x: float = 10`; `int` widens to `float`.
- Mutable collections are generic and their element/key/value operations are
  checked statically.
- An unannotated empty array is rejected because its element type is unknowable.
  Context supplies the type in `x: [int] = []`, typed arguments, and `return []`.
- Boolean conditions and boolean operators require `bool`; booleans are not ints.
- `int / int` performs truncating integer division. Division involving a float
  returns `float`. This deliberately evolves Milestone 1 so the target binary
  search expression produces a valid integer array index.
- `+` accepts numbers or two strings. Ordering accepts numbers or two strings.
- `in` checks arrays, maps, sets, strings, stacks, queues, deques, and heaps.
- Map keys must be primitive. Heap elements must be numeric or strings.

## Diagnostics

Lexical, parse, semantic, type, and runtime errors share structured source spans:

```text
solution.algo:2:5: Type error: expected int, got string
2 | x = "changed"
  |     ^^^^^^^^^
```

## Structured execution events

The interpreter accepts an optional `EventSink`. With no sink, a no-op sink is
used and ordinary execution behaves exactly as before. `TraceCollector` is the
first sink implementation and preserves emitted events in execution order.

```python
from algolang import trace_source
from algolang.tracing import VariableChanged

environment, trace = trace_source(source, "solution.algo")
changes = trace.of_type(VariableChanged)
```

Alternatively, applications can pass any object implementing
`emit(event: ExecutionEvent)` to `run_source(..., event_sink=sink)` and stream
events without retaining a full trace.

Event families currently include:

- `VariableDeclared` and `VariableChanged`
- `ExpressionEvaluated` and `ConditionEvaluated`
- `LoopStarted`, `LoopIteration`, and `LoopFinished`
- `FunctionCalled` and `FunctionReturned`
- `ArrayUpdated`, `MapUpdated`, and `SetUpdated`
- `StackPushed`, `StackPopped`, `QueueEnqueued`, and `QueueDequeued`
- `DequeUpdated`, `HeapPushed`, and `HeapPopped`

Every event is immutable and carries a source span, lexical scope ID, and active
call ID. Function events provide unique call IDs and parent call IDs. Loop events
provide unique loop IDs, one-based iteration numbers, and structured completion
reasons. Mutation events use stable execution-local collection IDs so aliases
can be correlated without exposing process memory addresses.

Observed values are recursively copied into immutable `RuntimeSnapshot` values.
Consequently, an earlier variable or collection state cannot be changed by a
later mutation. Snapshot and event data remain presentation-neutral: semantic
tags use enums, and no event contains a CLI sentence, table cell, or explanation.

## Dry runs and replay

Milestone 7 consumes the structured event stream without adding presentation
logic to the interpreter:

```sh
algo dryrun solution.algo
algo dryrun solution.algo --watch left --watch right --watch mid
algo dryrun solution.algo --watch left,right,mid
```

Without `--watch`, variables are discovered from executed declaration and change
events in first-observed order. With watches, only those variable columns and
their own declaration/change rows are selected; conditions, loop iterations,
function boundaries, and collection mutations remain visible because they give
the state transitions algorithmic context.

The report has independent sections for:

- a step-numbered state table with source line, call ID, semantic event, and
  watched values;
- a reconstructed function call tree with arguments and returned values;
- captured program output; and
- raw-versus-displayed event counts.

Watched mutable variables retain their stable collection identity, so later
array, map, set, stack, queue, deque, and heap mutations update the replayed
value even when mutation occurs through an alias.

The programmatic `ExecutionReplay` API supports `step_forward`, `step_backward`,
`seek`, and `reset`. Replay reconstructs variables, collection states, active
calls, and active loop iterations deterministically from the event sequence.
Backward movement rebuilds state from immutable snapshots rather than trying to
reverse runtime operations.

```python
from algolang import ExecutionReplay, trace_source

_, trace = trace_source(source, "solution.algo")
replay = ExecutionReplay(trace)
replay.step_forward()
replay.seek(len(trace.events) - 1)
state = replay.state
```

## Intentional limitations

- No union/optional types, user-defined generics, structs, classes, or closures.
- No array slicing, map/set literals, sorting API, or iterator protocol.
- Static analysis is intentionally local and conservative; it is not full
  control-flow or definite-assignment analysis.
- Top-level statements execute in source order. Functions are predeclared, but a
  global value must be initialized before a top-level call reads it.
- Runtime collection errors such as bounds errors, missing map keys, empty pops,
  and division by zero cannot generally be proven statically.
- Watches currently accept variable names, not arbitrary expressions such as
  `nums[mid]`.
- Replay is a Python API; an interactive terminal debugger is not implemented.

## Next milestone

Milestone 8 should add educational LeetCode runtime structures (`ListNode`,
`TreeNode`, `Graph`, `Trie`, and `UnionFind`) with static types and structured
mutation events. Their representations should integrate with the existing trace
and replay model so Milestone 9 visualizers do not need special interpreter paths.
