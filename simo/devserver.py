"""Development web server for Simo page projects."""

from __future__ import annotations

import functools
import http.server
import os
import socketserver
import threading
import webbrowser
from pathlib import Path
from typing import Callable

from simo.web import build


def _fingerprint(source: Path) -> tuple[tuple[str, int, int], ...]:
    files = [source]
    files.extend(source.parent.rglob("*.simo"))
    assets = source.parent / "assets"
    if assets.is_dir():
        files.extend(path for path in assets.rglob("*") if path.is_file())
    result: list[tuple[str, int, int]] = []
    for path in sorted(set(files)):
        try:
            stat = path.stat()
        except OSError:
            continue
        result.append((str(path), stat.st_mtime_ns, stat.st_size))
    return tuple(result)


def serve(
    source: Path,
    output: Path,
    *,
    target: str = "web",
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
) -> None:
    source = source.resolve()
    output = output.resolve()
    state = {"fingerprint": None}
    lock = threading.Lock()

    def rebuild() -> None:
        current = _fingerprint(source)
        if current == state["fingerprint"]:
            return
        with lock:
            current = _fingerprint(source)
            if current == state["fingerprint"]:
                return
            build(source, output, target)
            state["fingerprint"] = current
            print(f"Built {source.name} -> {output}")

    rebuild()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - inherited API
            try:
                rebuild()
            except Exception as exc:  # serve the last successful build
                print(f"Build failed: {exc}")
            super().do_GET()

        def end_headers(self) -> None:
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            print(f"[dev] {format % args}")

    handler = functools.partial(Handler, directory=str(output))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((host, port), handler) as server:
        url = f"http://{host}:{port}/"
        print(f"Simo development server: {url}")
        print("Files are rebuilt when the browser requests a page. Press Ctrl+C to stop.")
        if open_browser:
            threading.Timer(0.3, lambda: webbrowser.open(url)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nDevelopment server stopped.")
        finally:
            server.shutdown()
