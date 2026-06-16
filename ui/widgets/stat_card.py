from qtpy.QtWidgets import QHBoxLayout, QLabel
from qtpy.QtCore import Qt, Signal, QSize

from ui.widgets.card import Card
from ui.themes.colors import Colors
from ui.themes.typography import Typography
from ui.themes.tokens import Spacing, Radius
from ui.themes.icons import icon


class StatCard(Card):
    """A KPI card: icon + title + big value, with a colored leading accent and
    optional click navigation. Unifies the dashboard KPI and financial summary
    cards."""

    clicked = Signal()

    def __init__(self, title, icon_name, accent, value="0",
                 clickable=False, parent=None):
        super().__init__(padding=Spacing.LG, parent=parent)
        self._clickable = clickable
        # Leading accent (right side in RTL).
        self.setStyleSheet(
            f"QFrame#card {{ background-color: {Colors.SURFACE}; "
            f"border-radius: {Radius.LG}px; border-right: 5px solid {accent}; }}"
        )

        head = QHBoxLayout()
        head.setSpacing(8)
        icon_lbl = QLabel()
        qic = icon(icon_name, color=accent)
        if not qic.isNull():
            icon_lbl.setPixmap(qic.pixmap(QSize(22, 22)))
        head.addWidget(icon_lbl)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: {Typography.BASE}px;"
        )
        head.addWidget(title_lbl)
        head.addStretch()
        self.add_layout(head)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(
            f"color: {Colors.TEXT}; font-size: {Typography.DISPLAY}px; font-weight: bold;"
        )
        self.add(self.value_label)

        if clickable:
            self.setCursor(Qt.PointingHandCursor)

    def set_value(self, value):
        self.value_label.setText(str(value))

    def mousePressEvent(self, event):
        if self._clickable:
            self.clicked.emit()
        super().mousePressEvent(event)
