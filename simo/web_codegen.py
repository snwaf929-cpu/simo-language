"""JavaScript code generation for Simo."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

from simo import ast_nodes as ast
from simo.errors import BuildError


class WebCodegenMixin:
    def _block(self, statements: list[ast.Stmt], indent: int) -> list[str]:
        output: list[str] = []
        for statement in statements:
            output.extend(self._statement(statement, indent))
        return output

    def _statement(self, statement: ast.Stmt, indent: int) -> list[str]:
        pad = "  " * indent
        if isinstance(statement, ast.ImportStmt):
            return []
        if isinstance(statement, ast.VarDecl):
            keyword = "const" if statement.is_const else "let"
            return [f"{pad}{keyword} {statement.name} = {self._expression(statement.initializer)};"]
        if isinstance(statement, ast.Assign):
            return [f"{pad}{self._target(statement.target)} = {self._expression(statement.value)};"]
        if isinstance(statement, ast.ExprStmt):
            return [f"{pad}{self._expression(statement.expression)};"]
        if isinstance(statement, ast.ActionDecl):
            lines = [f"{pad}function {statement.name}({', '.join(statement.params)}) {{"]
            lines.extend(self._block(statement.body, indent + 1))
            lines.append(f"{pad}}}")
            return lines
        if isinstance(statement, ast.ReturnStmt):
            suffix = "" if statement.value is None else " " + self._expression(statement.value)
            return [f"{pad}return{suffix};"]
        if isinstance(statement, ast.IfStmt):
            lines: list[str] = []
            for index, (condition, body) in enumerate(statement.branches):
                prefix = "if" if index == 0 else "else if"
                lines.append(f"{pad}{prefix} ({self._expression(condition)}) {{")
                lines.extend(self._block(body, indent + 1))
                lines.append(f"{pad}}}")
            if statement.else_body:
                lines[-1] += " else {"
                lines.extend(self._block(statement.else_body, indent + 1))
                lines.append(f"{pad}}}")
            return lines
        if isinstance(statement, ast.LoopTimes):
            name = f"_simoIndex{statement.line}_{statement.column}"
            lines = [f"{pad}for (let {name} = 0; {name} < Number({self._expression(statement.count)}); {name}++) {{"]
            lines.extend(self._block(statement.body, indent + 1))
            lines.append(f"{pad}}}")
            return lines
        if isinstance(statement, ast.LoopWhile):
            lines = [f"{pad}while ({self._expression(statement.condition)}) {{"]
            lines.extend(self._block(statement.body, indent + 1))
            lines.append(f"{pad}}}")
            return lines
        if isinstance(statement, ast.LoopFor):
            lines = [f"{pad}for (const {statement.name} of Simo.iter({self._expression(statement.iterable)})) {{"]
            lines.extend(self._block(statement.body, indent + 1))
            lines.append(f"{pad}}}")
            return lines
        if isinstance(statement, ast.BreakStmt):
            return [f"{pad}break;"]
        if isinstance(statement, ast.ContinueStmt):
            return [f"{pad}continue;"]
        if isinstance(statement, ast.AttemptStmt):
            lines = [f"{pad}try {{"]
            lines.extend(self._block(statement.body, indent + 1))
            lines.append(f"{pad}}} catch (_simoError) {{")
            lines.append(f"{pad}  const error = Simo.text(_simoError?.message ?? _simoError);")
            lines.extend(self._block(statement.failure_body, indent + 1))
            lines.append(f"{pad}}}")
            return lines
        if isinstance(statement, ast.ChangeElement):
            target = json.dumps(statement.target_name)
            value = self._expression(statement.value)
            property_name = statement.property_name
            if property_name in {"text", "heading"}:
                return [f"{pad}$el({target}).textContent = Simo.text({value});"]
            if property_name == "color":
                return [f"{pad}$el({target}).style.color = Simo.text({value});"]
            if property_name in {"background", "background_color"}:
                return [f"{pad}$el({target}).style.background = Simo.text({value});"]
            if property_name == "value":
                return [f"{pad}$el({target}).value = Simo.text({value});"]
            if property_name == "visible":
                return [f"{pad}$el({target}).style.display = Simo.bool({value}) ? '' : 'none';"]
            return [f"{pad}$el({target}).style[{json.dumps(property_name)}] = Simo.text({value});"]
        if isinstance(statement, ast.ShowNotification):
            return [f"{pad}Simo.notify({self._expression(statement.value)});"]
        if isinstance(statement, ast.ShowElement):
            return []
        if isinstance(statement, ast.PageDecl):
            return []
        raise BuildError(
            f"Web compiler does not support {type(statement).__name__}",
            str(self.source_path),
            statement.line,
            statement.column,
        )

    def _target(self, expression: ast.Expr | None) -> str:
        if isinstance(expression, ast.Variable):
            return expression.name
        if isinstance(expression, ast.Get):
            if isinstance(expression.object, ast.Variable) and expression.object.name in self.element_ids:
                return f"$el({json.dumps(expression.object.name)}).{expression.name}"
            return f"{self._expression(expression.object)}[{json.dumps(expression.name)}]"
        if isinstance(expression, ast.Index):
            return f"{self._expression(expression.object)}[{self._expression(expression.index)}]"
        raise BuildError("Invalid assignment target", str(self.source_path))

    def _expression(self, expression: ast.Expr | None) -> str:
        if expression is None:
            return "null"
        if isinstance(expression, ast.Literal):
            if isinstance(expression.value, tuple):
                return json.dumps(f"{expression.value[0]}x{expression.value[1]}")
            return json.dumps(expression.value, ensure_ascii=False)
        if isinstance(expression, ast.Variable):
            builtin = {
                "say": "console.log",
                "text": "Simo.text",
                "number": "Simo.number",
                "bool": "Simo.bool",
                "len": "Simo.len",
                "range": "Simo.range",
                "add": "Simo.add",
                "remove": "Simo.remove",
                "contains": "Simo.contains",
                "keys": "Simo.keys",
                "values": "Simo.values",
                "assert": "Simo.assert",
                "save": "Simo.save",
                "load": "Simo.load",
                "random": "Math.random",
                "round": "Math.round",
                "floor": "Math.floor",
                "ceil": "Math.ceil",
                "pi": "Math.PI",
            }.get(expression.name)
            return builtin or expression.name
        if isinstance(expression, ast.ListLiteral):
            return "[" + ", ".join(self._expression(item) for item in expression.items) + "]"
        if isinstance(expression, ast.ObjectLiteral):
            return "{" + ", ".join(
                f"{json.dumps(key)}: {self._expression(value)}" for key, value in expression.items
            ) + "}"
        if isinstance(expression, ast.Unary):
            operator = "!" if expression.operator == "not" else expression.operator
            return f"({operator}{self._expression(expression.operand)})"
        if isinstance(expression, ast.Binary):
            left = self._expression(expression.left)
            right = self._expression(expression.right)
            if expression.operator == "+":
                return f"Simo.addValues({left}, {right})"
            if expression.operator in {"==", "!="}:
                equal = f"Simo.equal({left}, {right})"
                return equal if expression.operator == "==" else f"(!{equal})"
            operator = {"and": "&&", "or": "||"}.get(expression.operator, expression.operator)
            return f"({left} {operator} {right})"
        if isinstance(expression, ast.Call):
            return f"{self._expression(expression.callee)}(" + ", ".join(
                self._expression(argument) for argument in expression.arguments
            ) + ")"
        if isinstance(expression, ast.Get):
            if isinstance(expression.object, ast.Variable) and expression.object.name in self.element_ids:
                return f"$el({json.dumps(expression.object.name)}).{expression.name}"
            return f"Simo.get({self._expression(expression.object)}, {json.dumps(expression.name)})"
        if isinstance(expression, ast.Index):
            return f"{self._expression(expression.object)}[{self._expression(expression.index)}]"
        raise BuildError(
            f"Web compiler does not support expression {type(expression).__name__}",
            str(self.source_path),
            expression.line,
            expression.column,
        )
