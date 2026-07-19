"""Control-flow parsing for Simo."""

from typing import Any

from simo import ast_nodes as ast
from simo.errors import ParseError
from simo.tokens import Token, TokenType


class ParserControlMixin:
    def _loop_statement(self) -> ast.Stmt:
        keyword = self._previous()
        if self._match(TokenType.WHILE):
            condition = self._expression()
            self._line_end(required=True)
            body = self._block_until(TokenType.END)
            self._consume(TokenType.END, "Expected 'end' after loop")
            self._line_end()
            return ast.LoopWhile(
                condition=condition, body=body, line=keyword.line, column=keyword.column
            )

        if self._match(TokenType.FOR):
            name = self._consume(TokenType.IDENTIFIER, "Expected loop variable after 'for'")
            self._consume(TokenType.IN, "Expected 'in' after loop variable")
            iterable = self._expression()
            self._line_end(required=True)
            body = self._block_until(TokenType.END)
            self._consume(TokenType.END, "Expected 'end' after loop")
            self._line_end()
            return ast.LoopFor(
                name=name.lexeme,
                iterable=iterable,
                body=body,
                line=keyword.line,
                column=keyword.column,
            )

        count = self._expression()
        self._consume(TokenType.TIMES, "Expected 'times' after loop count")
        self._line_end(required=True)
        body = self._block_until(TokenType.END)
        self._consume(TokenType.END, "Expected 'end' after loop")
        self._line_end()
        return ast.LoopTimes(
            count=count, body=body, line=keyword.line, column=keyword.column
        )

    def _attempt_statement(self) -> ast.AttemptStmt:
        keyword = self._previous()
        self._line_end(required=True)
        body: list[ast.Stmt] = []
        self._skip_newlines()
        while not self._at_end() and not self._attempt_failure_marker():
            body.append(self._declaration())
            self._skip_newlines()
        if not self._attempt_failure_marker():
            self._error("Expected 'if it fails' after attempt body")
        self._advance()  # if
        self._advance()  # it
        self._advance()  # fails
        self._line_end(required=True)
        failure_body = self._block_until(TokenType.END)
        self._consume(TokenType.END, "Expected 'end' after attempt statement")
        self._line_end()
        return ast.AttemptStmt(
            body=body,
            failure_body=failure_body,
            line=keyword.line,
            column=keyword.column,
        )

    def _attempt_failure_marker(self) -> bool:
        return (
            self._check(TokenType.IF)
            and self._peek(1).type == TokenType.IT
            and self._peek(2).type == TokenType.FAILS
        )
