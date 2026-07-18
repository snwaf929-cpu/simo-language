"""Abstract syntax tree node definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    line: int = 0
    column: int = 0


@dataclass
class Program(Node):
    statements: list[Stmt] = field(default_factory=list)


# Statements


@dataclass
class Stmt(Node):
    pass


@dataclass
class VarDecl(Stmt):
    name: str = ""
    initializer: Expr | None = None
    is_const: bool = False


@dataclass
class Assign(Stmt):
    name: str = ""
    value: Expr | None = None


@dataclass
class ExprStmt(Stmt):
    expression: Expr | None = None


@dataclass
class ActionDecl(Stmt):
    name: str = ""
    params: list[str] = field(default_factory=list)
    body: list[Stmt] = field(default_factory=list)


@dataclass
class ReturnStmt(Stmt):
    value: Expr | None = None


@dataclass
class IfStmt(Stmt):
    branches: list[tuple[Expr, list[Stmt]]] = field(default_factory=list)
    else_body: list[Stmt] = field(default_factory=list)


@dataclass
class LoopTimes(Stmt):
    count: Expr | None = None
    body: list[Stmt] = field(default_factory=list)


@dataclass
class LoopWhile(Stmt):
    condition: Expr | None = None
    body: list[Stmt] = field(default_factory=list)


# Expressions


@dataclass
class Expr(Node):
    pass


@dataclass
class Literal(Expr):
    value: Any = None


@dataclass
class Variable(Expr):
    name: str = ""


@dataclass
class Unary(Expr):
    operator: str = ""
    operand: Expr | None = None


@dataclass
class Binary(Expr):
    operator: str = ""
    left: Expr | None = None
    right: Expr | None = None


@dataclass
class Call(Expr):
    callee: str = ""
    arguments: list[Expr] = field(default_factory=list)
