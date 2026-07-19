from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from simo.branding import bundled_icon, install_editor_support


class BrandingTests(unittest.TestCase):
    def test_bundled_icons_are_packaged(self) -> None:
        for extension in ("ico", "png", "icns"):
            icon = bundled_icon(extension)
            self.assertTrue(icon.exists())
            self.assertGreater(icon.stat().st_size, 0)

    def test_editor_support_installs_language_icons(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / ".vscode").mkdir()
            with patch("simo.branding.Path.home", return_value=home), patch(
                "simo.branding.shutil.which", return_value=None
            ):
                destinations = install_editor_support("auto")

            self.assertEqual(len(destinations), 1)
            extension = destinations[0]
            package = json.loads((extension / "package.json").read_text(encoding="utf-8"))
            language = package["contributes"]["languages"][0]
            self.assertEqual(language["extensions"], [".simo"])
            self.assertTrue((extension / language["icon"]["light"]).exists())
            self.assertTrue((extension / language["icon"]["dark"]).exists())


if __name__ == "__main__":
    unittest.main()
