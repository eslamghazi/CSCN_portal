import time
import urllib.error

import pytest

from application.services.peer_server import PeerServer
from application.services import peer_client

PORT = 50599


@pytest.fixture
def server():
    srv = PeerServer(token="testtok", port=PORT)
    srv.start()
    time.sleep(0.4)
    yield srv
    srv.stop()


def test_ping_needs_no_token(server):
    info = peer_client.ping("127.0.0.1", PORT, timeout=3)
    assert info["status"] == "ok"
    assert info["app"] == "CSCN"


def test_protected_endpoint_rejects_bad_token(server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        peer_client.fetch_logs("127.0.0.1", PORT, "wrong-token", timeout=3)
    assert exc.value.code == 403
