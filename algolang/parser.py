"""Recursive-descent parser for AlgoLang tokens."""

from __future__ import annotations

from collections.abc import Callable

from . import ast_nodes as ast
from .errors import ParseError
from .source import SourceSpan
from .tokens import Token, TokenKind as K

COLLECTION_NAMES = {"map", "set", "stack", "queue", "deque", "minheap", "maxheap"}


class Parser:
    """Build an abstract syntax tree from an AlgoLang token stream."""

    def __init__(self, tokens: list[Token], source: str):
        """Initialize the parser.

        Args:
            tokens (list[Token]): Complete token stream produced by the lexer.
            source (str): AlgoLang source text.

        Returns:
            None: No value is returned.
        """
        self.tokens, self.source, self.current = tokens, source, 0
        self._group_depth = 0

    def parse(self) -> ast.Program:
        """Parse the complete token stream into a program node.

        Returns:
            ast.Program: The parsed or processed abstract syntax tree node.
        """
        self._skip_separators()
        first = self._peek().span
        statements = self._statement_list(K.EOF)
        end = self._peek().span
        return ast.Program(SourceSpan.covering(first, end), tuple(statements))

    def _statement_list(self, terminator: K) -> list[ast.Statement]:
        """Parse statements until the requested terminator or end of input.

        Args:
            terminator (K): Token kind that ends the current statement list.

        Returns:
            list[ast.Statement]: The resulting collection.
        """
        statements: list[ast.Statement] = []
        while not self._check(terminator) and not self._check(K.EOF):
            statements.append(self._statement())
            if self._check(terminator) or self._check(K.EOF):
                break
            if not self._is_separator(self._peek().kind):
                self._raise(self._peek(), "expected newline or ';' after statement")
            self._skip_separators()
        return statements

    def _statement(self) -> ast.Statement:
        """Parse one declaration, control-flow statement, or expression statement.

        Returns:
            ast.Statement: The parsed or processed abstract syntax tree node.
        """
        if self._match(K.FN): return self._function(self._previous())
        if self._match(K.IF): return self._if_statement(self._previous())
        if self._match(K.WHILE): return self._while_statement(self._previous())
        if self._match(K.FOR): return self._for_statement(self._previous())
        if self._match(K.BREAK): return ast.BreakStatement(self._previous().span)
        if self._match(K.CONTINUE): return ast.ContinueStatement(self._previous().span)
        if self._match(K.RETURN): return self._return_statement(self._previous())
        if self._match(K.PRINT): return self._print_statement(self._previous())
        if self._check(K.IDENTIFIER) and self._check_next(K.COLON):
            return self._typed_assignment()
        expression = self._expression()
        if self._match(K.EQUAL):
            if not isinstance(expression, (ast.Identifier, ast.IndexExpression)):
                self._raise(self._previous(), "assignment target must be a variable or index")
            value = self._expression()
            return ast.AssignmentStatement(SourceSpan.covering(expression.span, value.span), expression, value)
        return ast.ExpressionStatement(expression.span, expression)

    def _function(self, keyword: Token) -> ast.FunctionDeclaration:
        """Parse a typed function declaration after the ``fn`` keyword.

        Args:
            keyword (Token): Previously consumed keyword token that begins the statement.

        Returns:
            ast.FunctionDeclaration: The parsed or processed abstract syntax tree node.
        """
        name = self._consume(K.IDENTIFIER, "expected function name")
        self._consume(K.LEFT_PAREN, "expected '(' after function name")
        self._skip_newlines()
        parameters: list[ast.Parameter] = []
        if not self._check(K.RIGHT_PAREN):
            while True:
                param = self._consume(K.IDENTIFIER, "expected parameter name")
                self._consume(K.COLON, "expected ':' after parameter name")
                type_node = self._type_node()
                parameters.append(
                    ast.Parameter(SourceSpan.covering(param.span, type_node.span), param.lexeme, type_node))
                self._skip_newlines()
                if not self._match(K.COMMA): break
                self._skip_newlines()
        self._consume(K.RIGHT_PAREN, "expected ')' after parameters")
        self._consume(K.ARROW, "expected '->' and a return type after parameters")
        return_type = self._type_node()
        body = self._block("expected '{' before function body")
        return ast.FunctionDeclaration(SourceSpan.covering(keyword.span, body.span), name.lexeme, tuple(parameters),
                                       return_type, body)

    def _if_statement(self, keyword: Token) -> ast.IfStatement:
        """Parse an if statement and its optional else branch.

        Args:
            keyword (Token): Previously consumed keyword token that begins the statement.

        Returns:
            ast.IfStatement: The parsed or processed abstract syntax tree node.
        """
        condition = self._expression()
        then_branch = self._block("expected '{' after if condition")
        before_separators = self.current
        self._skip_separators()
        else_branch: ast.BlockStatement | ast.IfStatement | None = None
        if self._match(K.ELSE):
            if self._match(K.IF):
                else_branch = self._if_statement(self._previous())
            else:
                else_branch = self._block("expected '{' or 'if' after 'else'")
        else:
            self.current = before_separators
        last = else_branch.span if else_branch else then_branch.span
        return ast.IfStatement(SourceSpan.covering(keyword.span, last), condition, then_branch, else_branch)

    def _while_statement(self, keyword: Token) -> ast.WhileStatement:
        """Parse a condition-controlled while loop.

        Args:
            keyword (Token): Previously consumed keyword token that begins the statement.

        Returns:
            ast.WhileStatement: The parsed or processed abstract syntax tree node.
        """
        condition = self._expression()
        body = self._block("expected '{' after while condition")
        return ast.WhileStatement(SourceSpan.covering(keyword.span, body.span), condition, body)

    def _for_statement(self, keyword: Token) -> ast.ForStatement:
        """Parse a value-only or indexed collection loop.

        Args:
            keyword (Token): Previously consumed keyword token that begins the statement.

        Returns:
            ast.ForStatement: The parsed or processed abstract syntax tree node.
        """
        first = self._consume(K.IDENTIFIER, "expected loop variable after 'for'")
        names = [first.lexeme]
        if self._match(K.COMMA):
            second = self._consume(K.IDENTIFIER, "expected value variable after ','")
            names.append(second.lexeme)
        self._consume(K.IN, "expected 'in' after loop variable")
        iterable = self._expression()
        body = self._block("expected '{' after for iterable")
        return ast.ForStatement(SourceSpan.covering(keyword.span, body.span), tuple(names), iterable, body)

    def _return_statement(self, keyword: Token) -> ast.ReturnStatement:
        """Parse a return statement with an optional value.

        Args:
            keyword (Token): Previously consumed keyword token that begins the statement.

        Returns:
            ast.ReturnStatement: The parsed or processed abstract syntax tree node.
        """
        if self._check(K.NEWLINE) or self._check(K.SEMICOLON) or self._check(K.RIGHT_BRACE) or self._check(K.EOF):
            return ast.ReturnStatement(keyword.span, None)
        value = self._expression()
        return ast.ReturnStatement(SourceSpan.covering(keyword.span, value.span), value)

    def _print_statement(self, keyword: Token) -> ast.PrintStatement:
        """Parse the built-in print statement.

        Args:
            keyword (Token): Previously consumed keyword token that begins the statement.

        Returns:
            ast.PrintStatement: The parsed or processed abstract syntax tree node.
        """
        self._consume(K.LEFT_PAREN, "expected '(' after 'print'")
        self._skip_newlines()
        expression = self._expression()
        self._skip_newlines()
        close = self._consume(K.RIGHT_PAREN, "expected ')' after printed expression")
        return ast.PrintStatement(SourceSpan.covering(keyword.span, close.span), expression)

    def _typed_assignment(self) -> ast.AssignmentStatement:
        """Parse an explicitly typed variable assignment.

        Returns:
            ast.AssignmentStatement: The parsed or processed abstract syntax tree node.
        """
        name = self._advance()
        target = ast.Identifier(name.span, name.lexeme)
        self._advance()
        annotation = self._type_node()
        self._consume(K.EQUAL, "expected '=' after variable type")
        value = self._expression()
        return ast.AssignmentStatement(SourceSpan.covering(name.span, value.span), target, value, annotation)

    def _block(self, message: str) -> ast.BlockStatement:
        """Parse a brace-delimited statement block.

        Args:
            message (str): Diagnostic message presented to the user.

        Returns:
            ast.BlockStatement: The parsed or processed abstract syntax tree node.
        """
        opening = self._consume(K.LEFT_BRACE, message)
        self._skip_separators()
        statements = self._statement_list(K.RIGHT_BRACE)
        close = self._consume(K.RIGHT_BRACE, "expected '}' after block")
        return ast.BlockStatement(SourceSpan.covering(opening.span, close.span), tuple(statements))

    def _type_node(self) -> ast.TypeNode:
        """Parse a primitive, array, or generic collection type.

        Returns:
            ast.TypeNode: The parsed or processed abstract syntax tree node.
        """
        if self._match(K.LEFT_BRACKET):
            opening = self._previous()
            element = self._type_node()
            close = self._consume(K.RIGHT_BRACKET, "expected ']' after array element type")
            return ast.TypeNode(SourceSpan.covering(opening.span, close.span), "array", (element,))
        if self._match(K.IDENTIFIER, K.NULL):
            name = self._previous()
        else:
            self._raise(self._peek(), "expected type name")
        arguments: list[ast.TypeNode] = []
        end = name.span
        if self._match(K.LESS):
            while True:
                arguments.append(self._type_node())
                if not self._match(K.COMMA): break
            close = self._consume(K.GREATER, "expected '>' after generic type arguments")
            end = close.span
        return ast.TypeNode(SourceSpan.covering(name.span, end), name.lexeme, tuple(arguments))

    def _expression(self) -> ast.Expression:
        """Parse an expression from the lowest precedence level.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        return self._left(self._and, (K.OR,))

    def _and(self) -> ast.Expression:
        """Parse left-associative boolean conjunctions.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        return self._left(self._equality, (K.AND,))

    def _equality(self) -> ast.Expression:
        """Parse equality and inequality expressions.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        return self._left(self._comparison, (K.EQUAL_EQUAL, K.BANG_EQUAL))

    def _comparison(self) -> ast.Expression:
        """Parse ordering and membership comparisons.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        return self._left(self._term, (K.LESS, K.LESS_EQUAL, K.GREATER, K.GREATER_EQUAL, K.IN))

    def _term(self) -> ast.Expression:
        """Parse left-associative addition and subtraction.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        return self._left(self._factor, (K.PLUS, K.MINUS))

    def _factor(self) -> ast.Expression:
        """Parse multiplication, division, and remainder expressions.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        return self._left(self._unary, (K.STAR, K.SLASH, K.PERCENT))

    def _left(self, operand: Callable[[], ast.Expression], kinds: tuple[K, ...]) -> ast.Expression:
        """Fold repeated operators into a left-associative binary tree.

        Args:
            operand (Callable[[], ast.Expression]): Function that parses or evaluates the next operand.
            kinds (tuple[K, ...]): Candidate token kinds accepted at the current position.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        expression = operand()
        while True:
            self._skip_newlines_if_grouped()
            if not self._match(*kinds): break
            operator = self._previous()
            self._skip_newlines_if_grouped()
            right = operand()
            expression = ast.BinaryExpression(SourceSpan.covering(expression.span, right.span), expression,
                                              operator.lexeme, right)
        return expression

    def _unary(self) -> ast.Expression:
        """Parse prefix negation or continue into postfix parsing.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        if self._match(K.MINUS, K.NOT):
            operator = self._previous()
            operand = self._unary()
            return ast.UnaryExpression(SourceSpan.covering(operator.span, operand.span), operator.lexeme, operand)
        return self._postfix()

    def _postfix(self) -> ast.Expression:
        """Parse calls, indexing, and member access after a primary expression.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        expression = self._primary()
        while True:
            if self._match(K.LEFT_PAREN):
                arguments, close = self._arguments()
                expression = ast.CallExpression(SourceSpan.covering(expression.span, close.span), expression,
                                                tuple(arguments))
            elif self._match(K.LEFT_BRACKET):
                self._skip_newlines()
                index = self._expression()
                self._skip_newlines()
                close = self._consume(K.RIGHT_BRACKET, "expected ']' after index")
                expression = ast.IndexExpression(SourceSpan.covering(expression.span, close.span), expression, index)
            elif self._match(K.DOT):
                name = self._consume(K.IDENTIFIER, "expected member name after '.'")
                expression = ast.MemberExpression(SourceSpan.covering(expression.span, name.span), expression,
                                                  name.lexeme)
            else:
                break
        return expression

    def _arguments(self) -> tuple[list[ast.Expression], Token]:
        """Parse a comma-separated argument list and return its closing token.

        Returns:
            tuple[list[ast.Expression], Token]: The resulting collection.
        """
        self._group_depth += 1
        self._skip_newlines()
        arguments: list[ast.Expression] = []
        if not self._check(K.RIGHT_PAREN):
            while True:
                arguments.append(self._expression())
                self._skip_newlines()
                if not self._match(K.COMMA): break
                self._skip_newlines()
        close = self._consume(K.RIGHT_PAREN, "expected ')' after arguments")
        self._group_depth -= 1
        return arguments, close

    def _primary(self) -> ast.Expression:
        """Parse a literal, identifier, group, array, or collection constructor.

        Returns:
            ast.Expression: The parsed or processed abstract syntax tree node.
        """
        literal_kinds = {
            K.INTEGER: ast.IntegerLiteral, K.FLOAT: ast.FloatLiteral,
            K.STRING: ast.StringLiteral,
        }
        for kind, cls in literal_kinds.items():
            if self._match(kind):
                token = self._previous()
                return cls(token.span, token.literal)
        if self._match(K.TRUE, K.FALSE):
            token = self._previous()
            return ast.BooleanLiteral(token.span, token.kind is K.TRUE)
        if self._match(K.NULL):
            return ast.NullLiteral(self._previous().span)
        if self._match(K.IDENTIFIER):
            token = self._previous()
            if token.lexeme in COLLECTION_NAMES and self._check(K.LESS):
                type_node = self._constructor_type(token)
                self._consume(K.LEFT_PAREN, "expected '(' after collection type")
                close = self._consume(K.RIGHT_PAREN, "collection constructors take no arguments")
                return ast.CollectionConstructor(SourceSpan.covering(token.span, close.span), type_node)
            return ast.Identifier(token.span, token.lexeme)
        if self._match(K.LEFT_BRACKET):
            opening = self._previous()
            self._group_depth += 1
            self._skip_newlines()
            elements: list[ast.Expression] = []
            if not self._check(K.RIGHT_BRACKET):
                while True:
                    elements.append(self._expression())
                    self._skip_newlines()
                    if not self._match(K.COMMA): break
                    self._skip_newlines()
                    if self._check(K.RIGHT_BRACKET): break
            close = self._consume(K.RIGHT_BRACKET, "expected ']' after array literal")
            self._group_depth -= 1
            return ast.ArrayLiteral(SourceSpan.covering(opening.span, close.span), tuple(elements))
        if self._match(K.LEFT_PAREN):
            opening = self._previous()
            self._group_depth += 1
            self._skip_newlines()
            expression = self._expression()
            self._skip_newlines()
            close = self._consume(K.RIGHT_PAREN, "expected ')' after expression")
            self._group_depth -= 1
            return ast.GroupingExpression(SourceSpan.covering(opening.span, close.span), expression)
        self._raise(self._peek(), "expected expression")

    def _constructor_type(self, name: Token) -> ast.TypeNode:
        """Parse the generic type attached to a collection constructor.

        Args:
            name (Token): Identifier or display name used by the operation.

        Returns:
            ast.TypeNode: The parsed or processed abstract syntax tree node.
        """
        self._consume(K.LESS, "expected '<'")
        arguments = [self._type_node()]
        while self._match(K.COMMA):
            arguments.append(self._type_node())
        close = self._consume(K.GREATER, "expected '>' after collection type arguments")
        return ast.TypeNode(SourceSpan.covering(name.span, close.span), name.lexeme, tuple(arguments))

    def _skip_newlines_if_grouped(self) -> None:
        """Allow newlines while parsing a grouped expression.

        Returns:
            None: No value is returned.
        """
        if self._group_depth: self._skip_newlines()

    def _skip_newlines(self) -> None:
        """Consume consecutive newline tokens.

        Returns:
            None: No value is returned.
        """
        while self._match(K.NEWLINE): pass

    def _skip_separators(self) -> None:
        """Consume consecutive newline and semicolon separators.

        Returns:
            None: No value is returned.
        """
        while self._match(K.NEWLINE, K.SEMICOLON): pass

    @staticmethod
    def _is_separator(kind: K) -> bool:
        """Return whether a token kind separates statements.

        Args:
            kind (K): Token, loop, or operation kind to process.

        Returns:
            bool: Whether the requested condition is satisfied.
        """
        return kind in (K.NEWLINE, K.SEMICOLON)

    def _match(self, *kinds: K) -> bool:
        """Consume the current token when its kind matches any candidate.

        Args:
            *kinds (K): Candidate token kinds accepted at the current position.

        Returns:
            bool: Whether the requested condition is satisfied.
        """
        if any(self._check(kind) for kind in kinds):
            self._advance()
            return True
        return False

    def _consume(self, kind: K, message: str) -> Token:
        """Consume an expected token or raise a parse error.

        Args:
            kind (K): Token, loop, or operation kind to process.
            message (str): Diagnostic message presented to the user.

        Returns:
            Token: The consumed, inspected, or generated token value.
        """
        if self._check(kind): return self._advance()
        self._raise(self._peek(), message)

    def _check(self, kind: K) -> bool:
        """Return whether the current token has the requested kind.

        Args:
            kind (K): Token, loop, or operation kind to process.

        Returns:
            bool: Whether the requested condition is satisfied.
        """
        return self._peek().kind is kind

    def _check_next(self, kind: K) -> bool:
        """Return whether the next token has the requested kind.

        Args:
            kind (K): Token, loop, or operation kind to process.

        Returns:
            bool: Whether the requested condition is satisfied.
        """
        return self.current + 1 < len(self.tokens) and self.tokens[self.current + 1].kind is kind

    def _advance(self) -> Token:
        """Consume and return the current token.

        Returns:
            Token: The consumed, inspected, or generated token value.
        """
        if not self._check(K.EOF): self.current += 1
        return self._previous()

    def _peek(self) -> Token:
        """Return the current token without consuming it.

        Returns:
            Token: The consumed, inspected, or generated token value.
        """
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Return the most recently consumed token.

        Returns:
            Token: The consumed, inspected, or generated token value.
        """
        return self.tokens[self.current - 1]

    def _raise(self, token: Token, message: str):
        """Raise a source-aware parse error at the supplied token.

        Args:
            token (Token): Token whose source span anchors parsing or diagnostics.
            message (str): Diagnostic message presented to the user.

        Returns:
            None: No value is returned.

        Raises:
            ParseError: When the operation cannot complete successfully.
        """
        raise ParseError(message, token.span, self.source)
