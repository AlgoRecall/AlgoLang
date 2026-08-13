from __future__ import annotations

from . import ast_nodes as ast
from .errors import SemanticError


class SemanticAnalyzer:
    """Validates context-sensitive rules that are independent of types."""

    def __init__(self, source: str):
        self.source = source
        self.loop_depth = 0
        self.function_depth = 0
        self.block_depth = 0

    def analyze(self, program: ast.Program) -> None:
        names: set[str] = set()
        for statement in program.statements:
            if isinstance(statement, ast.FunctionDeclaration):
                if statement.name in ("len", "range"):
                    self._error(statement, f"cannot redeclare built-in '{statement.name}'")
                if statement.name in names:
                    self._error(statement, f"function '{statement.name}' is already declared")
                names.add(statement.name)
        program.accept(self)

    def visit_program(self, node: ast.Program) -> None:
        for statement in node.statements: statement.accept(self)

    def visit_block_statement(self, node: ast.BlockStatement) -> None:
        self.block_depth += 1
        for statement in node.statements: statement.accept(self)
        self.block_depth -= 1

    def visit_function_declaration(self, node: ast.FunctionDeclaration) -> None:
        if self.block_depth or self.function_depth:
            self._error(node, "functions may only be declared at top level")
        names: set[str] = set()
        for parameter in node.parameters:
            if parameter.name in names:
                self._error(parameter, f"duplicate parameter '{parameter.name}'")
            names.add(parameter.name)
        old_loops = self.loop_depth
        self.loop_depth = 0
        self.function_depth += 1
        node.body.accept(self)
        self.function_depth -= 1
        self.loop_depth = old_loops

    def visit_if_statement(self, node: ast.IfStatement) -> None:
        node.condition.accept(self); node.then_branch.accept(self)
        if node.else_branch: node.else_branch.accept(self)

    def visit_while_statement(self, node: ast.WhileStatement) -> None:
        node.condition.accept(self); self.loop_depth += 1
        node.body.accept(self); self.loop_depth -= 1

    def visit_for_statement(self, node: ast.ForStatement) -> None:
        if len(set(node.names)) != len(node.names): self._error(node, "for-loop variables must be distinct")
        node.iterable.accept(self); self.loop_depth += 1
        node.body.accept(self); self.loop_depth -= 1

    def visit_break_statement(self, node: ast.BreakStatement) -> None:
        if not self.loop_depth: self._error(node, "'break' is only valid inside a loop")

    def visit_continue_statement(self, node: ast.ContinueStatement) -> None:
        if not self.loop_depth: self._error(node, "'continue' is only valid inside a loop")

    def visit_return_statement(self, node: ast.ReturnStatement) -> None:
        if not self.function_depth: self._error(node, "'return' is only valid inside a function")
        if node.value: node.value.accept(self)

    def visit_assignment_statement(self, node: ast.AssignmentStatement) -> None:
        node.target.accept(self); node.value.accept(self)
    def visit_expression_statement(self, node: ast.ExpressionStatement) -> None: node.expression.accept(self)
    def visit_print_statement(self, node: ast.PrintStatement) -> None: node.expression.accept(self)
    def visit_grouping_expression(self, node: ast.GroupingExpression) -> None: node.expression.accept(self)
    def visit_unary_expression(self, node: ast.UnaryExpression) -> None: node.operand.accept(self)
    def visit_binary_expression(self, node: ast.BinaryExpression) -> None: node.left.accept(self); node.right.accept(self)
    def visit_array_literal(self, node: ast.ArrayLiteral) -> None:
        for item in node.elements: item.accept(self)
    def visit_call_expression(self, node: ast.CallExpression) -> None:
        node.callee.accept(self)
        for argument in node.arguments: argument.accept(self)
    def visit_index_expression(self, node: ast.IndexExpression) -> None: node.collection.accept(self); node.index.accept(self)
    def visit_member_expression(self, node: ast.MemberExpression) -> None: node.object.accept(self)
    def visit_collection_constructor(self, node: ast.CollectionConstructor) -> None: pass
    def visit_identifier(self, node: ast.Identifier) -> None: pass
    def visit_integer_literal(self, node: ast.IntegerLiteral) -> None: pass
    def visit_float_literal(self, node: ast.FloatLiteral) -> None: pass
    def visit_boolean_literal(self, node: ast.BooleanLiteral) -> None: pass
    def visit_string_literal(self, node: ast.StringLiteral) -> None: pass
    def visit_null_literal(self, node: ast.NullLiteral) -> None: pass

    def _error(self, node: ast.Node, message: str):
        raise SemanticError(message, node.span, self.source)
