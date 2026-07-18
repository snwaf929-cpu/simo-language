"""Lexical environments for Sola execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from sola.errors import RuntimeError as SolaRuntimeError


@dataclass
class Binding:
    value: Any
    is_const: bool = False


@dataclass
class Environment:
    parent: Environment | None = None
    bindings: dict[str, Binding] = field(default_factory=dict)
    functions: dict[str, Callable[..., Any]] = field(default_factory=dict)

    def define(
        self,
        name: str,
        value: Any,
        *,
        is_const: bool = False,
        line: int = 0,
        column: int = 0,
        filename: str = "<stdin>",
    ) -> None:
        if name in self.bindings:
            raise SolaRuntimeError(
                f"Variable '{name}' is already defined in this scope",
                filename,
                line,
                column,
            )
        self.bindings[name] = Binding(value=value, is_const=is_const)

    def declare_or_assign(
        self,
        name: str,
        value: Any,
        *,
        line: int = 0,
        column: int = 0,
        filename: str = "<stdin>",
    ) -> None:
        """Handle `set name = value`: update nearest binding or create local."""
        env, binding = self._resolve_binding(name)
        if binding is not None:
            if binding.is_const:
                raise SolaRuntimeError(
                    f"Cannot reassign constant '{name}'",
                    filename,
                    line,
                    column,
                )
            env.bindings[name] = Binding(value=value, is_const=False)
            return
        self.define(name, value, is_const=False, line=line, column=column, filename=filename)

    def assign(
        self,
        name: str,
        value: Any,
        *,
        line: int = 0,
        column: int = 0,
        filename: str = "<stdin>",
    ) -> None:
        """Handle bare assignment: update nearest existing binding only."""
        env, binding = self._resolve_binding(name)
        if binding is None:
            raise SolaRuntimeError(
                f"Undefined variable '{name}'",
                filename,
                line,
                column,
            )
        if binding.is_const:
            raise SolaRuntimeError(
                f"Cannot reassign constant '{name}'",
                filename,
                line,
                column,
            )
        env.bindings[name] = Binding(value=value, is_const=False)

    def get(
        self,
        name: str,
        *,
        line: int = 0,
        column: int = 0,
        filename: str = "<stdin>",
    ) -> Any:
        env, binding = self._resolve_binding(name)
        if binding is None:
            raise SolaRuntimeError(
                f"Undefined variable '{name}'",
                filename,
                line,
                column,
            )
        return binding.value

    def _resolve_binding(self, name: str) -> tuple[Environment | None, Binding | None]:
        env: Environment | None = self
        while env is not None:
            if name in env.bindings:
                return env, env.bindings[name]
            env = env.parent
        return None, None

    def get_function(
        self,
        name: str,
        *,
        line: int = 0,
        column: int = 0,
        filename: str = "<stdin>",
    ) -> Callable[..., Any]:
        env: Environment | None = self
        while env is not None:
            if name in env.functions:
                return env.functions[name]
            env = env.parent
        raise SolaRuntimeError(
            f"Undefined function '{name}'",
            filename,
            line,
            column,
        )

    def define_function(self, name: str, func: Callable[..., Any]) -> None:
        self.functions[name] = func

    def child(self) -> Environment:
        return Environment(parent=self)
