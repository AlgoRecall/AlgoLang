from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from .source import SourceSpan

R = TypeVar("R")


class AstVisitor(Protocol[R]):
    """Structural visitor marker; concrete passes implement visit_* methods."""


@dataclass(frozen=True, slots=True)
class Node:
    span: SourceSpan

    def accept(self, visitor: AstVisitor[R]) -> R:
        name = self.__class__.__name__
        snake = "".join(("_" + c.lower()) if c.isupper() else c for c in name).lstrip("_")
        return getattr(visitor, f"visit_{snake}")(self)


class Statement(Node): pass
class Expression(Node): pass


@dataclass(frozen=True, slots=True)
class TypeNode(Node):
    name: str
    arguments: tuple["TypeNode", ...] = ()


@dataclass(frozen=True, slots=True)
class Parameter(Node):
    name: str
    type_node: TypeNode


@dataclass(frozen=True, slots=True)
class Program(Node):
    statements: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class BlockStatement(Statement):
    statements: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class AssignmentStatement(Statement):
    target: Expression
    value: Expression
    annotation: TypeNode | None = None

    @property
    def name(self) -> str:
        return self.target.name if isinstance(self.target, Identifier) else ""


@dataclass(frozen=True, slots=True)
class ExpressionStatement(Statement):
    expression: Expression


@dataclass(frozen=True, slots=True)
class PrintStatement(Statement):
    expression: Expression


@dataclass(frozen=True, slots=True)
class IfStatement(Statement):
    condition: Expression
    then_branch: BlockStatement
    else_branch: BlockStatement | "IfStatement" | None


@dataclass(frozen=True, slots=True)
class WhileStatement(Statement):
    condition: Expression
    body: BlockStatement


@dataclass(frozen=True, slots=True)
class ForStatement(Statement):
    names: tuple[str, ...]
    iterable: Expression
    body: BlockStatement


@dataclass(frozen=True, slots=True)
class BreakStatement(Statement): pass


@dataclass(frozen=True, slots=True)
class ContinueStatement(Statement): pass


@dataclass(frozen=True, slots=True)
class ReturnStatement(Statement):
    value: Expression | None


@dataclass(frozen=True, slots=True)
class FunctionDeclaration(Statement):
    name: str
    parameters: tuple[Parameter, ...]
    return_type: TypeNode
    body: BlockStatement


@dataclass(frozen=True, slots=True)
class IntegerLiteral(Expression): value: int
@dataclass(frozen=True, slots=True)
class FloatLiteral(Expression): value: float
@dataclass(frozen=True, slots=True)
class BooleanLiteral(Expression): value: bool
@dataclass(frozen=True, slots=True)
class StringLiteral(Expression): value: str
@dataclass(frozen=True, slots=True)
class NullLiteral(Expression): pass
@dataclass(frozen=True, slots=True)
class Identifier(Expression): name: str
@dataclass(frozen=True, slots=True)
class ArrayLiteral(Expression): elements: tuple[Expression, ...]
@dataclass(frozen=True, slots=True)
class GroupingExpression(Expression): expression: Expression
@dataclass(frozen=True, slots=True)
class UnaryExpression(Expression):
    operator: str
    operand: Expression
@dataclass(frozen=True, slots=True)
class BinaryExpression(Expression):
    left: Expression
    operator: str
    right: Expression
@dataclass(frozen=True, slots=True)
class CallExpression(Expression):
    callee: Expression
    arguments: tuple[Expression, ...]
@dataclass(frozen=True, slots=True)
class IndexExpression(Expression):
    collection: Expression
    index: Expression
@dataclass(frozen=True, slots=True)
class MemberExpression(Expression):
    object: Expression
    name: str
@dataclass(frozen=True, slots=True)
class CollectionConstructor(Expression):
    type_node: TypeNode

