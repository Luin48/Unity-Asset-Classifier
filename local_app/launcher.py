from __future__ import annotations

import socket
import threading
import time
import webbrowser

from app import AppHandler, ThreadingHTTPServer
from config import get_config


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main() -> None:
    cfg = get_config()
    url = f"http://127.0.0.1:{cfg.port}/"
    server = None
    thread = None

    if not _port_open(cfg.port):
        server = ThreadingHTTPServer(("127.0.0.1", cfg.port), AppHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.4)

    webbrowser.open(url)
    if thread is None:
        return

    try:
        while thread.is_alive():
            time.sleep(0.5)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
