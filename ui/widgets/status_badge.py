from qtpy.QtWidgets import QLabel, QWidget, QHBoxLayout
from qtpy.QtCore import Qt

from ui.themes.colors import Colors
from ui.themes.tokens import Radius

# Map a status "kind" to (background, text) colors.
_KIND_MAP = {
    "active": (Colors.SUCCESS_BG, Colors.SUCCESS_TEXT),
    "approved": (Colors.SUCCESS_BG, Colors.SUCCESS_TEXT),
    "completed": (Colors.SUCCESS_BG, Colors.SUCCESS_TEXT),
    "success": (Colors.SUCCESS_BG, Colors.SUCCESS_TEXT),
    "draft": (Colors.WARNING_BG, Colors.WARNING_TEXT),
    "pending": (Colors.WARNING_BG, Colors.WARNING_TEXT),
    "planned": (Colors.WARNING_BG, Colors.WARNING_TEXT),
    "inactive": (Colors.DANGER_BG, Colors.DANGER_TEXT),
    "archived": (Colors.DANGER_BG, Colors.DANGER_TEXT),
    "cancelled": (Colors.DANGER_BG, Colors.DANGER_TEXT),
    "info": (Colors.INFO_BG, Colors.INFO_TEXT),
}


class StatusBadge(QLabel):
    """A colored pill conveying a status."""

    def __init__(self, text: str, kind: str = "info", parent=None):
        super().__init__(text, parent)
        bg, fg = _KIND_MAP.get(kind, (Colors.INFO_BG, Colors.INFO_TEXT))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border-radius: {Radius.PILL}px; "
            f"padding: 4px 14px; font-size: 12px; font-weight: 600;"
        )

    @classmethod
    def for_cell(cls, text: str, kind: str = "info") -> QWidget:
        """Centered badge wrapper suitable for table.setCellWidget()."""
        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        lay.addWidget(cls(text, kind))
        return wrap
