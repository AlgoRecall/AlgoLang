from __future__ import annotations

from . import ast_nodes as ast
from .errors import TypeCheckError
from .types import (
    BOOL, FLOAT, INT, NULL, STRING, UNKNOWN, COLLECTION_ARITY, PRIMITIVES,
    FunctionType, SymbolTable, Type,
)


class TypeChecker:
    def __init__(self, source: str):
        self.source = source
        self.globals = SymbolTable()
        self.scope = self.globals
        self.current_return: Type | None = None

    def check(self, program: ast.Program) -> SymbolTable:
        for statement in program.statements:
            if isinstance(statement, ast.FunctionDeclaration):
                signature = FunctionType(
                    tuple(self._resolve_type(p.type_node) for p in statement.parameters),
                    self._resolve_type(statement.return_type),
                )
                self.globals.define(statement.name, signature)
        for statement in program.statements:
            if not isinstance(statement, ast.FunctionDeclaration): statement.accept(self)
        for statement in program.statements:
            if isinstance(statement, ast.FunctionDeclaration): statement.accept(self)
        return self.globals

    def visit_program(self, node: ast.Program) -> None: pass

    def visit_block_statement(self, node: ast.BlockStatement) -> None:
        self._begin_scope()
        try:
            for statement in node.statements: statement.accept(self)
        finally:
            self._end_scope()

    def visit_function_declaration(self, node: ast.FunctionDeclaration) -> None:
        signature = self.globals.resolve(node.name)
        assert isinstance(signature, FunctionType)
        previous_return = self.current_return
        previous_scope = self.scope
        self.scope = SymbolTable(self.globals)
        self.current_return = signature.result
        try:
            for parameter, type_ in zip(node.parameters, signature.parameters):
                self.scope.define(parameter.name, type_)
            node.body.accept(self)
            if signature.result != NULL and not self._definitely_returns(node.body):
                self._error(node, f"function '{node.name}' may finish without returning {signature.result}")
        finally:
            self.scope = previous_scope
            self.current_return = previous_return

    def visit_assignment_statement(self, node: ast.AssignmentStatement) -> None:
        value_type = self._expr(node.value)
        if isinstance(node.target, ast.Identifier):
            name = node.target.name
            if name in ("len", "range"):
                self._error(node.target, f"cannot assign to built-in '{name}'")
            if node.annotation:
                declared = self._resolve_type(node.annotation)
                if name in self.scope.symbols:
                    self._error(node.target, f"'{name}' is already declared in this scope")
                self._require_assignable(declared, value_type, node.value)
                self.scope.define(name, declared)
                return
            owner = self.scope.resolve_owner(name)
            if owner is None:
                if self._contains_unknown(value_type):
                    self._error(node.value, "cannot infer the element type of an empty array; add an explicit annotation")
                self.scope.define(name, value_type)
            else:
                expected = owner.symbols[name]
                if isinstance(expected, FunctionType): self._error(node.target, f"cannot assign to function '{name}'")
                self._require_assignable(expected, value_type, node.value)
            return
        if isinstance(node.target, ast.IndexExpression):
            collection_type = self._expr(node.target.collection)
            index_type = self._expr(node.target.index)
            expected = self._index_result(collection_type, index_type, node.target)
            if collection_type.name not in ("array", "map"):
                self._error(node.target, f"values of type {collection_type} do not support indexed assignment")
            self._require_assignable(expected, value_type, node.value)

    def visit_expression_statement(self, node: ast.ExpressionStatement) -> None: self._expr(node.expression)
    def visit_print_statement(self, node: ast.PrintStatement) -> None: self._expr(node.expression)

    def visit_if_statement(self, node: ast.IfStatement) -> None:
        self._require_exact(BOOL, self._expr(node.condition), node.condition, "if condition")
        node.then_branch.accept(self)
        if node.else_branch: node.else_branch.accept(self)

    def visit_while_statement(self, node: ast.WhileStatement) -> None:
        self._require_exact(BOOL, self._expr(node.condition), node.condition, "while condition")
        node.body.accept(self)

    def visit_for_statement(self, node: ast.ForStatement) -> None:
        iterable = self._expr(node.iterable)
        item = self._iterable_item(iterable, node.iterable)
        self._begin_scope()
        try:
            if len(node.names) == 1:
                self.scope.define(node.names[0], item)
            else:
                self.scope.define(node.names[0], INT)
                self.scope.define(node.names[1], item)
            node.body.accept(self)
        finally:
            self._end_scope()

    def visit_break_statement(self, node: ast.BreakStatement) -> None: pass
    def visit_continue_statement(self, node: ast.ContinueStatement) -> None: pass

    def visit_return_statement(self, node: ast.ReturnStatement) -> None:
        assert self.current_return is not None
        actual = NULL if node.value is None else self._expr(node.value)
        self._require_assignable(self.current_return, actual, node.value or node)

    def visit_integer_literal(self, node: ast.IntegerLiteral) -> Type: return INT
    def visit_float_literal(self, node: ast.FloatLiteral) -> Type: return FLOAT
    def visit_boolean_literal(self, node: ast.BooleanLiteral) -> Type: return BOOL
    def visit_string_literal(self, node: ast.StringLiteral) -> Type: return STRING
    def visit_null_literal(self, node: ast.NullLiteral) -> Type: return NULL

    def visit_identifier(self, node: ast.Identifier) -> Type | FunctionType:
        if node.name == "len": return FunctionType((UNKNOWN,), INT)
        if node.name == "range": return FunctionType((INT,), Type("array", (INT,)))
        found = self.scope.resolve(node.name)
        if found is None: self._error(node, f"undefined name '{node.name}'")
        return found

    def visit_array_literal(self, node: ast.ArrayLiteral) -> Type:
        element = UNKNOWN
        for expression in node.elements:
            element = self._merge(element, self._expr(expression), expression)
        return Type("array", (element,))

    def visit_grouping_expression(self, node: ast.GroupingExpression) -> Type | FunctionType:
        return node.expression.accept(self)

    def visit_unary_expression(self, node: ast.UnaryExpression) -> Type:
        operand = self._expr(node.operand)
        if node.operator == "not":
            self._require_exact(BOOL, operand, node.operand, "operand of 'not'")
            return BOOL
        if not self._numeric(operand): self._error(node.operand, f"unary '-' requires a number, got {operand}")
        return operand

    def visit_binary_expression(self, node: ast.BinaryExpression) -> Type:
        left = self._expr(node.left)
        if node.operator in ("and", "or"):
            right = self._expr(node.right)
            self._require_exact(BOOL, left, node.left, f"left operand of '{node.operator}'")
            self._require_exact(BOOL, right, node.right, f"right operand of '{node.operator}'")
            return BOOL
        right = self._expr(node.right)
        if node.operator in ("==", "!="): return BOOL
        if node.operator == "in":
            expected = self._membership_item(right, node.right)
            self._require_assignable(expected, left, node.left)
            return BOOL
        if node.operator == "+" and left == STRING and right == STRING: return STRING
        if node.operator in ("+", "-", "*", "/", "%"):
            if not self._numeric(left) or not self._numeric(right):
                self._error(node, f"operator '{node.operator}' requires numbers, got {left} and {right}")
            if node.operator == "/": return FLOAT if FLOAT in (left, right) else INT
            return FLOAT if FLOAT in (left, right) else INT
        if node.operator in ("<", "<=", ">", ">="):
            if not ((self._numeric(left) and self._numeric(right)) or left == right == STRING):
                self._error(node, f"operator '{node.operator}' cannot compare {left} and {right}")
            return BOOL
        self._error(node, f"unknown operator '{node.operator}'")

    def visit_call_expression(self, node: ast.CallExpression) -> Type:
        if isinstance(node.callee, ast.Identifier) and node.callee.name == "len":
            if len(node.arguments) != 1: self._error(node, "len expects exactly one argument")
            value = self._expr(node.arguments[0])
            if value.name not in ("array", "map", "set", "stack", "queue", "deque", "minheap", "maxheap", "string"):
                self._error(node.arguments[0], f"len does not accept {value}")
            return INT
        if isinstance(node.callee, ast.Identifier) and node.callee.name == "range":
            if len(node.arguments) not in (1, 2, 3): self._error(node, "range expects one, two, or three arguments")
            for argument in node.arguments: self._require_exact(INT, self._expr(argument), argument, "range argument")
            return Type("array", (INT,))
        callee = node.callee.accept(self)
        if not isinstance(callee, FunctionType): self._error(node.callee, f"value of type {callee} is not callable")
        if len(node.arguments) != len(callee.parameters):
            self._error(node, f"expected {len(callee.parameters)} arguments, got {len(node.arguments)}")
        for expected, argument in zip(callee.parameters, node.arguments):
            self._require_assignable(expected, self._expr(argument), argument)
        return callee.result

    def visit_index_expression(self, node: ast.IndexExpression) -> Type:
        return self._index_result(self._expr(node.collection), self._expr(node.index), node)

    def visit_member_expression(self, node: ast.MemberExpression) -> FunctionType:
        owner = self._expr(node.object)
        element = owner.arguments[-1] if owner.arguments else UNKNOWN
        methods: dict[str, FunctionType] = {}
        if owner.name == "array": methods = {"push": FunctionType((element,), NULL), "pop": FunctionType((), element)}
        elif owner.name == "set": methods = {"add": FunctionType((element,), NULL), "remove": FunctionType((element,), BOOL)}
        elif owner.name in ("stack", "minheap", "maxheap"):
            methods = {"push": FunctionType((element,), NULL), "pop": FunctionType((), element), "peek": FunctionType((), element)}
        elif owner.name == "queue":
            methods = {"enqueue": FunctionType((element,), NULL), "dequeue": FunctionType((), element), "front": FunctionType((), element)}
        elif owner.name == "deque":
            methods = {
                "push_front": FunctionType((element,), NULL), "push_back": FunctionType((element,), NULL),
                "pop_front": FunctionType((), element), "pop_back": FunctionType((), element),
                "front": FunctionType((), element), "back": FunctionType((), element),
            }
        if node.name == "len" and owner.name in COLLECTION_ARITY:
            return FunctionType((), INT)
        if node.name not in methods: self._error(node, f"type {owner} has no method '{node.name}'")
        return methods[node.name]

    def visit_collection_constructor(self, node: ast.CollectionConstructor) -> Type:
        type_ = self._resolve_type(node.type_node)
        if type_.name == "map" and type_.arguments[0].name not in PRIMITIVES:
            self._error(node, f"map keys must be primitive, got {type_.arguments[0]}")
        if type_.name in ("minheap", "maxheap") and not self._heap_comparable(type_.arguments[0]):
            self._error(
                node,
                f"heap elements must be int, float, string, or recursively comparable arrays, got {type_.arguments[0]}",
            )
        return type_

    def _resolve_type(self, node: ast.TypeNode) -> Type:
        if node.name in PRIMITIVES:
            if node.arguments: self._error(node, f"primitive type '{node.name}' takes no arguments")
            return PRIMITIVES[node.name]
        if node.name not in COLLECTION_ARITY: self._error(node, f"unknown type '{node.name}'")
        expected = COLLECTION_ARITY[node.name]
        if len(node.arguments) != expected:
            self._error(node, f"type '{node.name}' expects {expected} type argument(s), got {len(node.arguments)}")
        return Type(node.name, tuple(self._resolve_type(argument) for argument in node.arguments))

    def _index_result(self, collection: Type, index: Type, node: ast.Node) -> Type:
        if collection.name == "array":
            self._require_exact(INT, index, node, "array index")
            return collection.arguments[0]
        if collection == STRING:
            self._require_exact(INT, index, node, "string index")
            return STRING
        if collection.name == "map":
            self._require_assignable(collection.arguments[0], index, node)
            return collection.arguments[1]
        self._error(node, f"type {collection} is not indexable")

    def _iterable_item(self, type_: Type, node: ast.Node) -> Type:
        if type_.name in ("array", "set", "stack", "queue", "deque", "minheap", "maxheap"): return type_.arguments[0]
        if type_.name == "map": return type_.arguments[0]
        if type_ == STRING: return STRING
        self._error(node, f"type {type_} is not iterable")

    def _membership_item(self, type_: Type, node: ast.Node) -> Type:
        if type_.name in ("array", "set", "stack", "queue", "deque", "minheap", "maxheap"): return type_.arguments[0]
        if type_.name == "map": return type_.arguments[0]
        if type_ == STRING: return STRING
        self._error(node, f"operator 'in' does not support {type_}")

    def _expr(self, node: ast.Expression) -> Type:
        result = node.accept(self)
        if isinstance(result, FunctionType): self._error(node, "function value cannot be used here")
        return result

    @staticmethod
    def _numeric(type_: Type) -> bool: return type_ in (INT, FLOAT)

    def _heap_comparable(self, type_: Type) -> bool:
        if type_ in (INT, FLOAT, STRING): return True
        return type_.name == "array" and self._heap_comparable(type_.arguments[0])

    def _contains_unknown(self, type_: Type) -> bool:
        return type_ == UNKNOWN or any(self._contains_unknown(argument) for argument in type_.arguments)

    def _merge(self, left: Type, right: Type, node: ast.Node) -> Type:
        if left == UNKNOWN: return right
        if right == UNKNOWN: return left
        if self._numeric(left) and self._numeric(right): return FLOAT if FLOAT in (left, right) else INT
        if left == right: return left
        self._error(node, f"array elements must have one type, found {left} and {right}")

    def _require_assignable(self, expected: Type, actual: Type, node: ast.Node) -> None:
        if expected == UNKNOWN or actual == UNKNOWN: return
        if expected == FLOAT and actual == INT: return
        if expected.name == actual.name and len(expected.arguments) == len(actual.arguments):
            if all(self._assignable(e, a) for e, a in zip(expected.arguments, actual.arguments)): return
        if expected == actual: return
        self._error(node, f"expected {expected}, got {actual}")

    def _assignable(self, expected: Type, actual: Type) -> bool:
        if UNKNOWN in (expected, actual) or expected == actual or (expected == FLOAT and actual == INT): return True
        return expected.name == actual.name and len(expected.arguments) == len(actual.arguments) and all(
            self._assignable(e, a) for e, a in zip(expected.arguments, actual.arguments)
        )

    def _require_exact(self, expected: Type, actual: Type, node: ast.Node, context: str) -> None:
        if actual != expected: self._error(node, f"{context} must be {expected}, got {actual}")

    def _begin_scope(self) -> None: self.scope = SymbolTable(self.scope)
    def _end_scope(self) -> None:
        assert self.scope.enclosing is not None
        self.scope = self.scope.enclosing

    def _definitely_returns(self, statement: ast.Statement) -> bool:
        if isinstance(statement, ast.ReturnStatement): return True
        if isinstance(statement, ast.BlockStatement): return any(self._definitely_returns(s) for s in statement.statements)
        if isinstance(statement, ast.IfStatement):
            return statement.else_branch is not None and self._definitely_returns(statement.then_branch) and self._definitely_returns(statement.else_branch)
        return False

    def _error(self, node: ast.Node, message: str):
        raise TypeCheckError(message, node.span, self.source)
