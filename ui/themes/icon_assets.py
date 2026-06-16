"""Renders small qtawesome glyphs to PNG files so they can be referenced from
QSS `image: url(...)` (spin-box arrows, combo/date drop-down, checkbox tick).

Qt stops drawing native sub-control arrows once a widget is styled via QSS, so
we must supply images. Generation is guarded: it requires a running
QApplication and qtawesome; otherwise it returns {} and the stylesheet simply
omits the image lines (e.g. in unit tests with no QApplication).
"""
import tempfile
from pathlib import Path

from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QSize

from ui.themes.colors import Colors

try:
    import qtawesome as qta
    _HAVE_QTA = True
except Exception:  # pragma: no cover
    qta = None
    _HAVE_QTA = False

_CACHE_DIR = Path(tempfile.gettempdir()) / "CSCN_portal_qss_icons"

# name -> (fontawesome id, color, pixel size)
_SPECS = {
    "chevron_up": ("fa5s.chevron-up", Colors.TEXT_SECONDARY, 12),
    "chevron_down": ("fa5s.chevron-down", Colors.TEXT_SECONDARY, 12),
    # Solid carets read much better than thin chevrons inside spin buttons.
    "caret_up": ("fa5s.caret-up", Colors.PRIMARY, 16),
    "caret_down": ("fa5s.caret-down", Colors.PRIMARY, 16),
    "calendar": ("fa5s.calendar-alt", Colors.PRIMARY, 16),
    "check": ("fa5s.check", Colors.TEXT_ON_PRIMARY, 12),
}

_cache = None


def ensure_qss_assets() -> dict:
    """Return {name: posix_path} for the QSS glyphs, or {} if unavailable."""
    global _cache
    if _cache is not None:
        return _cache
    if not _HAVE_QTA or QApplication.instance() is None:
        return {}
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        result = {}
        for name, (fa_id, color, size) in _SPECS.items():
            path = _CACHE_DIR / f"{name}_{color.lstrip('#')}_{size}.png"
            if not path.exists():
                pixmap = qta.icon(fa_id, color=color).pixmap(QSize(size, size))
                pixmap.save(str(path), "PNG")
            result[name] = path.as_posix()
        _cache = result
        return result
    except Exception:  # pragma: no cover
        return {}
