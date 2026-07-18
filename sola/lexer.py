"""Lexical analyzer for Sola source code."""

from __future__ import annotations

from sola.errors import LexError
from sola.tokens import KEYWORDS, Token, TokenType


class Lexer:
    def __init__(self, source: str, filename: str = "<stdin>") -> None:
        self._source = source
        self._filename = filename
        self._pos = 0
        self._line = 1
        self._column = 1
        self._tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while not self._is_at_end():
            self._skip_whitespace_and_comments()
            if self._is_at_end():
                break
            self._scan_token()

        self._tokens.append(
            Token(TokenType.EOF, "", self._line, self._column)
        )
        return self._tokens

    def _is_at_end(self) -> bool:
        return self._pos >= len(self._source)

    def _current(self) -> str:
        if self._is_at_end():
            return "\0"
        return self._source[self._pos]

    def _advance(self) -> str:
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return ch

    def _peek(self, offset: int = 1) -> str:
        pos = self._pos + offset
        if pos >= len(self._source):
            return "\0"
        return self._source[pos]

    def _match(self, expected: str) -> bool:
        if self._current() != expected:
            return False
        self._advance()
        return True

    def _make_token(self, token_type: TokenType, lexeme: str, literal=None) -> Token:
        return Token(token_type, lexeme, self._line, self._column, literal)

    def _error(self, message: str) -> None:
        raise LexError(message, self._filename, self._line, self._column)

    def _skip_whitespace_and_comments(self) -> None:
        while not self._is_at_end():
            ch = self._current()
            if ch in " \t\r":
                self._advance()
            elif ch == "\n":
                self._advance()
            elif ch == "/" and self._peek() == "/":
                while not self._is_at_end() and self._current() != "\n":
                    self._advance()
            else:
                break

    def _scan_token(self) -> None:
        start_line = self._line
        start_column = self._column
        ch = self._advance()

        if ch == "(":
            self._tokens.append(Token(TokenType.LPAREN, ch, start_line, start_column))
        elif ch == ")":
            self._tokens.append(Token(TokenType.RPAREN, ch, start_line, start_column))
        elif ch == ",":
            self._tokens.append(Token(TokenType.COMMA, ch, start_line, start_column))
        elif ch == "+":
            self._tokens.append(Token(TokenType.PLUS, ch, start_line, start_column))
        elif ch == "-":
            self._tokens.append(Token(TokenType.MINUS, ch, start_line, start_column))
        elif ch == "*":
            self._tokens.append(Token(TokenType.STAR, ch, start_line, start_column))
        elif ch == "/":
            self._tokens.append(Token(TokenType.SLASH, ch, start_line, start_column))
        elif ch == "=":
            if self._match("="):
                self._tokens.append(Token(TokenType.EQ, "==", start_line, start_column))
            else:
                self._tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_column))
        elif ch == "!":
            if self._match("="):
                self._tokens.append(Token(TokenType.NEQ, "!=", start_line, start_column))
            else:
                self._error(f"Unexpected character '!'")
        elif ch == "<":
            if self._match("="):
                self._tokens.append(Token(TokenType.LTE, "<=", start_line, start_column))
            else:
                self._tokens.append(Token(TokenType.LT, "<", start_line, start_column))
        elif ch == ">":
            if self._match("="):
                self._tokens.append(Token(TokenType.GTE, ">=", start_line, start_column))
            else:
                self._tokens.append(Token(TokenType.GT, ">", start_line, start_column))
        elif ch == '"':
            self._string(start_line, start_column)
        elif ch.isdigit():
            self._number(ch, start_line, start_column)
        elif ch.isalpha() or ch == "_":
            self._identifier(ch, start_line, start_column)
        else:
            self._error(f"Unexpected character '{ch}'")

    def _string(self, start_line: int, start_column: int) -> None:
        value: list[str] = []
        while not self._is_at_end() and self._current() != '"':
            ch = self._advance()
            if ch == "\n":
                self._error("Unterminated string")
            if ch == "\\":
                if self._is_at_end():
                    self._error("Unterminated string escape")
                esc = self._advance()
                if esc == "n":
                    value.append("\n")
                elif esc == "t":
                    value.append("\t")
                elif esc == '"':
                    value.append('"')
                elif esc == "\\":
                    value.append("\\")
                else:
                    self._error(f"Invalid escape sequence '\\{esc}'")
            else:
                value.append(ch)

        if self._is_at_end():
            self._error("Unterminated string")

        self._advance()  # closing quote
        self._tokens.append(
            Token(TokenType.STRING, "".join(value), start_line, start_column, "".join(value))
        )

    def _number(self, first: str, start_line: int, start_column: int) -> None:
        digits = [first]
        while self._current().isdigit():
            digits.append(self._advance())

        if self._current() == "." and self._peek().isdigit():
            digits.append(self._advance())
            while self._current().isdigit():
                digits.append(self._advance())

        text = "".join(digits)
        value: int | float
        if "." in text:
            value = float(text)
        else:
            value = int(text)

        self._tokens.append(
            Token(TokenType.NUMBER, text, start_line, start_column, value)
        )

    def _identifier(self, first: str, start_line: int, start_column: int) -> None:
        chars = [first]
        while self._current().isalnum() or self._current() == "_":
            chars.append(self._advance())

        text = "".join(chars)
        lower = text.lower()

        if lower == "is":
            self._skip_whitespace_and_comments()
            if self._current() == "n":
                word = ["n"]
                self._advance()
                while self._current().isalnum() or self._current() == "_":
                    word.append(self._advance())
                if "".join(word).lower() == "not":
                    self._tokens.append(
                        Token(TokenType.IS_NOT, "is not", start_line, start_column)
                    )
                    return
                unknown = "".join(word)
                self._error(f"Unknown keyword 'is {unknown}'")
            self._tokens.append(Token(TokenType.IS, text, start_line, start_column))
            return

        token_type = KEYWORDS.get(lower)
        if token_type is not None and lower != "is":
            self._tokens.append(Token(token_type, text, start_line, start_column))
        else:
            self._tokens.append(
                Token(TokenType.IDENTIFIER, text, start_line, start_column)
            )
