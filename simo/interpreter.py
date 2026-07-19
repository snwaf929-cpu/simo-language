"""Tree-walking interpreter for console-oriented Simo programs."""

from __future__ import annotations

import sys
from pathlib import Path

from simo import ast_nodes as ast
from simo.environment import Environment
from simo.errors import RuntimeError as SimoRuntimeError
from simo.interpreter_builtins import InterpreterBuiltinsMixin
from simo.interpreter_evaluate import InterpreterEvaluateMixin
from simo.interpreter_execute import InterpreterExecuteMixin
from simo.interpreter_values import InterpreterValuesMixin


class Interpreter(
    InterpreterBuiltinsMixin,
    InterpreterExecuteMixin,
    InterpreterEvaluateMixin,
    InterpreterValuesMixin,
):
    def __init__(
        self,
        filename: str = "<stdin>",
        step_limit: int = 100_000,
        output_stream=None,
        input_stream=None,
    ) -> None:
        self.filename = filename
        self.step_limit = step_limit
        self.steps = 0
        self.output = output_stream if output_stream is not None else sys.stdout
        self.input = input_stream if input_stream is not None else sys.stdin
        self.builtins = Environment()
        self.globals = Environment(self.builtins)
        self.environment = self.globals
        self.loaded_modules: set[Path] = set()
        self.file_stack: list[Path] = []
        if filename not in {"<stdin>", "<memory>"}:
            self.file_stack.append(Path(filename).resolve())
        self._install_builtins()

    def interpret(self, program: ast.Program) -> None:
        for statement in program.statements:
            self._execute(statement)

    def _tick(self, node: ast.Node) -> None:
        self.steps += 1
        if self.steps > self.step_limit:
            raise SimoRuntimeError(
                f"Execution step limit ({self.step_limit}) exceeded",
                self.filename,
                node.line,
                node.column,
            )

    def _runtime_error(self, node: ast.Node, message: str) -> SimoRuntimeError:
        return SimoRuntimeError(message, self.filename, node.line, node.column)
