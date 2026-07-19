"""Native window lifecycle and Simo statement routing."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from simo import ast_nodes as ast
from simo.branding import bundled_icon
from simo.desktop_element import DesktopElement
from simo.desktop_native_api import DesktopNativeApiMixin
from simo.desktop_ui import DesktopUiMixin
from simo.environment import Environment
from simo.errors import BuildError
from simo.interpreter import Interpreter
from simo.project import load_project
from simo.source import load_program


class DesktopRuntime(DesktopNativeApiMixin, DesktopUiMixin, Interpreter):
    """Execute a Simo page as a native desktop window."""

    def __init__(
        self,
        source_path: Path,
        program: ast.Program | None = None,
        *,
        root: Any = None,
        tk_module: Any = None,
        filedialog_module: Any = None,
        messagebox_module: Any = None,
        simpledialog_module: Any = None,
    ) -> None:
        self.source_path = source_path.resolve()
        self.program = program or load_program(self.source_path)
        self.page = self._find_page()

        if tk_module is None:
            try:
                import tkinter as tk_module  # type: ignore[no-redef]
                from tkinter import filedialog as filedialog_module  # type: ignore[no-redef]
                from tkinter import messagebox as messagebox_module  # type: ignore[no-redef]
                from tkinter import simpledialog as simpledialog_module  # type: ignore[no-redef]
            except ImportError as exc:
                raise BuildError(
                    "Native desktop support requires Tk. Install a Python distribution "
                    "that includes tkinter, then run 'simo doctor'.",
                    str(self.source_path),
                ) from exc

        self.tk = tk_module
        self.filedialog = filedialog_module
        self.messagebox = messagebox_module
        self.simpledialog = simpledialog_module
        try:
            self.root = root or self.tk.Tk()
        except Exception as exc:
            raise BuildError(
                "Simo could not open a native window. Ensure a desktop session and Tk "
                "runtime are available.",
                str(self.source_path),
            ) from exc

        super().__init__(filename=str(self.source_path))
        self.elements: dict[str, DesktopElement] = {}
        self.images: list[Any] = []
        self.reactive_bindings: list[tuple[str, DesktopElement, ast.Expr, Environment]] = []
        self.default_input_color = "#17191c"
        self.placeholder_color = "#777777"
        self.container = self.tk.Frame(self.root, padx=24, pady=24)
        self.container.pack(fill="both", expand=True)
        self._configure_window()
        self._install_desktop_builtins()

    def _find_page(self) -> ast.PageDecl:
        pages = [statement for statement in self.program.statements if isinstance(statement, ast.PageDecl)]
        if not pages:
            raise BuildError(
                "Desktop programs require one 'page ... { }' declaration",
                str(self.source_path),
            )
        if len(pages) > 1:
            raise BuildError("A desktop app can contain only one page declaration", str(self.source_path))
        return pages[0]

    def _configure_window(self) -> None:
        title = self._evaluate_literal_title(self.page.title)
        self.root.title(title)
        if self.page.size:
            width, height = self.page.size
            self.root.geometry(f"{width}x{height}")
            try:
                self.root.minsize(min(width, 320), min(height, 240))
            except Exception:
                pass
        self._configure_window_icon()

    def _configure_window_icon(self) -> None:
        """Use project branding when supplied, otherwise Simo's built-in logo."""

        project = load_project(self.source_path)
        assets = project.root / "assets"
        png_icon = assets / "icon.png"
        if not png_icon.exists():
            png_icon = bundled_icon("png")
        try:
            image = self.tk.PhotoImage(file=str(png_icon))
            self.images.append(image)
            self.root.iconphoto(True, image)
        except Exception:
            pass

        if sys.platform == "win32":
            ico_icon = assets / "icon.ico"
            if not ico_icon.exists():
                ico_icon = bundled_icon("ico")
            try:
                self.root.iconbitmap(default=str(ico_icon))
            except Exception:
                pass

    def _evaluate_literal_title(self, expression: ast.Expr | None) -> str:
        if isinstance(expression, ast.Literal) and isinstance(expression.value, str):
            return expression.value
        raise BuildError("Desktop page title must be quoted text", str(self.source_path))

    def run(self) -> int:
        for statement in self.program.statements:
            if isinstance(statement, ast.PageDecl):
                continue
            self._execute(statement)
        for statement in self.page.body:
            self._execute(statement)
        self._wire_reactive_bindings()
        self.root.mainloop()
        return 0

    def _execute(self, statement: ast.Stmt) -> Any:
        if isinstance(statement, ast.PageDecl):
            for child in statement.body:
                self._execute(child)
            return None
        if isinstance(statement, ast.ShowElement):
            self._tick(statement)
            return self._create_element(statement)
        if isinstance(statement, ast.ChangeElement):
            self._tick(statement)
            return self._change_element(statement)
        if isinstance(statement, ast.ShowNotification):
            self._tick(statement)
            value = self._evaluate(statement.value)
            self.messagebox.showinfo("Simo", self._string(value), parent=self.root)
            return None
        return super()._execute(statement)
