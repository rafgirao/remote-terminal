import json
import urllib.request
import urllib.error
from unittest.mock import patch, MagicMock


# ============================================
# Version / Health
# ============================================

def test_unknown_path_returns_404(server_no_pin):
    url = server_no_pin["base_url"] + "/nonexistent"
    try:
        urllib.request.urlopen(url)
        assert False, "Should have raised HTTPError"
    except urllib.error.HTTPError as e:
        assert e.code == 404


def test_unknown_post_returns_404(server_no_pin):
    url = server_no_pin["base_url"] + "/nonexistent"
    req = urllib.request.Request(url, data=b"", method="POST")
    try:
        urllib.request.urlopen(req)
        assert False, "Should have raised HTTPError"
    except urllib.error.HTTPError as e:
        assert e.code == 404


# ============================================
# Main Page (no PIN)
# ============================================

def test_main_page_without_pin_returns_html(server_no_pin):
    url = server_no_pin["base_url"] + "/"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    body = resp.read().decode()
    assert "terminal" in body.lower()
    assert "__TTYD_URL__" not in body


def test_main_page_contains_terminal_websocket(server_no_pin):
    url = server_no_pin["base_url"] + "/"
    resp = urllib.request.urlopen(url)
    body = resp.read().decode()
    assert "terminal/ws" in body


# ============================================
# PIN Verification
# ============================================

def test_pin_page_shown_when_pin_required(server_with_pin):
    url = server_with_pin["base_url"] + "/"
    resp = urllib.request.urlopen(url)
    assert resp.status == 200
    body = resp.read().decode()
    assert "Enter the PIN" in body
    assert 'id="pin"' in body
    assert 'inputmode="numeric"' in body


def test_verify_pin_correct(server_with_pin):
    url = server_with_pin["base_url"] + "/api/verify-pin"
    data = json.dumps({"pin": "1234"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    assert resp.status == 200


def test_verify_pin_wrong(server_with_pin):
    url = server_with_pin["base_url"] + "/api/verify-pin"
    data = json.dumps({"pin": "0000"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        assert False, "Should have raised HTTPError"
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_verify_pin_malformed_json(server_with_pin):
    url = server_with_pin["base_url"] + "/api/verify-pin"
    req = urllib.request.Request(url, data=b"not json", headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        assert False, "Should have raised HTTPError"
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_verify_pin_empty_body(server_with_pin):
    url = server_with_pin["base_url"] + "/api/verify-pin"
    req = urllib.request.Request(url, data=b"", headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        assert False, "Should have raised HTTPError"
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_main_page_after_pin_verification(server_with_pin):
    base = server_with_pin["base_url"]

    # Verify PIN first
    data = json.dumps({"pin": "1234"}).encode()
    req = urllib.request.Request(base + "/api/verify-pin", data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

    # Now main page should show terminal
    resp = urllib.request.urlopen(base + "/")
    body = resp.read().decode()
    assert "Enter the PIN" not in body
    assert "terminal/ws" in body


# ============================================
# Copy API
# ============================================

def test_copy_unverified_returns_403(server_with_pin):
    url = server_with_pin["base_url"] + "/api/copy"
    try:
        urllib.request.urlopen(url)
        assert False, "Should have raised HTTPError"
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_copy_returns_tmux_output(server_no_pin):
    mock_result = MagicMock()
    mock_result.stdout = "hello world\n"

    with patch("subprocess.run", return_value=mock_result):
        url = server_no_pin["base_url"] + "/api/copy"
        resp = urllib.request.urlopen(url)
        assert resp.status == 200
        body = resp.read().decode()
        assert body == "hello world"


def test_copy_handles_tmux_failure(server_no_pin):
    with patch("subprocess.run", side_effect=Exception("tmux not found")):
        url = server_no_pin["base_url"] + "/api/copy"
        resp = urllib.request.urlopen(url)
        assert resp.status == 200
        body = resp.read().decode()
        assert body == ""


def test_copy_has_cors_header(server_no_pin):
    with patch("subprocess.run", return_value=MagicMock(stdout="")):
        url = server_no_pin["base_url"] + "/api/copy"
        resp = urllib.request.urlopen(url)
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"


# ============================================
# Paste API
# ============================================

def test_paste_unverified_returns_403(server_with_pin):
    url = server_with_pin["base_url"] + "/api/paste"
    data = json.dumps({"text": "hello"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        assert False, "Should have raised HTTPError"
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_paste_sends_to_tmux(server_no_pin):
    with patch("subprocess.run") as mock_run:
        url = server_no_pin["base_url"] + "/api/paste"
        data = json.dumps({"text": "hello"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req)
        assert resp.status == 200
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "tmux" in call_args
        assert "hello" in call_args


def test_paste_empty_text_does_not_call_tmux(server_no_pin):
    with patch("subprocess.run") as mock_run:
        url = server_no_pin["base_url"] + "/api/paste"
        data = json.dumps({"text": ""}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req)
        assert resp.status == 200
        mock_run.assert_not_called()


def test_paste_malformed_json_returns_200(server_no_pin):
    url = server_no_pin["base_url"] + "/api/paste"
    req = urllib.request.Request(url, data=b"not json", headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    assert resp.status == 200


def test_paste_has_cors_header(server_no_pin):
    url = server_no_pin["base_url"] + "/api/paste"
    data = json.dumps({"text": "x"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with patch("subprocess.run"):
        resp = urllib.request.urlopen(req)
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"


# ============================================
# CORS Preflight
# ============================================

def test_options_returns_cors_headers(server_no_pin):
    url = server_no_pin["base_url"] + "/api/paste"
    req = urllib.request.Request(url, method="OPTIONS")
    resp = urllib.request.urlopen(req)
    assert resp.status == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"
    assert "POST" in resp.headers.get("Access-Control-Allow-Methods", "")
    assert "Content-Type" in resp.headers.get("Access-Control-Allow-Headers", "")


# ============================================
# Server Config
# ============================================

def test_server_allows_reuse_address(server_no_pin):
    assert server_no_pin["server"].allow_reuse_address is True
