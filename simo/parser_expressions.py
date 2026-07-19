"""Expression parsing for Simo."""

from typing import Any

from simo import ast_nodes as ast
from simo.errors import ParseError
from simo.tokens import Token, TokenType


class ParserExpressionMixin:
    def _block_until(self, *stop_types: TokenType) -> list[ast.Stmt]:
        statements: list[ast.Stmt] = []
        self._skip_newlines()
        while not self._at_end() and not self._check(*stop_types):
            statements.append(self._declaration())
            self._skip_newlines()
        return statements

    # expressions -------------------------------------------------------
    def _expression(self) -> ast.Expr:
        return self._or()

    def _or(self) -> ast.Expr:
        expr = self._and()
        while self._match(TokenType.OR):
            operator = self._previous()
            expr = ast.Binary(
                operator="or",
                left=expr,
                right=self._and(),
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _and(self) -> ast.Expr:
        expr = self._equality()
        while self._match(TokenType.AND):
            operator = self._previous()
            expr = ast.Binary(
                operator="and",
                left=expr,
                right=self._equality(),
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _equality(self) -> ast.Expr:
        expr = self._comparison()
        while self._check(TokenType.EQ, TokenType.NEQ, TokenType.IS):
            operator = self._advance()
            op = operator.lexeme
            if operator.type == TokenType.IS:
                op = "!=" if self._match(TokenType.NOT) else "=="
            expr = ast.Binary(
                operator=op,
                left=expr,
                right=self._comparison(),
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _comparison(self) -> ast.Expr:
        expr = self._term()
        while self._match(TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE):
            operator = self._previous()
            expr = ast.Binary(
                operator=operator.lexeme,
                left=expr,
                right=self._term(),
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _term(self) -> ast.Expr:
        expr = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            expr = ast.Binary(
                operator=operator.lexeme,
                left=expr,
                right=self._factor(),
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _factor(self) -> ast.Expr:
        expr = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self._previous()
            expr = ast.Binary(
                operator=operator.lexeme,
                left=expr,
                right=self._unary(),
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _unary(self) -> ast.Expr:
        if self._match(TokenType.NOT, TokenType.MINUS, TokenType.PLUS):
            operator = self._previous()
            return ast.Unary(
                operator=operator.lexeme.lower(),
                operand=self._unary(),
                line=operator.line,
                column=operator.column,
            )
        return self._postfix()

    def _postfix(self) -> ast.Expr:
        expr = self._primary()
        while True:
            if self._match(TokenType.LPAREN):
                arguments: list[ast.Expr] = []
                if not self._check(TokenType.RPAREN):
                    while True:
                        arguments.append(self._expression())
                        if not self._match(TokenType.COMMA):
                            break
                closing = self._consume(TokenType.RPAREN, "Expected ')' after arguments")
                expr = ast.Call(
                    callee=expr,
                    arguments=arguments,
                    line=closing.line,
                    column=closing.column,
                )
                continue
            if self._match(TokenType.DOT):
                name = self._consume(TokenType.IDENTIFIER, "Expected property name after '.'")
                expr = ast.Get(
                    object=expr,
                    name=name.lexeme,
                    line=name.line,
                    column=name.column,
                )
                continue
            if self._match(TokenType.LBRACKET):
                index = self._expression()
                closing = self._consume(TokenType.RBRACKET, "Expected ']' after index")
                expr = ast.Index(
                    object=expr,
                    index=index,
                    line=closing.line,
                    column=closing.column,
                )
                continue
            break
        return expr

    def _primary(self) -> ast.Expr:
        if self._match(TokenType.FALSE, TokenType.NO):
            token = self._previous()
            return ast.Literal(value=False, line=token.line, column=token.column)
        if self._match(TokenType.TRUE, TokenType.YES):
            token = self._previous()
            return ast.Literal(value=True, line=token.line, column=token.column)
        if self._match(TokenType.NULL):
            token = self._previous()
            return ast.Literal(value=None, line=token.line, column=token.column)
        if self._match(TokenType.NUMBER, TokenType.STRING, TokenType.DIMENSION):
            token = self._previous()
            return ast.Literal(value=token.literal, line=token.line, column=token.column)
        if self._match(TokenType.IDENTIFIER):
            token = self._previous()
            return ast.Variable(name=token.lexeme, line=token.line, column=token.column)
        if self._match(TokenType.LPAREN):
            expression = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expression
        if self._match(TokenType.LBRACKET):
            opening = self._previous()
            items: list[ast.Expr] = []
            if not self._check(TokenType.RBRACKET):
                while True:
                    items.append(self._expression())
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RBRACKET, "Expected ']' after list")
            return ast.ListLiteral(items=items, line=opening.line, column=opening.column)
        if self._match(TokenType.LBRACE):
            opening = self._previous()
            items: list[tuple[str, ast.Expr]] = []
            if not self._check(TokenType.RBRACE):
                while True:
                    key = self._advance()
                    if key.type not in {TokenType.IDENTIFIER, TokenType.STRING}:
                        self._error("Expected object key", key)
                    key_name = str(key.literal if key.type == TokenType.STRING else key.lexeme)
                    self._consume(TokenType.COLON, "Expected ':' after object key")
                    items.append((key_name, self._expression()))
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RBRACE, "Expected '}' after object")
            return ast.ObjectLiteral(items=items, line=opening.line, column=opening.column)

        token = self._peek()
        self._error(f"Unexpected token {token.lexeme!r}", token)
