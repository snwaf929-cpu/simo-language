"""Statement execution for Simo."""

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


class InterpreterExecuteMixin:
    def _execute(self, statement: ast.Stmt) -> Any:
        self._tick(statement)

        if isinstance(statement, ast.ImportStmt):
            return self._execute_import(statement)
        if isinstance(statement, ast.VarDecl):
            value = self._evaluate(statement.initializer)
            self.environment.define(
                statement.name,
                value,
                is_const=statement.is_const,
                filename=self.filename,
                line=statement.line,
                column=statement.column,
            )
            return None
        if isinstance(statement, ast.Assign):
            value = self._evaluate(statement.value)
            self._assign_target(statement.target, value)
            return value
        if isinstance(statement, ast.ExprStmt):
            return self._evaluate(statement.expression)
        if isinstance(statement, ast.ActionDecl):
            function = UserFunction(statement, self.environment, self)
            self.environment.define(
                statement.name,
                function,
                is_const=True,
                filename=self.filename,
                line=statement.line,
                column=statement.column,
            )
            return None
        if isinstance(statement, ast.ReturnStmt):
            raise ReturnSignal(self._evaluate(statement.value) if statement.value else None)
        if isinstance(statement, ast.IfStmt):
            for condition, body in statement.branches:
                if self._truthy(self._evaluate(condition)):
                    self._execute_block(body, Environment(self.environment))
                    return None
            if statement.else_body:
                self._execute_block(statement.else_body, Environment(self.environment))
            return None
        if isinstance(statement, ast.LoopTimes):
            count = self._number(self._evaluate(statement.count), statement)
            if isinstance(count, float) and not count.is_integer():
                raise self._runtime_error(statement, "Loop count must be a whole number")
            for _ in range(max(0, int(count))):
                try:
                    self._execute_block(statement.body, Environment(self.environment))
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
            return None
        if isinstance(statement, ast.LoopWhile):
            while self._truthy(self._evaluate(statement.condition)):
                try:
                    self._execute_block(statement.body, Environment(self.environment))
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
            return None
        if isinstance(statement, ast.LoopFor):
            iterable = self._evaluate(statement.iterable)
            if not isinstance(iterable, (list, tuple, str, dict)):
                raise self._runtime_error(statement, "'loop for' requires a collection")
            values = iterable.keys() if isinstance(iterable, dict) else iterable
            for value in values:
                local = Environment(self.environment)
                local.define(statement.name, value)
                try:
                    self._execute_block(statement.body, local)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
            return None
        if isinstance(statement, ast.BreakStmt):
            raise BreakSignal()
        if isinstance(statement, ast.ContinueStmt):
            raise ContinueSignal()
        if isinstance(statement, ast.AttemptStmt):
            try:
                self._execute_block(statement.body, Environment(self.environment))
            except (SimoError, OSError, ValueError, TypeError, ZeroDivisionError) as exc:
                failure = Environment(self.environment)
                failure.define("error", str(exc), is_const=True)
                self._execute_block(statement.failure_body, failure)
            return None
        if isinstance(statement, ast.PageDecl):
            raise self._runtime_error(
                statement,
                "Page programs run in the browser. Use 'simo dev' or 'simo build'.",
            )
        if isinstance(statement, (ast.ShowElement, ast.ChangeElement, ast.ShowNotification)):
            raise self._runtime_error(
                statement,
                "UI statements require a page and the web/app compiler.",
            )
        raise self._runtime_error(statement, f"Unknown statement {type(statement).__name__}")

    def _execute_block(self, statements: list[ast.Stmt], environment: Environment) -> None:
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = previous

    def _execute_import(self, statement: ast.ImportStmt) -> None:
        base = self.file_stack[-1].parent if self.file_stack else Path.cwd()
        path = (base / statement.path).resolve()
        if path in self.loaded_modules:
            return
        if not path.exists():
            raise self._runtime_error(statement, f"Imported file not found: {path}")
        self.loaded_modules.add(path)
        source = path.read_text(encoding="utf-8")
        program = Parser(Lexer(source, str(path)).tokenize(), str(path)).parse()
        previous_filename = self.filename
        self.filename = str(path)
        self.file_stack.append(path)
        try:
            for imported_statement in program.statements:
                self._execute(imported_statement)
        finally:
            self.file_stack.pop()
            self.filename = previous_filename

    # expression evaluation --------------------------------------------
