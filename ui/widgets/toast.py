from qtpy.QtWidgets import QFrame, QHBoxLayout, QLabel
from qtpy.QtCore import QTimer, QSize

from ui.themes.colors import Colors
from ui.themes.tokens import Radius, Elevation
from ui.themes.effects import apply_shadow
from ui.themes.icons import icon

_KIND = {
    "success": (Colors.SUCCESS_BG, Colors.SUCCESS_TEXT, "success"),
    "error": (Colors.DANGER_BG, Colors.DANGER_TEXT, "error"),
    "info": (Colors.INFO_BG, Colors.INFO_TEXT, "info"),
}


class Toast(QFrame):
    """A transient, auto-dismissing notification anchored to the bottom-center
    of the top-level window. Use the success/error/info classmethods."""

    def __init__(self, parent, message, kind="info"):
        host = parent.window() if parent is not None else None
        super().__init__(host)
        bg, fg, icon_name = _KIND.get(kind, _KIND["info"])
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border-radius: {Radius.MD}px; }} "
            f"QLabel {{ color: {fg}; font-weight: 600; background: transparent; }}"
        )
        apply_shadow(self, Elevation.CARD)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)
        icon_lbl = QLabel()
        qic = icon(icon_name, color=fg)
        if not qic.isNull():
            icon_lbl.setPixmap(qic.pixmap(QSize(18, 18)))
        lay.addWidget(icon_lbl)
        lay.addWidget(QLabel(message))

        self._reposition()
        if host is not None:
            self.show()
            self.raise_()
            QTimer.singleShot(3200, self.close)

    def _reposition(self):
        host = self.parentWidget()
        if host is None:
            return
        self.adjustSize()
        x = (host.width() - self.width()) // 2
        y = host.height() - self.height() - 36
        self.move(max(0, x), max(0, y))

    @staticmethod
    def success(parent, message):
        return Toast(parent, message, "success")

    @staticmethod
    def error(parent, message):
        return Toast(parent, message, "error")

    @staticmethod
    def info(parent, message):
        return Toast(parent, message, "info")
