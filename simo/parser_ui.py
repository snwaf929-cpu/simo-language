"""Page and UI parsing for Simo."""

from typing import Any

from simo import ast_nodes as ast
from simo.errors import ParseError
from simo.tokens import Token, TokenType


class ParserUiMixin:
    def _page_declaration(self) -> ast.PageDecl:
        keyword = self._previous()
        title = self._expression()
        size: tuple[int, int] | None = None
        if self._match(TokenType.SIZE):
            dimension = self._consume(
                TokenType.DIMENSION, "Expected dimensions such as 800x600 after 'size'"
            )
            size = dimension.literal
        self._consume(TokenType.LBRACE, "Expected '{' after page declaration")
        self._line_end()
        body = self._block_until(TokenType.RBRACE)
        self._consume(TokenType.RBRACE, "Expected '}' after page body")
        self._line_end()
        return ast.PageDecl(
            title=title, size=size, body=body, line=keyword.line, column=keyword.column
        )

    def _show_statement(self) -> ast.Stmt:
        keyword = self._previous()
        if self._match(TokenType.NOTIFICATION):
            value = self._expression()
            self._line_end()
            return ast.ShowNotification(value=value, line=keyword.line, column=keyword.column)

        input_element = self._match(TokenType.INPUT)
        if input_element:
            self._match(TokenType.BOX)
            kind = "input"
        else:
            allowed = (
                TokenType.HEADING,
                TokenType.TEXT,
                TokenType.BUTTON,
                TokenType.IMAGE,
                TokenType.IDENTIFIER,
            )
            if not self._check(*allowed):
                self._error("Expected element type after 'show'")
            kind = self._word(self._advance())

        content: ast.Expr | None = None
        if not input_element and not self._check(
            TokenType.NAMED,
            TokenType.PLACEHOLDER,
            TokenType.SIZE,
            TokenType.LBRACE,
            TokenType.NEWLINE,
            TokenType.EOF,
        ):
            content = self._expression()

        name: str | None = None
        attributes: dict[str, Any] = {}
        events: list[ast.UiEvent] = []

        while not self._check(TokenType.LBRACE, TokenType.NEWLINE, TokenType.EOF):
            if self._match(TokenType.NAMED):
                name = self._consume(TokenType.IDENTIFIER, "Expected element name").lexeme
            elif self._match(TokenType.PLACEHOLDER):
                attributes["placeholder"] = self._attribute_atom()
            elif self._match(TokenType.SIZE):
                attributes["size"] = self._attribute_atom()
            elif self._match(TokenType.WHEN):
                watched = self._consume(TokenType.IDENTIFIER, "Expected input name after 'when'")
                self._consume(TokenType.CHANGES, "Expected 'changes' after input name")
                attributes["reactive_when"] = watched.lexeme
            else:
                token = self._advance()
                attributes[self._word(token)] = True

        if self._match(TokenType.LBRACE):
            self._line_end()
            closed = False
            while not self._at_end() and not self._check(TokenType.RBRACE):
                self._skip_newlines()
                if self._check(TokenType.RBRACE):
                    break
                if self._match(TokenType.WHEN):
                    event_token = self._advance()
                    event_name = self._word(event_token)
                    if event_name not in {"clicked", "changes"}:
                        self._error("Supported events are 'clicked' and 'changes'", event_token)
                    self._match(TokenType.COLON)
                    self._line_end(required=True)
                    event_body: list[ast.Stmt] = []
                    self._skip_newlines()
                    while not self._at_end() and not self._check(
                        TokenType.END, TokenType.RBRACE
                    ):
                        event_body.append(self._declaration())
                        self._skip_newlines()
                    if self._match(TokenType.END):
                        self._line_end()
                    else:
                        closed = True
                    events.append(
                        ast.UiEvent(
                            name=event_name,
                            body=event_body,
                            line=event_token.line,
                            column=event_token.column,
                        )
                    )
                    if closed:
                        break
                    continue

                key_token = self._advance()
                key = self._word(key_token)
                value_tokens: list[Token] = []
                while not self._check(TokenType.NEWLINE, TokenType.RBRACE, TokenType.EOF):
                    value_tokens.append(self._advance())
                attributes[key] = self._attribute_value(value_tokens)
                self._line_end()

            self._consume(TokenType.RBRACE, "Expected '}' after element block")
            self._line_end()
        else:
            self._line_end()

        if kind == "input" and name is None:
            self._error("Input elements require 'named <identifier>'", keyword)

        return ast.ShowElement(
            kind=kind,
            content=content,
            name=name,
            attributes=attributes,
            events=events,
            line=keyword.line,
            column=keyword.column,
        )

    def _attribute_atom(self) -> Any:
        token = self._advance()
        if token.type in {TokenType.STRING, TokenType.NUMBER, TokenType.DIMENSION}:
            return token.literal
        return token.lexeme

    def _attribute_value(self, tokens: list[Token]) -> Any:
        if not tokens:
            return True
        if len(tokens) == 1:
            token = tokens[0]
            if token.type in {TokenType.STRING, TokenType.NUMBER, TokenType.DIMENSION}:
                return token.literal
            return token.lexeme
        return " ".join(str(token.literal if token.literal is not None else token.lexeme) for token in tokens)

    def _change_statement(self) -> ast.ChangeElement:
        keyword = self._previous()
        property_token = self._advance()
        if property_token.type in {TokenType.NEWLINE, TokenType.EOF}:
            self._error("Expected property name after 'change'", property_token)
        self._consume(TokenType.OF, "Expected 'of' after property name")
        target = self._consume(TokenType.IDENTIFIER, "Expected element name after 'of'")
        self._consume(TokenType.TO, "Expected 'to' before the new value")
        value = self._expression()
        self._line_end()
        return ast.ChangeElement(
            property_name=self._word(property_token),
            target_name=target.lexeme,
            value=value,
            line=keyword.line,
            column=keyword.column,
        )

    def _expression_or_assignment(self) -> ast.Stmt:
        expression = self._expression()
        if self._match(TokenType.ASSIGN):
            if not isinstance(expression, (ast.Variable, ast.Get, ast.Index)):
                self._error("Invalid assignment target", self._previous())
            value = self._expression()
            self._line_end()
            return ast.Assign(
                target=expression,
                value=value,
                line=expression.line,
                column=expression.column,
            )
        self._line_end()
        return ast.ExprStmt(
            expression=expression, line=expression.line, column=expression.column
        )
