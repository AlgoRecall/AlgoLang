from __future__ import annotations

from . import ast_nodes as ast


class AstPrinter:
    def print(self, node: ast.Node) -> str:
        return node.accept(self)

    def visit_program(self, node: ast.Program) -> str:
        return self._form("program", node.statements)

    def visit_block_statement(self, node: ast.BlockStatement) -> str:
        return self._form("block", node.statements)

    def visit_assignment_statement(self, node: ast.AssignmentStatement) -> str:
        annotation = f" :{self._type(node.annotation)}" if node.annotation else ""
        target = node.target.name if isinstance(node.target, ast.Identifier) else node.target.accept(self)
        return f"(assign {target}{annotation} {node.value.accept(self)})"

    def visit_expression_statement(self, node: ast.ExpressionStatement) -> str:
        return f"(expression {node.expression.accept(self)})"

    def visit_print_statement(self, node: ast.PrintStatement) -> str:
        return f"(print {node.expression.accept(self)})"

    def visit_if_statement(self, node: ast.IfStatement) -> str:
        alternate = f" {node.else_branch.accept(self)}" if node.else_branch else ""
        return f"(if {node.condition.accept(self)} {node.then_branch.accept(self)}{alternate})"

    def visit_while_statement(self, node: ast.WhileStatement) -> str:
        return f"(while {node.condition.accept(self)} {node.body.accept(self)})"

    def visit_for_statement(self, node: ast.ForStatement) -> str:
        return f"(for ({' '.join(node.names)}) {node.iterable.accept(self)} {node.body.accept(self)})"

    def visit_break_statement(self, node: ast.BreakStatement) -> str: return "(break)"
    def visit_continue_statement(self, node: ast.ContinueStatement) -> str: return "(continue)"

    def visit_return_statement(self, node: ast.ReturnStatement) -> str:
        return f"(return{(' ' + node.value.accept(self)) if node.value else ''})"

    def visit_function_declaration(self, node: ast.FunctionDeclaration) -> str:
        params = " ".join(f"({p.name} {self._type(p.type_node)})" for p in node.parameters)
        return f"(fn {node.name} ({params}) {self._type(node.return_type)} {node.body.accept(self)})"

    def visit_integer_literal(self, node: ast.IntegerLiteral) -> str: return f"(int {node.value})"
    def visit_float_literal(self, node: ast.FloatLiteral) -> str: return f"(float {node.value})"
    def visit_boolean_literal(self, node: ast.BooleanLiteral) -> str: return f"(bool {str(node.value).lower()})"
    def visit_null_literal(self, node: ast.NullLiteral) -> str: return "(null)"

    def visit_string_literal(self, node: ast.StringLiteral) -> str:
        value = node.value.encode("unicode_escape").decode("ascii").replace('"', '\\"')
        return f'(string "{value}")'

    def visit_identifier(self, node: ast.Identifier) -> str: return f"(identifier {node.name})"
    def visit_array_literal(self, node: ast.ArrayLiteral) -> str: return self._form("array", node.elements)
    def visit_grouping_expression(self, node: ast.GroupingExpression) -> str: return f"(group {node.expression.accept(self)})"
    def visit_unary_expression(self, node: ast.UnaryExpression) -> str: return f"({node.operator} {node.operand.accept(self)})"
    def visit_binary_expression(self, node: ast.BinaryExpression) -> str: return f"({node.operator} {node.left.accept(self)} {node.right.accept(self)})"
    def visit_call_expression(self, node: ast.CallExpression) -> str: return self._form("call " + node.callee.accept(self), node.arguments)
    def visit_index_expression(self, node: ast.IndexExpression) -> str: return f"(index {node.collection.accept(self)} {node.index.accept(self)})"
    def visit_member_expression(self, node: ast.MemberExpression) -> str: return f"(member {node.object.accept(self)} {node.name})"
    def visit_collection_constructor(self, node: ast.CollectionConstructor) -> str: return f"(new {self._type(node.type_node)})"

    def _form(self, name: str, children) -> str:
        body = " ".join(child.accept(self) for child in children)
        return f"({name}{(' ' + body) if body else ''})"

    def _type(self, node: ast.TypeNode | None) -> str:
        assert node is not None
        if node.name == "array": return f"[{self._type(node.arguments[0])}]"
        if node.arguments: return f"{node.name}<{', '.join(self._type(a) for a in node.arguments)}>"
        return node.name
