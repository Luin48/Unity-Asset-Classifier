from __future__ import annotations

import json
import mimetypes
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from config import AppConfig, RESOURCE_DIR, Tag, get_config, reload_config
from organizer import organize
from scanner import scan_assets
from state_store import set_root_asset, set_tag, set_vendor_group


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0:
        return {}
    try:
        return json.loads(handler.rfile.read(length).decode("utf-8"))
    except Exception:
        return {}


def _config_payload() -> dict:
    cfg = get_config()
    return {
        "assetsRoot": cfg.assets_root,
        "port": cfg.port,
        "tags": [tag.__dict__ for tag in cfg.tags],
        "ignoredTopFolders": cfg.ignored_top_folders,
    }


class AppHandler(BaseHTTPRequestHandler):
    server_version = "UnityAssetClassifier/0.1"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self._json({"status": "ok"})

    def do_GET(self) -> None:
        path = self._path()
        if path == "/ping":
            self._json({"status": "ok", "app": "UnityAssetClassifier"})
        elif path == "/api/config":
            self._json(_config_payload())
        elif path == "/api/assets":
            self._json(scan_assets())
        else:
            self._static(path)

    def do_POST(self) -> None:
        path = self._path()
        data = _read_json(self)
        if path == "/api/config":
            self._save_config(data)
        elif path == "/api/organize":
            try:
                self._json(organize([str(item) for item in data.get("ids", [])]))
            except Exception as exc:
                self._json({"error": str(exc)}, 500)
        elif path == "/api/groups/root-asset":
            set_root_asset(str(data.get("id", "")).strip())
            self._json({"status": "saved"})
        elif path == "/api/groups/vendor-group":
            for item_id in data.get("ids", []):
                set_vendor_group(str(item_id).strip())
            self._json({"status": "saved"})
        elif path == "/api/shutdown":
            self._shutdown()
        else:
            self._json({"error": "not found"}, 404)

    def do_PATCH(self) -> None:
        path = self._path()
        if path.startswith("/api/assets/"):
            item_id = unquote(path.removeprefix("/api/assets/"))
            data = _read_json(self)
            if "tag" in data:
                set_tag(item_id, str(data.get("tag", "")).strip())
            self._json({"status": "saved"})
        else:
            self._json({"error": "not found"}, 404)

    def log_message(self, fmt: str, *args) -> None:
        return

    def _path(self) -> str:
        return urlparse(self.path).path

    def _json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _save_config(self, data: dict) -> None:
        current = get_config()
        tags = [
            Tag(id=tag.get("id") or str(uuid.uuid4()), name=tag["name"], color=tag.get("color", "#2563eb"))
            for tag in data.get("tags", [tag.__dict__ for tag in current.tags])
            if tag.get("name")
        ]
        cfg = AppConfig(
            assets_root=data.get("assetsRoot", current.assets_root),
            port=int(data.get("port", current.port)),
            tags=tags,
            ignored_top_folders=[tag.name for tag in tags if tag.name],
        )
        cfg.save()
        reload_config()
        self._json({"status": "saved"})

    def _shutdown(self) -> None:
        self._json({"status": "shutting_down"})
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _static(self, path: str) -> None:
        root = RESOURCE_DIR / "webui"
        rel = "index.html" if path == "/" else unquote(path).lstrip("/")
        target = (root / rel).resolve()
        if not str(target).startswith(str(root.resolve())) or not target.exists():
            target = root / "index.html"
        content = target.read_bytes()
        mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.suffix == ".js":
            mime = "text/javascript"
        self.send_response(200)
        self.send_header("Content-Type", f"{mime}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    cfg = get_config()
    server = ThreadingHTTPServer(("127.0.0.1", cfg.port), AppHandler)
    print(f"Unity Asset Classifier: http://127.0.0.1:{cfg.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
