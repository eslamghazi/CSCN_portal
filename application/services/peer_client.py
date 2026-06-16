"""Client helpers (stdlib urllib) to talk to a remote portal's PeerServer."""
import json
import urllib.request

from application.services.peer_server import DEFAULT_PORT, DEFAULT_TOKEN  # noqa: F401


def _get(host: str, port: int, path: str, token: str = None, timeout: int = 10) -> bytes:
    url = f"http://{host}:{port}{path}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("X-Token", token)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def ping(host: str, port: int = DEFAULT_PORT, timeout: int = 5) -> dict:
    return json.loads(_get(host, port, "/ping", timeout=timeout))


def fetch_logs(host: str, port: int, token: str, timeout: int = 15) -> list:
    return json.loads(_get(host, port, "/logs", token=token, timeout=timeout))["logs"]


def download_export(host: str, port: int, token: str, dest: str, timeout: int = 180) -> str:
    data = _get(host, port, "/export", token=token, timeout=timeout)
    with open(dest, "wb") as f:
        f.write(data)
    return dest
