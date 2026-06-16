from qtpy.QtWidgets import QLineEdit, QTextEdit, QComboBox
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from application.services.quality_service import QualityService, StandardDTO
from domain.entities.standard import Standard


class StandardDialog(BaseDialog):
    def __init__(self, quality_service: QualityService, parent=None, standard: Standard = None):
        super().__init__("إضافة معيار جديد" if not standard else "تعديل المعيار", parent)
        self.quality_service = quality_service
        self.standard = standard
        self.categories = self.quality_service.get_all_categories()

        self.code_field = self.add_field("كود المعيار:", QLineEdit(), required=True)
        self.name_field = self.add_field("اسم المعيار:", QLineEdit(), required=True)

        category = QComboBox()
        category.addItem("غير محدد", None)
        for cat in self.categories:
            category.addItem(cat.name, cat.id)
        self.category_field = self.add_field("التصنيف:", category)

        desc = QTextEdit()
        desc.setMaximumHeight(100)
        self.desc_field = self.add_field("الوصف:", desc)

        status = QComboBox()
        status.addItems(["نشط", "غير نشط"])
        self.status_field = self.add_field("الحالة:", status)

        self.build_buttons()
        self.populate_data()

    def populate_data(self):
        if not self.standard:
            return
        self.code_field.widget.setText(self.standard.code)
        self.name_field.widget.setText(self.standard.name)
        self.desc_field.widget.setPlainText(self.standard.description or "")
        if self.standard.category_id:
            idx = self.category_field.widget.findData(self.standard.category_id)
            if idx >= 0:
                self.category_field.widget.setCurrentIndex(idx)
        self.status_field.widget.setCurrentIndex(0 if self.standard.status == "active" else 1)

    def on_save(self):
        self.code_field.clear_error()
        self.name_field.clear_error()
        code = self.code_field.text().strip()
        name = self.name_field.text().strip()
        if not code:
            self.code_field.set_error("كود المعيار مطلوب.")
            return
        if not name:
            self.name_field.set_error("اسم المعيار مطلوب.")
            return

        dto = StandardDTO(
            code=code,
            name=name,
            description=self.desc_field.text().strip() or None,
            category_id=self.category_field.widget.currentData(),
            status="active" if self.status_field.widget.currentIndex() == 0 else "inactive",
        )
        try:
            if self.standard:
                dto.id = self.standard.id
                self.quality_service.update_standard(dto)
            else:
                self.quality_service.create_standard(dto)
            self.accept()
        except Exception as e:
            logger.error(f"Save standard failed: {e}")
            self.code_field.set_error("تعذّر الحفظ — تأكد أن الكود غير مكرر.")
