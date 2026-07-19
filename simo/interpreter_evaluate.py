"""Expression evaluation for Simo."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any, Callable

from simo import ast_nodes as ast
from simo.environment import Environment
from simo.errors import RuntimeError as SimoRuntimeError
from simo.errors import SimoError
from simo.lexer import Lexer
from simo.parser import Parser
from simo.interpreter_support import BreakSignal, ContinueSignal, ReturnSignal, UserFunction


class InterpreterEvaluateMixin:
    def _evaluate(self, expression: ast.Expr | None) -> Any:
        if expression is None:
            return None
        self._tick(expression)

        if isinstance(expression, ast.Literal):
            return expression.value
        if isinstance(expression, ast.Variable):
            return self.environment.get(
                expression.name,
                filename=self.filename,
                line=expression.line,
                column=expression.column,
            )
        if isinstance(expression, ast.ListLiteral):
            return [self._evaluate(item) for item in expression.items]
        if isinstance(expression, ast.ObjectLiteral):
            return {key: self._evaluate(value) for key, value in expression.items}
        if isinstance(expression, ast.Unary):
            value = self._evaluate(expression.operand)
            if expression.operator == "not":
                return not self._truthy(value)
            if expression.operator == "-":
                return -self._number(value, expression)
            if expression.operator == "+":
                return self._number(value, expression)
            raise self._runtime_error(expression, f"Unknown unary operator {expression.operator}")
        if isinstance(expression, ast.Binary):
            if expression.operator == "and":
                left = self._evaluate(expression.left)
                return self._evaluate(expression.right) if self._truthy(left) else left
            if expression.operator == "or":
                left = self._evaluate(expression.left)
                return left if self._truthy(left) else self._evaluate(expression.right)
            left = self._evaluate(expression.left)
            right = self._evaluate(expression.right)
            return self._binary(expression, left, right)
        if isinstance(expression, ast.Call):
            callee = self._evaluate(expression.callee)
            if not callable(callee):
                raise self._runtime_error(expression, "Only actions can be called")
            arguments = [self._evaluate(argument) for argument in expression.arguments]
            try:
                return callee(*arguments)
            except SimoError:
                raise
            except TypeError as exc:
                raise self._runtime_error(expression, f"Invalid action arguments: {exc}") from exc
        if isinstance(expression, ast.Get):
            value = self._evaluate(expression.object)
            if isinstance(value, dict):
                if expression.name not in value:
                    raise self._runtime_error(
                        expression, f"Object has no property '{expression.name}'"
                    )
                return value[expression.name]
            if expression.name == "length" and isinstance(value, (list, str, tuple)):
                return len(value)
            try:
                return getattr(value, expression.name)
            except AttributeError as exc:
                raise self._runtime_error(
                    expression, f"Value has no property '{expression.name}'"
                ) from exc
        if isinstance(expression, ast.Index):
            value = self._evaluate(expression.object)
            index = self._evaluate(expression.index)
            try:
                return value[index]
            except (TypeError, KeyError, IndexError) as exc:
                raise self._runtime_error(expression, f"Invalid index {index!r}") from exc
        raise self._runtime_error(expression, f"Unknown expression {type(expression).__name__}")

    def _assign_target(self, target: ast.Expr | None, value: Any) -> None:
        if isinstance(target, ast.Variable):
            self.environment.assign(
                target.name,
                value,
                filename=self.filename,
                line=target.line,
                column=target.column,
            )
            return
        if isinstance(target, ast.Get):
            owner = self._evaluate(target.object)
            if isinstance(owner, dict):
                owner[target.name] = value
                return
            try:
                setattr(owner, target.name, value)
                return
            except (AttributeError, TypeError) as exc:
                raise self._runtime_error(target, "Cannot assign this property") from exc
        if isinstance(target, ast.Index):
            owner = self._evaluate(target.object)
            index = self._evaluate(target.index)
            try:
                owner[index] = value
                return
            except (TypeError, KeyError, IndexError) as exc:
                raise self._runtime_error(target, "Cannot assign this index") from exc
        raise SimoRuntimeError("Invalid assignment target", self.filename)
