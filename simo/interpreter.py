"""Tree-walking interpreter for Simo."""

from __future__ import annotations

import sys
from typing import Any, Callable

from simo import ast_nodes as ast
from simo.environment import Environment
from simo.errors import RuntimeError as SimoRuntimeError


class ReturnSignal(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


class Interpreter:
    def __init__(
        self,
        filename: str = "<stdin>",
        step_limit: int = 100_000,
        output_stream=None,
    ) -> None:
        self._filename = filename
        self._step_limit = step_limit
        self._steps = 0
        self._output = output_stream if output_stream is not None else sys.stdout
        self._globals = Environment()
        self._env = self._globals
        self._register_builtins()

    def interpret(self, program: ast.Program) -> None:
        for statement in program.statements:
            self._execute(statement)

    def _register_builtins(self) -> None:
        def say(value: Any) -> None:
            print(self._to_string(value), file=self._output)

        self._globals.define_function("say", say)

    def _tick(self, line: int = 0, column: int = 0) -> None:
        self._steps += 1
        if self._steps > self._step_limit:
            raise SimoRuntimeError(
                f"Execution step limit ({self._step_limit}) exceeded",
                self._filename,
                line,
                column,
            )

    def _execute(self, stmt: ast.Stmt) -> Any:
        self._tick(stmt.line, stmt.column)

        if isinstance(stmt, ast.VarDecl):
            value = self._evaluate(stmt.initializer) if stmt.initializer else None
            if stmt.is_const:
                self._env.define(
                    stmt.name,
                    value,
                    is_const=True,
                    line=stmt.line,
                    column=stmt.column,
                    filename=self._filename,
                )
            else:
                self._env.declare_or_assign(
                    stmt.name,
                    value,
                    line=stmt.line,
                    column=stmt.column,
                    filename=self._filename,
                )
            return None

        if isinstance(stmt, ast.Assign):
            value = self._evaluate(stmt.value)
            self._env.assign(
                stmt.name,
                value,
                line=stmt.line,
                column=stmt.column,
                filename=self._filename,
            )
            return None

        if isinstance(stmt, ast.ExprStmt):
            return self._evaluate(stmt.expression)

        if isinstance(stmt, ast.ActionDecl):
            self._define_user_function(stmt)
            return None

        if isinstance(stmt, ast.ReturnStmt):
            if self._env is self._globals:
                raise SimoRuntimeError(
                    "'return' used outside of a function",
                    self._filename,
                    stmt.line,
                    stmt.column,
                )
            value = self._evaluate(stmt.value) if stmt.value is not None else None
            raise ReturnSignal(value)

        if isinstance(stmt, ast.IfStmt):
            for condition, body in stmt.branches:
                if self._is_truthy(self._evaluate(condition)):
                    self._execute_block(body)
                    return None
            if stmt.else_body:
                self._execute_block(stmt.else_body)
            return None

        if isinstance(stmt, ast.LoopTimes):
            count_value = self._evaluate(stmt.count)
            count = self._as_non_negative_int(
                count_value,
                stmt.line,
                stmt.column,
                "loop count",
            )
            for _ in range(count):
                self._execute_block(stmt.body)
            return None

        if isinstance(stmt, ast.LoopWhile):
            while self._is_truthy(self._evaluate(stmt.condition)):
                self._execute_block(stmt.body)
            return None

        raise SimoRuntimeError(
            f"Unknown statement type: {type(stmt).__name__}",
            self._filename,
            stmt.line,
            stmt.column,
        )

    def _execute_block(self, statements: list[ast.Stmt]) -> None:
        for statement in statements:
            self._execute(statement)

    def _define_user_function(self, decl: ast.ActionDecl) -> None:
        def callable_func(*args: Any) -> Any:
            if len(args) != len(decl.params):
                raise SimoRuntimeError(
                    f"Function '{decl.name}' expects {len(decl.params)} argument(s), got {len(args)}",
                    self._filename,
                    decl.line,
                    decl.column,
                )

            previous_env = self._env
            local_env = self._globals.child()
            for param, value in zip(decl.params, args):
                local_env.define(param, value)
            self._env = local_env

            try:
                self._execute_block(decl.body)
                return None
            except ReturnSignal as signal:
                return signal.value
            finally:
                self._env = previous_env

        self._globals.define_function(decl.name, callable_func)

    def _evaluate(self, expr: ast.Expr | None) -> Any:
        if expr is None:
            return None

        self._tick(expr.line, expr.column)

        if isinstance(expr, ast.Literal):
            return expr.value

        if isinstance(expr, ast.Variable):
            return self._env.get(
                expr.name,
                line=expr.line,
                column=expr.column,
                filename=self._filename,
            )

        if isinstance(expr, ast.Unary):
            value = self._evaluate(expr.operand)
            if expr.operator == "not":
                return not self._is_truthy(value)
            if expr.operator == "-":
                number = self._as_number(value, expr.line, expr.column, "operand of '-'")
                return -number
            raise SimoRuntimeError(
                f"Unknown unary operator '{expr.operator}'",
                self._filename,
                expr.line,
                expr.column,
            )

        if isinstance(expr, ast.Binary):
            if expr.operator == "and":
                left = self._evaluate(expr.left)
                if not self._is_truthy(left):
                    return left
                return self._evaluate(expr.right)
            if expr.operator == "or":
                left = self._evaluate(expr.left)
                if self._is_truthy(left):
                    return left
                return self._evaluate(expr.right)

            left = self._evaluate(expr.left)
            right = self._evaluate(expr.right)
            return self._evaluate_binary(expr.operator, left, right, expr.line, expr.column)

        if isinstance(expr, ast.Call):
            args = [self._evaluate(arg) for arg in expr.arguments]
            if expr.callee == "say":
                if len(args) != 1:
                    raise SimoRuntimeError(
                        f"Function 'say' expects 1 argument, got {len(args)}",
                        self._filename,
                        expr.line,
                        expr.column,
                    )
                self._globals.get_function("say")
                say = self._globals.functions["say"]
                say(args[0])
                return None

            func = self._env.get_function(
                expr.callee,
                line=expr.line,
                column=expr.column,
                filename=self._filename,
            )
            return func(*args)

        raise SimoRuntimeError(
            f"Unknown expression type: {type(expr).__name__}",
            self._filename,
            expr.line,
            expr.column,
        )

    def _evaluate_binary(
        self,
        operator: str,
        left: Any,
        right: Any,
        line: int,
        column: int,
    ) -> Any:
        if operator == "+":
            if isinstance(left, str) or isinstance(right, str):
                return self._to_string(left) + self._to_string(right)
            left_num = self._as_number(left, line, column, "left operand of '+'")
            right_num = self._as_number(right, line, column, "right operand of '+'")
            return left_num + right_num

        if operator == "-":
            left_num = self._as_number(left, line, column, "left operand of '-'")
            right_num = self._as_number(right, line, column, "right operand of '-'")
            return left_num - right_num

        if operator == "*":
            left_num = self._as_number(left, line, column, "left operand of '*'")
            right_num = self._as_number(right, line, column, "right operand of '*'")
            return left_num * right_num

        if operator == "/":
            left_num = self._as_number(left, line, column, "left operand of '/'")
            right_num = self._as_number(right, line, column, "right operand of '/'")
            if right_num == 0:
                raise SimoRuntimeError("Division by zero", self._filename, line, column)
            return left_num / right_num

        if operator in ("==", "!="):
            result = self._compare_equality(left, right, line, column)
            return result if operator == "==" else not result
        if operator == "<":
            return self._compare_numbers(left, right, line, column) < 0
        if operator == "<=":
            return self._compare_numbers(left, right, line, column) <= 0
        if operator == ">":
            return self._compare_numbers(left, right, line, column) > 0
        if operator == ">=":
            return self._compare_numbers(left, right, line, column) >= 0

        raise SimoRuntimeError(
            f"Unknown binary operator '{operator}'",
            self._filename,
            line,
            column,
        )

    def _compare_equality(self, left: Any, right: Any, line: int, column: int) -> bool:
        self._validate_equality_operand(left, line, column, "left operand of equality comparison")
        self._validate_equality_operand(right, line, column, "right operand of equality comparison")
        return left == right

    def _validate_equality_operand(
        self,
        value: Any,
        line: int,
        column: int,
        context: str,
    ) -> None:
        if isinstance(value, (str, int, float, bool)):
            return
        raise SimoRuntimeError(
            f"Expected string, number, or boolean for {context}, got {self._type_name(value)}",
            self._filename,
            line,
            column,
        )

    def _compare_numbers(self, left: Any, right: Any, line: int, column: int) -> int:
        left_num = self._as_number(left, line, column, "comparison left operand")
        right_num = self._as_number(right, line, column, "comparison right operand")
        if left_num < right_num:
            return -1
        if left_num > right_num:
            return 1
        return 0

    def _is_truthy(self, value: Any) -> bool:
        return bool(value)

    def _as_number(self, value: Any, line: int, column: int, context: str) -> int | float:
        if isinstance(value, bool):
            raise SimoRuntimeError(
                f"Expected number for {context}, got boolean",
                self._filename,
                line,
                column,
            )
        if isinstance(value, (int, float)):
            return value
        raise SimoRuntimeError(
            f"Expected number for {context}, got {self._type_name(value)}",
            self._filename,
            line,
            column,
        )

    def _as_non_negative_int(
        self,
        value: Any,
        line: int,
        column: int,
        context: str,
    ) -> int:
        if isinstance(value, bool):
            raise SimoRuntimeError(
                f"Expected non-negative integer for {context}, got boolean",
                self._filename,
                line,
                column,
            )
        if isinstance(value, int) and value >= 0:
            return value
        if isinstance(value, float) and value.is_integer() and value >= 0:
            return int(value)
        raise SimoRuntimeError(
            f"Expected non-negative integer for {context}, got {self._type_name(value)}",
            self._filename,
            line,
            column,
        )

    def _to_string(self, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def _type_name(self, value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "number"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        return type(value).__name__
