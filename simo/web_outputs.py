"""Asset copying and installable PWA output generation."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

class WebOutputsMixin:
    def _copy_assets(self, output_dir: Path) -> None:
        assets = self.source_path.parent / "assets"
        if assets.is_dir():
            shutil.copytree(assets, output_dir / "assets", dirs_exist_ok=True)

    def _write_pwa(self, output_dir: Path, title: str) -> None:
        manifest = {
            "name": title,
            "short_name": title[:24],
            "start_url": "./",
            "display": "standalone",
            "background_color": "#f5f6f8",
            "theme_color": "#17191c",
            "icons": [
                {"src": "icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}
            ],
        }
        (output_dir / "manifest.webmanifest").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        files = ["./", "./index.html", "./styles.css", "./app.js", "./icon.svg"]
        service_worker = f"""const CACHE = 'simo-app-v1';
const FILES = {json.dumps(files)};
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(FILES))));
self.addEventListener('fetch', event => event.respondWith(caches.match(event.request).then(hit => hit || fetch(event.request))));
"""
        (output_dir / "sw.js").write_text(service_worker, encoding="utf-8")
        initial = html.escape((title[:1] or "S").upper())
        icon = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="112" fill="#17191c"/>
<text x="256" y="335" text-anchor="middle" font-family="system-ui, sans-serif" font-size="260" font-weight="700" fill="white">{initial}</text>
</svg>"""
        (output_dir / "icon.svg").write_text(icon, encoding="utf-8")
