from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from qtpy.QtCore import Signal

from ui.themes.colors import Colors
from ui.themes.typography import Typography
from ui.widgets.icon_button import IconButton


class PageHeader(QWidget):
    """A page title (+ optional subtitle) with an optional right-aligned action
    button. Replaces the repeated title-label + stretch + primary-button header."""

    action_clicked = Signal()

    def __init__(self, title, subtitle=None, action_text=None,
                 action_icon=None, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"font-size: {Typography.XL}px; font-weight: bold; color: {Colors.PRIMARY};"
        )
        text_col.addWidget(title_lbl)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet(
                f"font-size: {Typography.BASE}px; color: {Colors.TEXT_SECONDARY};"
            )
            text_col.addWidget(sub)
        row.addLayout(text_col)
        row.addStretch()

        self.action_button = None
        if action_text:
            self.action_button = IconButton(
                action_text, icon_name=action_icon, variant="primary"
            )
            self.action_button.setMinimumHeight(40)
            self.action_button.clicked.connect(self.action_clicked.emit)
            row.addWidget(self.action_button)
