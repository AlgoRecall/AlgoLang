"""Context-sensitive validation independent of static types."""

from __future__ import annotations

from . import ast_nodes as ast
from .errors import SemanticError


class SemanticAnalyzer:
    """Validates context-sensitive rules that are independent of types."""

    def __init__(self, source: str):
        """Initialize the semantic analyzer.

        Args:
            source (str): AlgoLang source text.

        Returns:
            None: No value is returned.
        """
        self.source = source
        self.loop_depth = 0
        self.function_depth = 0
        self.block_depth = 0

    def analyze(self, program: ast.Program) -> None:
        """Validate a complete program and return it unchanged on success.

        Args:
            program (ast.Program): Program node to validate or execute.

        Returns:
            None: No value is returned.
        """
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
        """Validate the program node.

        Args:
            node (ast.Program): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        for statement in node.statements: statement.accept(self)

    def visit_block_statement(self, node: ast.BlockStatement) -> None:
        """Validate the block statement node.

        Args:
            node (ast.BlockStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        self.block_depth += 1
        for statement in node.statements: statement.accept(self)
        self.block_depth -= 1

    def visit_function_declaration(self, node: ast.FunctionDeclaration) -> None:
        """Validate the function declaration node.

        Args:
            node (ast.FunctionDeclaration): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
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
        """Validate the if statement node.

        Args:
            node (ast.IfStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.condition.accept(self);
        node.then_branch.accept(self)
        if node.else_branch: node.else_branch.accept(self)

    def visit_while_statement(self, node: ast.WhileStatement) -> None:
        """Validate the while statement node.

        Args:
            node (ast.WhileStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.condition.accept(self);
        self.loop_depth += 1
        node.body.accept(self);
        self.loop_depth -= 1

    def visit_for_statement(self, node: ast.ForStatement) -> None:
        """Validate the for statement node.

        Args:
            node (ast.ForStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        if len(set(node.names)) != len(node.names): self._error(node, "for-loop variables must be distinct")
        node.iterable.accept(self);
        self.loop_depth += 1
        node.body.accept(self);
        self.loop_depth -= 1

    def visit_break_statement(self, node: ast.BreakStatement) -> None:
        """Validate the break statement node.

        Args:
            node (ast.BreakStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        if not self.loop_depth: self._error(node, "'break' is only valid inside a loop")

    def visit_continue_statement(self, node: ast.ContinueStatement) -> None:
        """Validate the continue statement node.

        Args:
            node (ast.ContinueStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        if not self.loop_depth: self._error(node, "'continue' is only valid inside a loop")

    def visit_return_statement(self, node: ast.ReturnStatement) -> None:
        """Validate the return statement node.

        Args:
            node (ast.ReturnStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        if not self.function_depth: self._error(node, "'return' is only valid inside a function")
        if node.value: node.value.accept(self)

    def visit_assignment_statement(self, node: ast.AssignmentStatement) -> None:
        """Validate the assignment statement node.

        Args:
            node (ast.AssignmentStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.target.accept(self);
        node.value.accept(self)

    def visit_expression_statement(self, node: ast.ExpressionStatement) -> None:
        """Validate the expression statement node.

        Args:
            node (ast.ExpressionStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.expression.accept(self)

    def visit_print_statement(self, node: ast.PrintStatement) -> None:
        """Validate the print statement node.

        Args:
            node (ast.PrintStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.expression.accept(self)

    def visit_grouping_expression(self, node: ast.GroupingExpression) -> None:
        """Validate the grouping expression node.

        Args:
            node (ast.GroupingExpression): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.expression.accept(self)

    def visit_unary_expression(self, node: ast.UnaryExpression) -> None:
        """Validate the unary expression node.

        Args:
            node (ast.UnaryExpression): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.operand.accept(self)

    def visit_binary_expression(self, node: ast.BinaryExpression) -> None:
        """Validate the binary expression node.

        Args:
            node (ast.BinaryExpression): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.left.accept(self);
        node.right.accept(self)

    def visit_array_literal(self, node: ast.ArrayLiteral) -> None:
        """Validate the array literal node.

        Args:
            node (ast.ArrayLiteral): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        for item in node.elements: item.accept(self)

    def visit_call_expression(self, node: ast.CallExpression) -> None:
        """Validate the call expression node.

        Args:
            node (ast.CallExpression): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.callee.accept(self)
        for argument in node.arguments: argument.accept(self)

    def visit_index_expression(self, node: ast.IndexExpression) -> None:
        """Validate the index expression node.

        Args:
            node (ast.IndexExpression): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.collection.accept(self);
        node.index.accept(self)

    def visit_member_expression(self, node: ast.MemberExpression) -> None:
        """Validate the member expression node.

        Args:
            node (ast.MemberExpression): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        node.object.accept(self)

    def visit_collection_constructor(self, node: ast.CollectionConstructor) -> None:
        """Validate the collection constructor node.

        Args:
            node (ast.CollectionConstructor): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        pass

    def visit_identifier(self, node: ast.Identifier) -> None:
        """Validate the identifier node.

        Args:
            node (ast.Identifier): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        pass

    def visit_integer_literal(self, node: ast.IntegerLiteral) -> None:
        """Validate the integer literal node.

        Args:
            node (ast.IntegerLiteral): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        pass

    def visit_float_literal(self, node: ast.FloatLiteral) -> None:
        """Validate the float literal node.

        Args:
            node (ast.FloatLiteral): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        pass

    def visit_boolean_literal(self, node: ast.BooleanLiteral) -> None:
        """Validate the boolean literal node.

        Args:
            node (ast.BooleanLiteral): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        pass

    def visit_string_literal(self, node: ast.StringLiteral) -> None:
        """Validate the string literal node.

        Args:
            node (ast.StringLiteral): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        pass

    def visit_null_literal(self, node: ast.NullLiteral) -> None:
        """Validate the null literal node.

        Args:
            node (ast.NullLiteral): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        pass

    def _error(self, node: ast.Node, message: str):
        """Raise a source-aware semantic error for an AST node.

        Args:
            node (ast.Node): Abstract syntax tree node to process.
            message (str): Diagnostic message presented to the user.

        Returns:
            None: No value is returned.

        Raises:
            SemanticError: When the operation cannot complete successfully.
        """
        raise SemanticError(message, node.span, self.source)
