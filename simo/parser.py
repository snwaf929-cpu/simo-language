"""Recursive-descent parser for the Simo language."""

from simo import ast_nodes as ast
from simo.parser_control import ParserControlMixin
from simo.parser_expressions import ParserExpressionMixin
from simo.parser_statements import ParserStatementMixin
from simo.parser_tokens import ParserTokenMixin
from simo.parser_ui import ParserUiMixin
from simo.tokens import Token


class Parser(
    ParserUiMixin,
    ParserControlMixin,
    ParserStatementMixin,
    ParserExpressionMixin,
    ParserTokenMixin,
):
    def __init__(self, tokens: list[Token], filename: str = "<stdin>") -> None:
        self.tokens = tokens
        self.filename = filename
        self.current = 0

    def parse(self) -> ast.Program:
        statements: list[ast.Stmt] = []
        self._skip_newlines()
        while not self._at_end():
            statements.append(self._declaration())
            self._skip_newlines()
        return ast.Program(statements=statements)
