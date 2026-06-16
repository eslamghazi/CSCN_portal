from qtpy.QtWidgets import QLineEdit, QTextEdit, QComboBox, QSpinBox
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.toast import Toast
from application.services.record_service import RecordService
from domain.entities.record import Record


class RecordDialog(BaseDialog):
    def __init__(self, record_service: RecordService, parent=None, record: Record = None):
        super().__init__("إضافة سجل جديد" if not record else "تعديل السجل", parent)
        self.record_service = record_service
        self.record = record
        self.record_types = self.record_service.get_all_record_types()

        self.num_field, self.title_field = self.add_row(
            ("رقم السجل:", QLineEdit(), True), ("عنوان السجل:", QLineEdit(), True))

        type_combo = QComboBox()
        type_combo.addItem("غير محدد", None)
        for rt in self.record_types:
            type_combo.addItem(rt.name, rt.id)
        self.type_field, self.loc_field = self.add_row(
            ("النوع:", type_combo), ("مكان الحفظ:", QLineEdit()))

        retention = QSpinBox()
        retention.setRange(0, 1200)
        status = QComboBox()
        status.addItems(["نشط", "مؤرشف"])
        self.retention_field, self.status_field = self.add_row(
            ("فترة الحفظ (أشهر):", retention), ("الحالة:", status))

        self.disposal_field = self.add_field("طريقة الإتلاف:", QLineEdit())
        notes = QTextEdit()
        notes.setMaximumHeight(80)
        self.notes_field = self.add_field("ملاحظات:", notes)

        self.build_buttons()
        self.populate_data()

    def populate_data(self):
        if not self.record:
            return
        self.num_field.widget.setText(self.record.record_number)
        self.title_field.widget.setText(self.record.title)
        if self.record.record_type_id:
            idx = self.type_field.widget.findData(self.record.record_type_id)
            if idx >= 0:
                self.type_field.widget.setCurrentIndex(idx)
        self.loc_field.widget.setText(self.record.storage_location or "")
        self.retention_field.widget.setValue(self.record.retention_period_months or 0)
        self.status_field.widget.setCurrentIndex(0 if self.record.status == "active" else 1)
        self.disposal_field.widget.setText(self.record.disposal_method or "")
        self.notes_field.widget.setPlainText(self.record.notes or "")

    def on_save(self):
        self.num_field.clear_error()
        self.title_field.clear_error()
        num = self.num_field.text().strip()
        title = self.title_field.text().strip()
        if not num:
            self.num_field.set_error("رقم السجل مطلوب.")
            return
        if not title:
            self.title_field.set_error("عنوان السجل مطلوب.")
            return

        status = "active" if self.status_field.widget.currentIndex() == 0 else "archived"
        try:
            if self.record:
                self.record.record_number = num
                self.record.title = title
                self.record.record_type_id = self.type_field.widget.currentData()
                self.record.storage_location = self.loc_field.text().strip() or None
                self.record.retention_period_months = self.retention_field.widget.value() or None
                self.record.disposal_method = self.disposal_field.text().strip() or None
                self.record.status = status
                self.record.notes = self.notes_field.text().strip() or None
                self.record_service.update_record(self.record)
            else:
                self.record_service.add_record(
                    record_number=num,
                    title=title,
                    record_type_id=self.type_field.widget.currentData(),
                    storage_location=self.loc_field.text().strip() or None,
                    retention_period_months=self.retention_field.widget.value() or None,
                    disposal_method=self.disposal_field.text().strip() or None,
                    status=status,
                    notes=self.notes_field.text().strip() or None,
                )
            self.accept()
        except Exception as e:
            logger.error(f"Save record failed: {e}")
            Toast.error(self, "تعذّر حفظ السجل — تأكد أن رقم السجل غير مكرر")
