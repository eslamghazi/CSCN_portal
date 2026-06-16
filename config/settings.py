import os
import sys
from pathlib import Path


def apply_env_file(path: Path):
    """Apply KEY=VALUE lines from a .env-style file into os.environ WITHOUT
    overriding variables already set. Ignores blanks/comments. Never raises."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


def _load_dotenv():
    """Load a .env file into the environment. Searched (in order): the bundle
    embedded inside a frozen exe (PyInstaller _MEIPASS), next to the executable
    when frozen, the project root in dev, and the CWD. The embedded copy means a
    built exe needs no external .env. Must run before any env var below is read."""
    candidates = []
    if getattr(sys, "frozen", False):
        # PyInstaller --onefile extracts bundled data here; --add-data ".env;."
        # places the embedded .env in this directory.
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass))
        candidates.append(Path(sys.executable).resolve().parent)
    else:
        candidates.append(Path(__file__).resolve().parent.parent)
    candidates.append(Path.cwd())

    seen = set()
    for directory in candidates:
        env_path = directory / ".env"
        if env_path in seen:
            continue
        seen.add(env_path)
        if env_path.exists():
            apply_env_file(env_path)


_load_dotenv()

# All runtime data is stored in a fixed, writable location OUTSIDE the app
# bundle so it persists across updates and works for frozen (PyInstaller)
# builds (onedir/onefile). Override with the CSCN_portal_DATA_DIR env var if needed.
DATA_DIR = Path(os.environ.get("CSCN_portal_DATA_DIR", r"C:\CSCN"))

# Database path (forward slashes in the URL work on Windows too)
DB_FILE = DATA_DIR / "center_management.db"
DATABASE_URL = f"sqlite:///{DB_FILE.as_posix()}"

# File storage paths
UPLOADS_DIR = DATA_DIR / "uploads"
EXPORTS_DIR = DATA_DIR / "exports"
REPORTS_DIR = DATA_DIR / "reports"
BACKUPS_DIR = DATA_DIR / "backups"
LOGS_DIR = DATA_DIR / "logs"

# Ensure all data directories exist (best-effort; never fail import).
for _directory in (DATA_DIR, UPLOADS_DIR, EXPORTS_DIR, REPORTS_DIR, BACKUPS_DIR, LOGS_DIR):
    try:
        _directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
