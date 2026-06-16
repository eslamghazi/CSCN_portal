from qtpy.QtWidgets import (
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem
)
from qtpy.QtCore import Qt
from sqlalchemy.exc import IntegrityError
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from application.services.quality_service import QualityService, IndicatorDTO

STATUS = [("active", "نشط"), ("compliant", "مطابق"), ("non_compliant", "غير مطابق")]
STATUS_LABELS = dict(STATUS)


class IndicatorDialog(BaseDialog):
    """Create/edit a single indicator under a standard."""

    def __init__(self, quality_service: QualityService, standard, parent=None,
                 indicator=None):
        super().__init__(
            "إضافة مؤشر" if not indicator else "تعديل المؤشر", parent, min_width=480)
        self.qs = quality_service
        self.standard = standard
        self.indicator = indicator

        self.code = self.add_field("كود المؤشر:", QLineEdit(), required=True)
        self.name = self.add_field("اسم المؤشر:", QLineEdit(), required=True)

        weight = QDoubleSpinBox()
        weight.setRange(0, 100)
        weight.setDecimals(2)
        status = QComboBox()
        for value, label in STATUS:
            status.addItem(label, value)
        self.weight, self.status = self.add_row(
            ("الوزن النسبي:", weight), ("الحالة:", status))

        parent_combo = QComboBox()
        parent_combo.addItem("— مؤشر رئيسي —", None)
        for ind in self._flatten(self.qs.get_indicators(standard.id)):
            if not indicator or ind.id != indicator.id:
                parent_combo.addItem(ind.name, ind.id)
        self.parent_field = self.add_field("المؤشر الأب (اختياري):", parent_combo)

        notes = QTextEdit()
        notes.setMaximumHeight(70)
        self.desc = self.add_field("الوصف:", notes)

        self.build_buttons()
        self.populate()

    @staticmethod
    def _flatten(roots):
        out = []
        stack = list(roots)
        while stack:
            node = stack.pop(0)
            out.append(node)
            stack[0:0] = list(node.sub_indicators)
        return out

    def populate(self):
        if not self.indicator:
            return
        i = self.indicator
        self.code.widget.setText(i.code)
        self.name.widget.setText(i.name)
        self.weight.widget.setValue(float(i.weight) if i.weight is not None else 0)
        for idx in range(self.status.widget.count()):
            if self.status.widget.itemData(idx) == i.status:
                self.status.widget.setCurrentIndex(idx)
        if i.parent_id:
            pidx = self.parent_field.widget.findData(i.parent_id)
            if pidx >= 0:
                self.parent_field.widget.setCurrentIndex(pidx)
        self.desc.widget.setPlainText(i.description or "")

    def on_save(self):
        self.code.clear_error()
        self.name.clear_error()
        code = self.code.text().strip()
        name = self.name.text().strip()
        if not code:
            self.code.set_error("كود المؤشر مطلوب.")
            return
        if not name:
            self.name.set_error("اسم المؤشر مطلوب.")
            return
        dto = IndicatorDTO(
            id=self.indicator.id if self.indicator else None,
            code=code, name=name,
            description=self.desc.text().strip() or None,
            standard_id=self.standard.id,
            parent_id=self.parent_field.widget.currentData(),
            weight=self.weight.widget.value() or None,
            status=self.status.widget.currentData(),
        )
        try:
            if self.indicator:
                self.qs.update_indicator(dto)
            else:
                self.qs.create_indicator(dto)
            self.accept()
        except IntegrityError:
            self.code.set_error("الكود مكرّر — اختر كودًا فريدًا.")
        except Exception as e:
            logger.error(f"Save indicator failed: {e}")
            Toast.error(self, "تعذّر حفظ المؤشر")


class IndicatorsDialog(BaseDialog):
    """Manage (tree view) the indicators of a standard."""

    def __init__(self, quality_service: QualityService, standard, parent=None):
        super().__init__(f"مؤشرات المعيار: {standard.name}", parent, min_width=640)
        self.qs = quality_service
        self.standard = standard

        top = QHBoxLayout()
        top.addStretch()
        add_btn = IconButton("إضافة مؤشر", "add", variant="primary")
        add_btn.clicked.connect(self.on_add)
        top.addWidget(add_btn)
        self.content.addLayout(top)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["الكود", "اسم المؤشر", "الوزن", "الحالة"])
        self.tree.setColumnWidth(1, 260)
        self.add_widget(self.tree)

        actions = QHBoxLayout()
        actions.addStretch()
        edit_btn = IconButton("تعديل المحدد", "edit", variant="secondary")
        edit_btn.clicked.connect(self.on_edit)
        del_btn = IconButton("حذف المحدد", "delete", variant="danger")
        del_btn.clicked.connect(self.on_delete)
        actions.addWidget(edit_btn)
        actions.addWidget(del_btn)
        self.content.addLayout(actions)

        self._root.addStretch()
        close_row = QHBoxLayout()
        close_row.addStretch()
        close = IconButton("إغلاق", "cancel", variant="secondary")
        close.clicked.connect(self.accept)
        close_row.addWidget(close)
        self._root.addLayout(close_row)

        self.load()

    def load(self):
        self.tree.clear()
        for ind in self.qs.get_indicators(self.standard.id):
            self._add_node(ind, self.tree)

    def _add_node(self, indicator, parent):
        weight = str(indicator.weight) if indicator.weight is not None else "-"
        item = QTreeWidgetItem(parent, [
            indicator.code, indicator.name, weight,
            STATUS_LABELS.get(indicator.status, indicator.status),
        ])
        item.setData(0, Qt.UserRole, indicator.id)
        for sub in indicator.sub_indicators:
            self._add_node(sub, item)
        if isinstance(parent, QTreeWidget):
            item.setExpanded(True)

    def _selected_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def on_add(self):
        if IndicatorDialog(self.qs, self.standard, self).exec():
            self.load()
            Toast.success(self, "تمت إضافة المؤشر")

    def on_edit(self):
        indicator_id = self._selected_id()
        if not indicator_id:
            Toast.error(self, "اختر مؤشرًا أولًا")
            return
        indicator = self.qs.get_indicator(indicator_id)
        if indicator and IndicatorDialog(self.qs, self.standard, self, indicator).exec():
            self.load()

    def on_delete(self):
        indicator_id = self._selected_id()
        if not indicator_id:
            Toast.error(self, "اختر مؤشرًا أولًا")
            return
        if not confirm(self, "هل تريد حذف هذا المؤشر؟ سيتأثر حساب نسبة المطابقة."):
            return
        try:
            self.qs.delete_indicator(indicator_id)
            self.load()
            Toast.success(self, "تم الحذف")
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لوجود مؤشرات فرعية مرتبطة")
        except Exception as e:
            logger.error(f"Delete indicator failed: {e}")
            Toast.error(self, "تعذّر الحذف")
