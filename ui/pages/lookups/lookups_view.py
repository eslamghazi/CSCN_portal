"""Admin/superadmin page to manage all lookup (reference) data that populates
the select inputs across the app: standard categories, document categories,
record types, and job positions."""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTabWidget
)
from sqlalchemy.exc import IntegrityError
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from ui.widgets.data_table import DataTable, Row, Action
from ui.themes.colors import Colors


class _LookupDialog(BaseDialog):
    """Add/edit dialog for a single lookup item. `on_submit(name, desc)` performs
    the create or update; `initial` pre-fills the fields when editing."""

    def __init__(self, title, on_submit, initial=None, parent=None):
        super().__init__(title, parent, min_width=420)
        self.on_submit = on_submit
        self.name = self.add_field("الاسم:", QLineEdit(), required=True)
        self.desc = self.add_field("الوصف (اختياري):", QLineEdit())
        if initial:
            self.name.widget.setText(initial[0] or "")
            self.desc.widget.setText(initial[1] or "")
        self.build_buttons()

    def on_save(self):
        self.name.clear_error()
        name = self.name.text().strip()
        if not name:
            self.name.set_error("الاسم مطلوب.")
            return
        try:
            self.on_submit(name, self.desc.text().strip() or None)
            self.accept()
        except IntegrityError:
            self.name.set_error("الاسم مكرّر.")
        except Exception as e:
            logger.error(f"Save lookup failed: {e}")
            Toast.error(self, "تعذّر الحفظ")


class _LookupSection(QWidget):
    """One lookup tab: a titled header with an add button and a DataTable with
    per-row edit + delete actions. `loader()` returns (item_id, name, description)
    tuples; `creator(name, desc)`, `updater(id, name, desc)` and `deleter(id)`
    mutate the underlying table."""

    def __init__(self, title, loader, creator, updater, deleter, parent=None):
        super().__init__(parent)
        self.title = title
        self.loader = loader
        self.creator = creator
        self.updater = updater
        self.deleter = deleter

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)

        head = QHBoxLayout()
        label = QLabel(title)
        label.setStyleSheet(f"font-weight: 600; color: {Colors.PRIMARY};")
        head.addWidget(label)
        head.addStretch()
        add_btn = IconButton("إضافة", "add", variant="primary")
        add_btn.clicked.connect(self.on_add)
        head.addWidget(add_btn)
        layout.addLayout(head)

        self.table = DataTable(["الاسم", "الوصف", "إجراءات"])
        layout.addWidget(self.table)

        self.refresh()

    def on_add(self):
        if _LookupDialog(f"إضافة - {self.title}", self.creator, parent=self).exec():
            self.refresh()
            Toast.success(self, "تمت الإضافة بنجاح")

    def on_edit(self, item_id, name, desc):
        def submit(new_name, new_desc):
            self.updater(item_id, new_name, new_desc)
        if _LookupDialog(f"تعديل - {self.title}", submit,
                         initial=(name, desc), parent=self).exec():
            self.refresh()
            Toast.success(self, "تم التعديل بنجاح")

    def on_delete(self, item_id):
        if not confirm(self, "هل تريد حذف هذا العنصر؟"):
            return
        try:
            self.deleter(item_id)
            self.refresh()
            Toast.success(self, "تم الحذف")
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لاستخدامه في سجلات قائمة")
        except Exception as e:
            logger.error(f"Delete lookup failed: {e}")
            Toast.error(self, "تعذّر الحذف")

    def refresh(self):
        try:
            items = self.loader()
        except Exception as e:
            logger.error(f"Lookup load failed: {e}")
            items = []
        rows = []
        for item_id, name, desc in items:
            actions = [
                Action("edit", "تعديل",
                       lambda i=item_id, n=name, d=desc: self.on_edit(i, n, d),
                       variant="secondary"),
                Action("delete", "حذف",
                       lambda i=item_id: self.on_delete(i), variant="danger"),
            ]
            rows.append(Row(
                cells=[name, desc or "-"], actions=actions,
                search=f"{name} {desc or ''}", sort=[name, desc or ""]))
        self.table.set_records(rows)


class LookupsView(QWidget):
    def __init__(self, services: dict, permission=None):
        super().__init__()
        self.services = services
        self.permission = permission
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        card.add(PageHeader(
            "البيانات المرجعية",
            subtitle="إدارة القوائم المنسدلة: تصنيفات المعايير والوثائق وأنواع السجلات والمناصب."))

        q = self.services["quality"]
        d = self.services["document"]
        r = self.services["record"]
        hr = self.services["hr"]

        tabs = QTabWidget()
        tabs.addTab(_LookupSection(
            "تصنيفات المعايير",
            lambda: [(c.id, c.name, c.description) for c in q.get_all_categories()],
            q.create_category, q.update_category, q.delete_category),
            "تصنيفات المعايير")
        tabs.addTab(_LookupSection(
            "تصنيفات الوثائق",
            lambda: [(c.id, c.name, c.description) for c in d.get_categories()],
            d.create_category, d.update_category, d.delete_category),
            "تصنيفات الوثائق")
        tabs.addTab(_LookupSection(
            "أنواع السجلات",
            lambda: [(t.id, t.name, t.description) for t in r.get_all_record_types()],
            r.add_record_type, r.update_record_type, r.delete_record_type),
            "أنواع السجلات")
        tabs.addTab(_LookupSection(
            "المناصب الوظيفية",
            lambda: [(p.id, p.title, p.description) for p in hr.get_all_positions()],
            lambda name, desc: hr.create_position(name, desc),
            lambda pid, title, desc: hr.update_position(pid, title, desc),
            hr.delete_position),
            "المناصب الوظيفية")
        card.add(tabs)

        main_layout.addWidget(card)
