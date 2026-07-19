"""Native widget values exposed to Simo desktop programs."""

from __future__ import annotations

from typing import Any

class DesktopElement:
    """A Simo-facing wrapper around a native widget."""

    def __init__(
        self,
        runtime: "DesktopRuntime",
        widget: Any,
        kind: str,
        *,
        string_var: Any = None,
        pack_options: dict[str, Any] | None = None,
        placeholder: str | None = None,
    ) -> None:
        self.runtime = runtime
        self.widget = widget
        self.kind = kind
        self.string_var = string_var
        self.pack_options = pack_options or {}
        self.placeholder = placeholder or ""
        self.placeholder_active = False
        self._visible = True

    @property
    def text(self) -> str:
        if self.kind == "input":
            return self.value
        try:
            return str(self.widget.cget("text"))
        except Exception:
            return ""

    @text.setter
    def text(self, value: Any) -> None:
        rendered = self.runtime._string(value)
        if self.kind == "input":
            self.value = rendered
        else:
            self.widget.configure(text=rendered)

    @property
    def value(self) -> str:
        if self.kind == "input":
            if self.placeholder_active:
                return ""
            return str(self.string_var.get())
        return self.text

    @value.setter
    def value(self, value: Any) -> None:
        rendered = self.runtime._string(value)
        if self.kind == "input":
            self.placeholder_active = False
            self.string_var.set(rendered)
            self._set_entry_color(active=True)
        else:
            self.text = rendered

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: Any) -> None:
        should_show = self.runtime._truthy(value)
        if should_show and not self._visible:
            self.widget.pack(**self.pack_options)
        elif not should_show and self._visible:
            self.widget.pack_forget()
        self._visible = should_show

    @property
    def color(self) -> str:
        try:
            return str(self.widget.cget("fg"))
        except Exception:
            return ""

    @color.setter
    def color(self, value: Any) -> None:
        self.widget.configure(fg=self.runtime._string(value))

    @property
    def background(self) -> str:
        try:
            return str(self.widget.cget("bg"))
        except Exception:
            return ""

    @background.setter
    def background(self, value: Any) -> None:
        self.widget.configure(bg=self.runtime._string(value))

    @property
    def enabled(self) -> bool:
        try:
            return str(self.widget.cget("state")) != "disabled"
        except Exception:
            return True

    @enabled.setter
    def enabled(self, value: Any) -> None:
        self.widget.configure(state="normal" if self.runtime._truthy(value) else "disabled")

    def focus(self) -> None:
        self.widget.focus_set()

    def clear(self) -> None:
        self.value = ""

    def _set_entry_color(self, *, active: bool) -> None:
        if self.kind != "input":
            return
        color = self.runtime.default_input_color if active else self.runtime.placeholder_color
        try:
            self.widget.configure(fg=color)
        except Exception:
            pass

    def install_placeholder(self) -> None:
        if self.kind != "input" or not self.placeholder:
            return

        def show_placeholder() -> None:
            if not self.string_var.get():
                self.placeholder_active = True
                self.string_var.set(self.placeholder)
                self._set_entry_color(active=False)

        def on_focus_in(_event: Any = None) -> None:
            if self.placeholder_active:
                self.placeholder_active = False
                self.string_var.set("")
                self._set_entry_color(active=True)

        def on_focus_out(_event: Any = None) -> None:
            show_placeholder()

        self.widget.bind("<FocusIn>", on_focus_in)
        self.widget.bind("<FocusOut>", on_focus_out)
        show_placeholder()
