"""Control signals and user actions for the Simo interpreter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from simo import ast_nodes as ast
from simo.environment import Environment
from simo.errors import RuntimeError as SimoRuntimeError


class ReturnSignal(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


@dataclass
class UserFunction:
    declaration: ast.ActionDecl
    closure: Environment
    interpreter: Interpreter

    def __call__(self, *arguments: Any) -> Any:
        if len(arguments) != len(self.declaration.params):
            raise SimoRuntimeError(
                f"Action '{self.declaration.name}' expects "
                f"{len(self.declaration.params)} argument(s), got {len(arguments)}",
                self.interpreter.filename,
                self.declaration.line,
                self.declaration.column,
            )
        environment = Environment(self.closure)
        for name, value in zip(self.declaration.params, arguments, strict=True):
            environment.define(name, value)
        try:
            self.interpreter._execute_block(self.declaration.body, environment)
        except ReturnSignal as signal:
            return signal.value
        return None
