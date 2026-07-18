"""Token definitions for the Sola lexer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
  # Single-character tokens
  LPAREN = auto()
  RPAREN = auto()
  COMMA = auto()
  PLUS = auto()
  MINUS = auto()
  STAR = auto()
  SLASH = auto()

  # Multi-character operators
  EQ = auto()       # ==
  NEQ = auto()      # !=
  LT = auto()       # <
  LTE = auto()      # <=
  GT = auto()       # >
  GTE = auto()      # >=
  ASSIGN = auto()   # =
  IS = auto()       # is (comparison alias for ==)
  IS_NOT = auto()   # is not (comparison alias for !=)

  # Literals
  IDENTIFIER = auto()
  NUMBER = auto()
  STRING = auto()

  # Keywords
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
  AND = auto()
  OR = auto()
  NOT = auto()
  TRUE = auto()
  FALSE = auto()
  YES = auto()
  NO = auto()

  # Structural
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
  "and": TokenType.AND,
  "or": TokenType.OR,
  "not": TokenType.NOT,
  "true": TokenType.TRUE,
  "false": TokenType.FALSE,
  "yes": TokenType.YES,
  "no": TokenType.NO,
  "is": TokenType.IS,
}


@dataclass(frozen=True)
class Token:
  type: TokenType
  lexeme: str
  line: int
  column: int
  literal: Any = None
