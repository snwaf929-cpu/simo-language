"""Token definitions for the Simo lexer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    # punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()

    # operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()

    # literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    DIMENSION = auto()

    # core language
    SET = auto()
    FIX = auto()
    ACTION = auto()
    RETURN = auto()
    END = auto()
    IF = auto()
    ELSE = auto()
    LOOP = auto()
    TIMES = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    BREAK = auto()
    CONTINUE = auto()
    IMPORT = auto()
    ATTEMPT = auto()
    IT = auto()
    FAILS = auto()

    # logical and primitive keywords
    AND = auto()
    OR = auto()
    NOT = auto()
    IS = auto()
    TRUE = auto()
    FALSE = auto()
    YES = auto()
    NO = auto()
    NULL = auto()

    # UI / app language
    PAGE = auto()
    SHOW = auto()
    HEADING = auto()
    TEXT = auto()
    BUTTON = auto()
    IMAGE = auto()
    INPUT = auto()
    BOX = auto()
    NOTIFICATION = auto()
    NAMED = auto()
    PLACEHOLDER = auto()
    SIZE = auto()
    WHEN = auto()
    CLICKED = auto()
    CHANGES = auto()
    CHANGE = auto()
    OF = auto()
    TO = auto()

    NEWLINE = auto()
    EOF = auto()


KEYWORDS: dict[str, TokenType] = {
    "set": TokenType.SET,
    "fix": TokenType.FIX,
    "action": TokenType.ACTION,
    "return": TokenType.RETURN,
    "end": TokenType.END,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "loop": TokenType.LOOP,
    "times": TokenType.TIMES,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "import": TokenType.IMPORT,
    "attempt": TokenType.ATTEMPT,
    "it": TokenType.IT,
    "fails": TokenType.FAILS,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "is": TokenType.IS,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "yes": TokenType.YES,
    "no": TokenType.NO,
    "null": TokenType.NULL,
    "page": TokenType.PAGE,
    "show": TokenType.SHOW,
    "heading": TokenType.HEADING,
    "text": TokenType.TEXT,
    "button": TokenType.BUTTON,
    "image": TokenType.IMAGE,
    "input": TokenType.INPUT,
    "box": TokenType.BOX,
    "notification": TokenType.NOTIFICATION,
    "named": TokenType.NAMED,
    "placeholder": TokenType.PLACEHOLDER,
    "size": TokenType.SIZE,
    "when": TokenType.WHEN,
    "clicked": TokenType.CLICKED,
    "changes": TokenType.CHANGES,
    "change": TokenType.CHANGE,
    "of": TokenType.OF,
    "to": TokenType.TO,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
    literal: Any = None
