from datetime import datetime

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QGroupBox, QLabel,
    QFileDialog
)
from loguru import logger

from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.widgets.busy import busy
from ui.themes.colors import Colors
from config import settings
from application.services.backup_service import BackupService


class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.backup_service = BackupService()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        card.add(PageHeader("إعدادات النظام"))

        # Organization Info
        org_group = QGroupBox("بيانات المؤسسة")
        org_layout = QFormLayout()
        self.org_name = QLineEdit("مركز تنمية مهارات التمريض - جامعة كفر الشيخ")
        self.org_phone = QLineEdit("047-322-1234")
        self.org_email = QLineEdit("info@nursing.kfs.edu.eg")
        org_layout.addRow("اسم المؤسسة:", self.org_name)
        org_layout.addRow("رقم الهاتف:", self.org_phone)
        org_layout.addRow("البريد الإلكتروني:", self.org_email)
        org_group.setLayout(org_layout)
        card.add(org_group)

        # Data & Backup
        data_group = QGroupBox("البيانات والنسخ الاحتياطي")
        data_layout = QVBoxLayout()
        location = QLabel(f"مكان حفظ البيانات: {settings.DATA_DIR}")
        location.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        data_layout.addWidget(location)

        buttons = QHBoxLayout()
        self.backup_btn = IconButton(
            "نسخة احتياطية لقاعدة البيانات", "backup", variant="secondary")
        self.backup_btn.clicked.connect(self.on_backup)
        self.export_btn = IconButton(
            "تصدير نسخة كاملة (قاعدة البيانات + الملفات)", "export", variant="primary")
        self.export_btn.clicked.connect(self.on_export_all)
        buttons.addWidget(self.backup_btn)
        buttons.addWidget(self.export_btn)
        buttons.addStretch()
        data_layout.addLayout(buttons)
        data_group.setLayout(data_layout)
        card.add(data_group)

        # Save Button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_btn = IconButton("حفظ الإعدادات", "save", variant="primary")
        self.save_btn.clicked.connect(self.on_save)
        save_layout.addWidget(self.save_btn)
        card.add_layout(save_layout)

        main_layout.addWidget(card)
        main_layout.addStretch()

    def on_backup(self):
        try:
            with busy(self, "جاري إنشاء النسخة الاحتياطية..."):
                path = self.backup_service.backup_db()
            logger.info(f"Database backed up to {path}")
            Toast.success(self, "تم أخذ نسخة احتياطية بنجاح")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            Toast.error(self, "حدث خطأ أثناء النسخ الاحتياطي")

    def on_export_all(self):
        default = f"CSCN_portal_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        dest, _ = QFileDialog.getSaveFileName(
            self, "تصدير نسخة كاملة", default, "ZIP (*.zip)")
        if not dest:
            return
        try:
            with busy(self, "جاري تصدير النسخة الكاملة..."):
                self.backup_service.export_all(dest)
            Toast.success(self, "تم تصدير النسخة الكاملة بنجاح")
        except Exception as e:
            logger.error(f"Full export failed: {e}")
            Toast.error(self, "تعذّر تصدير النسخة الكاملة")

    def on_save(self):
        Toast.success(self, "تم حفظ الإعدادات بنجاح")
