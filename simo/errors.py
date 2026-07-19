"""Error types and source locations for the Simo toolchain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLocation:
    filename: str = "<stdin>"
    line: int = 0
    column: int = 0

    def render(self) -> str:
        location = f"{self.filename}:{self.line}"
        if self.column:
            location += f":{self.column}"
        return location


class SimoError(Exception):
    """Base exception for user-facing Simo failures."""

    category = "SimoError"

    def __init__(
        self,
        message: str,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.location = SourceLocation(filename, line, column)

    def __str__(self) -> str:
        return f"[{self.category}] {self.location.render()}: {self.message}"


class LexError(SimoError):
    category = "LexError"


class ParseError(SimoError):
    category = "ParseError"


class RuntimeError(SimoError):
    category = "RuntimeError"


class BuildError(SimoError):
    category = "BuildError"


class ProjectError(SimoError):
    category = "ProjectError"
