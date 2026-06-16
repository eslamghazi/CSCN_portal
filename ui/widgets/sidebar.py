from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QScrollArea
)
from qtpy.QtCore import Qt, Signal, QSize

from ui.themes.colors import Colors
from ui.themes.icons import icon
from ui.permissions import can

# Sidebar nav key -> permission module for the "view" gate.
MODULE_PERMISSION = {
    "standards": "quality",
    "documents": "documents",
    "records": "records",
    "training": "training",
    "hr": "hr",
    "financial": "financial",
    "reports": "reports",
}


def can_view(permission, nav_key: str) -> bool:
    """Whether the current user may see a content page (dashboard/profile always)."""
    module = MODULE_PERMISSION.get(nav_key)
    if module is None:
        return True
    return can(permission, module, "view")


class Sidebar(QFrame):
    navigation_requested = Signal(str)  # Emits the name of the module to navigate to

    def __init__(self, auth_service=None, permission=None):
        super().__init__()
        self.auth_service = auth_service
        self.permission = permission
        self.setObjectName("sidebar")
        self.setFixedWidth(264)
        self.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.SIDEBAR_BG_TOP}, stop:1 {Colors.SIDEBAR_BG_BOTTOM});
                color: {Colors.SIDEBAR_TEXT};
                border: none;
            }}
            QPushButton {{
                /* With RTL layout direction, text-align:left visually
                   right-aligns the content and places the icon on the right. */
                text-align: left;
                padding: 12px 18px;
                background-color: transparent;
                color: {Colors.SIDEBAR_TEXT};
                border: none;
                font-size: 14px;
                font-weight: 600;
                border-radius: 8px;
                margin: 2px 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SIDEBAR_HOVER_BG};
            }}
            QPushButton:checked {{
                background-color: {Colors.SIDEBAR_ACTIVE_BG};
                border-right: 3px solid {Colors.SIDEBAR_ACTIVE_BAR};
                color: {Colors.SIDEBAR_TEXT};
            }}
            QLabel#logoLabel {{
                background-color: transparent;
                font-size: 15px;
                font-weight: bold;
                color: {Colors.SIDEBAR_TEXT};
                padding: 8px 10px;
            }}
            QFrame#separator {{
                background-color: rgba(255, 255, 255, 0.18);
                border: none;
                max-height: 1px;
                margin: 4px 16px 10px 16px;
            }}
            QPushButton#logoutBtn {{
                color: {Colors.SIDEBAR_LOGOUT};
                margin-top: 10px;
            }}
            QPushButton#logoutBtn:hover {{
                background-color: rgba(252, 165, 165, 0.15);
            }}
            QScrollArea#sidebarScroll {{
                background: transparent;
                border: none;
            }}
            QScrollArea#sidebarScroll > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 2px 2px 2px 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.22);
                border-radius: 4px;
                min-height: 36px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.40);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0; background: none; border: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        self.setup_ui()

    def refresh(self):
        """Rebuild the nav (role-gated items) — call after login/logout."""
        self.setup_ui()

    def setup_ui(self):
        # Allow rebuilding: detach the previous layout onto a throwaway widget.
        if self.layout() is not None:
            QWidget().setLayout(self.layout())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(4)

        # Logo / Title Area (pinned at top) — full Arabic center name (not the
        # "CSCN" abbreviation), matching the login screen branding.
        logo_label = QLabel("مركز الخدمه المجتمعيه بكلية التمريض\nجامعة كفر الشيخ")
        logo_label.setObjectName("logoLabel")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setWordWrap(True)
        layout.addWidget(logo_label)

        separator = QFrame()
        separator.setObjectName("separator")
        layout.addWidget(separator)

        # Scrollable nav area: the nav buttons live here so they scroll (with a
        # styled thin scrollbar) when they don't all fit; logo stays pinned above
        # and logout/version pinned below.
        scroll = QScrollArea()
        scroll.setObjectName("sidebarScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.viewport().setStyleSheet("background: transparent;")
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)
        scroll.setWidget(nav_container)

        # Navigation Buttons (key, label). Content pages are gated by the
        # current user's "view" permission for the mapped module.
        self.nav_buttons = {}
        content = [
            ("dashboard", "لوحة القيادة"),
            ("standards", "إدارة المعايير"),
            ("documents", "نظام الوثائق"),
            ("records", "السجلات"),
            ("training", "البرامج التدريبية"),
            ("hr", "شؤون العاملين"),
            ("financial", "المالية والشراكات"),
            ("reports", "التقارير والإحصائيات"),
        ]
        modules = [
            (key, label) for key, label in content
            if can_view(self.permission, key)
        ]

        current_user = self.auth_service.get_current_user() if self.auth_service else None
        role = current_user.role_name if current_user else None
        # Lookups (reference data) for admin + superadmin.
        if role in ("superadmin", "admin"):
            modules.append(("lookups", "البيانات المرجعية"))
        # System admin / backup / remote oversight are superadmin-only.
        if role == "superadmin":
            modules.append(("admin", "إدارة النظام"))
            modules.append(("backup", "النسخ الاحتياطي"))
            modules.append(("remote", "البوابات والإدارة عن بُعد"))
        modules.append(("profile", "إعدادات الحساب"))

        for key, text in modules:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(icon(key, color=Colors.SIDEBAR_TEXT))
            btn.setIconSize(QSize(18, 18))
            # RTL so the icon sits on the right of the text and content hugs the right.
            btn.setLayoutDirection(Qt.RightToLeft)
            btn.clicked.connect(lambda checked=False, k=key: self.handle_nav_click(k))
            self.nav_buttons[key] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        layout.addWidget(scroll, 1)

        # Logout (pinned at bottom)
        self.logout_btn = QPushButton("تسجيل الخروج")
        self.logout_btn.setObjectName("logoutBtn")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setIcon(icon("logout", color=Colors.SIDEBAR_LOGOUT))
        self.logout_btn.setIconSize(QSize(18, 18))
        self.logout_btn.setLayoutDirection(Qt.RightToLeft)
        self.logout_btn.clicked.connect(lambda: self.navigation_requested.emit("logout"))
        layout.addWidget(self.logout_btn)

        # Version Label
        version_label = QLabel("v1.1.0")
        version_label.setStyleSheet(
            f"color: {Colors.SIDEBAR_TEXT_MUTED}; font-size: 11px; background: transparent;"
        )
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        if "dashboard" in self.nav_buttons:
            self.nav_buttons["dashboard"].setChecked(True)

    def set_active(self, key: str):
        """Sync the checked state to the active module (used by programmatic nav)."""
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)

    def handle_nav_click(self, key: str):
        self.set_active(key)
        self.navigation_requested.emit(key)
