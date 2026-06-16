from qtpy.QtWidgets import QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox
from qtpy.QtCore import QDate
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.toast import Toast
from application.services.training_service import TrainingService, TrainingProgramDTO
from domain.entities.training import TrainingProgram

TYPE_VALUES = ["training", "workshop", "course"]
TYPE_LABELS = ["تدريب", "ورشة عمل", "دورة تأهيلية"]
STATUS_VALUES = ["planned", "active", "completed", "cancelled"]
STATUS_LABELS = ["مخطط", "نشط", "مكتمل", "ملغى"]


class TrainingDialog(BaseDialog):
    def __init__(self, training_service: TrainingService, parent=None,
                 program: TrainingProgram = None):
        super().__init__(
            "إضافة برنامج تدريبي" if not program else "تعديل البرنامج", parent)
        self.training_service = training_service
        self.program = program

        self.name_field = self.add_field("اسم البرنامج:", QLineEdit(), required=True)

        type_combo = QComboBox()
        type_combo.addItems(TYPE_LABELS)
        status_combo = QComboBox()
        status_combo.addItems(STATUS_LABELS)
        self.type_field, self.status_field = self.add_row(
            ("النوع:", type_combo), ("الحالة:", status_combo))

        start = QDateEdit()
        start.setCalendarPopup(True)
        start.setDate(QDate.currentDate())
        end = QDateEdit()
        end.setCalendarPopup(True)
        end.setDate(QDate.currentDate().addDays(7))
        self.start_field, self.end_field = self.add_row(
            ("تاريخ البدء:", start), ("تاريخ الانتهاء:", end))

        hours = QSpinBox()
        hours.setRange(1, 500)
        hours.setValue(10)
        self.hours_field = self.add_field("إجمالي الساعات:", hours)

        desc = QTextEdit()
        desc.setMaximumHeight(90)
        self.desc_field = self.add_field("الوصف:", desc)

        self.build_buttons()
        self.populate_data()

    def populate_data(self):
        if not self.program:
            return
        self.name_field.widget.setText(self.program.name)
        self.desc_field.widget.setPlainText(self.program.description or "")
        if self.program.program_type in TYPE_VALUES:
            self.type_field.widget.setCurrentIndex(TYPE_VALUES.index(self.program.program_type))
        if self.program.status in STATUS_VALUES:
            self.status_field.widget.setCurrentIndex(STATUS_VALUES.index(self.program.status))
        if self.program.start_date:
            self.start_field.widget.setDate(self.program.start_date)
        if self.program.end_date:
            self.end_field.widget.setDate(self.program.end_date)
        if self.program.total_hours:
            self.hours_field.widget.setValue(self.program.total_hours)

    def on_save(self):
        self.name_field.clear_error()
        name = self.name_field.text().strip()
        if not name:
            self.name_field.set_error("اسم البرنامج مطلوب.")
            return

        dto = TrainingProgramDTO(
            name=name,
            description=self.desc_field.text().strip() or None,
            program_type=TYPE_VALUES[self.type_field.widget.currentIndex()],
            start_date=self.start_field.widget.date().toPython(),
            end_date=self.end_field.widget.date().toPython(),
            total_hours=self.hours_field.widget.value(),
            status=STATUS_VALUES[self.status_field.widget.currentIndex()],
        )
        try:
            if self.program:
                dto.id = self.program.id
                self.training_service.update_program(dto)
            else:
                self.training_service.create_program(dto)
            self.accept()
        except Exception as e:
            logger.error(f"Save training program failed: {e}")
            Toast.error(self, "تعذّر حفظ البرنامج")
