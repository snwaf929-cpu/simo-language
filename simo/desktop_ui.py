"""Native widget creation, events, reactivity, and element changes."""

from __future__ import annotations

from typing import Any, Callable

from simo import ast_nodes as ast
from simo.desktop_element import DesktopElement
from simo.environment import Environment
from simo.errors import BuildError, SimoError


class DesktopUiMixin:
    def _create_element(self, element: ast.ShowElement) -> DesktopElement:
        element_name = element.name or f"simo_{element.kind}_{len(self.elements) + 1}"
        if element_name in self.elements:
            raise self._runtime_error(element, f"Duplicate element name '{element_name}'")

        attributes = {key.lower().replace(" ", "_"): value for key, value in element.attributes.items()}
        content = self._string(self._evaluate(element.content)) if element.content is not None else ""
        pack_options: dict[str, Any] = {"fill": "x", "padx": 4, "pady": 6}
        kind = element.kind
        string_var = None
        placeholder = str(attributes.get("placeholder", ""))

        if kind in {"heading", "text"}:
            default_size = 24 if kind == "heading" else 12
            widget = self.tk.Label(
                self.container,
                text=content,
                anchor="center" if str(attributes.get("align", "")).lower() == "center" else "w",
                justify="center" if str(attributes.get("align", "")).lower() == "center" else "left",
                wraplength=max(240, (self.page.size[0] - 72) if self.page.size else 640),
                font=("TkDefaultFont", default_size, "bold" if kind == "heading" else "normal"),
            )
        elif kind == "button":
            widget = self.tk.Button(self.container, text=content, cursor="hand2")
        elif kind == "input":
            string_var = self.tk.StringVar(value="")
            widget = self.tk.Entry(self.container, textvariable=string_var)
        elif kind == "image":
            path = (self.source_path.parent / content).resolve()
            try:
                image = self.tk.PhotoImage(file=str(path))
            except Exception as exc:
                raise self._runtime_error(
                    element,
                    f"Cannot load image '{content}'. Native Tk images support PNG and GIF.",
                ) from exc
            self.images.append(image)
            widget = self.tk.Label(self.container, image=image)
        else:
            widget = self.tk.Label(self.container, text=content)

        wrapper = DesktopElement(
            self,
            widget,
            kind,
            string_var=string_var,
            pack_options=pack_options,
            placeholder=placeholder,
        )
        wrapper.widget.pack(**pack_options)
        self._apply_attributes(wrapper, attributes)
        wrapper.install_placeholder()
        self.elements[element_name] = wrapper
        if element.name:
            self.environment.define(
                element.name,
                wrapper,
                is_const=True,
                filename=self.filename,
                line=element.line,
                column=element.column,
            )

        for event in element.events:
            self._bind_event(wrapper, event, self.environment)

        watched = attributes.get("reactive_when")
        if watched and element.content is not None:
            self.reactive_bindings.append((str(watched), wrapper, element.content, self.environment))
        return wrapper

    def _apply_attributes(self, element: DesktopElement, attributes: dict[str, Any]) -> None:
        widget = element.widget
        size = attributes.get("size")
        if isinstance(size, str):
            font_size = {"small": 10, "medium": 12, "big": 24, "large": 24}.get(size.lower())
            if font_size and element.kind in {"heading", "text", "button", "input"}:
                widget.configure(font=("TkDefaultFont", font_size, "bold" if element.kind == "heading" else "normal"))
        elif isinstance(size, tuple) and len(size) == 2:
            width, height = size
            try:
                widget.configure(width=max(1, int(width) // 10), height=max(1, int(height) // 24))
            except Exception:
                pass

        font_size = attributes.get("font_size")
        if isinstance(font_size, (int, float)):
            widget.configure(font=("TkDefaultFont", int(font_size)))
        if "color" in attributes:
            try:
                widget.configure(fg=str(attributes["color"]))
            except Exception:
                pass
        background = attributes.get("background", attributes.get("background_color"))
        if background is not None:
            try:
                widget.configure(bg=str(background), activebackground=str(background))
            except Exception:
                try:
                    widget.configure(bg=str(background))
                except Exception:
                    pass
        if "width" in attributes:
            try:
                widget.configure(width=int(attributes["width"]))
            except Exception:
                pass
        if "height" in attributes:
            try:
                widget.configure(height=int(attributes["height"]))
            except Exception:
                pass
        if str(attributes.get("visible", "true")).lower() in {"false", "no", "0"}:
            element.visible = False
        if str(attributes.get("enabled", "true")).lower() in {"false", "no", "0"}:
            element.enabled = False

    def _bind_event(self, element: DesktopElement, event: ast.UiEvent, captured: Environment) -> None:
        handler = self._event_handler(event.body, captured)
        if event.name == "clicked":
            if element.kind == "button":
                element.widget.configure(command=handler)
            else:
                element.widget.bind("<Button-1>", lambda _event: handler())
            return
        if event.name == "changes" and element.kind == "input":
            element.string_var.trace_add("write", lambda *_args: self._run_if_not_placeholder(element, handler))

    def _run_if_not_placeholder(self, element: DesktopElement, handler: Callable[[], None]) -> None:
        if not element.placeholder_active:
            handler()

    def _event_handler(self, body: list[ast.Stmt], captured: Environment) -> Callable[[], None]:
        def run() -> None:
            previous = self.environment
            try:
                self.environment = Environment(captured)
                for statement in body:
                    self._execute(statement)
            except SimoError as exc:
                self.messagebox.showerror("Simo Error", str(exc), parent=self.root)
            except Exception as exc:  # native API failure
                self.messagebox.showerror("Simo Error", str(exc), parent=self.root)
            finally:
                self.environment = previous

        return run

    def _wire_reactive_bindings(self) -> None:
        for watched_name, target, expression, captured in self.reactive_bindings:
            watched = self.elements.get(watched_name)
            if watched is None or watched.kind != "input":
                raise BuildError(
                    f"Reactive UI references unknown input '{watched_name}'",
                    str(self.source_path),
                )

            def update(*_args: Any, target=target, expression=expression, captured=captured, watched=watched) -> None:
                if watched.placeholder_active:
                    return
                previous = self.environment
                try:
                    self.environment = captured
                    target.text = self._evaluate(expression)
                finally:
                    self.environment = previous

            watched.string_var.trace_add("write", update)

    def _change_element(self, statement: ast.ChangeElement) -> None:
        element = self.elements.get(statement.target_name)
        if element is None:
            raise self._runtime_error(statement, f"Unknown element '{statement.target_name}'")
        value = self._evaluate(statement.value)
        property_name = statement.property_name.lower().replace(" ", "_")
        aliases = {"heading": "text", "background_color": "background"}
        property_name = aliases.get(property_name, property_name)
        if not hasattr(element, property_name):
            raise self._runtime_error(
                statement,
                f"Element '{statement.target_name}' has no changeable property '{property_name}'",
            )
        setattr(element, property_name, value)
