from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .tracing import (
    ArrayUpdated, ConditionEvaluated, DequeUpdated, ExecutionEvent,
    FunctionCalled, FunctionReturned, HeapPopped, HeapPushed, LoopFinished,
    LoopIteration, LoopStarted, MapUpdated, QueueDequeued, QueueEnqueued,
    RuntimeSnapshot, SetUpdated, StackPopped, StackPushed, TraceCollector,
    VariableChanged, VariableDeclared,
)


@dataclass(frozen=True, slots=True)
class VariableKey:
    call_id: int | None
    scope_id: int
    name: str


@dataclass(frozen=True, slots=True)
class VariableRecord:
    value: RuntimeSnapshot
    event_index: int
    collection_id: int | None


@dataclass(slots=True)
class ReplayState:
    variables: dict[VariableKey, VariableRecord] = field(default_factory=dict)
    collections: dict[int, RuntimeSnapshot] = field(default_factory=dict)
    active_calls: list[int] = field(default_factory=list)
    active_loops: dict[int, int] = field(default_factory=dict)

    def copy(self) -> "ReplayState":
        return ReplayState(
            dict(self.variables), dict(self.collections),
            list(self.active_calls), dict(self.active_loops),
        )


COLLECTION_EVENTS = (
    ArrayUpdated, MapUpdated, SetUpdated, StackPushed, StackPopped,
    QueueEnqueued, QueueDequeued, DequeUpdated, HeapPushed, HeapPopped,
)


class ExecutionReplay:
    """Deterministically replays a collected trace in either direction."""

    def __init__(self, trace: TraceCollector | Iterable[ExecutionEvent]):
        self.events = tuple(trace.events if isinstance(trace, TraceCollector) else trace)
        self.position = -1
        self._state = ReplayState()

    @property
    def state(self) -> ReplayState:
        return self._state.copy()

    @property
    def current_event(self) -> ExecutionEvent | None:
        return None if self.position < 0 else self.events[self.position]

    def step_forward(self) -> ExecutionEvent | None:
        if self.position + 1 >= len(self.events): return None
        self.position += 1
        event = self.events[self.position]
        self._apply(event, self.position)
        return event

    def step_backward(self) -> ExecutionEvent | None:
        if self.position < 0: return None
        self.seek(self.position - 1)
        return self.current_event

    def seek(self, position: int) -> ExecutionEvent | None:
        if position < -1 or position >= len(self.events):
            raise IndexError(f"trace position {position} is outside -1..{len(self.events) - 1}")
        if position < self.position:
            self.position = -1
            self._state = ReplayState()
        while self.position < position: self.step_forward()
        return self.current_event

    def reset(self) -> None:
        self.position = -1
        self._state = ReplayState()

    def visible_variables(self, call_id: int | None) -> dict[str, RuntimeSnapshot]:
        visible: dict[str, VariableRecord] = {}
        for key, record in self._state.variables.items():
            if key.call_id not in (None, call_id): continue
            current = visible.get(key.name)
            if current is None or record.event_index > current.event_index:
                visible[key.name] = record
        return {
            name: self._state.collections.get(record.collection_id, record.value)
            if record.collection_id is not None else record.value
            for name, record in visible.items()
        }

    def _apply(self, event: ExecutionEvent, index: int) -> None:
        if isinstance(event, VariableDeclared):
            key = VariableKey(event.call_id, event.scope_id, event.name)
            self._state.variables[key] = VariableRecord(event.value, index, event.collection_id)
        elif isinstance(event, VariableChanged):
            key = VariableKey(event.call_id, event.scope_id, event.name)
            self._state.variables[key] = VariableRecord(event.new_value, index, event.collection_id)
        elif isinstance(event, COLLECTION_EVENTS):
            self._state.collections[event.collection_id] = event.state
        elif isinstance(event, FunctionCalled):
            self._state.active_calls.append(event.call_id)
        elif isinstance(event, FunctionReturned):
            if self._state.active_calls and self._state.active_calls[-1] == event.call_id:
                self._state.active_calls.pop()
            else:
                self._state.active_calls = [call for call in self._state.active_calls if call != event.call_id]
        elif isinstance(event, LoopStarted):
            self._state.active_loops[event.loop_id] = 0
        elif isinstance(event, LoopIteration):
            self._state.active_loops[event.loop_id] = event.iteration
        elif isinstance(event, LoopFinished):
            self._state.active_loops.pop(event.loop_id, None)


@dataclass(frozen=True, slots=True)
class DryRunRow:
    step: int
    line: int
    call: str
    event: str
    values: tuple[str, ...]


@dataclass(slots=True)
class CallNode:
    call_id: int
    name: str
    arguments: tuple[RuntimeSnapshot, ...]
    result: RuntimeSnapshot | None = None
    returned: bool = False
    children: list["CallNode"] = field(default_factory=list)

    def label(self) -> str:
        arguments = ", ".join(format_snapshot(value) for value in self.arguments)
        result = f" -> {format_snapshot(self.result)}" if self.returned and self.result else ""
        return f"{self.name}({arguments}){result}"


def build_call_forest(events: Iterable[ExecutionEvent]) -> list[CallNode]:
    nodes: dict[int, CallNode] = {}
    roots: list[CallNode] = []
    for event in events:
        if isinstance(event, FunctionCalled):
            node = CallNode(event.call_id, event.function_name, event.arguments)
            nodes[event.call_id] = node
            parent = nodes.get(event.parent_call_id) if event.parent_call_id is not None else None
            if parent: parent.children.append(node)
            else: roots.append(node)
        elif isinstance(event, FunctionReturned) and event.call_id in nodes:
            nodes[event.call_id].result = event.value
            nodes[event.call_id].returned = True
    return roots


def render_call_forest(roots: Iterable[CallNode]) -> str:
    lines: list[str] = []
    roots = list(roots)
    for root_index, root in enumerate(roots):
        if root_index: lines.append("")
        lines.append(root.label())
        _render_children(root, "", lines)
    return "\n".join(lines)


def _render_children(node: CallNode, prefix: str, lines: list[str]) -> None:
    for index, child in enumerate(node.children):
        last = index == len(node.children) - 1
        lines.append(prefix + ("└── " if last else "├── ") + child.label())
        _render_children(child, prefix + ("    " if last else "│   "), lines)


def render_dry_run(
    trace: TraceCollector,
    filename: str,
    output: Iterable[str] = (),
    watches: Iterable[str] = (),
) -> str:
    watch_names = _normalize_watches(watches)
    if not watch_names:
        watch_names = _discovered_names(trace.events)
    replay = ExecutionReplay(trace)
    rows: list[DryRunRow] = []
    for event in replay.events:
        replay.step_forward()
        if not _display_event(event, watch_names): continue
        variables = replay.visible_variables(event.call_id)
        rows.append(DryRunRow(
            len(rows) + 1,
            event.span.start.line,
            "global" if event.call_id is None else f"#{event.call_id}",
            _describe_event(event),
            tuple(format_snapshot(variables[name]) if name in variables else "·" for name in watch_names),
        ))

    sections = [f"Dry run: {filename}", "", "State transitions"]
    if rows:
        headers = ("Step", "Line", "Call", "Event", *watch_names)
        data = [
            (str(row.step), str(row.line), row.call, row.event, *row.values)
            for row in rows
        ]
        sections.append(_render_table(headers, data))
    else:
        sections.append("(no observable state transitions)")

    forest = build_call_forest(trace.events)
    if forest:
        sections.extend(("", "Call tree", render_call_forest(forest)))

    output = list(output)
    sections.extend(("", "Program output", "\n".join(output) if output else "(none)"))
    sections.extend(("", f"Trace: {len(trace.events)} events, {len(rows)} displayed steps"))
    return "\n".join(sections)


def format_snapshot(value: RuntimeSnapshot | None) -> str:
    if value is None: return "·"
    if value.kind == "null": return "null"
    if value.kind == "bool": return "true" if value.value else "false"
    if value.kind == "string": return f'"{value.value}"'
    if value.kind in ("array", "stack", "queue", "deque", "minheap", "maxheap"):
        return "[" + ", ".join(format_snapshot(item) for item in value.value) + "]"
    if value.kind == "set": return "{" + ", ".join(format_snapshot(item) for item in value.value) + "}"
    if value.kind == "map":
        return "{" + ", ".join(
            f"{format_snapshot(key)}: {format_snapshot(item)}" for key, item in value.value
        ) + "}"
    return str(value.value)


def _normalize_watches(watches: Iterable[str]) -> tuple[str, ...]:
    names: list[str] = []
    for watch in watches:
        for name in watch.split(","):
            name = name.strip()
            if name and name not in names: names.append(name)
    return tuple(names)


def _discovered_names(events: Iterable[ExecutionEvent]) -> tuple[str, ...]:
    names: list[str] = []
    for event in events:
        if isinstance(event, (VariableDeclared, VariableChanged)) and event.name not in names:
            names.append(event.name)
    return tuple(names)


def _display_event(event: ExecutionEvent, watches: tuple[str, ...]) -> bool:
    if isinstance(event, (VariableDeclared, VariableChanged)):
        return not watches or event.name in watches
    return isinstance(event, (
        ConditionEvaluated, LoopIteration, FunctionCalled, FunctionReturned,
        *COLLECTION_EVENTS,
    ))


def _describe_event(event: ExecutionEvent) -> str:
    if isinstance(event, VariableDeclared): return f"declare {event.name}"
    if isinstance(event, VariableChanged): return f"change {event.name}"
    if isinstance(event, ConditionEvaluated): return f"{event.context} condition = {'true' if event.value else 'false'}"
    if isinstance(event, LoopIteration): return f"{event.kind.value} iteration {event.iteration}"
    if isinstance(event, FunctionCalled): return f"call {event.function_name}"
    if isinstance(event, FunctionReturned): return f"return {event.function_name}"
    if isinstance(event, ArrayUpdated): return f"array {event.operation.value}"
    if isinstance(event, MapUpdated): return "map set"
    if isinstance(event, SetUpdated): return f"set {event.operation.value}"
    if isinstance(event, StackPushed): return "stack push"
    if isinstance(event, StackPopped): return "stack pop"
    if isinstance(event, QueueEnqueued): return "queue enqueue"
    if isinstance(event, QueueDequeued): return "queue dequeue"
    if isinstance(event, DequeUpdated): return f"deque {event.operation.value}"
    if isinstance(event, HeapPushed): return f"{event.heap_kind} push"
    if isinstance(event, HeapPopped): return f"{event.heap_kind} pop"
    return type(event).__name__


def _render_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row): widths[index] = max(widths[index], len(cell))
    line = lambda row: " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)).rstrip()
    separator = "-+-".join("-" * width for width in widths)
    return "\n".join((line(headers), separator, *(line(row) for row in rows)))
