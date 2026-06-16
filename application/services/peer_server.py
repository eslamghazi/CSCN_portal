"""Embedded LAN server that lets the (superadmin/developer) portal remotely pull
the full data export and audit logs from another portal on the same internal
network. Runs in a daemon thread. All endpoints except /ping require a shared
token (X-Token header or ?token=).

Endpoints:
  GET /ping              -> {"app":"CSCN","status":"ok"}            (no token)
  GET /logs              -> {"logs":[...]}                          (token)
  GET /export            -> application/zip (full DB + resources)   (token)
"""
import os
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from loguru import logger

DEFAULT_PORT = 50525
DEFAULT_TOKEN = "cscn-internal"


def get_token() -> str:
    return os.environ.get("CSCN_portal_PEER_TOKEN", DEFAULT_TOKEN)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence default stderr logging
        pass

    def _auth_ok(self) -> bool:
        provided = self.headers.get("X-Token")
        if not provided:
            provided = parse_qs(urlparse(self.path).query).get("token", [None])[0]
        return provided == self.server.token

    def _send_json(self, code: int, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/ping":
            self._send_json(200, {"app": "CSCN", "status": "ok"})
            return
        if not self._auth_ok():
            self._send_json(403, {"error": "forbidden"})
            return
        try:
            if path == "/logs":
                self._send_json(200, {"logs": self._collect_logs()})
            elif path == "/export":
                self._send_export()
            else:
                self._send_json(404, {"error": "not found"})
        except Exception as e:  # pragma: no cover - network/runtime
            logger.error(f"Peer request {path} failed: {e}")
            self._send_json(500, {"error": "internal error"})

    @staticmethod
    def _collect_logs(limit: int = 1000):
        from database.session import SessionLocal
        from domain.entities.audit import AuditLog
        from domain.entities.user import User
        session = SessionLocal()
        try:
            rows = (session.query(AuditLog, User.username)
                    .outerjoin(User, AuditLog.user_id == User.id)
                    .order_by(AuditLog.timestamp.desc()).limit(limit).all())
            return [
                {
                    "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
                    "user": username or "System",
                    "module": log.module,
                    "action": log.action,
                    "entity": log.entity_type or "",
                }
                for log, username in rows
            ]
        finally:
            session.close()

    def _send_export(self):
        from application.services.backup_service import BackupService
        tmp = os.path.join(tempfile.gettempdir(), "cscn_remote_export.zip")
        BackupService().export_all(tmp)
        with open(tmp, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", "attachment; filename=cscn_export.zip")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class PeerServer:
    def __init__(self, token: str = None, port: int = DEFAULT_PORT):
        self.token = token or get_token()
        self.port = port
        self._httpd = None
        self._thread = None

    def start(self):
        try:
            self._httpd = ThreadingHTTPServer(("0.0.0.0", self.port), _Handler)
            self._httpd.token = self.token
            self._thread = threading.Thread(
                target=self._httpd.serve_forever, daemon=True, name="cscn-peer-server")
            self._thread.start()
            logger.info(f"Peer server listening on 0.0.0.0:{self.port}")
        except Exception as e:
            logger.warning(f"Peer server could not start on :{self.port} ({e})")

    def stop(self):
        if self._httpd is not None:
            try:
                self._httpd.shutdown()
            except Exception:
                pass
