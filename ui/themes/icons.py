"""Semantic icon registry backed by qtawesome (FontAwesome 5).

qtawesome is imported defensively so the app — and the test suite, which does
`import main` — still works if the package is missing. Every lookup degrades to
an empty QIcon() and never raises. Icons also require a running QApplication;
if called too early, the guarded call simply returns an empty icon.
"""
from qtpy.QtGui import QIcon
from qtpy.QtCore import QSize
from qtpy.QtWidgets import QLabel

from ui.themes.colors import Colors

try:
    import qtawesome as qta
    _HAVE_QTA = True
except Exception:  # pragma: no cover - environment without qtawesome
    qta = None
    _HAVE_QTA = False

# Semantic name -> FontAwesome 5 id
REGISTRY = {
    # app / brand
    "app": "fa5s.user-nurse",
    # navigation
    "dashboard": "fa5s.tachometer-alt",
    "standards": "fa5s.clipboard-check",
    "documents": "fa5s.folder-open",
    "records": "fa5s.archive",
    "training": "fa5s.graduation-cap",
    "hr": "fa5s.users",
    "financial": "fa5s.coins",
    "reports": "fa5s.chart-line",
    "lookups": "fa5s.tags",
    "admin": "fa5s.user-shield",
    "profile": "fa5s.user-cog",
    "settings": "fa5s.cog",
    "logout": "fa5s.sign-out-alt",
    # chrome
    "calendar": "fa5s.calendar-alt",
    "home": "fa5s.home",
    "search": "fa5s.search",
    "lock": "fa5s.lock",
    "user": "fa5s.user",
    "chevron": "fa5s.chevron-left",
    # actions
    "add": "fa5s.plus",
    "edit": "fa5s.pen",
    "delete": "fa5s.trash",
    "view": "fa5s.eye",
    "download": "fa5s.download",
    "upload": "fa5s.upload",
    "save": "fa5s.check",
    "cancel": "fa5s.times",
    "agreements": "fa5s.file-signature",
    "browse": "fa5s.paperclip",
    "backup": "fa5s.database",
    "export": "fa5s.file-export",
    "refresh": "fa5s.sync-alt",
    # status / toast
    "success": "fa5s.check-circle",
    "warning": "fa5s.exclamation-triangle",
    "error": "fa5s.times-circle",
    "info": "fa5s.info-circle",
    # remote / network
    "remote": "fa5s.network-wired",
    "server": "fa5s.server",
    # social / brand
    "github": "fa5b.github",
    "linkedin": "fa5b.linkedin",
    "facebook": "fa5b.facebook",
    # kpi
    "kpi_employees": "fa5s.users",
    "kpi_standards": "fa5s.clipboard-list",
    "kpi_docs": "fa5s.folder-open",
    "kpi_training": "fa5s.graduation-cap",
}


def icon(name: str, color: str = Colors.TEXT, size: int = None) -> QIcon:
    """Return a colored QIcon for a semantic name, or an empty QIcon on any failure."""
    if not _HAVE_QTA:
        return QIcon()
    fa_id = REGISTRY.get(name, name)
    try:
        return qta.icon(fa_id, color=color)
    except Exception:
        return QIcon()


def pixmap_label(name: str, size: int = 16, color: str = Colors.TEXT) -> QLabel:
    """A QLabel showing a semantic icon as a pixmap (for non-button contexts)."""
    label = QLabel()
    qicon = icon(name, color=color)
    if not qicon.isNull():
        label.setPixmap(qicon.pixmap(QSize(size, size)))
    return label
