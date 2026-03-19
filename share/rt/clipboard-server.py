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
PIN = sys.argv[4] if len(sys.argv) > 4 else ""
HTML_PATH = Path(__file__).parent / "clipboard.html"

verified_clients = set()

PIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Remote Terminal</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    height: 100dvh;
    background: #1e1e2e;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  }
  .pin-box {
    text-align: center;
    padding: 40px 30px;
  }
  .pin-box h1 {
    color: #cdd6f4;
    font-size: 20px;
    margin-bottom: 8px;
  }
  .pin-box p {
    color: #6c7086;
    font-size: 14px;
    margin-bottom: 24px;
  }
  .pin-input {
    width: 160px;
    background: #313244;
    color: #cdd6f4;
    border: 2px solid #45475a;
    border-radius: 12px;
    padding: 16px;
    font-size: 32px;
    font-family: monospace;
    text-align: center;
    letter-spacing: 8px;
    outline: none;
    -webkit-appearance: none;
  }
  .pin-input:focus { border-color: #89b4fa; }
  .pin-input.error { border-color: #f38ba8; animation: shake 0.3s; }
  @keyframes shake {
    25% { transform: translateX(-4px); }
    75% { transform: translateX(4px); }
  }
  .error-msg {
    color: #f38ba8;
    font-size: 13px;
    margin-top: 12px;
    min-height: 20px;
  }
</style>
</head>
<body>
<div class="pin-box">
  <h1>Remote Terminal</h1>
  <p>Enter the PIN shown on your Mac</p>
  <input class="pin-input" id="pin" type="tel" inputmode="numeric" pattern="[0-9]*" maxlength="4" autofocus>
  <div class="error-msg" id="error"></div>
</div>
<script>
const input = document.getElementById('pin');
const error = document.getElementById('error');
input.addEventListener('input', () => {
  input.classList.remove('error');
  error.textContent = '';
  if (input.value.length === 4) {
    fetch('api/verify-pin', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({pin: input.value})
    }).then(r => {
      if (r.ok) {
        window.location.reload();
      } else {
        input.classList.add('error');
        error.textContent = 'Wrong PIN';
        input.value = '';
      }
    });
  }
});
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silence logs

    def _client_ip(self):
        return self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()

    def _is_verified(self):
        if not PIN:
            return True
        return self._client_ip() in verified_clients

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            if not self._is_verified():
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(PIN_PAGE.encode())
                return

            html = HTML_PATH.read_text().replace("__TTYD_URL__", TTYD_URL)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
        elif self.path == "/api/copy":
            if not self._is_verified():
                self.send_response(403)
                self.end_headers()
                return
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
        if self.path == "/api/verify-pin":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                if data.get("pin") == PIN:
                    verified_clients.add(self._client_ip())
                    self.send_response(200)
                    self.end_headers()
                    return
            except Exception:
                pass
            self.send_response(403)
            self.end_headers()
        elif self.path == "/api/paste":
            if not self._is_verified():
                self.send_response(403)
                self.end_headers()
                return
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
