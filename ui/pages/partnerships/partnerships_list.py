from qtpy.QtWidgets import QWidget, QVBoxLayout, QApplication
from sqlalchemy.exc import IntegrityError
from loguru import logger

from ui.widgets.data_table import DataTable, Row, Action
from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.loading_overlay import LoadingOverlay
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from ui.permissions import can
from application.services.partnership_service import PartnershipService
from ui.pages.partnerships.partnership_dialog import (
    PartnershipDialog, PartnerDetailsDialog, AgreementsDialog,
)

MODULE = "partnership"


class PartnershipsListView(QWidget):
    def __init__(self, partner_service: PartnershipService, permission=None):
        super().__init__()
        self.partner_service = partner_service
        self.permission = permission
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        header = PageHeader(
            "إدارة الشراكات والبروتوكولات",
            action_text="إضافة شريك جديد", action_icon="add",
        )
        header.action_clicked.connect(self.on_add_clicked)
        card.add(header)

        columns = ["اسم الجهة", "مسؤول التواصل", "البريد الإلكتروني", "رقم الهاتف", "إجراءات"]
        self.table = DataTable(columns)
        card.add(self.table)
        main_layout.addWidget(card)

        self.overlay = LoadingOverlay(self)

    def load_data(self):
        self.overlay.start()
        QApplication.processEvents()
        try:
            partners = self.partner_service.get_all_partners()
            rows = []
            for p in partners:
                rows.append(Row(
                    cells=[p.name, p.contact_person or "-", p.email or "-", p.phone or "-"],
                    actions=[
                        Action("view", "عرض",
                               (lambda partner=p: self.on_view(partner)), "secondary"),
                        Action("agreements", "الاتفاقيات",
                               (lambda partner=p: self.on_agreements(partner)), "primary"),
                        Action("delete", "حذف",
                               (lambda partner=p: self.on_delete_clicked(partner)), "danger"),
                    ],
                    search=f"{p.name} {p.contact_person or ''} {p.email or ''}",
                    sort=[p.name, p.contact_person or "", p.email or "", p.phone or ""],
                ))
            self.table.set_records(rows)
        except Exception as e:
            logger.error(f"Partnerships load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب البيانات")
        finally:
            self.overlay.stop()

    def on_add_clicked(self):
        if not can(self.permission, MODULE, "create"):
            Toast.error(self, "ليس لديك صلاحية للإضافة")
            return
        dialog = PartnershipDialog(self.partner_service, self)
        if dialog.exec():
            self.load_data()
            Toast.success(self, "تمت إضافة الشريك بنجاح")

    def on_view(self, partner):
        PartnerDetailsDialog(partner, self).exec()

    def on_agreements(self, partner):
        AgreementsDialog(self.partner_service, partner, self).exec()

    def on_delete_clicked(self, partner):
        if not can(self.permission, MODULE, "delete"):
            Toast.error(self, "ليس لديك صلاحية للحذف")
            return
        if not confirm(self, f"هل تريد حذف الجهة \"{partner.name}\"؟"):
            return
        try:
            self.partner_service.delete_partner(partner.id)
            Toast.success(self, "تم الحذف بنجاح")
            self.load_data()
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لوجود اتفاقيات مرتبطة بالجهة")
        except Exception as e:
            logger.error(f"Delete partner failed: {e}")
            Toast.error(self, "تعذّر الحذف")
