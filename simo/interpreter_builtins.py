"""Standard library installation for Simo."""

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


class InterpreterBuiltinsMixin:
    def _install_builtins(self) -> None:
        def say(value: Any = "") -> None:
            print(self._string(value), file=self.output)

        def ask(prompt: Any = "") -> str:
            if prompt:
                print(self._string(prompt), end="", file=self.output, flush=True)
            return self.input.readline().rstrip("\n")

        def simo_len(value: Any) -> int:
            try:
                return len(value)
            except TypeError as exc:
                raise SimoRuntimeError("len() requires text, a list, or an object") from exc

        def number(value: Any) -> int | float:
            if isinstance(value, bool):
                return 1 if value else 0
            if isinstance(value, (int, float)):
                return value
            text = str(value).strip()
            try:
                return float(text) if "." in text else int(text)
            except ValueError as exc:
                raise SimoRuntimeError(f"Cannot convert {value!r} to a number") from exc

        def boolean(value: Any) -> bool:
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"true", "yes", "1", "on"}:
                    return True
                if lowered in {"false", "no", "0", "off", ""}:
                    return False
            return self._truthy(value)

        def simo_range(*args: Any) -> list[int]:
            numbers = [int(number(value)) for value in args]
            if not 1 <= len(numbers) <= 3:
                raise SimoRuntimeError("range() expects 1 to 3 arguments")
            return list(range(*numbers))

        def add(collection: Any, value: Any) -> Any:
            if not isinstance(collection, list):
                raise SimoRuntimeError("add() requires a list as its first argument")
            collection.append(value)
            return collection

        def remove(collection: Any, value: Any) -> Any:
            if isinstance(collection, list):
                if value in collection:
                    collection.remove(value)
                return collection
            if isinstance(collection, dict):
                collection.pop(str(value), None)
                return collection
            raise SimoRuntimeError("remove() requires a list or object")

        def contains(collection: Any, value: Any) -> bool:
            try:
                return value in collection
            except TypeError as exc:
                raise SimoRuntimeError("contains() requires a collection") from exc

        def read_file(path: Any) -> str:
            return Path(str(path)).read_text(encoding="utf-8")

        def write_file(path: Any, content: Any) -> None:
            target = Path(str(path))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self._string(content), encoding="utf-8")

        def storage_path() -> Path:
            base = self.file_stack[0].parent if self.file_stack else Path.cwd()
            return base / ".simo-storage.json"

        def save(key: Any, value: Any) -> Any:
            path = storage_path()
            data: dict[str, Any] = {}
            if path.exists():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        data = loaded
                except (OSError, json.JSONDecodeError):
                    data = {}
            data[str(key)] = value
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return value

        def load(key: Any, fallback: Any = None) -> Any:
            path = storage_path()
            if not path.exists():
                return fallback
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return fallback
            return data.get(str(key), fallback) if isinstance(data, dict) else fallback

        def assert_true(condition: Any, message: Any = "Assertion failed") -> None:
            if not self._truthy(condition):
                raise SimoRuntimeError(self._string(message))

        builtins: dict[str, Callable[..., Any] | Any] = {
            "say": say,
            "ask": ask,
            "len": simo_len,
            "text": self._string,
            "number": number,
            "bool": boolean,
            "range": simo_range,
            "add": add,
            "remove": remove,
            "contains": contains,
            "keys": lambda value: list(value.keys()) if isinstance(value, dict) else [],
            "values": lambda value: list(value.values()) if isinstance(value, dict) else [],
            "read_file": read_file,
            "write_file": write_file,
            "save": save,
            "load": load,
            "assert": assert_true,
            "random": lambda minimum=0, maximum=1: random.uniform(minimum, maximum),
            "round": round,
            "floor": math.floor,
            "ceil": math.ceil,
            "pi": math.pi,
        }
        for name, value in builtins.items():
            self.builtins.define(name, value, is_const=True)

    # statement execution ----------------------------------------------
