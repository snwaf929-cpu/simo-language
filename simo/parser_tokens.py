"""Token navigation helpers for the Simo parser."""

from typing import Any

from simo import ast_nodes as ast
from simo.errors import ParseError
from simo.tokens import Token, TokenType


class ParserTokenMixin:
    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self, offset: int = 0) -> Token:
        index = min(self.current + offset, len(self.tokens) - 1)
        return self.tokens[index]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        if not self._at_end():
            self.current += 1
        return self._previous()

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _match(self, *types: TokenType) -> bool:
        if self._check(*types):
            self._advance()
            return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        self._error(message)

    def _error(self, message: str, token: Token | None = None) -> None:
        found = token or self._peek()
        raise ParseError(message, self.filename, found.line, found.column)

    def _skip_newlines(self) -> None:
        while self._match(TokenType.NEWLINE):
            pass

    def _line_end(self, required: bool = False) -> None:
        if self._match(TokenType.NEWLINE):
            self._skip_newlines()
            return
        if self._check(TokenType.EOF, TokenType.END, TokenType.ELSE, TokenType.RBRACE):
            return
        if required:
            self._error("Expected end of line")

    def _word(self, token: Token) -> str:
        return token.lexeme.lower()

    # statements --------------------------------------------------------
