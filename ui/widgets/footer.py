from qtpy.QtWidgets import QWidget, QHBoxLayout, QLabel
from qtpy.QtCore import QUrl
from qtpy.QtGui import QDesktopServices

from ui.themes.colors import Colors
from ui.widgets.icon_button import IconButton

# (icon name, tooltip, url)
_LINKS = [
    ("github", "GitHub", "https://github.com/eslamghazi/"),
    ("linkedin", "LinkedIn", "https://www.linkedin.com/in/eslam-gamal-ghazi/"),
    ("facebook", "Facebook", "https://www.facebook.com/eslam.ghazi.7"),
]


class Footer(QWidget):
    """App footer: developer credit + social links."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setStyleSheet(
            f"background-color: {Colors.SURFACE}; "
            f"border-top: 1px solid {Colors.BORDER};"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(8)

        credit = QLabel("تطوير وتنفيذ: إسلام جمال غازي")
        credit.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        layout.addWidget(credit)
        layout.addStretch()

        for name, tooltip, url in _LINKS:
            btn = IconButton(icon_name=name, variant="secondary",
                             tooltip=tooltip, icon_only=True)
            btn.clicked.connect(
                lambda _checked, u=url: QDesktopServices.openUrl(QUrl(u)))
            layout.addWidget(btn)
