from qtpy.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from qtpy.QtCore import Qt, QSize, Signal

from ui.themes.colors import Colors
from ui.themes.icons import icon


class Breadcrumb(QWidget):
    home_clicked = Signal()  # emitted when the "الرئيسية" item is clicked

    def __init__(self):
        super().__init__()
        self.setFixedHeight(46)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.SURFACE};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(24, 0, 24, 0)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    def set_path(self, path_items: list):
        """path_items: e.g. ["الرئيسية", "إدارة المعايير"]. The home item is clickable."""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, item_text in enumerate(path_items):
            is_last = i == len(path_items) - 1

            if i == 0 and item_text == "الرئيسية":
                home = QPushButton(item_text)
                home.setFlat(True)
                home.setCursor(Qt.PointingHandCursor)
                home.setLayoutDirection(Qt.RightToLeft)
                hi = icon("home", color=Colors.TEXT_MUTED)
                if not hi.isNull():
                    home.setIcon(hi)
                    home.setIconSize(QSize(14, 14))
                home.setStyleSheet(f"""
                    QPushButton {{ border: none; background: transparent;
                        color: {Colors.TEXT_MUTED}; font-weight: 600; padding: 0 2px; }}
                    QPushButton:hover {{ color: {Colors.PRIMARY}; }}
                """)
                home.clicked.connect(self.home_clicked.emit)
                self.layout.addWidget(home)
            else:
                label = QLabel(item_text)
                if is_last:
                    label.setStyleSheet(
                        f"color: {Colors.PRIMARY}; font-weight: 600; border: none;")
                else:
                    label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; border: none;")
                self.layout.addWidget(label)

            if not is_last:
                separator = QLabel("‹")
                separator.setStyleSheet(
                    f"color: {Colors.BORDER_STRONG}; font-weight: bold; border: none;")
                self.layout.addWidget(separator)
