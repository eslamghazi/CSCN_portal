from qtpy.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from qtpy.QtCore import Qt, QDate, QSize

from ui.themes.colors import Colors
from ui.themes.effects import apply_shadow
from ui.themes.tokens import Elevation
from ui.themes.icons import icon


class TopBar(QFrame):
    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.setFixedHeight(64)
        apply_shadow(self, Elevation.TOPBAR)
        self.setStyleSheet(f"QFrame {{ background-color: {Colors.SURFACE}; border: none; }}")
        self.setup_ui()

    def setup_ui(self):
        # Clear existing layout if re-called (on login / profile change)
        if self.layout():
            QWidget().setLayout(self.layout())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(10)

        self.title_label = QLabel("الرئيسية")
        self.title_label.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {Colors.PRIMARY}; border: none;"
        )
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Date Display (icon + text)
        date_icon = QLabel()
        di = icon("calendar", color=Colors.TEXT_SECONDARY)
        if not di.isNull():
            date_icon.setPixmap(di.pixmap(QSize(15, 15)))
        layout.addWidget(date_icon)

        today = QDate.currentDate().toString("yyyy-MM-dd")
        date_label = QLabel(today)
        # Force LTR so the date reads 2026-06-10; in the app's RTL layout the
        # neutral digit/hyphen sequence would otherwise be flipped to 10-06-2026.
        date_label.setLayoutDirection(Qt.LeftToRight)
        date_label.setStyleSheet(
            f"font-size: 14px; color: {Colors.TEXT_SECONDARY}; border: none; margin-left: 16px;"
        )
        layout.addWidget(date_label)

        # User Info
        current_user = self.auth_service.get_current_user()
        user_name = current_user.full_name if current_user else "مستخدم"
        initials = user_name.split()[0][0] if user_name else "م"

        self.user_label = QLabel(f"مرحباً، {user_name}")
        self.user_label.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {Colors.TEXT}; "
            f"border: none; margin-left: 8px;"
        )
        layout.addWidget(self.user_label)

        # Avatar Circle
        avatar = QLabel(initials)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(38, 38)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_ON_PRIMARY};
                border-radius: 19px;
                font-weight: bold;
                font-size: 16px;
            }}
        """)
        layout.addWidget(avatar)

    def set_title(self, title: str):
        self.title_label.setText(title)
