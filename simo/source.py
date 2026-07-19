"""Source loading, parsing, and import expansion helpers."""

from __future__ import annotations

from pathlib import Path

from simo import ast_nodes as ast
from simo.errors import BuildError
from simo.lexer import Lexer
from simo.parser import Parser


def parse_source(source: str, filename: str = "<memory>") -> ast.Program:
    return Parser(Lexer(source, filename).tokenize(), filename).parse()


def parse_file(path: Path) -> ast.Program:
    path = path.resolve()
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"Cannot read source file: {exc}", str(path)) from exc
    return parse_source(source, str(path))


def load_program(path: Path) -> ast.Program:
    """Parse a program and inline imports in dependency order."""

    path = path.resolve()
    seen: set[Path] = set()
    loading: list[Path] = []

    def visit(current: Path) -> list[ast.Stmt]:
        current = current.resolve()
        if current in seen:
            return []
        if current in loading:
            chain = " -> ".join(str(item) for item in [*loading, current])
            raise BuildError(f"Import cycle detected: {chain}", str(current))
        if not current.exists():
            raise BuildError(f"Imported file does not exist: {current}", str(current))

        loading.append(current)
        program = parse_file(current)
        statements: list[ast.Stmt] = []
        for statement in program.statements:
            if isinstance(statement, ast.ImportStmt):
                statements.extend(visit(current.parent / statement.path))
            else:
                statements.append(statement)
        loading.pop()
        seen.add(current)
        return statements

    return ast.Program(statements=visit(path))
