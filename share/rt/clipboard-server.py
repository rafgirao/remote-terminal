#!/usr/bin/env python3
"""Clipboard bridge server for remote terminal.
Serves the clipboard HTML page and handles paste/copy via tmux."""

import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

TMUX_SESSION = sys.argv[1] if len(sys.argv) > 1 else "remote"
TTYD_URL = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:7681"
PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 7680
HTML_PATH = Path(__file__).parent / "clipboard.html"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silence logs

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            html = HTML_PATH.read_text().replace("__TTYD_URL__", TTYD_URL)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
        elif self.path == "/api/copy":
            try:
                result = subprocess.run(
                    ["tmux", "capture-pane", "-t", TMUX_SESSION, "-p", "-S", "-50"],
                    capture_output=True, text=True, timeout=5
                )
                text = result.stdout.rstrip()
            except Exception:
                text = ""
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(text.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/paste":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                text = data.get("text", "")
                if text:
                    subprocess.run(
                        ["tmux", "send-keys", "-t", TMUX_SESSION, "-l", text],
                        timeout=5
                    )
            except Exception:
                pass
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    server.serve_forever()
