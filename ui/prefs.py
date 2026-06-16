"""Lightweight per-machine UI preferences (e.g. 'remember me' username),
stored as JSON under the data dir. Never stores passwords."""
import json

from config import settings

_PATH = settings.DATA_DIR / "app_prefs.json"


def load_prefs() -> dict:
    try:
        return json.loads(_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_prefs(prefs: dict):
    try:
        _PATH.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
