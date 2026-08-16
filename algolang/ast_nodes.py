"""Abstract syntax tree node definitions and visitor dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from .source import SourceSpan

R = TypeVar("R")


class AstVisitor(Protocol[R]):
    """Structural visitor marker; concrete passes implement visit_* methods."""


@dataclass(frozen=True, slots=True)
class Node:
    """Base class for all source-spanned abstract syntax tree nodes."""
    span: SourceSpan

    def accept(self, visitor: AstVisitor[R]) -> R:
        """Dispatch this node to the visitor method for its concrete type.

        Args:
            visitor (AstVisitor[R]): Visitor implementing the operation for this node type.

        Returns:
            R: The value returned by the concrete visitor method.
        """
        name = self.__class__.__name__
        snake = "".join(("_" + c.lower()) if c.isupper() else c for c in name).lstrip("_")
        return getattr(visitor, f"visit_{snake}")(self)


class Statement(Node):
    """Base class for executable statement nodes."""
    pass


class Expression(Node):
    """Base class for value-producing expression nodes."""
    pass


@dataclass(frozen=True, slots=True)
class TypeNode(Node):
    """Represent a primitive, array, or generic collection type annotation."""
    name: str
    arguments: tuple["TypeNode", ...] = ()


@dataclass(frozen=True, slots=True)
class Parameter(Node):
    """Represent an AlgoLang parameter node."""
    name: str
    type_node: TypeNode


@dataclass(frozen=True, slots=True)
class Program(Node):
    """Represent an AlgoLang program node."""
    statements: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class BlockStatement(Statement):
    """Represent an AlgoLang block statement node."""
    statements: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class AssignmentStatement(Statement):
    """Represent an AlgoLang assignment statement node."""
    target: Expression
    value: Expression
    annotation: TypeNode | None = None

    @property
    def name(self) -> str:
        """Return the assigned identifier name, or an empty string for a complex target.

        Returns:
            str: The resulting text.
        """
        return self.target.name if isinstance(self.target, Identifier) else ""


@dataclass(frozen=True, slots=True)
class ExpressionStatement(Statement):
    """Represent an AlgoLang expression statement node."""
    expression: Expression


@dataclass(frozen=True, slots=True)
class PrintStatement(Statement):
    """Represent an AlgoLang print statement node."""
    expression: Expression


@dataclass(frozen=True, slots=True)
class IfStatement(Statement):
    """Represent an AlgoLang if statement node."""
    condition: Expression
    then_branch: BlockStatement
    else_branch: BlockStatement | "IfStatement" | None


@dataclass(frozen=True, slots=True)
class WhileStatement(Statement):
    """Represent an AlgoLang while statement node."""
    condition: Expression
    body: BlockStatement


@dataclass(frozen=True, slots=True)
class ForStatement(Statement):
    """Represent an AlgoLang for statement node."""
    names: tuple[str, ...]
    iterable: Expression
    body: BlockStatement


@dataclass(frozen=True, slots=True)
class BreakStatement(Statement):
    """Represent an AlgoLang break statement node."""
    pass


@dataclass(frozen=True, slots=True)
class ContinueStatement(Statement):
    """Represent an AlgoLang continue statement node."""
    pass


@dataclass(frozen=True, slots=True)
class ReturnStatement(Statement):
    """Represent an AlgoLang return statement node."""
    value: Expression | None


@dataclass(frozen=True, slots=True)
class FunctionDeclaration(Statement):
    """Represent an AlgoLang function declaration node."""
    name: str
    parameters: tuple[Parameter, ...]
    return_type: TypeNode
    body: BlockStatement


@dataclass(frozen=True, slots=True)
class IntegerLiteral(Expression):
    """Represent an AlgoLang integer literal node."""
    value: int


@dataclass(frozen=True, slots=True)
class FloatLiteral(Expression):
    """Represent an AlgoLang float literal node."""
    value: float


@dataclass(frozen=True, slots=True)
class BooleanLiteral(Expression):
    """Represent an AlgoLang boolean literal node."""
    value: bool


@dataclass(frozen=True, slots=True)
class StringLiteral(Expression):
    """Represent an AlgoLang string literal node."""
    value: str


@dataclass(frozen=True, slots=True)
class NullLiteral(Expression):
    """Represent an AlgoLang null literal node."""
    pass


@dataclass(frozen=True, slots=True)
class Identifier(Expression):
    """Represent an AlgoLang identifier node."""
    name: str


@dataclass(frozen=True, slots=True)
class ArrayLiteral(Expression):
    """Represent an AlgoLang array literal node."""
    elements: tuple[Expression, ...]


@dataclass(frozen=True, slots=True)
class GroupingExpression(Expression):
    """Represent an AlgoLang grouping expression node."""
    expression: Expression


@dataclass(frozen=True, slots=True)
class UnaryExpression(Expression):
    """Represent an AlgoLang unary expression node."""
    operator: str
    operand: Expression


@dataclass(frozen=True, slots=True)
class BinaryExpression(Expression):
    """Represent an AlgoLang binary expression node."""
    left: Expression
    operator: str
    right: Expression


@dataclass(frozen=True, slots=True)
class CallExpression(Expression):
    """Represent an AlgoLang call expression node."""
    callee: Expression
    arguments: tuple[Expression, ...]


@dataclass(frozen=True, slots=True)
class IndexExpression(Expression):
    """Represent an AlgoLang index expression node."""
    collection: Expression
    index: Expression


@dataclass(frozen=True, slots=True)
class MemberExpression(Expression):
    """Represent an AlgoLang member expression node."""
    object: Expression
    name: str


@dataclass(frozen=True, slots=True)
class CollectionConstructor(Expression):
    """Represent an AlgoLang collection constructor node."""
    type_node: TypeNode
