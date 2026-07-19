"""Assets, PWA files, and desktop scaffold generation."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

from simo import ast_nodes as ast
from simo.errors import BuildError


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

    def _write_desktop_scaffold(self, output_dir: Path, title: str) -> None:
        desktop = output_dir / "src-tauri"
        (desktop / "src").mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^a-zA-Z0-9-]", "-", title.lower()).strip("-") or "simo-app"
        config = {
            "$schema": "https://schema.tauri.app/config/2",
            "productName": title,
            "version": "0.1.0",
            "identifier": f"dev.simo.{safe_name}",
            "build": {"frontendDist": ".."},
            "app": {"windows": [{"title": title, "width": 900, "height": 650}]},
            "bundle": {"active": True, "targets": "all"},
        }
        (desktop / "tauri.conf.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
        (desktop / "Cargo.toml").write_text(
            """[package]
name = "simo_desktop_app"
version = "0.1.0"
edition = "2021"

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = [] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
""",
            encoding="utf-8",
        )
        (desktop / "build.rs").write_text("fn main() { tauri_build::build() }\n", encoding="utf-8")
        (desktop / "src" / "main.rs").write_text(
            "#![cfg_attr(not(debug_assertions), windows_subsystem = \"windows\")]\nfn main() { tauri::Builder::default().run(tauri::generate_context!()).expect(\"error running app\"); }\n",
            encoding="utf-8",
        )
        (output_dir / "DESKTOP.md").write_text(
            """# Desktop package

This directory contains a generated Tauri 2 scaffold in `src-tauri`.
Install Rust and the Tauri CLI, then run `cargo tauri build` from this output directory.
The web application files in this directory are used as the frontend.
""",
            encoding="utf-8",
        )
