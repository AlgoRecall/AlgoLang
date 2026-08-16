"""Presentation-neutral events and snapshots for observable execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from .runtime import (
    AlgoDeque, AlgoFunction, AlgoHeap, AlgoQueue, AlgoStack, NativeFunction,
    RuntimeValue,
)
from .source import SourceSpan


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    """Immutable, presentation-neutral copy of an observable runtime value."""

    kind: str
    value: Any


def snapshot(value: RuntimeValue) -> RuntimeSnapshot:
    """Convert a runtime value into an immutable tracing snapshot."""
    if value is None: return RuntimeSnapshot("null", None)
    if isinstance(value, bool): return RuntimeSnapshot("bool", value)
    if isinstance(value, int): return RuntimeSnapshot("int", value)
    if isinstance(value, float): return RuntimeSnapshot("float", value)
    if isinstance(value, str): return RuntimeSnapshot("string", value)
    if isinstance(value, list): return RuntimeSnapshot("array", tuple(snapshot(item) for item in value))
    if isinstance(value, dict):
        return RuntimeSnapshot("map", tuple((snapshot(key), snapshot(item)) for key, item in value.items()))
    if isinstance(value, set):
        items = tuple(sorted((snapshot(item) for item in value), key=repr))
        return RuntimeSnapshot("set", items)
    if isinstance(value, AlgoStack): return RuntimeSnapshot("stack", tuple(snapshot(item) for item in value.items))
    if isinstance(value, AlgoQueue): return RuntimeSnapshot("queue", tuple(snapshot(item) for item in value.items))
    if isinstance(value, AlgoDeque): return RuntimeSnapshot("deque", tuple(snapshot(item) for item in value.items))
    if isinstance(value, AlgoHeap): return RuntimeSnapshot("maxheap" if value.maximum else "minheap", tuple(snapshot(item) for item in value.values()))
    if isinstance(value, AlgoFunction): return RuntimeSnapshot("function", value.declaration.name)
    if isinstance(value, NativeFunction): return RuntimeSnapshot("native_function", value.name)
    return RuntimeSnapshot(type(value).__name__, repr(value))


class LoopKind(Enum):
    """Identify the AlgoLang loop construct that emitted an event."""
    WHILE = "while"
    FOR = "for"


class LoopExitReason(Enum):
    """Identify why an executing loop stopped."""
    COMPLETED = "completed"
    BREAK = "break"
    RETURN = "return"
    ERROR = "error"


class MutationOperation(Enum):
    """Identify a collection mutation recorded in the trace."""
    PUSH = "push"
    POP = "pop"
    ADD = "add"
    REMOVE = "remove"
    SET = "set"
    ENQUEUE = "enqueue"
    DEQUEUE = "dequeue"
    PUSH_FRONT = "push_front"
    PUSH_BACK = "push_back"
    POP_FRONT = "pop_front"
    POP_BACK = "pop_back"


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    """Base record for an observable execution event at a source span."""
    span: SourceSpan
    scope_id: int
    call_id: int | None


@dataclass(frozen=True, slots=True)
class VariableDeclared(ExecutionEvent):
    """Record creation of a variable binding."""
    name: str
    value: RuntimeSnapshot
    collection_id: int | None


@dataclass(frozen=True, slots=True)
class VariableChanged(ExecutionEvent):
    """Record reassignment of an existing variable binding."""
    name: str
    old_value: RuntimeSnapshot
    new_value: RuntimeSnapshot
    collection_id: int | None


@dataclass(frozen=True, slots=True)
class ExpressionEvaluated(ExecutionEvent):
    """Record the value produced by an expression."""
    expression_kind: str
    value: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class ConditionEvaluated(ExecutionEvent):
    """Record the boolean result of a control-flow condition."""
    context: str
    value: bool


@dataclass(frozen=True, slots=True)
class LoopStarted(ExecutionEvent):
    """Record entry into a uniquely identified loop."""
    loop_id: int
    kind: LoopKind


@dataclass(frozen=True, slots=True)
class LoopIteration(ExecutionEvent):
    """Record the start of one loop iteration."""
    loop_id: int
    kind: LoopKind
    iteration: int


@dataclass(frozen=True, slots=True)
class LoopFinished(ExecutionEvent):
    """Record loop completion and its exit reason."""
    loop_id: int
    kind: LoopKind
    iterations: int
    reason: LoopExitReason


@dataclass(frozen=True, slots=True)
class FunctionCalled(ExecutionEvent):
    """Record a function invocation and its parent call."""
    function_name: str
    arguments: tuple[RuntimeSnapshot, ...]
    parent_call_id: int | None


@dataclass(frozen=True, slots=True)
class FunctionReturned(ExecutionEvent):
    """Record the value returned by a function invocation."""
    function_name: str
    value: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class ArrayUpdated(ExecutionEvent):
    """Record an array mutation and resulting collection state."""
    collection_id: int
    operation: MutationOperation
    index: int
    old_value: RuntimeSnapshot | None
    new_value: RuntimeSnapshot | None
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class MapUpdated(ExecutionEvent):
    """Record a map assignment and resulting collection state."""
    collection_id: int
    key: RuntimeSnapshot
    existed: bool
    old_value: RuntimeSnapshot | None
    new_value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class SetUpdated(ExecutionEvent):
    """Record a set mutation and resulting collection state."""
    collection_id: int
    operation: MutationOperation
    value: RuntimeSnapshot
    changed: bool
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class StackPushed(ExecutionEvent):
    """Record a value pushed onto a stack."""
    collection_id: int
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class StackPopped(ExecutionEvent):
    """Record a value popped from a stack."""
    collection_id: int
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class QueueEnqueued(ExecutionEvent):
    """Record a value enqueued into a queue."""
    collection_id: int
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class QueueDequeued(ExecutionEvent):
    """Record a value dequeued from a queue."""
    collection_id: int
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class DequeUpdated(ExecutionEvent):
    """Record a deque mutation and resulting collection state."""
    collection_id: int
    operation: MutationOperation
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class HeapPushed(ExecutionEvent):
    """Record a value pushed onto a heap."""
    collection_id: int
    heap_kind: str
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class HeapPopped(ExecutionEvent):
    """Record a value popped from a heap."""
    collection_id: int
    heap_kind: str
    value: RuntimeSnapshot
    state: RuntimeSnapshot


class EventSink(Protocol):
    """Protocol for consumers of structured execution events."""
    def emit(self, event: ExecutionEvent) -> None:
        """Receive an execution event."""
        ...


class NullEventSink:
    """Discard execution events when tracing is disabled."""
    def emit(self, event: ExecutionEvent) -> None:
        """Discard an execution event."""
        pass


@dataclass(slots=True)
class TraceCollector:
    """Collect execution events in emission order."""
    events: list[ExecutionEvent] = field(default_factory=list)

    def emit(self, event: ExecutionEvent) -> None:
        """Append an execution event to the trace."""
        self.events.append(event)

    def of_type(self, event_type: type[Any]) -> list[Any]:
        """Return all collected events matching a concrete event type."""
        return [event for event in self.events if isinstance(event, event_type)]
