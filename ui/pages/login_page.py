from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSpacerItem,
    QSizePolicy, QCheckBox
)
from qtpy.QtCore import Qt, Signal, QSize

from ui.themes.colors import Colors
from ui.themes.effects import apply_shadow
from ui.themes.tokens import Elevation
from ui.themes.icons import icon
from ui.prefs import load_prefs, save_prefs


class LoginPage(QWidget):
    login_successful = Signal()

    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Main login container (card)
        login_container = QFrame()
        login_container.setObjectName("loginCard")
        login_container.setMinimumWidth(420)
        login_container.setMaximumWidth(460)
        apply_shadow(login_container, Elevation.DIALOG)
        login_container.setStyleSheet(f"""
            QFrame#loginCard {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-top: 5px solid {Colors.ACCENT};
                border-radius: 14px;
            }}
        """)
        container_layout = QVBoxLayout(login_container)
        container_layout.setContentsMargins(36, 40, 36, 40)
        container_layout.setSpacing(18)

        # Lock icon
        lock = QLabel()
        li = icon("lock", color=Colors.PRIMARY)
        if not li.isNull():
            lock.setPixmap(li.pixmap(QSize(40, 40)))
        lock.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(lock)

        header_label = QLabel("تسجيل الدخول")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {Colors.PRIMARY}; border: none;"
        )
        container_layout.addWidget(header_label)

        sub_label = QLabel("مركز الخدمه المجتمعيه بكلية التمريض\nجامعة كفر الشيخ")
        sub_label.setAlignment(Qt.AlignCenter)
        sub_label.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT_SECONDARY}; border: none;")
        container_layout.addWidget(sub_label)

        container_layout.addItem(QSpacerItem(20, 16, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Username Input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        self.username_input.setMinimumHeight(42)
        container_layout.addWidget(self.username_input)

        # Password Input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(42)
        self.password_input.returnPressed.connect(self.handle_login)
        container_layout.addWidget(self.password_input)

        # Options row: show password.
        options = QHBoxLayout()
        self.show_pw = QCheckBox("إظهار كلمة المرور")
        self.show_pw.toggled.connect(self._toggle_password)
        options.addWidget(self.show_pw)
        options.addStretch()
        container_layout.addLayout(options)

        # Single "stay signed in" toggle: remembers the username AND skips the
        # login screen on the next launch (auto-login).
        auto_row = QHBoxLayout()
        self.auto_login = QCheckBox("إبقاء تسجيل الدخول (الدخول تلقائيًا عند فتح البرنامج)")
        auto_row.addStretch()
        auto_row.addWidget(self.auto_login)
        container_layout.addLayout(auto_row)

        # Inline error label (hidden until needed)
        self.error_label = QLabel("")
        self.error_label.setObjectName("fieldError")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        container_layout.addWidget(self.error_label)

        self._restore_remembered()

        # Login Button
        self.login_btn = QPushButton("تسجيل الدخول")
        self.login_btn.setMinimumHeight(46)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setProperty("class", "primary")
        self.login_btn.clicked.connect(self.handle_login)
        container_layout.addWidget(self.login_btn)

        main_layout.addWidget(login_container)

    def _toggle_password(self, show: bool):
        self.password_input.setEchoMode(QLineEdit.Normal if show else QLineEdit.Password)

    def _restore_remembered(self):
        prefs = load_prefs()
        if prefs.get("username"):
            self.username_input.setText(prefs["username"])
            self.password_input.setFocus()
        if prefs.get("auto_login"):
            self.auto_login.setChecked(True)

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()

    def handle_login(self):
        self.error_label.hide()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("يرجى إدخال اسم المستخدم وكلمة المرور.")
            return

        result = self.auth_service.login(username, password)
        if result.success:
            # Persist preferences for the next launch (never the password). A
            # single "stay signed in" toggle: when on, remember the username and
            # auto-login (restore the session, skip the login screen) next time.
            # The username is kept so that if auto-login later fails (e.g. the
            # account was removed) the login screen still shows it pre-filled.
            prefs = load_prefs()
            if self.auto_login.isChecked():
                prefs["auto_login"] = True
                prefs["username"] = username
                prefs["session_user_id"] = result.user.id
            else:
                prefs["auto_login"] = False
                prefs.pop("username", None)
                prefs.pop("session_user_id", None)
            prefs.pop("remember", None)  # drop the legacy flag
            save_prefs(prefs)
            self.login_successful.emit()
        else:
            self._show_error(result.message)
            self.password_input.clear()
            self.password_input.setFocus()
