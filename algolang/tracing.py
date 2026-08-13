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
    WHILE = "while"
    FOR = "for"


class LoopExitReason(Enum):
    COMPLETED = "completed"
    BREAK = "break"
    RETURN = "return"
    ERROR = "error"


class MutationOperation(Enum):
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
    span: SourceSpan
    scope_id: int
    call_id: int | None


@dataclass(frozen=True, slots=True)
class VariableDeclared(ExecutionEvent):
    name: str
    value: RuntimeSnapshot
    collection_id: int | None


@dataclass(frozen=True, slots=True)
class VariableChanged(ExecutionEvent):
    name: str
    old_value: RuntimeSnapshot
    new_value: RuntimeSnapshot
    collection_id: int | None


@dataclass(frozen=True, slots=True)
class ExpressionEvaluated(ExecutionEvent):
    expression_kind: str
    value: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class ConditionEvaluated(ExecutionEvent):
    context: str
    value: bool


@dataclass(frozen=True, slots=True)
class LoopStarted(ExecutionEvent):
    loop_id: int
    kind: LoopKind


@dataclass(frozen=True, slots=True)
class LoopIteration(ExecutionEvent):
    loop_id: int
    kind: LoopKind
    iteration: int


@dataclass(frozen=True, slots=True)
class LoopFinished(ExecutionEvent):
    loop_id: int
    kind: LoopKind
    iterations: int
    reason: LoopExitReason


@dataclass(frozen=True, slots=True)
class FunctionCalled(ExecutionEvent):
    function_name: str
    arguments: tuple[RuntimeSnapshot, ...]
    parent_call_id: int | None


@dataclass(frozen=True, slots=True)
class FunctionReturned(ExecutionEvent):
    function_name: str
    value: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class ArrayUpdated(ExecutionEvent):
    collection_id: int
    operation: MutationOperation
    index: int
    old_value: RuntimeSnapshot | None
    new_value: RuntimeSnapshot | None
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class MapUpdated(ExecutionEvent):
    collection_id: int
    key: RuntimeSnapshot
    existed: bool
    old_value: RuntimeSnapshot | None
    new_value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class SetUpdated(ExecutionEvent):
    collection_id: int
    operation: MutationOperation
    value: RuntimeSnapshot
    changed: bool
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class StackPushed(ExecutionEvent):
    collection_id: int
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class StackPopped(ExecutionEvent):
    collection_id: int
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class QueueEnqueued(ExecutionEvent):
    collection_id: int
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class QueueDequeued(ExecutionEvent):
    collection_id: int
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class DequeUpdated(ExecutionEvent):
    collection_id: int
    operation: MutationOperation
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class HeapPushed(ExecutionEvent):
    collection_id: int
    heap_kind: str
    value: RuntimeSnapshot
    state: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class HeapPopped(ExecutionEvent):
    collection_id: int
    heap_kind: str
    value: RuntimeSnapshot
    state: RuntimeSnapshot


class EventSink(Protocol):
    def emit(self, event: ExecutionEvent) -> None: ...


class NullEventSink:
    def emit(self, event: ExecutionEvent) -> None:
        pass


@dataclass(slots=True)
class TraceCollector:
    events: list[ExecutionEvent] = field(default_factory=list)

    def emit(self, event: ExecutionEvent) -> None:
        self.events.append(event)

    def of_type(self, event_type: type[Any]) -> list[Any]:
        return [event for event in self.events if isinstance(event, event_type)]
