"""Recursive-descent parser for Sola."""

from __future__ import annotations

from sola import ast_nodes as ast
from sola.errors import ParseError
from sola.tokens import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token], filename: str = "<stdin>") -> None:
        self._tokens = tokens
        self._filename = filename
        self._current = 0

    def parse(self) -> ast.Program:
        statements: list[ast.Stmt] = []
        while not self._is_at_end():
            statements.append(self._declaration())
        return ast.Program(statements=statements)

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self._tokens[self._current]

    def _previous(self) -> Token:
        return self._tokens[self._current - 1]

    def _advance(self) -> Token:
        if not self._is_at_end():
            self._current += 1
        return self._previous()

    def _check(self, *types: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type in types

    def _match(self, *types: TokenType) -> bool:
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        token = self._peek()
        raise ParseError(message, self._filename, token.line, token.column)

    def _error(self, message: str, token: Token | None = None) -> None:
        tok = token or self._peek()
        raise ParseError(message, self._filename, tok.line, tok.column)

    def _declaration(self) -> ast.Stmt:
        if self._match(TokenType.SET):
            return self._var_declaration(is_const=False)
        if self._match(TokenType.FIX):
            return self._var_declaration(is_const=True)
        if self._match(TokenType.ACTION):
            return self._action_declaration()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.LOOP):
            return self._loop_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._check(TokenType.IDENTIFIER):
            name_token = self._advance()
            if self._check(TokenType.ASSIGN):
                self._advance()
                value = self._expression()
                return ast.Assign(
                    name=name_token.lexeme,
                    value=value,
                    line=name_token.line,
                    column=name_token.column,
                )
            self._current -= 1
        return self._expression_statement()

    def _var_declaration(self, is_const: bool) -> ast.VarDecl:
        keyword = self._previous()
        name_token = self._consume(TokenType.IDENTIFIER, "Expected variable name after declaration keyword")
        self._consume(TokenType.ASSIGN, "Expected '=' after variable name")
        initializer = self._expression()
        return ast.VarDecl(
            name=name_token.lexeme,
            initializer=initializer,
            is_const=is_const,
            line=keyword.line,
            column=keyword.column,
        )

    def _action_declaration(self) -> ast.ActionDecl:
        keyword = self._previous()
        name_token = self._consume(TokenType.IDENTIFIER, "Expected function name after 'action'")
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        params: list[str] = []
        if not self._check(TokenType.RPAREN):
            while True:
                param = self._consume(TokenType.IDENTIFIER, "Expected parameter name")
                params.append(param.lexeme)
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RPAREN, "Expected ')' after parameters")

        body: list[ast.Stmt] = []
        while not self._check(TokenType.END) and not self._is_at_end():
            body.append(self._declaration())
        self._consume(TokenType.END, "Expected 'end' after function body")

        return ast.ActionDecl(
            name=name_token.lexeme,
            params=params,
            body=body,
            line=keyword.line,
            column=keyword.column,
        )

    def _return_statement(self) -> ast.ReturnStmt:
        keyword = self._previous()
        value: ast.Expr | None = None
        if not self._check(TokenType.END, TokenType.ELSE) and not self._is_at_end():
            value = self._expression()
        return ast.ReturnStmt(value=value, line=keyword.line, column=keyword.column)

    def _if_statement(self) -> ast.IfStmt:
        keyword = self._previous()
        condition = self._expression()
        body = self._block_until(TokenType.ELSE, TokenType.END)
        branches: list[tuple[ast.Expr, list[ast.Stmt]]] = [(condition, body)]
        else_body: list[ast.Stmt] = []

        while self._match(TokenType.ELSE):
            if self._match(TokenType.IF):
                condition = self._expression()
                body = self._block_until(TokenType.ELSE, TokenType.END)
                branches.append((condition, body))
            else:
                else_body = self._block_until(TokenType.END)
                self._consume(TokenType.END, "Expected 'end' after if statement")
                return ast.IfStmt(
                    branches=branches,
                    else_body=else_body,
                    line=keyword.line,
                    column=keyword.column,
                )

        self._consume(TokenType.END, "Expected 'end' after if statement")
        return ast.IfStmt(
            branches=branches,
            else_body=else_body,
            line=keyword.line,
            column=keyword.column,
        )

    def _loop_statement(self) -> ast.LoopStmt:
        keyword = self._previous()
        if self._match(TokenType.WHILE):
            condition = self._expression()
            body = self._block_until(TokenType.END)
            self._consume(TokenType.END, "Expected 'end' after loop body")
            return ast.LoopWhile(
                condition=condition,
                body=body,
                line=keyword.line,
                column=keyword.column,
            )

        count = self._expression()
        self._consume(TokenType.TIMES, "Expected 'times' after loop count")
        body = self._block_until(TokenType.END)
        self._consume(TokenType.END, "Expected 'end' after loop body")
        return ast.LoopTimes(
            count=count,
            body=body,
            line=keyword.line,
            column=keyword.column,
        )

    def _block_until(self, *stop_types: TokenType) -> list[ast.Stmt]:
        statements: list[ast.Stmt] = []
        while not self._is_at_end():
            if self._check(*stop_types):
                break
            statements.append(self._declaration())
        return statements

    def _is_statement_start(self) -> bool:
        return self._check(
            TokenType.SET,
            TokenType.FIX,
            TokenType.ACTION,
            TokenType.RETURN,
            TokenType.IF,
            TokenType.LOOP,
            TokenType.IDENTIFIER,
            TokenType.NUMBER,
            TokenType.STRING,
            TokenType.TRUE,
            TokenType.FALSE,
            TokenType.YES,
            TokenType.NO,
            TokenType.NOT,
            TokenType.MINUS,
            TokenType.LPAREN,
        )

    def _expression_statement(self) -> ast.ExprStmt:
        expr = self._expression()
        return ast.ExprStmt(expression=expr, line=expr.line, column=expr.column)

    def _expression(self) -> ast.Expr:
        return self._logical_or()

    def _logical_or(self) -> ast.Expr:
        expr = self._logical_and()
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._logical_and()
            expr = ast.Binary(
                operator=operator.lexeme,
                left=expr,
                right=right,
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _logical_and(self) -> ast.Expr:
        expr = self._equality()
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expr = ast.Binary(
                operator=operator.lexeme,
                left=expr,
                right=right,
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _equality(self) -> ast.Expr:
        expr = self._comparison()
        while self._match(TokenType.EQ, TokenType.NEQ, TokenType.IS, TokenType.IS_NOT):
            operator = self._previous()
            op = "==" if operator.type == TokenType.IS else "!=" if operator.type == TokenType.IS_NOT else operator.lexeme
            right = self._comparison()
            expr = ast.Binary(
                operator=op,
                left=expr,
                right=right,
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _comparison(self) -> ast.Expr:
        expr = self._term()
        while self._match(TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE):
            operator = self._previous()
            right = self._term()
            expr = ast.Binary(
                operator=operator.lexeme,
                left=expr,
                right=right,
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _term(self) -> ast.Expr:
        expr = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._factor()
            expr = ast.Binary(
                operator=operator.lexeme,
                left=expr,
                right=right,
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _factor(self) -> ast.Expr:
        expr = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous()
            right = self._unary()
            expr = ast.Binary(
                operator=operator.lexeme,
                left=expr,
                right=right,
                line=operator.line,
                column=operator.column,
            )
        return expr

    def _unary(self) -> ast.Expr:
        if self._match(TokenType.NOT, TokenType.MINUS):
            operator = self._previous()
            operand = self._unary()
            return ast.Unary(
                operator=operator.lexeme,
                operand=operand,
                line=operator.line,
                column=operator.column,
            )
        return self._call()

    def _call(self) -> ast.Expr:
        expr = self._primary()
        while self._match(TokenType.LPAREN):
            expr = self._finish_call(expr)
        return expr

    def _finish_call(self, callee_expr: ast.Expr) -> ast.Call:
        if not isinstance(callee_expr, ast.Variable):
            self._error("Can only call functions by name", self._previous())

        arguments: list[ast.Expr] = []
        if not self._check(TokenType.RPAREN):
            while True:
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
        paren = self._consume(TokenType.RPAREN, "Expected ')' after arguments")
        return ast.Call(
            callee=callee_expr.name,
            arguments=arguments,
            line=callee_expr.line,
            column=callee_expr.column,
        )

    def _primary(self) -> ast.Expr:
        if self._match(TokenType.FALSE, TokenType.NO):
            token = self._previous()
            return ast.Literal(value=False, line=token.line, column=token.column)
        if self._match(TokenType.TRUE, TokenType.YES):
            token = self._previous()
            return ast.Literal(value=True, line=token.line, column=token.column)
        if self._match(TokenType.NUMBER, TokenType.STRING):
            token = self._previous()
            return ast.Literal(value=token.literal, line=token.line, column=token.column)
        if self._match(TokenType.IDENTIFIER):
            token = self._previous()
            return ast.Variable(name=token.lexeme, line=token.line, column=token.column)
        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        token = self._peek()
        self._error(f"Unexpected token '{token.lexeme}'", token)
