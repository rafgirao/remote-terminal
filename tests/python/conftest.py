import socket
import sys
import threading
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).parent.parent.parent / "share" / "rt"


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(pin):
    port = get_free_port()

    test_argv = ["clipboard-server.py", "test-session", "/test/terminal/", str(port), pin]

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        f"clipboard_server_{port}",
        SERVER_DIR / "clipboard-server.py",
        submodule_search_locations=[],
    )
    mod = importlib.util.module_from_spec(spec)

    # Patch sys.argv before exec
    old_argv = sys.argv
    sys.argv = test_argv
    spec.loader.exec_module(mod)
    sys.argv = old_argv

    server = mod.ReusableHTTPServer(("127.0.0.1", port), mod.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    return {
        "base_url": f"http://127.0.0.1:{port}",
        "port": port,
        "server": server,
        "module": mod,
    }, server


@pytest.fixture
def server_no_pin():
    info, server = start_server(pin="")
    yield info
    server.shutdown()


@pytest.fixture
def server_with_pin():
    info, server = start_server(pin="1234")
    yield info
    server.shutdown()
