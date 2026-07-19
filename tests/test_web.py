from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from simo.errors import BuildError
from simo.web import build


WEB_SOURCE = '''
page "Counter App" size 500x420 {
    set count = 0

    action update_name()
        change text of greeting to "Hello, " + username.value
    end

    show heading "Counter" named title {
        size big
        align center
    }

    show text "Count: " + count named counter_text
    show input box named username placeholder "Your name"
    show text "Hello" named greeting

    show button "Add point" named add_button {
        background #111
        color white
        rounded
        when clicked:
            count = count + 1
            change text of counter_text to "Count: " + count
            update_name()
            show notification "Point added"
        end
    }
}
'''


class WebCompilerTests(unittest.TestCase):
    def _project(self, source: str = WEB_SOURCE):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        main = root / "main.simo"
        main.write_text(source, encoding="utf-8")
        return temporary, root, main

    def test_web_build_writes_runnable_bundle(self) -> None:
        temporary, root, main = self._project()
        self.addCleanup(temporary.cleanup)
        output = build(main, root / "dist", "web")
        self.assertTrue((output / "index.html").exists())
        self.assertTrue((output / "styles.css").exists())
        javascript = (output / "app.js").read_text(encoding="utf-8")
        self.assertIn('addEventListener("click"', javascript)
        self.assertIn('$el("username").value', javascript)
        self.assertIn('Simo.notify("Point added")', javascript)
        styles = (output / "styles.css").read_text(encoding="utf-8")
        self.assertIn("#add_button", styles)
        self.assertIn("background: #111", styles)

    def test_app_build_is_installable_pwa(self) -> None:
        temporary, root, main = self._project()
        self.addCleanup(temporary.cleanup)
        output = build(main, root / "dist", "app")
        for name in ["manifest.webmanifest", "sw.js", "icon.svg"]:
            self.assertTrue((output / name).exists(), name)
        self.assertIn("standalone", (output / "manifest.webmanifest").read_text())

    def test_desktop_build_writes_tauri_scaffold(self) -> None:
        temporary, root, main = self._project()
        self.addCleanup(temporary.cleanup)
        output = build(main, root / "dist", "desktop")
        self.assertTrue((output / "src-tauri" / "tauri.conf.json").exists())
        self.assertTrue((output / "src-tauri" / "src" / "main.rs").exists())
        self.assertTrue((output / "DESKTOP.md").exists())

    def test_assets_are_copied(self) -> None:
        temporary, root, main = self._project(
            'page "Images" {\n    show image "assets/logo.txt" named logo\n}\n'
        )
        self.addCleanup(temporary.cleanup)
        (root / "assets").mkdir()
        (root / "assets" / "logo.txt").write_text("asset")
        output = build(main, root / "dist", "web")
        self.assertEqual((output / "assets" / "logo.txt").read_text(), "asset")

    def test_page_required_for_web_build(self) -> None:
        temporary, root, main = self._project('say("console")\n')
        self.addCleanup(temporary.cleanup)
        with self.assertRaises(BuildError):
            build(main, root / "dist", "web")


if __name__ == "__main__":
    unittest.main()
