"""Stable parenthesized rendering for AlgoLang abstract syntax trees."""

from __future__ import annotations

from . import ast_nodes as ast


class AstPrinter:
    """Render abstract syntax tree nodes as stable parenthesized forms."""

    def print(self, node: ast.Node) -> str:
        """Render a node and all of its descendants as a text form.

        Args:
            node (ast.Node): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return node.accept(self)

    def visit_program(self, node: ast.Program) -> str:
        """Render the program node.

        Args:
            node (ast.Program): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return self._form("program", node.statements)

    def visit_block_statement(self, node: ast.BlockStatement) -> str:
        """Render the block statement node.

        Args:
            node (ast.BlockStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return self._form("block", node.statements)

    def visit_assignment_statement(self, node: ast.AssignmentStatement) -> str:
        """Render the assignment statement node.

        Args:
            node (ast.AssignmentStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        annotation = f" :{self._type(node.annotation)}" if node.annotation else ""
        target = node.target.name if isinstance(node.target, ast.Identifier) else node.target.accept(self)
        return f"(assign {target}{annotation} {node.value.accept(self)})"

    def visit_expression_statement(self, node: ast.ExpressionStatement) -> str:
        """Render the expression statement node.

        Args:
            node (ast.ExpressionStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(expression {node.expression.accept(self)})"

    def visit_print_statement(self, node: ast.PrintStatement) -> str:
        """Render the print statement node.

        Args:
            node (ast.PrintStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(print {node.expression.accept(self)})"

    def visit_if_statement(self, node: ast.IfStatement) -> str:
        """Render the if statement node.

        Args:
            node (ast.IfStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        alternate = f" {node.else_branch.accept(self)}" if node.else_branch else ""
        return f"(if {node.condition.accept(self)} {node.then_branch.accept(self)}{alternate})"

    def visit_while_statement(self, node: ast.WhileStatement) -> str:
        """Render the while statement node.

        Args:
            node (ast.WhileStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(while {node.condition.accept(self)} {node.body.accept(self)})"

    def visit_for_statement(self, node: ast.ForStatement) -> str:
        """Render the for statement node.

        Args:
            node (ast.ForStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(for ({' '.join(node.names)}) {node.iterable.accept(self)} {node.body.accept(self)})"

    def visit_break_statement(self, node: ast.BreakStatement) -> str:
        """Render the break statement node.

        Args:
            node (ast.BreakStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return "(break)"

    def visit_continue_statement(self, node: ast.ContinueStatement) -> str:
        """Render the continue statement node.

        Args:
            node (ast.ContinueStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return "(continue)"

    def visit_return_statement(self, node: ast.ReturnStatement) -> str:
        """Render the return statement node.

        Args:
            node (ast.ReturnStatement): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(return{(' ' + node.value.accept(self)) if node.value else ''})"

    def visit_function_declaration(self, node: ast.FunctionDeclaration) -> str:
        """Render the function declaration node.

        Args:
            node (ast.FunctionDeclaration): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        params = " ".join(f"({p.name} {self._type(p.type_node)})" for p in node.parameters)
        return f"(fn {node.name} ({params}) {self._type(node.return_type)} {node.body.accept(self)})"

    def visit_integer_literal(self, node: ast.IntegerLiteral) -> str:
        """Render the integer literal node.

        Args:
            node (ast.IntegerLiteral): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(int {node.value})"

    def visit_float_literal(self, node: ast.FloatLiteral) -> str:
        """Render the float literal node.

        Args:
            node (ast.FloatLiteral): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(float {node.value})"

    def visit_boolean_literal(self, node: ast.BooleanLiteral) -> str:
        """Render the boolean literal node.

        Args:
            node (ast.BooleanLiteral): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(bool {str(node.value).lower()})"

    def visit_null_literal(self, node: ast.NullLiteral) -> str:
        """Render the null literal node.

        Args:
            node (ast.NullLiteral): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return "(null)"

    def visit_string_literal(self, node: ast.StringLiteral) -> str:
        """Render the string literal node.

        Args:
            node (ast.StringLiteral): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        value = node.value.encode("unicode_escape").decode("ascii").replace('"', '\\"')
        return f'(string "{value}")'

    def visit_identifier(self, node: ast.Identifier) -> str:
        """Render the identifier node.

        Args:
            node (ast.Identifier): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(identifier {node.name})"

    def visit_array_literal(self, node: ast.ArrayLiteral) -> str:
        """Render the array literal node.

        Args:
            node (ast.ArrayLiteral): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return self._form("array", node.elements)

    def visit_grouping_expression(self, node: ast.GroupingExpression) -> str:
        """Render the grouping expression node.

        Args:
            node (ast.GroupingExpression): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(group {node.expression.accept(self)})"

    def visit_unary_expression(self, node: ast.UnaryExpression) -> str:
        """Render the unary expression node.

        Args:
            node (ast.UnaryExpression): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"({node.operator} {node.operand.accept(self)})"

    def visit_binary_expression(self, node: ast.BinaryExpression) -> str:
        """Render the binary expression node.

        Args:
            node (ast.BinaryExpression): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"({node.operator} {node.left.accept(self)} {node.right.accept(self)})"

    def visit_call_expression(self, node: ast.CallExpression) -> str:
        """Render the call expression node.

        Args:
            node (ast.CallExpression): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return self._form("call " + node.callee.accept(self), node.arguments)

    def visit_index_expression(self, node: ast.IndexExpression) -> str:
        """Render the index expression node.

        Args:
            node (ast.IndexExpression): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(index {node.collection.accept(self)} {node.index.accept(self)})"

    def visit_member_expression(self, node: ast.MemberExpression) -> str:
        """Render the member expression node.

        Args:
            node (ast.MemberExpression): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(member {node.object.accept(self)} {node.name})"

    def visit_collection_constructor(self, node: ast.CollectionConstructor) -> str:
        """Render the collection constructor node.

        Args:
            node (ast.CollectionConstructor): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return f"(new {self._type(node.type_node)})"

    def _form(self, name: str, children) -> str:
        """Render a named parenthesized form containing child nodes.

        Args:
            name (str): Identifier or display name used by the operation.
            children (object): Child nodes to include in the rendered form.

        Returns:
            str: The resulting text.
        """
        body = " ".join(child.accept(self) for child in children)
        return f"({name}{(' ' + body) if body else ''})"

    def _type(self, node: ast.TypeNode | None) -> str:
        """Render an AST type node using AlgoLang type syntax.

        Args:
            node (ast.TypeNode | None): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        assert node is not None
        if node.name == "array": return f"[{self._type(node.arguments[0])}]"
        if node.arguments: return f"{node.name}<{', '.join(self._type(a) for a in node.arguments)}>"
        return node.name
