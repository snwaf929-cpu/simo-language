from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from simo.cli import main
from simo.desktop import DesktopRuntime
from simo.desktop_build import build_desktop
from simo.project import create_project
from simo.source import parse_source


DESKTOP_SOURCE = '''
page "Calculator" size 420x360 {
    show input box named first placeholder "First number"
    show text "Result: 0" named result_text
    show button "Copy input" named copy_button {
        when clicked:
            change text of result_text to "Result: " + first.value
        end
    }
}
'''


class FakeVar:
    def __init__(self, value="") -> None:
        self.value = value
        self.callbacks = []

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        for callback in list(self.callbacks):
            callback("name", "index", "write")

    def trace_add(self, _mode, callback):
        self.callbacks.append(callback)


class FakeWidget:
    def __init__(self, _parent=None, **options) -> None:
        self.options = dict(options)
        self.bindings = {}
        self.packed = False
        self.pack_options = {}

    def configure(self, **options):
        self.options.update(options)

    config = configure

    def cget(self, name):
        return self.options.get(name, "")

    def pack(self, **options):
        self.packed = True
        self.pack_options = dict(options)

    def pack_forget(self):
        self.packed = False

    def bind(self, name, callback):
        self.bindings[name] = callback

    def focus_set(self):
        self.options["focused"] = True


class FakeRoot(FakeWidget):
    def __init__(self) -> None:
        super().__init__()
        self.window_title = ""
        self.window_geometry = ""
        self.mainloop_called = False
        self.clipboard = ""

    def title(self, value):
        self.window_title = value

    def geometry(self, value):
        self.window_geometry = value

    def minsize(self, *_args):
        pass

    def mainloop(self):
        self.mainloop_called = True

    def destroy(self):
        self.options["destroyed"] = True

    def clipboard_get(self):
        return self.clipboard

    def clipboard_clear(self):
        self.clipboard = ""

    def clipboard_append(self, value):
        self.clipboard += value

    def update_idletasks(self):
        pass


class FakeTk:
    Frame = FakeWidget
    Label = FakeWidget
    Button = FakeWidget
    Entry = FakeWidget
    StringVar = FakeVar

    @staticmethod
    def PhotoImage(**_options):
        return object()


class FakeDialogs:
    @staticmethod
    def askopenfilename(**_options):
        return "/tmp/open.txt"

    @staticmethod
    def asksaveasfilename(**_options):
        return "/tmp/save.txt"

    @staticmethod
    def askdirectory(**_options):
        return "/tmp"


class FakeSimpleDialog:
    @staticmethod
    def askstring(*_args, **_kwargs):
        return "answer"


class FakeMessages:
    calls = []

    @classmethod
    def showinfo(cls, *args, **kwargs):
        cls.calls.append(("info", args, kwargs))

    @classmethod
    def showerror(cls, *args, **kwargs):
        cls.calls.append(("error", args, kwargs))


class DesktopTests(unittest.TestCase):
    def _source(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        source = root / "main.simo"
        source.write_text(DESKTOP_SOURCE, encoding="utf-8")
        return temporary, root, source

    def test_native_runtime_creates_widgets_and_runs_event(self) -> None:
        temporary, _root, source = self._source()
        self.addCleanup(temporary.cleanup)
        native_root = FakeRoot()
        runtime = DesktopRuntime(
            source,
            root=native_root,
            tk_module=FakeTk,
            filedialog_module=FakeDialogs,
            messagebox_module=FakeMessages,
            simpledialog_module=FakeSimpleDialog,
        )
        self.assertEqual(runtime.run(), 0)
        self.assertTrue(native_root.mainloop_called)
        self.assertEqual(native_root.window_title, "Calculator")
        self.assertEqual(native_root.window_geometry, "420x360")

        runtime.elements["first"].value = "42"
        runtime.elements["copy_button"].widget.options["command"]()
        self.assertEqual(runtime.elements["result_text"].text, "Result: 42")
        expression = parse_source("say(result_text.text)\n").statements[0].expression.arguments[0]
        self.assertEqual(runtime._evaluate(expression), "Result: 42")

    def test_desktop_template_and_run_routing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "calculator"
            project = create_project(destination, "desktop")
            self.assertEqual(project.target, "desktop")
            with patch("simo.cli.run_desktop", return_value=0) as run_native:
                result = main(["run", str(destination / "main.simo")])
            self.assertEqual(result, 0)
            run_native.assert_called_once_with((destination / "main.simo").resolve())

    def test_desktop_build_invokes_onefile_native_packager(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "calculator"
            project = create_project(destination, "desktop")
            output = destination / "dist"
            commands = []

            def fake_run(command, check):
                self.assertTrue(check)
                commands.append(command)
                dist = Path(command[command.index("--distpath") + 1])
                name = command[command.index("--name") + 1]
                dist.mkdir(parents=True, exist_ok=True)
                (dist / name).write_text("native")

            with patch("simo.desktop_build.ensure_pyinstaller"), patch(
                "simo.desktop_build.subprocess.run", side_effect=fake_run
            ):
                artifact = build_desktop(
                    project.entry,
                    output,
                    project=project,
                    auto_install_tools=False,
                )

            self.assertTrue(artifact.exists())
            command = commands[0]
            self.assertIn("--onefile", command)
            self.assertIn("--windowed", command)
            self.assertIn("--add-data", command)
            self.assertIn("tkinter", command)
            self.assertNotIn("cargo", " ".join(command).lower())


if __name__ == "__main__":
    unittest.main()
