from qtpy.QtWidgets import QLineEdit, QTextEdit, QLabel, QHBoxLayout, QComboBox, QDateEdit
from qtpy.QtCore import QDate
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.data_table import DataTable
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.themes.colors import Colors
from application.services.partnership_service import PartnershipService, PartnershipDTO
from application.validators.validators import is_valid_email


class PartnershipDialog(BaseDialog):
    """Create a new partner organization."""

    def __init__(self, partner_service: PartnershipService, parent=None):
        super().__init__("إضافة شريك جديد", parent)
        self.partner_service = partner_service

        self.name_field = self.add_field("اسم الجهة:", QLineEdit(), required=True)
        self.contact_field, self.email_field = self.add_row(
            ("مسؤول التواصل:", QLineEdit()), ("البريد الإلكتروني:", QLineEdit()))
        self.phone_field = self.add_field("رقم الهاتف:", QLineEdit())
        address = QTextEdit()
        address.setMaximumHeight(70)
        self.address_field = self.add_field("العنوان:", address)

        self.build_buttons()

    def on_save(self):
        self.name_field.clear_error()
        self.email_field.clear_error()
        name = self.name_field.text().strip()
        email = self.email_field.text().strip()
        if not name:
            self.name_field.set_error("اسم الجهة مطلوب.")
            return
        if email and not is_valid_email(email):
            self.email_field.set_error("بريد إلكتروني غير صالح.")
            return
        dto = PartnershipDTO(
            name=name,
            contact_person=self.contact_field.text().strip() or None,
            email=self.email_field.text().strip() or None,
            phone=self.phone_field.text().strip() or None,
            address=self.address_field.text().strip() or None,
        )
        try:
            self.partner_service.add_partner(dto)
            self.accept()
        except Exception as e:
            logger.error(f"Add partner failed: {e}")
            Toast.error(self, "تعذّر حفظ الشريك")


class PartnerDetailsDialog(BaseDialog):
    """Read-only partner details."""

    def __init__(self, partner, parent=None):
        super().__init__(f"تفاصيل: {partner.name}", parent)
        rows = [
            ("اسم الجهة", partner.name),
            ("مسؤول التواصل", partner.contact_person or "-"),
            ("البريد الإلكتروني", partner.email or "-"),
            ("رقم الهاتف", partner.phone or "-"),
            ("العنوان", partner.address or "-"),
        ]
        for label_text, value in rows:
            row = QHBoxLayout()
            lbl = QLabel(label_text + ":")
            lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-weight: 600;")
            val = QLabel(str(value))
            val.setStyleSheet(f"color: {Colors.TEXT};")
            val.setWordWrap(True)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            self.content.addLayout(row)

        self._add_close_button()

    def _add_close_button(self):
        self._root.addStretch()
        bar = QHBoxLayout()
        bar.addStretch()
        close = IconButton("إغلاق", "cancel", variant="secondary")
        close.clicked.connect(self.accept)
        bar.addWidget(close)
        self._root.addLayout(bar)


class AddAgreementDialog(BaseDialog):
    """Add an agreement to a partner."""

    TYPES = [("agreement", "اتفاقية"), ("mou", "مذكرة تفاهم"), ("contract", "عقد")]

    def __init__(self, partner_service: PartnershipService, partner, parent=None):
        super().__init__("إضافة اتفاقية", parent)
        self.partner_service = partner_service
        self.partner = partner

        self.title_field = self.add_field("عنوان الاتفاقية:", QLineEdit(), required=True)
        type_combo = QComboBox()
        for value, label in self.TYPES:
            type_combo.addItem(label, value)
        self.type_field = self.add_field("النوع:", type_combo)

        start = QDateEdit()
        start.setCalendarPopup(True)
        start.setDate(QDate.currentDate())
        end = QDateEdit()
        end.setCalendarPopup(True)
        end.setDate(QDate.currentDate().addYears(1))
        self.start_field, self.end_field = self.add_row(
            ("تاريخ البداية:", start), ("تاريخ النهاية:", end))

        self.build_buttons()

    def on_save(self):
        self.title_field.clear_error()
        title = self.title_field.text().strip()
        if not title:
            self.title_field.set_error("عنوان الاتفاقية مطلوب.")
            return
        try:
            self.partner_service.add_agreement(
                self.partner.id,
                title,
                self.start_field.widget.date().toPython(),
                self.end_field.widget.date().toPython(),
                agreement_type=self.type_field.widget.currentData(),
            )
            self.accept()
        except Exception as e:
            logger.error(f"Add agreement failed: {e}")
            Toast.error(self, "تعذّر حفظ الاتفاقية")


class AgreementsDialog(BaseDialog):
    """List a partner's agreements with the ability to add new ones."""

    TYPE_LABELS = {"agreement": "اتفاقية", "mou": "مذكرة تفاهم", "contract": "عقد"}

    def __init__(self, partner_service: PartnershipService, partner, parent=None):
        super().__init__(f"اتفاقيات: {partner.name}", parent, min_width=640)
        self.partner_service = partner_service
        self.partner = partner

        add_btn = IconButton("إضافة اتفاقية", "add", variant="primary")
        add_btn.clicked.connect(self.on_add)
        bar = QHBoxLayout()
        bar.addStretch()
        bar.addWidget(add_btn)
        self.content.addLayout(bar)

        self.table = DataTable(["العنوان", "النوع", "من", "إلى", "الحالة"])
        self.add_widget(self.table)
        self.load()

        self._root.addStretch()
        close_bar = QHBoxLayout()
        close_bar.addStretch()
        close = IconButton("إغلاق", "cancel", variant="secondary")
        close.clicked.connect(self.accept)
        close_bar.addWidget(close)
        self._root.addLayout(close_bar)

    def load(self):
        agreements = self.partner_service.agreement_repo.get_by_partner(self.partner.id)
        rows = [
            [
                a.title,
                self.TYPE_LABELS.get(a.agreement_type, a.agreement_type),
                a.start_date.isoformat() if a.start_date else "-",
                a.end_date.isoformat() if a.end_date else "-",
                a.status,
            ]
            for a in agreements
        ]
        self.table.set_data(rows)

    def on_add(self):
        dialog = AddAgreementDialog(self.partner_service, self.partner, self)
        if dialog.exec():
            self.load()
            Toast.success(self, "تمت إضافة الاتفاقية")
