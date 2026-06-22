import shutil
from pathlib import Path

from qtpy.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QApplication
from qtpy.QtCore import QUrl
from qtpy.QtGui import QDesktopServices
from sqlalchemy.exc import IntegrityError
from loguru import logger

from ui.widgets.data_table import DataTable, Row, Badge, Action
from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.loading_overlay import LoadingOverlay
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from ui.permissions import can
from application.services.document_service import DocumentService

MODULE = "documents"


class DocumentsListView(QWidget):
    def __init__(self, doc_service: DocumentService, permission=None):
        super().__init__()
        self.doc_service = doc_service
        self.permission = permission
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        can_create = can(self.permission, MODULE, "create")
        header = PageHeader(
            "إدارة الوثائق والسياسات",
            action_text="رفع وثيقة جديدة" if can_create else None,
            action_icon="upload" if can_create else None,
        )
        if can_create:
            header.action_clicked.connect(self.on_upload_clicked)
        card.add(header)

        columns = [
            "عنوان الوثيقة", "النوع", "التصنيف", "الإصدار الحالي",
            "تاريخ السريان", "الحالة", "إجراءات",
        ]
        self.table = DataTable(columns)
        self.table.refresh_requested.connect(self.load_data)
        self.table.set_export_title("الوثائق")
        self.table.add_filter("الحالة", [("معتمد", "approved"), ("مسودة", "draft")])
        card.add(self.table)
        main_layout.addWidget(card)

        self.overlay = LoadingOverlay(self)

    def load_data(self):
        self.overlay.start()
        QApplication.processEvents()
        try:
            docs = self.doc_service.get_all_documents()
            edit_ok = can(self.permission, MODULE, "edit")
            del_ok = can(self.permission, MODULE, "delete")
            rows = []
            for d in docs:
                category = d.category.name if d.category else "غير محدد"
                eff = d.effective_date.strftime("%Y-%m-%d") if d.effective_date else "غير محدد"
                approved = d.status == "approved"
                status_text = "معتمد" if approved else "مسودة"
                acts = [
                    Action("view", "عرض",
                           (lambda doc=d: self._open_document(doc)), "secondary"),
                    Action("download", "تحميل",
                           (lambda doc=d: self._download_document(doc)), "secondary"),
                ]
                if edit_ok:
                    acts.insert(1, Action("edit", "تعديل",
                                          (lambda doc=d: self.on_edit_clicked(doc)), "primary"))
                if del_ok:
                    acts.append(Action("delete", "حذف",
                                       (lambda doc=d: self.on_delete_clicked(doc)), "danger"))
                rows.append(Row(
                    cells=[
                        d.title, d.doc_type, category, d.current_version, eff,
                        Badge(status_text, "approved" if approved else "draft"),
                    ],
                    actions=acts,
                    search=f"{d.title} {d.doc_type} {category}",
                    sort=[d.title, d.doc_type, category, d.current_version, eff, status_text],
                    tags={"الحالة": d.status},
                ))
            self.table.set_records(rows)
        except Exception as e:
            logger.error(f"Documents load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب البيانات")
        finally:
            self.overlay.stop()

    def _open_document(self, document):
        path = self.doc_service.get_document_file_path(document.id)
        if not path or not Path(path).exists():
            Toast.error(self, "لا يوجد ملف مرفق لهذه الوثيقة")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _download_document(self, document):
        path = self.doc_service.get_document_file_path(document.id)
        if not path or not Path(path).exists():
            Toast.error(self, "لا يوجد ملف مرفق لهذه الوثيقة")
            return
        suffix = Path(path).suffix
        dest, _ = QFileDialog.getSaveFileName(
            self, "حفظ الوثيقة", f"{document.title}{suffix}", f"*{suffix}")
        if not dest:
            return
        try:
            shutil.copy2(path, dest)
            Toast.success(self, "تم تنزيل الوثيقة بنجاح")
        except OSError as e:
            logger.error(f"Document download failed: {e}")
            Toast.error(self, "تعذّر تنزيل الوثيقة")

    def on_upload_clicked(self):
        if not can(self.permission, MODULE, "create"):
            Toast.error(self, "ليس لديك صلاحية للإضافة")
            return
        from ui.pages.documents.document_dialog import DocumentDialog
        dialog = DocumentDialog(self.doc_service, self)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تم رفع الوثيقة بنجاح")

    def on_edit_clicked(self, document):
        if not can(self.permission, MODULE, "edit"):
            Toast.error(self, "ليس لديك صلاحية للتعديل")
            return
        from ui.pages.documents.document_dialog import DocumentDialog
        dialog = DocumentDialog(self.doc_service, self, document)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تم حفظ التعديلات بنجاح")

    def on_delete_clicked(self, document):
        if not can(self.permission, MODULE, "delete"):
            Toast.error(self, "ليس لديك صلاحية للحذف")
            return
        if not confirm(self, f"هل تريد حذف الوثيقة \"{document.title}\"؟"):
            return
        try:
            self.doc_service.delete_document(document.id)
            Toast.success(self, "تم الحذف بنجاح")
            self.load_data()
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لارتباط الوثيقة بسجلات أخرى")
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            Toast.error(self, "تعذّر الحذف")
