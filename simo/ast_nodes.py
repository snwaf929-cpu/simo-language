"""Abstract syntax tree nodes shared by the interpreter and compilers."""

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
class ImportStmt(Stmt):
    path: str = ""


@dataclass
class VarDecl(Stmt):
    name: str = ""
    initializer: Expr | None = None
    is_const: bool = False


@dataclass
class Assign(Stmt):
    target: Expr | None = None
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


@dataclass
class LoopFor(Stmt):
    name: str = ""
    iterable: Expr | None = None
    body: list[Stmt] = field(default_factory=list)


@dataclass
class BreakStmt(Stmt):
    pass


@dataclass
class ContinueStmt(Stmt):
    pass


@dataclass
class AttemptStmt(Stmt):
    body: list[Stmt] = field(default_factory=list)
    failure_body: list[Stmt] = field(default_factory=list)


@dataclass
class PageDecl(Stmt):
    title: Expr | None = None
    size: tuple[int, int] | None = None
    body: list[Stmt] = field(default_factory=list)


@dataclass
class UiEvent(Node):
    name: str = ""
    body: list[Stmt] = field(default_factory=list)


@dataclass
class ShowElement(Stmt):
    kind: str = "text"
    content: Expr | None = None
    name: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[UiEvent] = field(default_factory=list)


@dataclass
class ChangeElement(Stmt):
    property_name: str = ""
    target_name: str = ""
    value: Expr | None = None


@dataclass
class ShowNotification(Stmt):
    value: Expr | None = None


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
class ListLiteral(Expr):
    items: list[Expr] = field(default_factory=list)


@dataclass
class ObjectLiteral(Expr):
    items: list[tuple[str, Expr]] = field(default_factory=list)


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
    callee: Expr | None = None
    arguments: list[Expr] = field(default_factory=list)


@dataclass
class Get(Expr):
    object: Expr | None = None
    name: str = ""


@dataclass
class Index(Expr):
    object: Expr | None = None
    index: Expr | None = None
