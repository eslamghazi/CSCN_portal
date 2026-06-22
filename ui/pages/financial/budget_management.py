from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
    QDateEdit, QDoubleSpinBox
)
from qtpy.QtCore import QDate
from sqlalchemy.exc import IntegrityError
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.data_table import DataTable, Row, Action
from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from ui.widgets.busy import busy
from ui.permissions import can
from application.services.financial_service import (
    FinancialService, FiscalYearDTO, BudgetItemDTO,
)

MODULE = "financial"
FY_STATUS = [("active", "نشطة"), ("closed", "مغلقة")]
FY_STATUS_LABELS = dict(FY_STATUS)


class FiscalYearDialog(BaseDialog):
    def __init__(self, financial_service, parent=None, fiscal_year=None):
        super().__init__(
            "إضافة سنة مالية" if not fiscal_year else "تعديل السنة المالية",
            parent, min_width=460)
        self.fs = financial_service
        self.fiscal_year = fiscal_year

        self.name = self.add_field("اسم السنة المالية:", QLineEdit(), required=True)
        start = QDateEdit()
        start.setCalendarPopup(True)
        start.setDate(QDate(QDate.currentDate().year(), 1, 1))
        end = QDateEdit()
        end.setCalendarPopup(True)
        end.setDate(QDate(QDate.currentDate().year(), 12, 31))
        self.start, self.end = self.add_row(
            ("تاريخ البداية:", start), ("تاريخ النهاية:", end))
        status = QComboBox()
        for value, label in FY_STATUS:
            status.addItem(label, value)
        self.status = self.add_field("الحالة:", status)
        self.build_buttons()
        self._populate()

    def _populate(self):
        if not self.fiscal_year:
            return
        fy = self.fiscal_year
        self.name.widget.setText(fy.name)
        if fy.start_date:
            self.start.widget.setDate(fy.start_date)
        if fy.end_date:
            self.end.widget.setDate(fy.end_date)
        for idx in range(self.status.widget.count()):
            if self.status.widget.itemData(idx) == fy.status:
                self.status.widget.setCurrentIndex(idx)

    def on_save(self):
        self.name.clear_error()
        name = self.name.text().strip()
        if not name:
            self.name.set_error("الاسم مطلوب.")
            return
        dto = FiscalYearDTO(
            id=self.fiscal_year.id if self.fiscal_year else None,
            name=name,
            start_date=self.start.widget.date().toPython(),
            end_date=self.end.widget.date().toPython(),
            status=self.status.widget.currentData(),
        )
        try:
            if self.fiscal_year:
                self.fs.update_fiscal_year(dto)
            else:
                self.fs.create_fiscal_year(dto)
            self.accept()
        except IntegrityError:
            self.name.set_error("اسم السنة المالية مكرّر.")
        except Exception as e:
            logger.error(f"Save fiscal year failed: {e}")
            Toast.error(self, "تعذّر الحفظ")


class BudgetItemDialog(BaseDialog):
    def __init__(self, financial_service, fiscal_year_id, parent=None, item=None):
        super().__init__(
            "إضافة بند ميزانية" if not item else "تعديل البند", parent, min_width=460)
        self.fs = financial_service
        self.fiscal_year_id = fiscal_year_id
        self.item = item

        self.name = self.add_field("اسم البند:", QLineEdit(), required=True)
        amount = QDoubleSpinBox()
        amount.setRange(0, 1_000_000_000)
        amount.setDecimals(2)
        self.amount = self.add_field("المبلغ المخصّص (EGP):", amount)
        desc = QTextEdit()
        desc.setMaximumHeight(70)
        self.desc = self.add_field("الوصف:", desc)
        self.build_buttons()
        self._populate()

    def _populate(self):
        if not self.item:
            return
        self.name.widget.setText(self.item.name)
        self.amount.widget.setValue(float(self.item.allocated_amount or 0))
        self.desc.widget.setPlainText(self.item.description or "")

    def on_save(self):
        self.name.clear_error()
        name = self.name.text().strip()
        if not name:
            self.name.set_error("الاسم مطلوب.")
            return
        dto = BudgetItemDTO(
            id=self.item.id if self.item else None,
            fiscal_year_id=self.fiscal_year_id,
            name=name,
            allocated_amount=self.amount.widget.value(),
            description=self.desc.text().strip() or None,
        )
        try:
            if self.item:
                self.fs.update_budget_item(dto)
            else:
                self.fs.create_budget_item(dto)
            self.accept()
        except Exception as e:
            logger.error(f"Save budget item failed: {e}")
            Toast.error(self, "تعذّر الحفظ")


class BudgetManagementView(QWidget):
    def __init__(self, financial_service: FinancialService, permission=None):
        super().__init__()
        self.fs = financial_service
        self.permission = permission
        self.setup_ui()
        self.reload_years()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        header = PageHeader("إدارة الميزانية",
                            subtitle="السنوات المالية وبنود الميزانية لكل سنة.")
        card.add(header)

        fy_row = QHBoxLayout()
        fy_row.setSpacing(10)
        fy_row.addWidget(QLabel("السنة المالية:"))
        self.fy_combo = QComboBox()
        self.fy_combo.setMinimumWidth(220)
        self.fy_combo.currentIndexChanged.connect(self.reload_items)
        fy_row.addWidget(self.fy_combo)
        add_fy = IconButton("سنة جديدة", "add", variant="secondary")
        add_fy.clicked.connect(self.on_add_fy)
        edit_fy = IconButton("تعديل", "edit", variant="secondary", compact=True)
        edit_fy.clicked.connect(self.on_edit_fy)
        del_fy = IconButton("حذف", "delete", variant="danger", compact=True)
        del_fy.clicked.connect(self.on_delete_fy)
        fy_row.addWidget(add_fy)
        fy_row.addWidget(edit_fy)
        fy_row.addWidget(del_fy)
        fy_row.addStretch()
        add_item = IconButton("إضافة بند", "add", variant="primary")
        add_item.clicked.connect(self.on_add_item)
        fy_row.addWidget(add_item)
        card.add_layout(fy_row)

        self.table = DataTable(
            ["البند", "المخصّص", "المستهلَك", "المتاح", "إجراءات"])
        self.table.refresh_requested.connect(self.reload_items)
        self.table.set_export_title("بنود الميزانية")
        card.add(self.table)
        main_layout.addWidget(card)

    def _selected_fy_id(self):
        return self.fy_combo.currentData()

    def reload_years(self):
        self.fy_combo.blockSignals(True)
        self.fy_combo.clear()
        for fy in self.fs.list_fiscal_years():
            self.fy_combo.addItem(f"{fy.name} ({FY_STATUS_LABELS.get(fy.status, fy.status)})", fy.id)
        self.fy_combo.blockSignals(False)
        self.reload_items()

    def reload_items(self):
        fy_id = self._selected_fy_id()
        if not fy_id:
            self.table.set_records([])
            return
        with busy(self, "جاري تحميل بنود الميزانية..."):
            self._populate_items(fy_id)

    def _populate_items(self, fy_id):
        items = self.fs.list_budget_items(fy_id)
        rows = []
        for it in items:
            allocated = float(it.allocated_amount or 0)
            used = self.fs.budget_item_used(it.id)
            available = allocated - used
            rows.append(Row(
                cells=[
                    it.name, f"{allocated:,.2f}", f"{used:,.2f}", f"{available:,.2f}",
                ],
                actions=[
                    Action("edit", "تعديل",
                           (lambda i=it: self.on_edit_item(i)), "primary"),
                    Action("delete", "حذف",
                           (lambda i=it: self.on_delete_item(i)), "danger"),
                ],
                search=it.name,
                sort=[it.name, allocated, used, available],
            ))
        self.table.set_records(rows)

    # ---- fiscal year actions ----
    def on_add_fy(self):
        if not can(self.permission, MODULE, "create"):
            Toast.error(self, "ليس لديك صلاحية للإضافة")
            return
        if FiscalYearDialog(self.fs, self).exec():
            self.reload_years()
            Toast.success(self, "تمت إضافة السنة المالية")

    def on_edit_fy(self):
        fy_id = self._selected_fy_id()
        if not fy_id:
            return
        fy = next((f for f in self.fs.list_fiscal_years() if f.id == fy_id), None)
        if fy and FiscalYearDialog(self.fs, self, fy).exec():
            self.reload_years()
            Toast.success(self, "تم حفظ التعديلات")

    def on_delete_fy(self):
        fy_id = self._selected_fy_id()
        if not fy_id:
            return
        if not can(self.permission, MODULE, "delete"):
            Toast.error(self, "ليس لديك صلاحية للحذف")
            return
        if not confirm(self, "هل تريد حذف السنة المالية؟"):
            return
        try:
            self.fs.delete_fiscal_year(fy_id)
            self.reload_years()
            Toast.success(self, "تم الحذف")
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لوجود بنود/إيرادات مرتبطة")
        except Exception as e:
            logger.error(f"Delete fiscal year failed: {e}")
            Toast.error(self, "تعذّر الحذف")

    # ---- budget item actions ----
    def on_add_item(self):
        fy_id = self._selected_fy_id()
        if not fy_id:
            Toast.error(self, "أضِف سنة مالية أولًا")
            return
        if not can(self.permission, MODULE, "create"):
            Toast.error(self, "ليس لديك صلاحية للإضافة")
            return
        if BudgetItemDialog(self.fs, fy_id, self).exec():
            self.reload_items()
            Toast.success(self, "تمت الإضافة")

    def on_edit_item(self, item):
        if not can(self.permission, MODULE, "edit"):
            Toast.error(self, "ليس لديك صلاحية للتعديل")
            return
        if BudgetItemDialog(self.fs, item.fiscal_year_id, self, item).exec():
            self.reload_items()
            Toast.success(self, "تم حفظ التعديلات")

    def on_delete_item(self, item):
        if not can(self.permission, MODULE, "delete"):
            Toast.error(self, "ليس لديك صلاحية للحذف")
            return
        if not confirm(self, f"هل تريد حذف البند \"{item.name}\"؟"):
            return
        try:
            self.fs.delete_budget_item(item.id)
            self.reload_items()
            Toast.success(self, "تم الحذف")
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لوجود مصروفات مرتبطة بالبند")
        except Exception as e:
            logger.error(f"Delete budget item failed: {e}")
            Toast.error(self, "تعذّر الحذف")
