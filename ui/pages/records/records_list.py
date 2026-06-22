from qtpy.QtWidgets import QWidget, QVBoxLayout, QApplication
from sqlalchemy.exc import IntegrityError
from loguru import logger

from ui.widgets.data_table import DataTable, Row, Badge, Action
from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.loading_overlay import LoadingOverlay
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from ui.permissions import can
from application.services.record_service import RecordService
from ui.pages.records.record_dialog import RecordDialog

MODULE = "records"


class RecordsListView(QWidget):
    def __init__(self, record_service: RecordService, permission=None):
        super().__init__()
        self.record_service = record_service
        self.permission = permission
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        can_create = can(self.permission, MODULE, "create")
        header = PageHeader(
            "السجلات والمحفوظات",
            action_text="إضافة سجل جديد" if can_create else None,
            action_icon="add" if can_create else None,
        )
        if can_create:
            header.action_clicked.connect(self.on_add_clicked)
        card.add(header)

        columns = ["رقم السجل", "عنوان السجل", "النوع", "مكان الحفظ", "حالة السجل", "إجراءات"]
        self.table = DataTable(columns)
        self.table.refresh_requested.connect(self.load_data)
        self.table.set_export_title("السجلات")
        self.table.add_filter("الحالة", [("نشط", "active"), ("مؤرشف", "archived")])
        card.add(self.table)
        main_layout.addWidget(card)

        self.overlay = LoadingOverlay(self)

    def load_data(self):
        self.overlay.start()
        QApplication.processEvents()
        try:
            records = self.record_service.get_all_records()
            edit_ok = can(self.permission, MODULE, "edit")
            del_ok = can(self.permission, MODULE, "delete")
            rows = []
            for r in records:
                type_name = r.record_type.name if r.record_type else "غير محدد"
                location = r.storage_location or "غير محدد"
                is_active = r.status == "active"
                status_text = "نشط" if is_active else "مؤرشف"
                acts = []
                if edit_ok:
                    acts.append(Action("edit", "تعديل",
                                       (lambda rec=r: self.on_edit_clicked(rec)), "primary"))
                if del_ok:
                    acts.append(Action("delete", "حذف",
                                       (lambda rec=r: self.on_delete_clicked(rec)), "danger"))
                rows.append(Row(
                    cells=[
                        r.record_number, r.title, type_name, location,
                        Badge(status_text, "active" if is_active else "archived"),
                    ],
                    actions=acts,
                    search=f"{r.record_number} {r.title} {type_name}",
                    sort=[r.record_number, r.title, type_name, location, status_text],
                    tags={"الحالة": r.status},
                ))
            self.table.set_records(rows)
        except Exception as e:
            logger.error(f"Records load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب البيانات")
        finally:
            self.overlay.stop()

    def on_add_clicked(self):
        if not can(self.permission, MODULE, "create"):
            Toast.error(self, "ليس لديك صلاحية للإضافة")
            return
        dialog = RecordDialog(self.record_service, self)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تمت إضافة السجل بنجاح")

    def on_edit_clicked(self, record):
        if not can(self.permission, MODULE, "edit"):
            Toast.error(self, "ليس لديك صلاحية للتعديل")
            return
        dialog = RecordDialog(self.record_service, self, record)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تم حفظ التعديلات بنجاح")

    def on_delete_clicked(self, record):
        if not can(self.permission, MODULE, "delete"):
            Toast.error(self, "ليس لديك صلاحية للحذف")
            return
        if not confirm(self, f"هل تريد حذف السجل \"{record.title}\"؟"):
            return
        try:
            self.record_service.delete_record(record.id)
            Toast.success(self, "تم الحذف بنجاح")
            self.load_data()
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لارتباط السجل بسجلات أخرى")
        except Exception as e:
            logger.error(f"Delete record failed: {e}")
            Toast.error(self, "تعذّر الحذف")
