"""Runtime environments, callable values, and collection implementations."""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, TypeAlias

RuntimeValue: TypeAlias = Any


@dataclass(slots=True)
class Environment:
    """Store runtime bindings with lexical parent-scope lookup."""
    enclosing: "Environment | None" = None
    values: dict[str, RuntimeValue] = field(default_factory=dict)
    scope_id: int = 0

    def define(self, name: str, value: RuntimeValue) -> None:
        """Define or replace a binding in this environment."""
        self.values[name] = value

    def assign(self, name: str, value: RuntimeValue) -> None:
        """Assign a binding in its owning scope or define it locally."""
        if name in self.values:
            self.values[name] = value
        elif self.enclosing is not None and self.enclosing.contains(name):
            self.enclosing.assign(name, value)
        else:
            self.values[name] = value

    def set(self, name: str, value: RuntimeValue) -> None:
        """Assign a value using normal lexical-scope resolution."""
        self.assign(name, value)

    def contains(self, name: str) -> bool:
        """Return whether this environment or an ancestor contains a name."""
        return name in self.values or (self.enclosing is not None and self.enclosing.contains(name))

    def owner(self, name: str) -> "Environment | None":
        """Return the nearest environment that owns a name."""
        if name in self.values: return self
        return self.enclosing.owner(name) if self.enclosing else None

    def get(self, name: str) -> RuntimeValue:
        """Resolve a runtime value through the lexical environment chain."""
        if name in self.values: return self.values[name]
        if self.enclosing is not None: return self.enclosing.get(name)
        raise KeyError(name)


@dataclass(slots=True)
class AlgoStack:
    """Store values with last-in, first-out stack semantics."""
    items: list[RuntimeValue] = field(default_factory=list)


@dataclass(slots=True)
class AlgoQueue:
    """Store values with first-in, first-out queue semantics."""
    items: deque[RuntimeValue] = field(default_factory=deque)


@dataclass(slots=True)
class AlgoDeque:
    """Store values that can be added or removed at either end."""
    items: deque[RuntimeValue] = field(default_factory=deque)


@dataclass(order=False, slots=True)
class _MaxItem:
    """Wrap a heap item with reversed comparison for maximum heaps."""
    value: RuntimeValue
    def __lt__(self, other: "_MaxItem") -> bool:
        """Reverse heap ordering so larger values receive higher priority."""
        return self.value > other.value


@dataclass(slots=True)
class AlgoHeap:
    """Provide a minimum or maximum priority heap over runtime values."""
    maximum: bool
    items: list[RuntimeValue] = field(default_factory=list)

    def push(self, value: RuntimeValue) -> None:
        """Push a value onto the heap."""
        heapq.heappush(self.items, _MaxItem(value) if self.maximum else value)

    def pop(self) -> RuntimeValue:
        """Remove and return the highest-priority value."""
        value = heapq.heappop(self.items)
        return value.value if self.maximum else value

    def peek(self) -> RuntimeValue:
        """Return the highest-priority value without removing it."""
        value = self.items[0]
        return value.value if self.maximum else value

    def values(self) -> list[RuntimeValue]:
        """Return heap values in priority order for display and tracing."""
        raw = [value.value if self.maximum else value for value in self.items]
        return sorted(raw, reverse=self.maximum)


@dataclass(frozen=True, slots=True)
class NativeFunction:
    """Wrap an interpreter-provided callable as an AlgoLang function."""
    name: str
    function: Callable[..., RuntimeValue]


@dataclass(frozen=True, slots=True)
class AlgoFunction:
    """Pair a user function declaration with its captured environment."""
    declaration: Any
    closure: Environment


def type_name(value: RuntimeValue) -> str:
    """Return the AlgoLang type name for a runtime value."""
    if value is None: return "null"
    if isinstance(value, bool): return "bool"
    if isinstance(value, int): return "int"
    if isinstance(value, float): return "float"
    if isinstance(value, str): return "string"
    if isinstance(value, list): return "array"
    if isinstance(value, dict): return "map"
    if isinstance(value, set): return "set"
    if isinstance(value, AlgoStack): return "stack"
    if isinstance(value, AlgoQueue): return "queue"
    if isinstance(value, AlgoDeque): return "deque"
    if isinstance(value, AlgoHeap): return "maxheap" if value.maximum else "minheap"
    if isinstance(value, (AlgoFunction, NativeFunction)): return "function"
    return type(value).__name__


def display(value: RuntimeValue) -> str:
    """Render a runtime value using AlgoLang's user-facing notation."""
    if value is None: return "null"
    if isinstance(value, bool): return str(value).lower()
    if isinstance(value, str): return value
    if isinstance(value, list): return "[" + ", ".join(display(v) for v in value) + "]"
    if isinstance(value, dict): return "{" + ", ".join(f"{display(k)}: {display(v)}" for k, v in value.items()) + "}"
    if isinstance(value, set): return "{" + ", ".join(sorted(display(v) for v in value)) + "}"
    if isinstance(value, (AlgoStack, AlgoQueue, AlgoDeque)): return display(list(value.items))
    if isinstance(value, AlgoHeap): return display(value.values())
    return str(value)
