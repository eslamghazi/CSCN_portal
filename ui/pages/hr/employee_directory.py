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
from application.services.hr_service import HRService, EmployeeDTO
from ui.pages.hr.employee_dialog import EmployeeDialog

MODULE = "hr"


class EmployeeDirectoryView(QWidget):
    def __init__(self, hr_service: HRService, permission=None):
        super().__init__()
        self.hr_service = hr_service
        self.permission = permission
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        header = PageHeader(
            "دليل شؤون العاملين",
            action_text="إضافة موظف جديد", action_icon="add",
        )
        header.action_clicked.connect(self.on_add_clicked)
        card.add(header)

        columns = ["الرقم التعريفي", "الاسم بالكامل", "رقم الهاتف", "المنصب", "الحالة", "إجراءات"]
        self.table = DataTable(columns)
        self.table.refresh_requested.connect(self.load_data)
        self.table.set_export_title("الموظفون")
        if can(self.permission, MODULE, "create"):
            self.table.enable_import(
                ["الاسم بالكامل", "البريد الإلكتروني", "رقم الهاتف"],
                self._import_row,
                ["محمد أحمد", "m@example.com", "0100000000"])
        self.table.add_filter("الحالة", [("نشط", "active"), ("غير نشط", "inactive")])
        card.add(self.table)
        main_layout.addWidget(card)

        self.overlay = LoadingOverlay(self)

    def _import_row(self, d):
        def s(key):
            v = d.get(key)
            return None if v in (None, "") else str(v).strip()
        name = s("الاسم بالكامل")
        if not name:
            raise ValueError("الاسم مطلوب")
        self.hr_service.add_employee(EmployeeDTO(
            full_name=name, email=s("البريد الإلكتروني"), phone=s("رقم الهاتف")))

    def load_data(self):
        self.overlay.start()
        QApplication.processEvents()
        try:
            employees = self.hr_service.get_all_employees()
            rows = []
            for e in employees:
                pos_name = e.position.title if e.position else "غير محدد"
                is_active = e.status == "active"
                status_text = "نشط" if is_active else "غير نشط"
                rows.append(Row(
                    cells=[
                        str(e.id), e.full_name, e.phone or "-", pos_name,
                        Badge(status_text, "active" if is_active else "inactive"),
                    ],
                    actions=[
                        Action("edit", "تعديل",
                               (lambda emp=e: self.on_edit_clicked(emp)), "primary"),
                        Action("delete", "حذف",
                               (lambda emp=e: self.on_delete_clicked(emp)), "danger"),
                    ],
                    search=f"{e.id} {e.full_name} {pos_name}",
                    sort=[e.id, e.full_name, e.phone or "", pos_name, status_text],
                    tags={"الحالة": e.status},
                ))
            self.table.set_records(rows)
        except Exception as e:
            logger.error(f"Employees load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب البيانات")
        finally:
            self.overlay.stop()

    def on_add_clicked(self):
        if not can(self.permission, MODULE, "create"):
            Toast.error(self, "ليس لديك صلاحية للإضافة")
            return
        dialog = EmployeeDialog(self.hr_service, self)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تمت إضافة الموظف بنجاح")

    def on_edit_clicked(self, employee):
        if not can(self.permission, MODULE, "edit"):
            Toast.error(self, "ليس لديك صلاحية للتعديل")
            return
        dialog = EmployeeDialog(self.hr_service, self, employee)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تم حفظ التعديلات بنجاح")

    def on_delete_clicked(self, employee):
        if not can(self.permission, MODULE, "delete"):
            Toast.error(self, "ليس لديك صلاحية للحذف")
            return
        if not confirm(self, f"هل تريد حذف الموظف \"{employee.full_name}\"؟"):
            return
        try:
            self.hr_service.delete_employee(employee.id)
            Toast.success(self, "تم الحذف بنجاح")
            self.load_data()
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لارتباط الموظف بسجلات أخرى")
        except Exception as e:
            logger.error(f"Delete employee failed: {e}")
            Toast.error(self, "تعذّر الحذف")
