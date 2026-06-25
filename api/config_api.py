"""Web-server configuration: host/port, the signed-cookie session secret, and
resource-path resolution that works both in dev and inside a frozen PyInstaller
build."""
import os
import sys
import secrets
from pathlib import Path

from config.settings import DATA_DIR

# ----------------------------------------------------------------- server
# Bind 0.0.0.0 so other PCs on the LAN can reach the portal; the local user is
# pointed at 127.0.0.1 by the launcher.
HOST = os.environ.get("CSCN_portal_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.environ.get("CSCN_portal_PORT", "8765"))


def get_active_port() -> int:
    """The port the server actually bound (set by the launcher), else the default."""
    try:
        return int(os.environ.get("CSCN_portal_ACTIVE_PORT", DEFAULT_PORT))
    except (TypeError, ValueError):
        return DEFAULT_PORT

# Cookie lifetime (seconds). "Remember me" uses REMEMBER_MAX_AGE, otherwise a
# shorter session lifetime.
SESSION_MAX_AGE = 60 * 60 * 12          # 12 hours
REMEMBER_MAX_AGE = 60 * 60 * 24 * 30    # 30 days


# ------------------------------------------------------- resource resolution
def project_root() -> Path:
    """Repo root in dev; the PyInstaller bundle dir (_MEIPASS) when frozen."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resolve_resource(rel: str) -> Path:
    """Resolve a path relative to the project root / frozen bundle."""
    return project_root() / rel


# Built React SPA location (vite build output).
FRONTEND_DIST = resolve_resource("frontend/dist")


# ----------------------------------------------------------- session secret
def get_session_secret() -> str:
    """Return a stable secret for signing session cookies. Order:
    env var -> persisted file in DATA_DIR -> freshly generated (then persisted),
    so logins survive server restarts."""
    env = os.environ.get("CSCN_portal_SESSION_SECRET")
    if env:
        return env
    secret_file = DATA_DIR / ".session_secret"
    try:
        if secret_file.exists():
            value = secret_file.read_text(encoding="utf-8").strip()
            if value:
                return value
        value = secrets.token_urlsafe(48)
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        secret_file.write_text(value, encoding="utf-8")
        return value
    except OSError:
        # Last resort: ephemeral secret (cookies won't survive a restart).
        return secrets.token_urlsafe(48)
