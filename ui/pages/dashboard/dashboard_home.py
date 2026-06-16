from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout
from loguru import logger

from ui.themes.colors import Colors
from ui.themes.typography import Typography
from ui.widgets.stat_card import StatCard
from ui.widgets.busy import busy
from ui.widgets.toast import Toast
from ui.permissions import can

# (permission module, nav key, title, icon, accent, value function)
_KPIS = [
    ("hr", "hr", "عدد الموظفين", "kpi_employees", Colors.KPI_GREEN,
     lambda s: len(s["hr"].get_all_employees())),
    ("quality", "standards", "إجمالي المعايير", "kpi_standards", Colors.KPI_BLUE,
     lambda s: len(s["quality"].get_all_standards())),
    ("documents", "documents", "الوثائق المعتمدة", "kpi_docs", Colors.KPI_AMBER,
     lambda s: len([d for d in s["document"].get_all_documents() if d.status == "approved"])),
    ("training", "training", "البرامج التدريبية", "kpi_training", Colors.KPI_PURPLE,
     lambda s: len(s["training"].get_all_programs())),
]


class DashboardHome(QWidget):
    def __init__(self, services: dict, navigate=None, permission=None):
        super().__init__()
        self.services = services
        self.navigate = navigate
        self.permission = permission
        self._kpis = []  # (StatCard, value_fn) for the cards this user may see
        self.setup_ui()
        self.load_kpis()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(24)

        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.PRIMARY}, stop:1 {Colors.ACCENT});
                border-radius: 14px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(28, 26, 28, 26)
        banner_layout.setSpacing(6)
        welcome_label = QLabel("مرحباً بك في نظام إدارة مركز تنمية مهارات التمريض")
        welcome_label.setStyleSheet(
            f"color: {Colors.TEXT_ON_PRIMARY}; font-size: {Typography.XXL}px; font-weight: bold;")
        welcome_label.setWordWrap(True)
        banner_layout.addWidget(welcome_label)
        sub_welcome = QLabel(
            "جامعة كفر الشيخ — يمكن الوصول السريع لجميع الخدمات من القائمة الجانبية.")
        sub_welcome.setStyleSheet(f"color: {Colors.ACCENT_SOFT}; font-size: {Typography.BASE}px;")
        banner_layout.addWidget(sub_welcome)
        layout.addWidget(banner)

        kpi_title = QLabel("نظرة عامة")
        kpi_title.setStyleSheet(
            f"font-size: {Typography.LG}px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(kpi_title)

        grid = QGridLayout()
        grid.setSpacing(18)
        col = 0
        for module, nav_key, title, icon_name, accent, value_fn in _KPIS:
            if not can(self.permission, module, "view"):
                continue
            card = StatCard(title, icon_name, accent, clickable=True)
            card.clicked.connect(lambda k=nav_key: self._go(k))
            grid.addWidget(card, 0, col)
            self._kpis.append((card, value_fn))
            col += 1
        layout.addLayout(grid)
        layout.addStretch()

    def _go(self, module_key: str):
        if self.navigate:
            self.navigate(module_key)

    def load_kpis(self):
        try:
            with busy(self, "جاري تحميل البيانات..."):
                for card, value_fn in self._kpis:
                    card.set_value(value_fn(self.services))
        except Exception as e:
            logger.error(f"Failed to load dashboard KPIs: {e}")
            Toast.error(self, "تعذّر تحميل بيانات اللوحة")
