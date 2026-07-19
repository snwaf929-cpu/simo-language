"""Lexical environments used by the Simo interpreter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from simo.errors import RuntimeError as SimoRuntimeError


@dataclass
class Binding:
    value: Any
    is_const: bool = False


class Environment:
    def __init__(self, parent: Environment | None = None) -> None:
        self.parent = parent
        self.values: dict[str, Binding] = {}

    def define(
        self,
        name: str,
        value: Any,
        *,
        is_const: bool = False,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
        replace: bool = False,
    ) -> None:
        if name in self.values and not replace:
            raise SimoRuntimeError(
                f"Variable '{name}' is already defined in this scope",
                filename,
                line,
                column,
            )
        self.values[name] = Binding(value, is_const)

    def resolve(self, name: str) -> tuple[Environment | None, Binding | None]:
        environment: Environment | None = self
        while environment is not None:
            binding = environment.values.get(name)
            if binding is not None:
                return environment, binding
            environment = environment.parent
        return None, None

    def get(
        self,
        name: str,
        *,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
    ) -> Any:
        _, binding = self.resolve(name)
        if binding is None:
            raise SimoRuntimeError(
                f"Undefined variable or action '{name}'", filename, line, column
            )
        return binding.value

    def assign(
        self,
        name: str,
        value: Any,
        *,
        filename: str = "<stdin>",
        line: int = 0,
        column: int = 0,
    ) -> None:
        environment, binding = self.resolve(name)
        if environment is None or binding is None:
            raise SimoRuntimeError(f"Undefined variable '{name}'", filename, line, column)
        if binding.is_const:
            raise SimoRuntimeError(
                f"Cannot reassign constant '{name}'", filename, line, column
            )
        environment.values[name] = Binding(value, False)
