from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from qtpy.QtCore import Signal
from ui.widgets.sidebar import Sidebar
from ui.widgets.topbar import TopBar
from ui.widgets.breadcrumb import Breadcrumb
from ui.widgets.footer import Footer
from ui.themes.colors import Colors
from ui.pages.standards.standards_list import StandardsListView

class DashboardLayout(QWidget):
    logout_requested = Signal()
    
    def __init__(self, services: dict):
        super().__init__()
        self.services = services
        self.auth_service = services["auth"]
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Sidebar
        self.sidebar = Sidebar(self.auth_service, permission=self.services.get("permission"))
        self.sidebar.navigation_requested.connect(self.handle_navigation)
        
        # 2. Main Content Area
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {Colors.BG};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top Bar
        self.topbar = TopBar(self.auth_service)
        content_layout.addWidget(self.topbar)
        
        # Breadcrumb
        self.breadcrumb = Breadcrumb()
        self.breadcrumb.set_path(["الرئيسية"])
        self.breadcrumb.home_clicked.connect(lambda: self.handle_navigation("dashboard"))
        content_layout.addWidget(self.breadcrumb)
        
        # Module Stack
        self.module_stack = QStackedWidget()
        content_layout.addWidget(self.module_stack)

        # Footer (developer credit + social links)
        content_layout.addWidget(Footer())

        # Assemble (Sidebar on Right in RTL)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_widget)
        
        self.init_modules()
        
    def init_modules(self):
        # Create placeholders for modules
        self.modules = {}
        
        module_names = {
            "dashboard": "لوحة القيادة",
            "standards": "إدارة المعايير",
            "documents": "نظام الوثائق",
            "records": "السجلات",
            "training": "البرامج التدريبية",
            "hr": "شؤون العاملين",
            "financial": "المالية والشراكات",
            "reports": "التقارير والإحصائيات",
            "lookups": "البيانات المرجعية",
            "admin": "إدارة النظام",
            "backup": "النسخ الاحتياطي",
            "remote": "البوابات والإدارة عن بُعد",
            "profile": "إعدادات الحساب",
            "settings": "الإعدادات"
        }
        
        perm = self.services.get("permission")
        for key, title in module_names.items():
            if key == "standards":
                widget = StandardsListView(self.services["quality"], permission=perm)
            elif key == "dashboard":
                from ui.pages.dashboard.dashboard_home import DashboardHome
                widget = DashboardHome(self.services, navigate=self.handle_navigation,
                                       permission=self.services.get("permission"))
            elif key == "documents":
                from ui.pages.documents.documents_list import DocumentsListView
                widget = DocumentsListView(self.services["document"], permission=perm)
            elif key == "hr":
                from ui.pages.hr.employee_directory import EmployeeDirectoryView
                widget = EmployeeDirectoryView(self.services["hr"], permission=perm)
            elif key == "training":
                from ui.pages.training.training_list import TrainingListView
                widget = TrainingListView(self.services["training"], permission=perm)
            elif key == "financial":
                from qtpy.QtWidgets import QTabWidget
                from ui.pages.financial.financial_dashboard import FinancialDashboardView
                from ui.pages.financial.budget_management import BudgetManagementView
                from ui.pages.partnerships.partnerships_list import PartnershipsListView

                # Financial + Budget + Partnerships combined into a tabbed module.
                tabs = QTabWidget()
                tabs.addTab(FinancialDashboardView(self.services["financial"], permission=perm),
                            "الإدارة المالية")
                tabs.addTab(BudgetManagementView(self.services["financial"], permission=perm),
                            "إدارة الميزانية")
                tabs.addTab(PartnershipsListView(self.services["partnership"], permission=perm),
                            "إدارة الشراكات")

                widget = tabs
            elif key == "reports":
                from ui.pages.reports.reports_dashboard import ReportsDashboardView
                widget = ReportsDashboardView(self.services)
            elif key == "settings":
                from ui.pages.settings.settings_view import SettingsView
                widget = SettingsView()
            elif key == "records":
                from ui.pages.records.records_list import RecordsListView
                widget = RecordsListView(self.services["record"], permission=perm)
            elif key == "admin":
                from ui.pages.admin.admin_dashboard import AdminDashboardView
                widget = AdminDashboardView(self.services)
            elif key == "backup":
                from ui.pages.backup.backup_restore import BackupRestoreView
                widget = BackupRestoreView(permission=perm)
            elif key == "remote":
                from ui.pages.remote.remote_portals import RemotePortalsView
                widget = RemotePortalsView(permission=perm)
            elif key == "lookups":
                from ui.pages.lookups.lookups_view import LookupsView
                widget = LookupsView(self.services, permission=perm)
            elif key == "profile":
                # This is a bit of a hack: ProfileDialog is a QDialog, not a QWidget to be embedded.
                # Since the sidebar emits navigation events, we can intercept it in handle_navigation instead.
                # So we won't add it to the stack here.
                continue
            
            self.module_stack.addWidget(widget)
            self.modules[key] = {
                "widget": widget,
                "title": title
            }
            
        self.module_stack.setCurrentWidget(self.modules["dashboard"]["widget"])

    def handle_navigation(self, module_key: str):
        if module_key == "logout":
            from ui.widgets.confirm import confirm
            if confirm(self, "هل تريد تسجيل الخروج من النظام؟", title="تأكيد الخروج"):
                self.logout_requested.emit()
            return
            
        if module_key == "profile":
            from ui.pages.admin.profile_dialog import ProfileDialog
            dialog = ProfileDialog(self.auth_service, self)
            dialog.exec()
            # If username changed, update topbar
            self.topbar.setup_ui()
            return
            
        if module_key in self.modules:
            # Defense: only allow navigation to pages the current user may see
            # (the sidebar's nav buttons reflect the role/permission gating).
            if module_key not in self.sidebar.nav_buttons:
                return
            self.module_stack.setCurrentWidget(self.modules[module_key]["widget"])
            self.topbar.set_title(self.modules[module_key]["title"])
            self.breadcrumb.set_path(["الرئيسية", self.modules[module_key]["title"]])
            # Keep the sidebar selection in sync (e.g. when navigating from a KPI).
            self.sidebar.set_active(module_key)
