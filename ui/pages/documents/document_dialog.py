import os

from qtpy.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QComboBox, QDateEdit, QFileDialog
from qtpy.QtCore import QDate
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.themes.colors import Colors
from application.services.document_service import DocumentService, DocumentDTO
from domain.entities.document import Document

TYPE_VALUES = ["policy", "procedure", "form", "manual", "other"]
TYPE_LABELS = ["سياسة", "إجراء", "نموذج", "دليل", "أخرى"]
STATUS_VALUES = ["draft", "approved", "archived"]
STATUS_LABELS = ["مسودة", "معتمد", "مؤرشف"]


class DocumentDialog(BaseDialog):
    def __init__(self, doc_service: DocumentService, parent=None, document: Document = None):
        super().__init__("إضافة وثيقة جديدة" if not document else "تعديل الوثيقة", parent)
        self.doc_service = doc_service
        self.document = document
        self.categories = self.doc_service.get_categories()
        self.selected_file_path = None

        self.title_field = self.add_field("عنوان الوثيقة:", QLineEdit(), required=True)

        type_combo = QComboBox()
        type_combo.addItems(TYPE_LABELS)
        category_combo = QComboBox()
        category_combo.addItem("غير محدد", None)
        for cat in self.categories:
            category_combo.addItem(cat.name, cat.id)
        self.type_field, self.category_field = self.add_row(
            ("النوع:", type_combo), ("التصنيف:", category_combo))

        eff = QDateEdit()
        eff.setCalendarPopup(True)
        eff.setDate(QDate.currentDate())
        rev = QDateEdit()
        rev.setCalendarPopup(True)
        rev.setDate(QDate.currentDate().addYears(1))
        self.eff_field, self.rev_field = self.add_row(
            ("تاريخ التفعيل:", eff), ("تاريخ المراجعة القادمة:", rev))

        status_combo = QComboBox()
        status_combo.addItems(STATUS_LABELS)
        self.status_field = self.add_field("الحالة:", status_combo)

        if not self.document:
            file_row = QWidget()
            row = QHBoxLayout(file_row)
            row.setContentsMargins(0, 0, 0, 0)
            browse = IconButton("اختيار ملف...", "browse", variant="secondary")
            browse.clicked.connect(self.on_browse)
            self.file_label = QLabel("لم يتم تحديد ملف")
            self.file_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
            row.addWidget(browse)
            row.addWidget(self.file_label)
            row.addStretch()
            self.add_widget(file_row)

        self.build_buttons()
        self.populate_data()

    def on_browse(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختيار وثيقة", "",
            "All Files (*.*);;PDF Files (*.pdf);;Word Documents (*.docx)")
        if file_path:
            self.selected_file_path = file_path
            self.file_label.setText(os.path.basename(file_path))

    def populate_data(self):
        if not self.document:
            return
        self.title_field.widget.setText(self.document.title)
        if self.document.doc_type in TYPE_VALUES:
            self.type_field.widget.setCurrentIndex(TYPE_VALUES.index(self.document.doc_type))
        if self.document.category_id:
            idx = self.category_field.widget.findData(self.document.category_id)
            if idx >= 0:
                self.category_field.widget.setCurrentIndex(idx)
        if self.document.status in STATUS_VALUES:
            self.status_field.widget.setCurrentIndex(STATUS_VALUES.index(self.document.status))
        if self.document.effective_date:
            self.eff_field.widget.setDate(self.document.effective_date)
        if self.document.review_date:
            self.rev_field.widget.setDate(self.document.review_date)

    def on_save(self):
        self.title_field.clear_error()
        title = self.title_field.text().strip()
        if not title:
            self.title_field.set_error("عنوان الوثيقة مطلوب.")
            return
        if not self.document and not self.selected_file_path:
            Toast.error(self, "يرجى اختيار ملف لرفعه")
            return

        dto = DocumentDTO(
            title=title,
            doc_type=TYPE_VALUES[self.type_field.widget.currentIndex()],
            category_id=self.category_field.widget.currentData(),
            status=STATUS_VALUES[self.status_field.widget.currentIndex()],
            effective_date=self.eff_field.widget.date().toPython(),
            review_date=self.rev_field.widget.date().toPython(),
        )
        try:
            if self.document:
                dto.id = self.document.id
                self.doc_service.update_document(dto)
            else:
                self.doc_service.upload_document(dto, self.selected_file_path)
            self.accept()
        except Exception as e:
            logger.error(f"Save document failed: {e}")
            Toast.error(self, "تعذّر حفظ الوثيقة")
