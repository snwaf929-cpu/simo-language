"""Value and operator helpers for Simo."""

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


class InterpreterValuesMixin:
    def _binary(self, node: ast.Binary, left: Any, right: Any) -> Any:
        operator = node.operator
        if operator == "+":
            if isinstance(left, str) or isinstance(right, str):
                return self._string(left) + self._string(right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            return self._number(left, node) + self._number(right, node)
        if operator == "-":
            return self._number(left, node) - self._number(right, node)
        if operator == "*":
            if isinstance(left, str) and self._is_number(right):
                return left * int(right)
            return self._number(left, node) * self._number(right, node)
        if operator == "/":
            divisor = self._number(right, node)
            if divisor == 0:
                raise self._runtime_error(node, "Division by zero")
            return self._number(left, node) / divisor
        if operator == "%":
            divisor = self._number(right, node)
            if divisor == 0:
                raise self._runtime_error(node, "Division by zero")
            return self._number(left, node) % divisor
        if operator in {"==", "!="}:
            equal = self._equal(left, right)
            return equal if operator == "==" else not equal
        if operator in {"<", "<=", ">", ">="}:
            left_number = self._number(left, node)
            right_number = self._number(right, node)
            return {
                "<": left_number < right_number,
                "<=": left_number <= right_number,
                ">": left_number > right_number,
                ">=": left_number >= right_number,
            }[operator]
        raise self._runtime_error(node, f"Unknown binary operator {operator}")

    def _equal(self, left: Any, right: Any) -> bool:
        if isinstance(left, bool) or isinstance(right, bool):
            return isinstance(left, bool) and isinstance(right, bool) and left == right
        if self._is_number(left) and self._is_number(right):
            return float(left) == float(right)
        return type(left) is type(right) and left == right

    def _number(self, value: Any, node: ast.Node) -> int | float:
        if not self._is_number(value):
            raise self._runtime_error(node, f"Expected a number, got {self._type_name(value)}")
        return value

    def _is_number(self, value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _truthy(self, value: Any) -> bool:
        return bool(value)

    def _type_name(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if self._is_number(value):
            return "number"
        if isinstance(value, str):
            return "text"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "object"
        return type(value).__name__

    def _string(self, value: Any) -> str:
        if value is None:
            return "null"
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        if isinstance(value, list):
            return "[" + ", ".join(self._string(item) for item in value) + "]"
        if isinstance(value, dict):
            pairs = ", ".join(f"{key}: {self._string(item)}" for key, item in value.items())
            return "{" + pairs + "}"
        return str(value)
