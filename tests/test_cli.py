from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from simo.cli import main
from simo.formatter import format_source
from simo.project import create_project, load_project


class CliTests(unittest.TestCase):
    def test_new_console_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "hello"
            result = main(["new", str(destination), "--template", "console"])
            self.assertEqual(result, 0)
            self.assertTrue((destination / "main.simo").exists())
            self.assertEqual(load_project(destination).target, "console")

    def test_new_web_project_builds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "site"
            create_project(destination, "web")
            result = main(
                [
                    "build",
                    str(destination / "main.simo"),
                    "--target",
                    "web",
                    "--output",
                    str(destination / "dist"),
                ]
            )
            self.assertEqual(result, 0)
            self.assertTrue((destination / "dist" / "index.html").exists())

    def test_new_desktop_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "calculator"
            result = main(["new", str(destination), "--template", "desktop"])
            self.assertEqual(result, 0)
            self.assertEqual(load_project(destination).target, "desktop")
            self.assertIn("page", (destination / "main.simo").read_text())
            self.assertTrue((destination / "assets" / "icon.ico").exists())
            self.assertTrue((destination / "assets" / "icon.png").exists())
            self.assertTrue((destination / "assets" / "icon.icns").exists())

    def test_setup_icons_command(self) -> None:
        installed = Path("/tmp/simo-editor-extension")
        output = StringIO()
        with patch("simo.cli.install_editor_support", return_value=[installed]) as install, patch(
            "simo.cli.register_windows_file_type", return_value='cursor.exe "%1"'
        ) as register, patch("simo.cli.sys.platform", "win32"), redirect_stdout(output):
            result = main(["setup-icons", "--editor", "cursor"])
        self.assertEqual(result, 0)
        install.assert_called_once_with("cursor")
        register.assert_called_once_with()
        self.assertIn("Installed Simo editor support", output.getvalue())
        self.assertIn("Registered .simo", output.getvalue())

    def test_check_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary) / "main.simo"
            file.write_text('say("ok")\n')
            output = StringIO()
            with redirect_stdout(output):
                result = main(["check", str(file)])
            self.assertEqual(result, 0)
            self.assertIn("OK", output.getvalue())

    def test_formatter(self) -> None:
        source = 'if true\nsay("yes")\nelse\nsay("no")\nend\n'
        formatted = format_source(source)
        self.assertEqual(
            formatted,
            'if true\n    say("yes")\nelse\n    say("no")\nend\n',
        )


if __name__ == "__main__":
    unittest.main()
