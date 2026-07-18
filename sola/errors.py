"""Sola language error types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SolaError(Exception):
    """Base error for all Sola failures."""

    category: str
    message: str
    filename: str = "<stdin>"
    line: int = 0
    column: int = 0

    def __str__(self) -> str:
        location = f"{self.filename}:{self.line}"
        if self.column:
            location += f":{self.column}"
        return f"[{self.category}] {location}: {self.message}"


class LexError(SolaError):
    """Lexical analysis error."""

    def __init__(
        self,
        message: str,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
    ) -> None:
        super().__init__("LexError", message, filename, line, column)


class ParseError(SolaError):
    """Syntax analysis error."""

    def __init__(
        self,
        message: str,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
    ) -> None:
        super().__init__("ParseError", message, filename, line, column)


class RuntimeError(SolaError):
    """Runtime execution error."""

    def __init__(
        self,
        message: str,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
    ) -> None:
        super().__init__("RuntimeError", message, filename, line, column)
