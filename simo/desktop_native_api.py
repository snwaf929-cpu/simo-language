"""Desktop-specific dialogs, clipboard, storage, and system APIs."""

from __future__ import annotations

import json
import os
import re
import sys
import webbrowser
from pathlib import Path
from typing import Any, Callable


class DesktopNativeApiMixin:
    def _install_desktop_builtins(self) -> None:
        def ask(prompt: Any = "") -> str:
            value = self.simpledialog.askstring(
                self._evaluate_literal_title(self.page.title),
                self._string(prompt),
                parent=self.root,
            )
            return "" if value is None else str(value)

        def storage_path() -> Path:
            title = self._evaluate_literal_title(self.page.title)
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", title).strip("-.") or "simo-app"
            if sys.platform == "win32":
                base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            elif sys.platform == "darwin":
                base = Path.home() / "Library" / "Application Support"
            else:
                base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
            path = base / "Simo" / safe_name
            path.mkdir(parents=True, exist_ok=True)
            return path

        def save(key: Any, value: Any) -> Any:
            path = storage_path() / "storage.json"
            data: dict[str, Any] = {}
            if path.exists():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        data = loaded
                except (OSError, json.JSONDecodeError):
                    data = {}
            data[str(key)] = value
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return value

        def load(key: Any, fallback: Any = None) -> Any:
            path = storage_path() / "storage.json"
            if not path.exists():
                return fallback
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return fallback
            return data.get(str(key), fallback) if isinstance(data, dict) else fallback

        def open_file_dialog() -> str:
            return str(self.filedialog.askopenfilename(parent=self.root) or "")

        def save_file_dialog() -> str:
            return str(self.filedialog.asksaveasfilename(parent=self.root) or "")

        def select_folder() -> str:
            return str(self.filedialog.askdirectory(parent=self.root) or "")

        def desktop_notification(title: Any, message: Any = "") -> None:
            self.messagebox.showinfo(self._string(title), self._string(message), parent=self.root)

        def open_url(url: Any) -> bool:
            return bool(webbrowser.open(self._string(url)))

        def clipboard_get() -> str:
            try:
                return str(self.root.clipboard_get())
            except Exception:
                return ""

        def clipboard_set(value: Any) -> None:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._string(value))
            self.root.update_idletasks()

        desktop_builtins: dict[str, Callable[..., Any]] = {
            "ask": ask,
            "save": save,
            "load": load,
            "app_data_path": lambda: str(storage_path()),
            "open_file_dialog": open_file_dialog,
            "save_file_dialog": save_file_dialog,
            "select_folder": select_folder,
            "desktop_notification": desktop_notification,
            "open_url": open_url,
            "clipboard_get": clipboard_get,
            "clipboard_set": clipboard_set,
            "quit_app": self.root.destroy,
        }
        for name, value in desktop_builtins.items():
            self.builtins.define(name, value, is_const=True, replace=True)
