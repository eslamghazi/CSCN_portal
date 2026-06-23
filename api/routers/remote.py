"""Remote portals (superadmin): expose this device's connection info + a client
to pull data/logs from another portal on the LAN (via its PeerServer)."""
import socket
import tempfile
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.permissions import require_role
from api.responses import file_download
from application.services import peer_client, firewall

ZIP_MEDIA = "application/zip"
from application.services.peer_server import DEFAULT_PORT, get_token

router = APIRouter(prefix="/api/remote", tags=["remote"])


def local_ip_addresses() -> List[str]:
    ips: List[str] = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips:
                ips.append(ip)
    except OSError:
        pass
    return ips or ["127.0.0.1"]


@router.get("/server-info")
def server_info(user=Depends(require_role())):
    ips = local_ip_addresses()
    return {"ips": ips, "primary_ip": ips[0], "peer_port": DEFAULT_PORT,
            "token": get_token(), "is_windows": firewall.is_windows()}


@router.post("/firewall")
def allow_firewall(user=Depends(require_role())):
    ok = firewall.allow_port(DEFAULT_PORT)
    return {"success": ok,
            "message": "تم طلب فتح المنفذ عبر جدار الحماية." if ok else "تعذّر طلب فتح المنفذ."}


class ConnectBody(BaseModel):
    host: str
    port: int = DEFAULT_PORT
    token: Optional[str] = None


@router.post("/ping")
def remote_ping(body: ConnectBody, user=Depends(require_role())):
    try:
        result = peer_client.ping(body.host, body.port)
        return {"connected": True, "info": result}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.post("/logs")
def remote_logs(body: ConnectBody, user=Depends(require_role())):
    try:
        logs = peer_client.fetch_logs(body.host, body.port, body.token or get_token())
        return {"success": True, "logs": logs}
    except Exception as e:
        raise HTTPException(502, f"تعذّر جلب السجلات: {e}")


@router.post("/download")
def remote_download(body: ConnectBody, user=Depends(require_role())):
    from datetime import datetime
    dest = tempfile.gettempdir() + f"/CSCN_remote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    try:
        peer_client.download_export(body.host, body.port, body.token or get_token(), dest)
    except Exception as e:
        raise HTTPException(502, f"تعذّر تنزيل البيانات: {e}")
    import os
    return file_download(dest, os.path.basename(dest), ZIP_MEDIA)
