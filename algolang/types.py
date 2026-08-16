"""Static type values and lexically scoped symbol tables."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Type:
    """Represent a primitive or parameterized AlgoLang type."""
    name: str
    arguments: tuple["Type", ...] = ()

    def __str__(self) -> str:
        """Return the canonical AlgoLang representation."""
        if self.name == "array": return f"[{self.arguments[0]}]"
        if self.arguments: return f"{self.name}<{', '.join(map(str, self.arguments))}>"
        return self.name


@dataclass(frozen=True, slots=True)
class FunctionType:
    """Represent function parameter and return types."""
    parameters: tuple[Type, ...]
    result: Type

    def __str__(self) -> str:
        """Return the canonical AlgoLang representation."""
        return f"fn({', '.join(map(str, self.parameters))}) -> {self.result}"


INT, FLOAT, BOOL, STRING, NULL, UNKNOWN = (Type(name) for name in ("int", "float", "bool", "string", "null", "unknown"))
COLLECTION_ARITY = {
    "array": 1, "map": 2, "set": 1, "stack": 1, "queue": 1,
    "deque": 1, "minheap": 1, "maxheap": 1,
}
PRIMITIVES = {"int": INT, "float": FLOAT, "bool": BOOL, "string": STRING, "null": NULL}


@dataclass(slots=True)
class SymbolTable:
    """Store static types across nested lexical scopes."""
    enclosing: "SymbolTable | None" = None
    symbols: dict[str, Type | FunctionType] = field(default_factory=dict)

    def define(self, name: str, type_: Type | FunctionType) -> None:
        """Define or replace a type binding in the current scope."""
        self.symbols[name] = type_

    def resolve(self, name: str) -> Type | FunctionType | None:
        """Resolve a type binding through the lexical scope chain."""
        if name in self.symbols: return self.symbols[name]
        return self.enclosing.resolve(name) if self.enclosing else None

    def resolve_owner(self, name: str) -> "SymbolTable | None":
        """Return the innermost symbol table that owns a binding."""
        if name in self.symbols: return self
        return self.enclosing.resolve_owner(name) if self.enclosing else None
