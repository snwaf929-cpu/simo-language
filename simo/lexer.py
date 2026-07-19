"""Lexical analyzer for Simo source files."""

from __future__ import annotations

from simo.errors import LexError
from simo.tokens import KEYWORDS, Token, TokenType


class Lexer:
    def __init__(self, source: str, filename: str = "<stdin>") -> None:
        self.source = source
        self.filename = filename
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_line = 1
        self.start_column = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while not self._at_end():
            self.start = self.current
            self.start_line = self.line
            self.start_column = self.column
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def _at_end(self) -> bool:
        return self.current >= len(self.source)

    def _peek(self, offset: int = 0) -> str:
        index = self.current + offset
        if index >= len(self.source):
            return "\0"
        return self.source[index]

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.current] != expected:
            return False
        self._advance()
        return True

    def _add(self, token_type: TokenType, literal=None, lexeme: str | None = None) -> None:
        text = self.source[self.start : self.current] if lexeme is None else lexeme
        self.tokens.append(
            Token(token_type, text, self.start_line, self.start_column, literal)
        )

    def _error(self, message: str) -> None:
        raise LexError(message, self.filename, self.start_line, self.start_column)

    def _scan_token(self) -> None:
        char = self._advance()

        if char in " \t\r":
            return
        if char == "\n":
            self._add(TokenType.NEWLINE, lexeme="\n")
            return

        single = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            ".": TokenType.DOT,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "%": TokenType.PERCENT,
        }
        if char in single:
            self._add(single[char])
            return

        if char == "/":
            if self._match("/"):
                while self._peek() not in {"\n", "\0"}:
                    self._advance()
                return
            self._add(TokenType.SLASH)
            return

        if char == "=":
            self._add(TokenType.EQ if self._match("=") else TokenType.ASSIGN)
            return
        if char == "!":
            if not self._match("="):
                self._error("Expected '=' after '!'")
            self._add(TokenType.NEQ)
            return
        if char == "<":
            self._add(TokenType.LTE if self._match("=") else TokenType.LT)
            return
        if char == ">":
            self._add(TokenType.GTE if self._match("=") else TokenType.GT)
            return

        if char == "#":
            while self._peek().isalnum():
                self._advance()
            self._add(TokenType.STRING, self.source[self.start : self.current])
            return

        if char == '"':
            self._string()
            return
        if char.isdigit():
            self._number_or_dimension()
            return
        if char.isalpha() or char == "_":
            self._identifier()
            return

        self._error(f"Unexpected character {char!r}")

    def _string(self) -> None:
        value: list[str] = []
        while not self._at_end() and self._peek() != '"':
            char = self._advance()
            if char == "\n":
                self._error("Unterminated string")
            if char != "\\":
                value.append(char)
                continue
            if self._at_end():
                self._error("Unterminated string escape")
            escaped = self._advance()
            escapes = {
                "n": "\n",
                "t": "\t",
                "r": "\r",
                '"': '"',
                "\\": "\\",
            }
            if escaped not in escapes:
                self._error(f"Invalid escape sequence \\{escaped}")
            value.append(escapes[escaped])
        if self._at_end():
            self._error("Unterminated string")
        self._advance()
        self._add(TokenType.STRING, "".join(value))

    def _number_or_dimension(self) -> None:
        while self._peek().isdigit():
            self._advance()

        if self._peek().lower() == "x" and self._peek(1).isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
            text = self.source[self.start : self.current]
            width, height = text.lower().split("x", 1)
            self._add(TokenType.DIMENSION, (int(width), int(height)))
            return

        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        text = self.source[self.start : self.current]
        self._add(TokenType.NUMBER, float(text) if "." in text else int(text))

    def _identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[self.start : self.current]
        lowered = text.lower()

        # Beginner-readable comments: note: this is a comment
        if lowered == "note" and self._peek() == ":":
            self._advance()
            while self._peek() not in {"\n", "\0"}:
                self._advance()
            return

        self._add(KEYWORDS.get(lowered, TokenType.IDENTIFIER))
