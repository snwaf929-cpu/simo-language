"""HTML/CSS/JavaScript and installable-app compiler for Simo pages."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from simo import ast_nodes as ast
from simo.errors import BuildError
from simo.source import load_program
from simo.web_codegen import WebCodegenMixin
from simo.web_elements import WebElementsMixin
from simo.web_outputs import WebOutputsMixin
from simo.web_runtime import _BASE_CSS, _RUNTIME_JS


class WebCompiler(WebElementsMixin, WebCodegenMixin, WebOutputsMixin):
    def __init__(self, program: ast.Program, source_path: Path) -> None:
        self.program = program
        self.source_path = source_path.resolve()
        self.page = self._find_page()
        self.element_counter = 0
        self.element_ids: set[str] = set()
        self.element_id_by_node: dict[int, str] = {}
        self.styles: list[str] = []
        self.element_lines: list[str] = []
        self.event_lines: list[str] = []

    def _find_page(self) -> ast.PageDecl:
        pages = [statement for statement in self.program.statements if isinstance(statement, ast.PageDecl)]
        if not pages:
            raise BuildError(
                "Web/PWA builds require one 'page ... { }' declaration",
                str(self.source_path),
            )
        if len(pages) > 1:
            raise BuildError("A build can contain only one page declaration", str(self.source_path))
        return pages[0]

    def compile(self, output_dir: Path, target: str = "web") -> Path:
        output_dir = output_dir.resolve()
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        title = self._literal_title(self.page.title)
        body_statements = [
            statement
            for statement in self.program.statements
            if not isinstance(statement, (ast.PageDecl, ast.ImportStmt))
        ] + self.page.body

        ui_statements = [statement for statement in body_statements if isinstance(statement, ast.ShowElement)]
        self._reserve_element_ids(ui_statements)

        setup_lines: list[str] = []
        for statement in body_statements:
            if not isinstance(statement, ast.ShowElement):
                setup_lines.extend(self._statement(statement, 1))

        for element in ui_statements:
            self._compile_element(element)

        page_style = ""
        if self.page.size:
            width, height = self.page.size
            page_style = f"#simo-root {{ width: min(100%, {width}px); min-height: {height}px; }}\n"

        app_js = "\n".join(
            [
                _RUNTIME_JS,
                "document.addEventListener('DOMContentLoaded', () => {",
                *setup_lines,
                *[f"  {line}" for line in self.element_lines],
                *[f"  {line}" for line in self.event_lines],
                "});",
                "",
            ]
        )
        styles_css = _BASE_CSS + "\n" + page_style + "\n".join(self.styles) + "\n"
        index_html = self._html(title, target)

        (output_dir / "index.html").write_text(index_html, encoding="utf-8")
        (output_dir / "styles.css").write_text(styles_css, encoding="utf-8")
        (output_dir / "app.js").write_text(app_js, encoding="utf-8")
        self._copy_assets(output_dir)

        if target in {"pwa", "app"}:
            self._write_pwa(output_dir, title)
        return output_dir

    def _literal_title(self, expression: ast.Expr | None) -> str:
        if isinstance(expression, ast.Literal) and isinstance(expression.value, str):
            return expression.value
        raise BuildError("Page title must currently be quoted text", str(self.source_path))

    def _html(self, title: str, target: str) -> str:
        manifest = '<link rel="manifest" href="manifest.webmanifest">' if target in {"pwa", "app"} else ""
        service_worker = """
<script>
if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js'));
</script>""" if target in {"pwa", "app"} else ""
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#17191c">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="styles.css">
  {manifest}
</head>
<body>
  <main class="simo-shell"><section id="simo-root" class="simo-app"></section></main>
  <script src="app.js" defer></script>
  {service_worker}
</body>
</html>
"""

    def _reserve_element_ids(self, elements: list[ast.ShowElement]) -> None:
        for element in elements:
            self.element_counter += 1
            element_id = element.name or f"simo-{element.kind}-{self.element_counter}"
            if element_id in self.element_ids:
                raise BuildError(
                    f"Duplicate element name '{element_id}'",
                    str(self.source_path),
                    element.line,
                    element.column,
                )
            self.element_ids.add(element_id)
            self.element_id_by_node[id(element)] = element_id
        self.element_counter = 0



def build(source_path: Path, output_dir: Path, target: str = "web") -> Path:
    if target == "app":
        target = "pwa"
    if target not in {"web", "pwa"}:
        raise BuildError(f"Unknown browser build target '{target}'", str(source_path))
    program = load_program(source_path)
    return WebCompiler(program, source_path).compile(output_dir, target)
