from datetime import datetime

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QFileDialog, QMessageBox,
    QApplication
)
from loguru import logger

from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from ui.widgets.busy import busy
from ui.themes.colors import Colors
from config import settings
from application.services.backup_service import BackupService


class BackupRestoreView(QWidget):
    """Backup the database / export everything, and restore from a backup."""

    def __init__(self, permission=None):
        super().__init__()
        self.permission = permission
        self.backup_service = BackupService()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        card.add(PageHeader(
            "النسخ الاحتياطي والاستعادة",
            subtitle="حماية بياناتك: أخذ نسخ احتياطية، تصدير نسخة كاملة، أو الاستعادة."))

        location = QLabel(f"مكان حفظ البيانات: {settings.DATA_DIR}")
        location.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        card.add(location)

        # Backup / export
        backup_group = QGroupBox("النسخ الاحتياطي")
        b_layout = QHBoxLayout()
        self.backup_btn = IconButton(
            "نسخة احتياطية لقاعدة البيانات", "backup", variant="secondary")
        self.backup_btn.clicked.connect(self.on_backup)
        self.export_btn = IconButton(
            "تصدير نسخة كاملة (قاعدة البيانات + الملفات)", "export", variant="primary")
        self.export_btn.clicked.connect(self.on_export_all)
        b_layout.addWidget(self.backup_btn)
        b_layout.addWidget(self.export_btn)
        b_layout.addStretch()
        backup_group.setLayout(b_layout)
        card.add(backup_group)

        # Restore
        restore_group = QGroupBox("الاستعادة")
        r_layout = QVBoxLayout()
        warn = QLabel(
            "⚠ الاستعادة ستستبدل البيانات الحالية بالكامل، وسيُغلق البرنامج بعدها لإعادة التشغيل.")
        warn.setStyleSheet(f"color: {Colors.DANGER_TEXT}; background: transparent;")
        warn.setWordWrap(True)
        r_layout.addWidget(warn)
        r_buttons = QHBoxLayout()
        self.restore_db_btn = IconButton(
            "استعادة قاعدة بيانات (.db)", "refresh", variant="secondary")
        self.restore_db_btn.clicked.connect(self.on_restore_db)
        self.restore_zip_btn = IconButton(
            "استعادة نسخة كاملة (.zip)", "refresh", variant="secondary")
        self.restore_zip_btn.clicked.connect(self.on_restore_full)
        r_buttons.addWidget(self.restore_db_btn)
        r_buttons.addWidget(self.restore_zip_btn)
        r_buttons.addStretch()
        r_layout.addLayout(r_buttons)
        restore_group.setLayout(r_layout)
        card.add(restore_group)

        main_layout.addWidget(card)
        main_layout.addStretch()

    # ----------------------------------------------------------- backup
    def on_backup(self):
        try:
            with busy(self, "جاري إنشاء النسخة الاحتياطية..."):
                path = self.backup_service.backup_db()
            Toast.success(self, "تم أخذ نسخة احتياطية بنجاح")
            logger.info(f"Backup created: {path}")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            Toast.error(self, "حدث خطأ أثناء النسخ الاحتياطي")

    def on_export_all(self):
        default = f"CSCN_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        dest, _ = QFileDialog.getSaveFileName(self, "تصدير نسخة كاملة", default, "ZIP (*.zip)")
        if not dest:
            return
        try:
            with busy(self, "جاري تصدير النسخة الكاملة..."):
                self.backup_service.export_all(dest)
            Toast.success(self, "تم تصدير النسخة الكاملة بنجاح")
        except Exception as e:
            logger.error(f"Full export failed: {e}")
            Toast.error(self, "تعذّر تصدير النسخة الكاملة")

    # ----------------------------------------------------------- restore
    def _finish_restore(self):
        QMessageBox.information(
            self, "تمت الاستعادة",
            "تمت الاستعادة بنجاح. سيُغلق البرنامج الآن — أعد فتحه لتطبيق البيانات المستعادة.")
        QApplication.instance().quit()

    def on_restore_db(self):
        if not confirm(self, "سيتم استبدال قاعدة البيانات الحالية. هل تريد المتابعة؟"):
            return
        src, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف قاعدة بيانات", str(settings.BACKUPS_DIR), "Database (*.db)")
        if not src:
            return
        try:
            with busy(self, "جاري الاستعادة..."):
                self.backup_service.restore_db(src)
            self._finish_restore()
        except Exception as e:
            logger.error(f"Restore db failed: {e}")
            Toast.error(self, "تعذّرت الاستعادة")

    def on_restore_full(self):
        if not confirm(self, "سيتم استبدال كل البيانات والملفات الحالية. هل تريد المتابعة؟"):
            return
        src, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف نسخة كاملة", "", "ZIP (*.zip)")
        if not src:
            return
        try:
            with busy(self, "جاري الاستعادة..."):
                self.backup_service.restore_full(src)
            self._finish_restore()
        except Exception as e:
            logger.error(f"Restore full failed: {e}")
            Toast.error(self, "تعذّرت الاستعادة")
