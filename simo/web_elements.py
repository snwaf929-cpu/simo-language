"""HTML element and CSS generation for Simo."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

from simo import ast_nodes as ast
from simo.errors import BuildError


class WebElementsMixin:
    def _compile_element(self, element: ast.ShowElement) -> None:
        self.element_counter += 1
        element_id = self.element_id_by_node[id(element)]
        js_id = json.dumps(element_id)
        variable = f"_simoElement{self.element_counter}"
        tag = {
            "heading": "h1",
            "text": "p",
            "button": "button",
            "image": "img",
            "input": "input",
        }.get(element.kind, "div")
        self.element_lines.append(f"const {variable} = document.createElement({json.dumps(tag)});")
        self.element_lines.append(f"{variable}.id = {js_id};")

        if element.kind == "image":
            if element.content is not None:
                self.element_lines.append(f"{variable}.src = {self._expression(element.content)};")
            alt = element.attributes.get("alt", "")
            self.element_lines.append(f"{variable}.alt = {json.dumps(str(alt))};")
        elif element.kind == "input":
            self.element_lines.append(f"{variable}.type = 'text';")
            placeholder = element.attributes.get("placeholder")
            if placeholder is not None:
                self.element_lines.append(f"{variable}.placeholder = {json.dumps(str(placeholder))};")
        elif element.content is not None:
            self.element_lines.append(f"{variable}.textContent = Simo.text({self._expression(element.content)});")

        self.element_lines.append(f"$el('simo-root').appendChild({variable});")
        style = self._style_rule(element_id, element.attributes)
        if style:
            self.styles.append(style)

        for event in element.events:
            dom_event = "click" if event.name == "clicked" else "input"
            body = self._block(event.body, 2)
            self.event_lines.append(f"$el({js_id}).addEventListener({json.dumps(dom_event)}, () => {{")
            self.event_lines.extend([f"  {line}" for line in body])
            self.event_lines.append("});")

        watched = element.attributes.get("reactive_when")
        if watched and element.content is not None:
            expression = self._expression(element.content)
            self.event_lines.append(
                f"$el({json.dumps(str(watched))}).addEventListener('input', () => {{ $el({js_id}).textContent = Simo.text({expression}); }});"
            )

    def _style_rule(self, element_id: str, attributes: dict[str, Any]) -> str:
        declarations: list[str] = []
        for raw_key, value in attributes.items():
            key = raw_key.lower().replace("_", " ")
            if key in {"placeholder", "alt", "reactive when"}:
                continue
            if key == "size":
                if isinstance(value, tuple):
                    declarations.extend([f"width: {value[0]}px", f"height: {value[1]}px"])
                else:
                    font_size = {"small": "0.85rem", "medium": "1rem", "big": "2rem", "large": "2rem"}.get(str(value).lower())
                    if font_size:
                        declarations.append(f"font-size: {font_size}")
                continue
            if key == "rounded":
                declarations.append("border-radius: 999px" if value is True else f"border-radius: {value}")
                continue
            if key == "color":
                declarations.append(f"color: {value}")
                continue
            if key in {"background", "background color"}:
                declarations.append(f"background: {value}")
                continue
            if key == "align":
                declarations.append(f"text-align: {value}")
                continue
            if key == "position" and str(value).lower() == "center":
                declarations.append("margin-left: auto")
                declarations.append("margin-right: auto")
                continue
            if key == "visible" and str(value).lower() in {"false", "no"}:
                declarations.append("display: none")
                continue
            css_key = {
                "font size": "font-size",
                "text align": "text-align",
                "border radius": "border-radius",
            }.get(key, key.replace(" ", "-"))
            if re.fullmatch(r"[a-z-]+", css_key):
                rendered = str(value)
                if isinstance(value, (int, float)) and css_key not in {"opacity", "z-index", "font-weight"}:
                    rendered += "px"
                declarations.append(f"{css_key}: {rendered}")
        if not declarations:
            return ""
        return f"#{self._css_escape(element_id)} {{ " + "; ".join(declarations) + "; }"

    def _css_escape(self, value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_-]", lambda match: "\\" + match.group(0), value)

    # JavaScript generation --------------------------------------------
