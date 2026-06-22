from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from loguru import logger

from ui.widgets.data_table import DataTable
from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.stat_card import StatCard
from ui.widgets.loading_overlay import LoadingOverlay
from ui.widgets.toast import Toast
from ui.themes.colors import Colors
from ui.permissions import can
from application.services.financial_service import FinancialService
from ui.pages.financial.transaction_dialog import TransactionDialog

MODULE = "financial"


class FinancialDashboardView(QWidget):
    def __init__(self, financial_service: FinancialService, permission=None):
        super().__init__()
        self.financial_service = financial_service
        self.permission = permission
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        header = PageHeader(
            "الإدارة المالية والميزانية",
            action_text="إضافة معاملة", action_icon="add",
        )
        header.action_clicked.connect(self.on_add_clicked)
        card.add(header)

        # Summary StatCards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        self.revenue_card = StatCard("إجمالي الإيرادات", "financial", Colors.SUCCESS, "0.00")
        self.expense_card = StatCard("إجمالي المصروفات", "financial", Colors.DANGER, "0.00")
        self.balance_card = StatCard("الرصيد الحالي", "reports", Colors.PRIMARY, "0.00")
        for c in (self.revenue_card, self.expense_card, self.balance_card):
            cards_row.addWidget(c)
        card.add_layout(cards_row)

        columns = ["التاريخ", "النوع", "المبلغ", "التصنيف", "البيان"]
        self.table = DataTable(columns)
        self.table.refresh_requested.connect(self.load_data)
        self.table.set_export_title("المعاملات المالية")
        self.table.search_requested.connect(self.on_search)
        card.add(self.table)
        main_layout.addWidget(card)

        self.overlay = LoadingOverlay(self)

    def load_data(self, search_query=""):
        self.overlay.start()
        QApplication.processEvents()
        try:
            summary = self.financial_service.get_financial_summary()
            self.revenue_card.set_value(f"{summary['total_revenue']:,.2f} EGP")
            self.expense_card.set_value(f"{summary['total_expense']:,.2f} EGP")
            self.balance_card.set_value(f"{summary['balance']:,.2f} EGP")

            txs = self.financial_service.get_all_transactions()
            if search_query:
                q = search_query.lower()
                txs = [t for t in txs if q in t.description.lower()]

            table_data = []
            for t in txs:
                t_type = "إيراد" if t.transaction_type == "revenue" else "مصروف"
                table_data.append([
                    t.date.strftime("%Y-%m-%d"),
                    t_type,
                    f"{t.amount:,.2f}",
                    t.category or "-",
                    t.description,
                ])
            self.table.set_data(table_data)
        except Exception as e:
            logger.error(f"Financial load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب البيانات")
        finally:
            self.overlay.stop()

    def on_search(self, query):
        self.load_data(query)

    def on_add_clicked(self):
        if not can(self.permission, MODULE, "create"):
            Toast.error(self, "ليس لديك صلاحية للإضافة")
            return
        dialog = TransactionDialog(self.financial_service, self)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تمت إضافة المعاملة بنجاح")
