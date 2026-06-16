from qtpy.QtWidgets import QMainWindow, QStackedWidget
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_layout import DashboardLayout

class MainWindow(QMainWindow):
    def __init__(self, services: dict):
        super().__init__()
        self.services = services
        self.auth_service = services["auth"]
        
        self.setWindowTitle("النظام الإلكتروني لإدارة مركز الخدمه المجتمعيه بكلية التمريض جامعة كفر الشيخ")
        self.setMinimumSize(1024, 768)
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.init_pages()
        self.determine_initial_page()

    def init_pages(self):
        # Only the login page exists up-front. The dashboard is built AFTER login
        # so every page's role/permission gating (sidebar items, add/edit/delete
        # buttons, KPI cards) reflects the actual logged-in user.
        self.login_page = LoginPage(self.auth_service)
        self.login_page.login_successful.connect(self.on_login_success)
        self.stacked_widget.addWidget(self.login_page)
        self.dashboard_page = None

    def determine_initial_page(self):
        # If the user opted into "stay signed in", restore the session and go
        # straight to the dashboard; otherwise show the login page.
        if self._try_auto_login():
            return
        self.stacked_widget.setCurrentWidget(self.login_page)

    def _try_auto_login(self) -> bool:
        from ui.prefs import load_prefs
        prefs = load_prefs()
        if not prefs.get("auto_login"):
            return False
        user_id = prefs.get("session_user_id")
        if not user_id:
            return False
        if self.auth_service.restore_session(user_id) is None:
            return False  # account removed/deactivated -> fall back to login
        self.on_login_success()
        return True

    def on_login_success(self):
        # (Re)build the dashboard for the current user (handles re-login as a
        # different role too).
        if self.dashboard_page is not None:
            self.stacked_widget.removeWidget(self.dashboard_page)
            self.dashboard_page.deleteLater()
        self.dashboard_page = DashboardLayout(self.services)
        self.dashboard_page.logout_requested.connect(self.on_logout)
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.setCurrentWidget(self.dashboard_page)
        self.showMaximized()

    def on_logout(self):
        self.auth_service.logout()
        # An explicit logout disables auto-login, so the user reaches the login
        # screen and isn't signed straight back in. They can re-enable it on the
        # next login.
        from ui.prefs import load_prefs, save_prefs
        prefs = load_prefs()
        prefs["auto_login"] = False
        prefs.pop("session_user_id", None)
        save_prefs(prefs)
        self.login_page.auto_login.setChecked(False)
        self.login_page.password_input.clear()
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.showNormal()
