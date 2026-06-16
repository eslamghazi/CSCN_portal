from qtpy.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QApplication
from qtpy.QtCore import Qt
from sqlalchemy.exc import IntegrityError
from loguru import logger

from ui.widgets.data_table import DataTable, Row, Badge, Widget, Action
from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.loading_overlay import LoadingOverlay
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from ui.permissions import can
from application.services.quality_service import QualityService
from ui.pages.standards.standard_dialog import StandardDialog

MODULE = "quality"


def _progress(value: int) -> QProgressBar:
    bar = QProgressBar()
    bar.setValue(value)
    bar.setAlignment(Qt.AlignCenter)
    return bar


class StandardsListView(QWidget):
    def __init__(self, quality_service: QualityService, permission=None):
        super().__init__()
        self.quality_service = quality_service
        self.permission = permission
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        header = PageHeader(
            "إدارة معايير الجودة",
            action_text="إضافة معيار جديد", action_icon="add",
        )
        header.action_clicked.connect(self.on_add_clicked)
        card.add(header)

        columns = ["الكود", "اسم المعيار", "التصنيف", "الحالة", "نسبة الإنجاز", "إجراءات"]
        self.table = DataTable(columns)
        self.table.add_filter("الحالة", [("نشط", "active"), ("غير نشط", "inactive")])
        card.add(self.table)
        main_layout.addWidget(card)

        self.overlay = LoadingOverlay(self)

    def load_data(self):
        self.overlay.start()
        QApplication.processEvents()
        try:
            standards = self.quality_service.get_all_standards()
            rows = []
            for s in standards:
                compliance = int(self.quality_service.calculate_compliance(s.id))
                category = s.category.name if s.category else "غير محدد"
                is_active = s.status == "active"
                status_text = "نشط" if is_active else "غير نشط"
                rows.append(Row(
                    cells=[
                        s.code, s.name, category,
                        Badge(status_text, "active" if is_active else "inactive"),
                        Widget(lambda v=compliance: _progress(v)),
                    ],
                    actions=[
                        Action("standards", "المؤشرات",
                               (lambda st=s: self.on_indicators_clicked(st)), "secondary"),
                        Action("edit", "تعديل",
                               (lambda st=s: self.on_edit_clicked(st)), "primary"),
                        Action("delete", "حذف",
                               (lambda st=s: self.on_delete_clicked(st)), "danger"),
                    ],
                    search=f"{s.code} {s.name} {category}",
                    sort=[s.code, s.name, category, status_text, compliance],
                    tags={"الحالة": s.status},
                ))
            self.table.set_records(rows)
        except Exception as e:
            logger.error(f"Standards load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب البيانات")
        finally:
            self.overlay.stop()

    def on_add_clicked(self):
        if not can(self.permission, MODULE, "create"):
            Toast.error(self, "ليس لديك صلاحية للإضافة")
            return
        dialog = StandardDialog(self.quality_service, self)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تمت إضافة المعيار بنجاح")

    def on_edit_clicked(self, standard):
        if not can(self.permission, MODULE, "edit"):
            Toast.error(self, "ليس لديك صلاحية للتعديل")
            return
        dialog = StandardDialog(self.quality_service, self, standard)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تم حفظ التعديلات بنجاح")

    def on_indicators_clicked(self, standard):
        from ui.pages.standards.indicator_dialog import IndicatorsDialog
        IndicatorsDialog(self.quality_service, standard, self).exec()
        self.load_data()  # compliance % may have changed

    def on_delete_clicked(self, standard):
        if not can(self.permission, MODULE, "delete"):
            Toast.error(self, "ليس لديك صلاحية للحذف")
            return
        if not confirm(self, f"هل تريد حذف المعيار \"{standard.name}\"؟"):
            return
        try:
            self.quality_service.delete_standard(standard.id)
            Toast.success(self, "تم الحذف بنجاح")
            self.load_data()
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لارتباط المعيار بمؤشرات أو سجلات أخرى")
        except Exception as e:
            logger.error(f"Delete standard failed: {e}")
            Toast.error(self, "تعذّر الحذف")
