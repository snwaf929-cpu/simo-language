"""Simo language error types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimoError(Exception):
    """Base error for all Simo failures."""

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


class LexError(SimoError):
    """Lexical analysis error."""

    def __init__(
        self,
        message: str,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
    ) -> None:
        super().__init__("LexError", message, filename, line, column)


class ParseError(SimoError):
    """Syntax analysis error."""

    def __init__(
        self,
        message: str,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
    ) -> None:
        super().__init__("ParseError", message, filename, line, column)


class RuntimeError(SimoError):
    """Runtime execution error."""

    def __init__(
        self,
        message: str,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
    ) -> None:
        super().__init__("RuntimeError", message, filename, line, column)
