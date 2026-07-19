"""Core declaration parsing for Simo."""

from typing import Any

from simo import ast_nodes as ast
from simo.errors import ParseError
from simo.tokens import Token, TokenType


class ParserStatementMixin:
    def _declaration(self) -> ast.Stmt:
        self._skip_newlines()
        if self._match(TokenType.IMPORT):
            return self._import_statement()
        if self._match(TokenType.SET):
            return self._var_declaration(False)
        if self._match(TokenType.FIX):
            return self._var_declaration(True)
        if self._match(TokenType.ACTION):
            return self._action_declaration()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.LOOP):
            return self._loop_statement()
        if self._match(TokenType.BREAK):
            token = self._previous()
            self._line_end()
            return ast.BreakStmt(line=token.line, column=token.column)
        if self._match(TokenType.CONTINUE):
            token = self._previous()
            self._line_end()
            return ast.ContinueStmt(line=token.line, column=token.column)
        if self._match(TokenType.ATTEMPT):
            return self._attempt_statement()
        if self._match(TokenType.PAGE):
            return self._page_declaration()
        if self._match(TokenType.SHOW):
            return self._show_statement()
        if self._match(TokenType.CHANGE):
            return self._change_statement()
        return self._expression_or_assignment()

    def _import_statement(self) -> ast.ImportStmt:
        keyword = self._previous()
        path = self._consume(TokenType.STRING, "Expected a quoted path after 'import'")
        self._line_end()
        return ast.ImportStmt(path=str(path.literal), line=keyword.line, column=keyword.column)

    def _var_declaration(self, is_const: bool) -> ast.VarDecl:
        keyword = self._previous()
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name")
        self._consume(TokenType.ASSIGN, "Expected '=' after variable name")
        initializer = self._expression()
        self._line_end()
        return ast.VarDecl(
            name=name.lexeme,
            initializer=initializer,
            is_const=is_const,
            line=keyword.line,
            column=keyword.column,
        )

    def _action_declaration(self) -> ast.ActionDecl:
        keyword = self._previous()
        name = self._consume(TokenType.IDENTIFIER, "Expected action name")
        self._consume(TokenType.LPAREN, "Expected '(' after action name")
        params: list[str] = []
        if not self._check(TokenType.RPAREN):
            while True:
                params.append(
                    self._consume(TokenType.IDENTIFIER, "Expected parameter name").lexeme
                )
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RPAREN, "Expected ')' after action parameters")
        self._line_end(required=True)
        body = self._block_until(TokenType.END)
        self._consume(TokenType.END, "Expected 'end' after action body")
        self._line_end()
        return ast.ActionDecl(
            name=name.lexeme,
            params=params,
            body=body,
            line=keyword.line,
            column=keyword.column,
        )

    def _return_statement(self) -> ast.ReturnStmt:
        token = self._previous()
        value = None
        if not self._check(
            TokenType.NEWLINE, TokenType.END, TokenType.ELSE, TokenType.RBRACE, TokenType.EOF
        ):
            value = self._expression()
        self._line_end()
        return ast.ReturnStmt(value=value, line=token.line, column=token.column)

    def _if_statement(self) -> ast.IfStmt:
        keyword = self._previous()
        branches: list[tuple[ast.Expr, list[ast.Stmt]]] = []
        condition = self._expression()
        self._line_end(required=True)
        branches.append((condition, self._block_until(TokenType.ELSE, TokenType.END)))
        else_body: list[ast.Stmt] = []

        while self._match(TokenType.ELSE):
            if self._match(TokenType.IF):
                condition = self._expression()
                self._line_end(required=True)
                branches.append((condition, self._block_until(TokenType.ELSE, TokenType.END)))
                continue
            self._line_end()
            else_body = self._block_until(TokenType.END)
            break

        self._consume(TokenType.END, "Expected 'end' after if statement")
        self._line_end()
        return ast.IfStmt(
            branches=branches,
            else_body=else_body,
            line=keyword.line,
            column=keyword.column,
        )
