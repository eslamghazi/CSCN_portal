from qtpy.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox
from qtpy.QtCore import QDate
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.toast import Toast
from application.services.financial_service import FinancialService, TransactionDTO


class TransactionDialog(BaseDialog):
    def __init__(self, financial_service: FinancialService, parent=None):
        super().__init__("إضافة معاملة مالية", parent, min_width=460)
        self.financial_service = financial_service

        type_combo = QComboBox()
        type_combo.addItems(["إيراد", "مصروف"])
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        self.type_field, self.date_field = self.add_row(
            ("النوع:", type_combo), ("التاريخ:", date_input))

        amount = QDoubleSpinBox()
        amount.setRange(0.01, 1_000_000_000.0)
        amount.setDecimals(2)
        self.amount_field, self.category_field = self.add_row(
            ("المبلغ (EGP):", amount), ("التصنيف/المصدر:", QLineEdit()))

        self.desc_field = self.add_field("البيان:", QLineEdit(), required=True)
        self.ref_field = self.add_field("رقم المرجع / الإيصال:", QLineEdit())

        self.build_buttons()

    def on_save(self):
        self.desc_field.clear_error()
        desc = self.desc_field.text().strip()
        if not desc:
            self.desc_field.set_error("بيان المعاملة مطلوب.")
            return

        category = self.category_field.text().strip() or None
        dto = TransactionDTO(
            transaction_type="revenue" if self.type_field.widget.currentIndex() == 0 else "expense",
            amount=self.amount_field.widget.value(),
            date=self.date_field.widget.date().toPython(),
            description=desc,
            source=category,
            category=category,
            reference_number=self.ref_field.text().strip() or None,
        )
        try:
            self.financial_service.add_transaction(dto)
            self.accept()
        except Exception as e:
            logger.error(f"Add transaction failed: {e}")
            Toast.error(self, "تعذّر إضافة المعاملة")
