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
from application.services.training_service import TrainingService
from ui.pages.training.training_dialog import TrainingDialog

MODULE = "training"
STATUS_LABELS = {"planned": "مخطط", "active": "نشط", "completed": "مكتمل", "cancelled": "ملغى"}
STATUS_KIND = {"planned": "planned", "active": "active",
               "completed": "completed", "cancelled": "cancelled"}
TYPE_LABELS = {"training": "تدريب", "workshop": "ورشة عمل", "course": "دورة تأهيلية"}


class TrainingListView(QWidget):
    def __init__(self, training_service: TrainingService, permission=None,
                 financial_service=None):
        super().__init__()
        self.training_service = training_service
        self.financial_service = financial_service
        self.permission = permission
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        can_create = can(self.permission, MODULE, "create")
        header = PageHeader(
            "البرامج التدريبية",
            action_text="إضافة برنامج تدريبي" if can_create else None,
            action_icon="add" if can_create else None,
        )
        if can_create:
            header.action_clicked.connect(self.on_add_clicked)
        card.add(header)

        columns = ["اسم البرنامج", "نوع البرنامج", "الحالة", "إجراءات"]
        self.table = DataTable(columns)
        self.table.refresh_requested.connect(self.load_data)
        self.table.set_export_title("البرامج التدريبية")
        self.table.add_filter("الحالة", [(v, k) for k, v in STATUS_LABELS.items()])
        card.add(self.table)
        main_layout.addWidget(card)

        self.overlay = LoadingOverlay(self)

    def load_data(self):
        self.overlay.start()
        QApplication.processEvents()
        try:
            programs = self.training_service.get_all_programs()
            edit_ok = can(self.permission, MODULE, "edit")
            del_ok = can(self.permission, MODULE, "delete")
            rows = []
            for p in programs:
                type_label = TYPE_LABELS.get(p.program_type, "غير محدد")
                status_label = STATUS_LABELS.get(p.status, "غير محدد")
                acts = []
                if edit_ok:
                    acts.append(Action("agreements", "الجلسات",
                                       (lambda prog=p: self.on_sessions_clicked(prog)), "secondary"))
                    acts.append(Action("edit", "تعديل",
                                       (lambda prog=p: self.on_edit_clicked(prog)), "primary"))
                if del_ok:
                    acts.append(Action("delete", "حذف",
                                       (lambda prog=p: self.on_delete_clicked(prog)), "danger"))
                rows.append(Row(
                    cells=[
                        p.name, type_label,
                        Badge(status_label, STATUS_KIND.get(p.status, "info")),
                    ],
                    actions=acts,
                    search=f"{p.name} {type_label}",
                    sort=[p.name, type_label, status_label],
                    tags={"الحالة": p.status},
                ))
            self.table.set_records(rows)
        except Exception as e:
            logger.error(f"Training load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب البيانات")
        finally:
            self.overlay.stop()

    def on_add_clicked(self):
        if not can(self.permission, MODULE, "create"):
            Toast.error(self, "ليس لديك صلاحية للإضافة")
            return
        dialog = TrainingDialog(self.training_service, self)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تمت إضافة البرنامج بنجاح")

    def on_edit_clicked(self, program):
        if not can(self.permission, MODULE, "edit"):
            Toast.error(self, "ليس لديك صلاحية للتعديل")
            return
        dialog = TrainingDialog(self.training_service, self, program)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تم حفظ التعديلات بنجاح")

    def on_sessions_clicked(self, program):
        from ui.pages.training.program_detail import ProgramDetailDialog
        ProgramDetailDialog(self.training_service, program, self,
                            financial_service=self.financial_service).exec()

    def on_delete_clicked(self, program):
        if not can(self.permission, MODULE, "delete"):
            Toast.error(self, "ليس لديك صلاحية للحذف")
            return
        if not confirm(self, f"هل تريد حذف البرنامج \"{program.name}\"؟ سيتم حذف جلساته."):
            return
        try:
            self.training_service.delete_program(program.id)
            Toast.success(self, "تم الحذف بنجاح")
            self.load_data()
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لارتباط البرنامج بسجلات أخرى")
        except Exception as e:
            logger.error(f"Delete program failed: {e}")
            Toast.error(self, "تعذّر الحذف")
