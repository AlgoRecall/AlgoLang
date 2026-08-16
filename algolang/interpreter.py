"""Tree-walking execution engine for validated AlgoLang programs."""

from __future__ import annotations

from collections.abc import Callable

from . import ast_nodes as ast
from .errors import RuntimeError
from .runtime import (
    AlgoDeque, AlgoFunction, AlgoHeap, AlgoQueue, AlgoStack, Environment,
    NativeFunction, RuntimeValue, display, type_name,
)
from .tracing import (
    ArrayUpdated, ConditionEvaluated, DequeUpdated, EventSink,
    ExpressionEvaluated, FunctionCalled, FunctionReturned, HeapPopped,
    HeapPushed, LoopExitReason, LoopFinished, LoopIteration, LoopKind,
    LoopStarted, MapUpdated, MutationOperation, NullEventSink, QueueDequeued,
    QueueEnqueued, SetUpdated, StackPopped, StackPushed, VariableChanged,
    VariableDeclared, snapshot,
)


class _Break(Exception):
    """Unwind execution to the nearest loop for a break statement."""
    pass


class _Continue(Exception):
    """Unwind the current iteration for a continue statement."""
    pass


class _Return(Exception):
    """Carry a return value while unwinding a function body."""

    def __init__(self, value: RuntimeValue):
        """Initialize function unwinding with the returned value.

        Args:
            value (RuntimeValue): Runtime, source, or static value to process.

        Returns:
            None: No value is returned.
        """
        self.value = value


class Interpreter:
    """Execute a validated AlgoLang abstract syntax tree."""

    def __init__(
            self,
            source: str,
            output: Callable[[str], None] = print,
            environment: Environment | None = None,
            event_sink: EventSink | None = None,
    ):
        """Initialize the interpreter.

        Args:
            source (str): AlgoLang source text.
            output (Callable[[str], None]): Program output lines to include in the report.
            environment (Environment | None): Lexical runtime environment used for execution.
            event_sink (EventSink | None): Optional consumer for structured execution events.

        Returns:
            None: No value is returned.
        """
        self.source, self.output = source, output
        self.globals = environment or Environment()
        self.environment = self.globals
        self.event_sink = event_sink or NullEventSink()
        self._next_scope_id = max(1, self.globals.scope_id + 1)
        self._next_loop_id = 1
        self._next_call_id = 1
        self._next_collection_id = 1
        self._call_stack: list[int] = []
        self._collection_ids: dict[int, int] = {}
        self._collection_objects: dict[int, RuntimeValue] = {}

    def execute(self, program: ast.Program) -> Environment:
        """Execute a program and return the resulting global environment.

        Args:
            program (ast.Program): Program node to validate or execute.

        Returns:
            Environment: The resulting runtime environment.
        """
        for statement in program.statements:
            if isinstance(statement, ast.FunctionDeclaration):
                self.globals.define(statement.name, AlgoFunction(statement, self.globals))
        program.accept(self)
        return self.globals

    def visit_program(self, node: ast.Program) -> None:
        """Execute the program node.

        Args:
            node (ast.Program): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        for statement in node.statements:
            if not isinstance(statement, ast.FunctionDeclaration): statement.accept(self)

    def visit_block_statement(self, node: ast.BlockStatement) -> None:
        """Execute the block statement node.

        Args:
            node (ast.BlockStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        self._execute_block(node, self._new_environment(self.environment))

    def _execute_block(self, node: ast.BlockStatement, environment: Environment) -> None:
        """Execute statements in a supplied lexical environment.

        Args:
            node (ast.BlockStatement): Abstract syntax tree node to process.
            environment (Environment): Lexical runtime environment used for execution.

        Returns:
            None: No value is returned.
        """
        previous, self.environment = self.environment, environment
        try:
            for statement in node.statements: statement.accept(self)
        finally:
            self.environment = previous

    def visit_function_declaration(self, node: ast.FunctionDeclaration) -> None:
        """Execute the function declaration node.

        Args:
            node (ast.FunctionDeclaration): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        pass

    def visit_assignment_statement(self, node: ast.AssignmentStatement) -> None:
        """Execute the assignment statement node.

        Args:
            node (ast.AssignmentStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        value = self._value(node.value)
        if isinstance(node.target, ast.Identifier):
            name = node.target.name
            owner = None if node.annotation else self.environment.owner(name)
            if owner is None:
                self.environment.define(name, value)
                self.event_sink.emit(VariableDeclared(
                    node.span, self.environment.scope_id, self._call_id, name,
                    snapshot(value), self._collection_reference(value),
                ))
            else:
                old_value = owner.get(name)
                owner.assign(name, value)
                self.event_sink.emit(VariableChanged(
                    node.span, owner.scope_id, self._call_id, name,
                    snapshot(old_value), snapshot(value), self._collection_reference(value),
                ))
        elif isinstance(node.target, ast.IndexExpression):
            collection = self._value(node.target.collection)
            index = self._value(node.target.index)
            try:
                if isinstance(collection, list):
                    old_value = collection[index]
                    collection[index] = value
                    self.event_sink.emit(ArrayUpdated(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(collection), MutationOperation.SET,
                        index, snapshot(old_value), snapshot(value), snapshot(collection),
                    ))
                elif isinstance(collection, dict):
                    existed = index in collection
                    old_value = snapshot(collection[index]) if existed else None
                    collection[index] = value
                    self.event_sink.emit(MapUpdated(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(collection), snapshot(index), existed,
                        old_value, snapshot(value), snapshot(collection),
                    ))
                else:
                    collection[index] = value
            except (IndexError, KeyError, TypeError) as error:
                self._error(node.target, f"indexed assignment failed: {error}")

    def visit_expression_statement(self, node: ast.ExpressionStatement) -> None:
        """Execute the expression statement node.

        Args:
            node (ast.ExpressionStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        self._value(node.expression)

    def visit_print_statement(self, node: ast.PrintStatement) -> None:
        """Execute the print statement node.

        Args:
            node (ast.PrintStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        self.output(display(self._value(node.expression)))

    def visit_if_statement(self, node: ast.IfStatement) -> None:
        """Execute the if statement node.

        Args:
            node (ast.IfStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        if self._bool(node.condition, "if"):
            node.then_branch.accept(self)
        elif node.else_branch:
            node.else_branch.accept(self)

    def visit_while_statement(self, node: ast.WhileStatement) -> None:
        """Execute the while statement node.

        Args:
            node (ast.WhileStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        loop_id = self._allocate_loop_id()
        iterations = 0
        reason = LoopExitReason.COMPLETED
        self.event_sink.emit(LoopStarted(node.span, self.environment.scope_id, self._call_id, loop_id, LoopKind.WHILE))
        try:
            while self._bool(node.condition, "while"):
                iterations += 1
                self.event_sink.emit(LoopIteration(
                    node.span, self.environment.scope_id, self._call_id,
                    loop_id, LoopKind.WHILE, iterations,
                ))
                try:
                    node.body.accept(self)
                except _Continue:
                    continue
                except _Break:
                    reason = LoopExitReason.BREAK
                    break
        except _Return:
            reason = LoopExitReason.RETURN
            raise
        except Exception:
            reason = LoopExitReason.ERROR
            raise
        finally:
            self.event_sink.emit(LoopFinished(
                node.span, self.environment.scope_id, self._call_id,
                loop_id, LoopKind.WHILE, iterations, reason,
            ))

    def visit_for_statement(self, node: ast.ForStatement) -> None:
        """Execute the for statement node.

        Args:
            node (ast.ForStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        values = self._iterable(self._value(node.iterable), node.iterable)
        loop_environment = self._new_environment(self.environment)
        loop_id = self._allocate_loop_id()
        iterations = 0
        reason = LoopExitReason.COMPLETED
        self.event_sink.emit(LoopStarted(node.span, self.environment.scope_id, self._call_id, loop_id, LoopKind.FOR))
        try:
            for index, value in enumerate(values):
                iterations += 1
                self.event_sink.emit(LoopIteration(
                    node.span, loop_environment.scope_id, self._call_id,
                    loop_id, LoopKind.FOR, iterations,
                ))
                bindings = ((node.names[0], value),) if len(node.names) == 1 else (
                    (node.names[0], index), (node.names[1], value)
                )
                for name, bound_value in bindings:
                    if name in loop_environment.values:
                        old_value = loop_environment.get(name)
                        loop_environment.assign(name, bound_value)
                        self.event_sink.emit(VariableChanged(
                            node.span, loop_environment.scope_id, self._call_id,
                            name, snapshot(old_value), snapshot(bound_value),
                            self._collection_reference(bound_value),
                        ))
                    else:
                        loop_environment.define(name, bound_value)
                        self.event_sink.emit(VariableDeclared(
                            node.span, loop_environment.scope_id, self._call_id,
                            name, snapshot(bound_value), self._collection_reference(bound_value),
                        ))
                try:
                    self._execute_block(node.body, self._new_environment(loop_environment))
                except _Continue:
                    continue
                except _Break:
                    reason = LoopExitReason.BREAK
                    break
        except _Return:
            reason = LoopExitReason.RETURN
            raise
        except Exception:
            reason = LoopExitReason.ERROR
            raise
        finally:
            self.event_sink.emit(LoopFinished(
                node.span, loop_environment.scope_id, self._call_id,
                loop_id, LoopKind.FOR, iterations, reason,
            ))

    def visit_break_statement(self, node: ast.BreakStatement) -> None:
        """Execute the break statement node.

        Args:
            node (ast.BreakStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.

        Raises:
            _Break: When the operation cannot complete successfully.
        """
        raise _Break()

    def visit_continue_statement(self, node: ast.ContinueStatement) -> None:
        """Execute the continue statement node.

        Args:
            node (ast.ContinueStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.

        Raises:
            _Continue: When the operation cannot complete successfully.
        """
        raise _Continue()

    def visit_return_statement(self, node: ast.ReturnStatement) -> None:
        """Execute the return statement node.

        Args:
            node (ast.ReturnStatement): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.

        Raises:
            _Return: When the operation cannot complete successfully.
        """
        raise _Return(None if node.value is None else self._value(node.value))

    def visit_integer_literal(self, node: ast.IntegerLiteral) -> int:
        """Execute the integer literal node.

        Args:
            node (ast.IntegerLiteral): Abstract syntax tree node to process.

        Returns:
            int: The resulting integer.
        """
        return node.value

    def visit_float_literal(self, node: ast.FloatLiteral) -> float:
        """Execute the float literal node.

        Args:
            node (ast.FloatLiteral): Abstract syntax tree node to process.

        Returns:
            float: The resulting floating-point value.
        """
        return node.value

    def visit_boolean_literal(self, node: ast.BooleanLiteral) -> bool:
        """Execute the boolean literal node.

        Args:
            node (ast.BooleanLiteral): Abstract syntax tree node to process.

        Returns:
            bool: Whether the requested condition is satisfied.
        """
        return node.value

    def visit_string_literal(self, node: ast.StringLiteral) -> str:
        """Execute the string literal node.

        Args:
            node (ast.StringLiteral): Abstract syntax tree node to process.

        Returns:
            str: The resulting text.
        """
        return node.value

    def visit_null_literal(self, node: ast.NullLiteral) -> None:
        """Execute the null literal node.

        Args:
            node (ast.NullLiteral): Abstract syntax tree node to process.

        Returns:
            None: No value is returned.
        """
        return None

    def visit_array_literal(self, node: ast.ArrayLiteral) -> list[RuntimeValue]:
        """Execute the array literal node.

        Args:
            node (ast.ArrayLiteral): Abstract syntax tree node to process.

        Returns:
            list[RuntimeValue]: The resulting collection.
        """
        return [self._value(e) for e in node.elements]

    def visit_identifier(self, node: ast.Identifier) -> RuntimeValue:
        """Execute the identifier node.

        Args:
            node (ast.Identifier): Abstract syntax tree node to process.

        Returns:
            RuntimeValue: The resulting value.
        """
        if node.name == "len": return NativeFunction("len", self._collection_len)
        if node.name == "range": return NativeFunction("range", lambda *args: list(range(*args)))
        try:
            return self.environment.get(node.name)
        except KeyError:
            self._error(node, f"undefined variable '{node.name}'")

    def visit_grouping_expression(self, node: ast.GroupingExpression) -> RuntimeValue:
        """Execute the grouping expression node.

        Args:
            node (ast.GroupingExpression): Abstract syntax tree node to process.

        Returns:
            RuntimeValue: The resulting value.
        """
        return self._value(node.expression)

    def visit_unary_expression(self, node: ast.UnaryExpression) -> RuntimeValue:
        """Execute the unary expression node.

        Args:
            node (ast.UnaryExpression): Abstract syntax tree node to process.

        Returns:
            RuntimeValue: The resulting value.
        """
        operand = self._value(node.operand)
        if node.operator == "not": return not operand
        if node.operator == "-": return -operand
        self._error(node, f"unknown unary operator '{node.operator}'")

    def visit_binary_expression(self, node: ast.BinaryExpression) -> RuntimeValue:
        """Execute the binary expression node.

        Args:
            node (ast.BinaryExpression): Abstract syntax tree node to process.

        Returns:
            RuntimeValue: The resulting value.
        """
        left = self._value(node.left)
        if node.operator == "and": return left and self._value(node.right)
        if node.operator == "or": return left or self._value(node.right)
        right = self._value(node.right)
        try:
            if node.operator == "+": return left + right
            if node.operator == "-": return left - right
            if node.operator == "*": return left * right
            if node.operator == "/": return self._integer_quotient(left, right) if isinstance(left, int) and isinstance(
                right, int) else left / right
            if node.operator == "%":
                return left - self._integer_quotient(left, right) * right if isinstance(left, int) and isinstance(right,
                                                                                                                  int) else left % right
            if node.operator == "==": return left == right
            if node.operator == "!=": return left != right
            if node.operator == "<": return left < right
            if node.operator == "<=": return left <= right
            if node.operator == ">": return left > right
            if node.operator == ">=": return left >= right
            if node.operator == "in": return left in self._membership_container(right)
        except (ZeroDivisionError, TypeError) as error:
            self._error(node, "division by zero" if isinstance(error, ZeroDivisionError) else str(error))
        self._error(node, f"unknown binary operator '{node.operator}'")

    def visit_call_expression(self, node: ast.CallExpression) -> RuntimeValue:
        """Execute the call expression node.

        Args:
            node (ast.CallExpression): Abstract syntax tree node to process.

        Returns:
            RuntimeValue: The resulting value.
        """
        callee = self._evaluate(node.callee)
        arguments = [self._value(argument) for argument in node.arguments]
        if isinstance(callee, NativeFunction):
            try:
                return callee.function(*arguments)
            except (IndexError, KeyError, TypeError, ValueError) as error:
                self._error(node, f"{callee.name} failed: {error}")
        if isinstance(callee, AlgoFunction): return self._call_function(callee, arguments, node)
        self._error(node.callee, f"{type_name(callee)} value is not callable")

    def _call_function(self, function: AlgoFunction, arguments: list[RuntimeValue], node: ast.Node) -> RuntimeValue:
        """Invoke a user-defined function with evaluated arguments.

        Args:
            function (AlgoFunction): User-defined function value to invoke.
            arguments (list[RuntimeValue]): Arguments supplied to the operation.
            node (ast.Node): Abstract syntax tree node to process.

        Returns:
            RuntimeValue: The resulting value.
        """
        declaration = function.declaration
        if len(arguments) != len(declaration.parameters): self._error(node,
                                                                      f"expected {len(declaration.parameters)} arguments, got {len(arguments)}")
        environment = self._new_environment(function.closure)
        call_id = self._next_call_id
        self._next_call_id += 1
        parent_call_id = self._call_id
        self.event_sink.emit(FunctionCalled(
            node.span, self.environment.scope_id, call_id, declaration.name,
            tuple(snapshot(argument) for argument in arguments), parent_call_id,
        ))
        self._call_stack.append(call_id)
        for parameter, argument in zip(declaration.parameters, arguments):
            environment.define(parameter.name, argument)
            self.event_sink.emit(VariableDeclared(
                parameter.span, environment.scope_id, call_id,
                parameter.name, snapshot(argument), self._collection_reference(argument),
            ))
        result = None
        try:
            try:
                self._execute_block(declaration.body, self._new_environment(environment))
            except _Return as returned:
                result = returned.value
            self.event_sink.emit(FunctionReturned(
                node.span, environment.scope_id, call_id,
                declaration.name, snapshot(result),
            ))
            return result
        finally:
            self._call_stack.pop()

    def visit_index_expression(self, node: ast.IndexExpression) -> RuntimeValue:
        """Execute the index expression node.

        Args:
            node (ast.IndexExpression): Abstract syntax tree node to process.

        Returns:
            RuntimeValue: The resulting value.
        """
        collection, index = self._value(node.collection), self._value(node.index)
        try:
            return collection[index]
        except (IndexError, KeyError, TypeError) as error:
            self._error(node, f"index operation failed: {error}")

    def visit_member_expression(self, node: ast.MemberExpression) -> NativeFunction:
        """Execute the member expression node.

        Args:
            node (ast.MemberExpression): Abstract syntax tree node to process.

        Returns:
            NativeFunction: A bound native function implementing the collection method.
        """
        value = self._value(node.object)
        method = self._method(value, node.name, node)
        return NativeFunction(f"{type_name(value)}.{node.name}", method)

    def visit_collection_constructor(self, node: ast.CollectionConstructor) -> RuntimeValue:
        """Execute the collection constructor node.

        Args:
            node (ast.CollectionConstructor): Abstract syntax tree node to process.

        Returns:
            RuntimeValue: The resulting value.
        """
        return {
            "map": dict, "set": set, "stack": AlgoStack, "queue": AlgoQueue,
            "deque": AlgoDeque, "minheap": lambda: AlgoHeap(False),
            "maxheap": lambda: AlgoHeap(True),
        }[node.type_node.name]()

    def _method(self, value: RuntimeValue, name: str, node: ast.Node) -> Callable[..., RuntimeValue]:
        """Resolve a bound collection method and attach mutation tracing.

        Args:
            value (RuntimeValue): Runtime, source, or static value to process.
            name (str): Identifier or display name used by the operation.
            node (ast.Node): Abstract syntax tree node to process.

        Returns:
            Callable[..., RuntimeValue]: The resulting value.
        """

        def empty_checked(action: Callable[[], RuntimeValue]) -> Callable[[], RuntimeValue]:
            """Wrap an operation with an empty-collection runtime check.

            Args:
                action (Callable[[], RuntimeValue]): Callback that performs the concrete collection operation.

            Returns:
                Callable[[], RuntimeValue]: The resulting value.
            """

            def call():
                """Invoke the guarded operation after validating collection state.

                Returns:
                    object: The resulting value.
                """
                try:
                    return action()
                except (IndexError, KeyError):
                    self._error(node, f"cannot call '{name}' on an empty {type_name(value)}")

            return call

        if name == "len": return lambda: self._collection_len(value)
        if isinstance(value, list):
            if name == "push":
                def array_push(item):
                    """Append an item and emit the resulting array state.

                    Args:
                        item (object): Collection element to add, remove, or compare.

                    Returns:
                        None: No value is returned.
                    """
                    value.append(item)
                    self.event_sink.emit(ArrayUpdated(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), MutationOperation.PUSH,
                        len(value) - 1, None, snapshot(item), snapshot(value),
                    ))

                return array_push
            if name == "pop":
                def array_pop():
                    """Pop the final array item and emit the resulting state.

                    Returns:
                        object: The resulting value.
                    """
                    if not value: self._error(node, "cannot call 'pop' on an empty array")
                    index = len(value) - 1
                    item = value.pop()
                    self.event_sink.emit(ArrayUpdated(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), MutationOperation.POP,
                        index, snapshot(item), None, snapshot(value),
                    ))
                    return item

                return array_pop
        if isinstance(value, set):
            if name == "add":
                def set_add(item):
                    """Add an item and emit whether the set changed.

                    Args:
                        item (object): Collection element to add, remove, or compare.

                    Returns:
                        None: No value is returned.
                    """
                    changed = item not in value
                    value.add(item)
                    self.event_sink.emit(SetUpdated(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), MutationOperation.ADD,
                        snapshot(item), changed, snapshot(value),
                    ))

                return set_add
            if name == "remove":
                def set_remove(item):
                    """Remove an item and emit whether the set changed.

                    Args:
                        item (object): Collection element to add, remove, or compare.

                    Returns:
                        object: The resulting value.
                    """
                    changed = item in value
                    if changed: value.remove(item)
                    self.event_sink.emit(SetUpdated(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), MutationOperation.REMOVE,
                        snapshot(item), changed, snapshot(value),
                    ))
                    return changed

                return set_remove
        if isinstance(value, AlgoStack):
            if name == "push":
                def stack_push(item):
                    """Push an item and emit the resulting stack state.

                    Args:
                        item (object): Collection element to add, remove, or compare.

                    Returns:
                        None: No value is returned.
                    """
                    value.items.append(item)
                    self.event_sink.emit(StackPushed(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), snapshot(item), snapshot(value),
                    ))

                return stack_push
            if name == "pop":
                def stack_pop():
                    """Pop an item and emit the resulting stack state.

                    Returns:
                        object: The resulting value.
                    """
                    if not value.items: self._error(node, "cannot call 'pop' on an empty stack")
                    item = value.items.pop()
                    self.event_sink.emit(StackPopped(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), snapshot(item), snapshot(value),
                    ))
                    return item

                return stack_pop
            if name == "peek": return empty_checked(lambda: value.items[-1])
        if isinstance(value, AlgoQueue):
            if name == "enqueue":
                def enqueue(item):
                    """Enqueue an item and emit the resulting queue state.

                    Args:
                        item (object): Collection element to add, remove, or compare.

                    Returns:
                        None: No value is returned.
                    """
                    value.items.append(item)
                    self.event_sink.emit(QueueEnqueued(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), snapshot(item), snapshot(value),
                    ))

                return enqueue
            if name == "dequeue":
                def dequeue():
                    """Dequeue an item and emit the resulting queue state.

                    Returns:
                        object: The resulting value.
                    """
                    if not value.items: self._error(node, "cannot call 'dequeue' on an empty queue")
                    item = value.items.popleft()
                    self.event_sink.emit(QueueDequeued(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), snapshot(item), snapshot(value),
                    ))
                    return item

                return dequeue
            if name == "front": return empty_checked(lambda: value.items[0])
        if isinstance(value, AlgoDeque):
            def deque_push(operation, action):
                """Create a traced deque insertion operation.

                Args:
                    operation (object): Mutation kind recorded for tracing.
                    action (object): Callback that performs the concrete collection operation.

                Returns:
                    object: The resulting value.
                """

                def call(item):
                    """Insert an item at one end and emit the resulting deque state.

                    Args:
                        item (object): Collection element to add, remove, or compare.

                    Returns:
                        None: No value is returned.
                    """
                    action(item)
                    self.event_sink.emit(DequeUpdated(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), operation, snapshot(item), snapshot(value),
                    ))

                return call

            def deque_pop(operation, action):
                """Create a checked and traced deque removal operation.

                Args:
                    operation (object): Mutation kind recorded for tracing.
                    action (object): Callback that performs the concrete collection operation.

                Returns:
                    object: The resulting value.
                """

                def call():
                    """Remove an item from one end and emit the resulting deque state.

                    Returns:
                        object: The resulting value.
                    """
                    if not value.items: self._error(node, f"cannot call '{name}' on an empty deque")
                    item = action()
                    self.event_sink.emit(DequeUpdated(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), operation, snapshot(item), snapshot(value),
                    ))
                    return item

                return call

            methods = {
                "push_front": deque_push(MutationOperation.PUSH_FRONT, value.items.appendleft),
                "push_back": deque_push(MutationOperation.PUSH_BACK, value.items.append),
                "pop_front": deque_pop(MutationOperation.POP_FRONT, value.items.popleft),
                "pop_back": deque_pop(MutationOperation.POP_BACK, value.items.pop),
                "front": empty_checked(lambda: value.items[0]), "back": empty_checked(lambda: value.items[-1]),
            }
            if name in methods: return methods[name]
        if isinstance(value, AlgoHeap):
            if name == "push":
                def heap_push(item):
                    """Push an item and emit the resulting heap state.

                    Args:
                        item (object): Collection element to add, remove, or compare.

                    Returns:
                        None: No value is returned.
                    """
                    value.push(item)
                    self.event_sink.emit(HeapPushed(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), type_name(value),
                        snapshot(item), snapshot(value),
                    ))

                return heap_push
            if name == "pop":
                def heap_pop():
                    """Pop an item and emit the resulting heap state.

                    Returns:
                        object: The resulting value.
                    """
                    if not value.items: self._error(node, "cannot call 'pop' on an empty heap")
                    item = value.pop()
                    self.event_sink.emit(HeapPopped(
                        node.span, self.environment.scope_id, self._call_id,
                        self._collection_id(value), type_name(value),
                        snapshot(item), snapshot(value),
                    ))
                    return item

                return heap_pop
            if name == "peek": return empty_checked(value.peek)
        self._error(node, f"{type_name(value)} has no method '{name}'")

    def _collection_len(self, value: RuntimeValue) -> int:
        """Return the number of values stored in a supported collection.

        Args:
            value (RuntimeValue): Runtime, source, or static value to process.

        Returns:
            int: The resulting integer.
        """
        if isinstance(value, (AlgoStack, AlgoQueue, AlgoDeque)): return len(value.items)
        if isinstance(value, AlgoHeap): return len(value.items)
        return len(value)

    def _iterable(self, value: RuntimeValue, node: ast.Node) -> list[RuntimeValue]:
        """Return a stable iterable view of a runtime collection.

        Args:
            value (RuntimeValue): Runtime, source, or static value to process.
            node (ast.Node): Abstract syntax tree node to process.

        Returns:
            list[RuntimeValue]: The resulting collection.
        """
        if isinstance(value, AlgoHeap): return value.values()
        if isinstance(value, (AlgoStack, AlgoQueue, AlgoDeque)): return list(value.items)
        try:
            return list(value)
        except TypeError:
            self._error(node, f"{type_name(value)} is not iterable")

    @staticmethod
    def _membership_container(value: RuntimeValue):
        """Return the concrete container used for a membership test.

        Args:
            value (RuntimeValue): Runtime, source, or static value to process.

        Returns:
            object: The resulting value.
        """
        if isinstance(value, AlgoHeap): return value.values()
        if isinstance(value, (AlgoStack, AlgoQueue, AlgoDeque)): return value.items
        return value

    @staticmethod
    def _integer_quotient(left: int, right: int) -> int:
        """Apply truncating integer division and preserve division errors.

        Args:
            left (int): Left operand or type participating in the operation.
            right (int): Right operand or type participating in the operation.

        Returns:
            int: The resulting integer.
        """
        quotient = abs(left) // abs(right)
        return -quotient if (left < 0) != (right < 0) else quotient

    def _bool(self, expression: ast.Expression, context: str) -> bool:
        """Require a boolean condition value and return it.

        Args:
            expression (ast.Expression): Expression node to evaluate or inspect.
            context (str): Execution context associated with the operation.

        Returns:
            bool: Whether the requested condition is satisfied.
        """
        value = self._value(expression)
        if not isinstance(value, bool): self._error(expression, f"condition must be bool, got {type_name(value)}")
        self.event_sink.emit(ConditionEvaluated(
            expression.span, self.environment.scope_id, self._call_id,
            context, value,
        ))
        return value

    def _evaluate(self, expression: ast.Expression) -> RuntimeValue:
        """Evaluate an expression and emit its resulting snapshot.

        Args:
            expression (ast.Expression): Expression node to evaluate or inspect.

        Returns:
            RuntimeValue: The resulting value.
        """
        value = expression.accept(self)
        self.event_sink.emit(ExpressionEvaluated(
            expression.span, self.environment.scope_id, self._call_id,
            expression.__class__.__name__, snapshot(value),
        ))
        return value

    def _value(self, expression: ast.Expression) -> RuntimeValue:
        """Evaluate an expression without emitting an extra expression event.

        Args:
            expression (ast.Expression): Expression node to evaluate or inspect.

        Returns:
            RuntimeValue: The resulting value.
        """
        return self._evaluate(expression)

    def _new_environment(self, enclosing: Environment) -> Environment:
        """Create a uniquely identified lexical runtime environment.

        Args:
            enclosing (Environment): Optional enclosing lexical scope.

        Returns:
            Environment: The resulting runtime environment.
        """
        environment = Environment(enclosing=enclosing, scope_id=self._next_scope_id)
        self._next_scope_id += 1
        return environment

    def _allocate_loop_id(self) -> int:
        """Allocate the next loop id.

        Returns:
            int: The resulting integer.
        """
        loop_id = self._next_loop_id
        self._next_loop_id += 1
        return loop_id

    def _collection_id(self, value: RuntimeValue) -> int:
        """Return a stable trace identifier for a mutable collection.

        Args:
            value (RuntimeValue): Runtime, source, or static value to process.

        Returns:
            int: The resulting integer.
        """
        identity = id(value)
        if identity not in self._collection_ids:
            self._collection_ids[identity] = self._next_collection_id
            self._collection_objects[identity] = value
            self._next_collection_id += 1
        return self._collection_ids[identity]

    def _collection_reference(self, value: RuntimeValue) -> int | None:
        """Return collection identity and snapshot metadata for tracing.

        Args:
            value (RuntimeValue): Runtime, source, or static value to process.

        Returns:
            int | None: Stable collection ID, or ``None`` for immutable values.
        """
        if isinstance(value, (list, dict, set, AlgoStack, AlgoQueue, AlgoDeque, AlgoHeap)):
            return self._collection_id(value)
        return None

    @property
    def _call_id(self) -> int | None:
        """Return the currently executing function call identifier.

        Returns:
            int | None: Active call ID, or ``None`` at global scope.
        """
        return self._call_stack[-1] if self._call_stack else None

    def _error(self, node: ast.Node, message: str):
        """Raise a source-aware runtime error for an AST node.

        Args:
            node (ast.Node): Abstract syntax tree node to process.
            message (str): Diagnostic message presented to the user.

        Returns:
            None: No value is returned.

        Raises:
            RuntimeError: When the operation cannot complete successfully.
        """
        raise RuntimeError(message, node.span, self.source)
