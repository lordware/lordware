"""Read-only, loopback-only preview of this repository's profile README."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import subprocess
from urllib.parse import parse_qs, unquote, urlsplit


PREVIEW = Path(__file__).resolve().parent
ROOT = PREVIEW.parent
ASSETS = ROOT / "assets"
STATIC = {"/": "index.html", "/index.html": "index.html", "/style.css": "style.css", "/app.js": "app.js"}
IMAGE_TYPES = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".ico"}
ORIGINAL_ASSETS = "https://raw.githubusercontent.com/lordware/lordware/main/assets/"


def from_head(path):
    return subprocess.run(
        ["git", "show", f"HEAD:{path}"], cwd=ROOT, check=True,
        capture_output=True, timeout=10,
    ).stdout


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, data, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' https: data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        try:
            if path in STATIC:
                file = PREVIEW / STATIC[path]
                kind = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
                self.send_bytes(file.read_bytes(), kind + "; charset=utf-8")
                return
            if path == "/api/readme":
                version = parse_qs(parsed.query).get("version", ["after"])[0]
                if version not in {"before", "after"}:
                    self.send_error(400, "Unknown version")
                    return
                if version == "before":
                    content = from_head("README.md").decode("utf-8")
                    content = content.replace(ORIGINAL_ASSETS, "/before-assets/")
                else:
                    content = (ROOT / "README.md").read_text(encoding="utf-8-sig")
                    content = content.replace(ORIGINAL_ASSETS, "/assets/")
                data = json.dumps({"content": content, "version": version}, ensure_ascii=False).encode("utf-8")
                self.send_bytes(data, "application/json; charset=utf-8")
                return
            for prefix, original in (("/assets/", False), ("/before-assets/", True)):
                if not path.startswith(prefix):
                    continue
                relative = path[len(prefix):]
                # Refuse traversal, Windows separators/drives, and non-image files.
                if not relative or "\\" in relative or ":" in relative or any(part in {"", ".", ".."} for part in relative.split("/")):
                    self.send_error(404)
                    return
                file = (ASSETS / relative).resolve()
                if not file.is_relative_to(ASSETS.resolve()) or file.suffix.lower() not in IMAGE_TYPES:
                    self.send_error(404)
                    return
                data = from_head("assets/" + relative) if original else file.read_bytes()
                kind = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
                self.send_bytes(data, kind)
                return
            self.send_error(404)
        except (FileNotFoundError, subprocess.CalledProcessError):
            self.send_error(404, "Requested preview resource is unavailable")
        except subprocess.TimeoutExpired:
            self.send_error(503, "Git snapshot timed out")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Profile preview: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
