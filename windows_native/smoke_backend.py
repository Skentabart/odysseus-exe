from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class SmokeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib HTTP handler API
        if self.path not in {"/health", "/status"}:
            self.send_error(404)
            return
        payload = json.dumps({"ok": True, "service": "odysseus-windows-native-smoke"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - stdlib signature
        return


def run(host: str = "127.0.0.1", port: int = 7000) -> None:
    ThreadingHTTPServer((host, port), SmokeHandler).serve_forever()


if __name__ == "__main__":
    run()
