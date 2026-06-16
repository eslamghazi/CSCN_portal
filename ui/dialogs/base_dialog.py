from qtpy.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel
from qtpy.QtCore import Qt

from ui.themes.colors import Colors
from ui.themes.typography import Typography
from ui.themes.tokens import Spacing
from ui.widgets.icon_button import IconButton


class Field:
    """Wraps an input widget plus its inline error label so dialogs can show
    field-level validation feedback instead of a QMessageBox."""

    def __init__(self, widget, error_label: QLabel):
        self.widget = widget
        self.error_label = error_label

    def text(self) -> str:
        """Best-effort text getter across input widget types."""
        for getter in ("text", "currentText", "toPlainText"):
            if hasattr(self.widget, getter):
                return getattr(self.widget, getter)()
        return ""

    def set_error(self, message: str):
        self.widget.setProperty("error", True)
        self._repolish()
        self.error_label.setText(message)
        self.error_label.show()

    def clear_error(self):
        if self.widget.property("error"):
            self.widget.setProperty("error", False)
            self._repolish()
        self.error_label.hide()

    def _repolish(self):
        style = self.widget.style()
        style.unpolish(self.widget)
        style.polish(self.widget)


class BaseDialog(QDialog):
    """Base for all modal dialogs. Provides the standard chrome (heading, token
    margins) and helpers — add_field/add_row/build_buttons — so individual
    dialogs no longer copy-paste a stylesheet or reimplement validation.

    Input styling now comes entirely from the global generated stylesheet.
    Subclasses implement on_save().
    """

    def __init__(self, title: str, parent=None, min_width: int = 500):
        super().__init__(parent)
        self.setObjectName("appDialog")
        self.setWindowTitle(title)
        self.setMinimumWidth(min_width)

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        self._root.setSpacing(Spacing.MD)

        heading = QLabel(title)
        heading.setStyleSheet(
            f"font-size: {Typography.LG}px; font-weight: bold; color: {Colors.PRIMARY};"
        )
        self._root.addWidget(heading)

        self.content = QVBoxLayout()
        self.content.setSpacing(Spacing.MD)
        self._root.addLayout(self.content)

    def _make_field(self, label_text, widget, required=False) -> tuple:
        from qtpy.QtWidgets import QVBoxLayout as _V
        col = _V()
        col.setSpacing(4)
        label = QLabel()
        if required:
            label.setTextFormat(Qt.RichText)
            label.setText(
                f"{label_text} <span style='color:{Colors.DANGER}'>*</span>")
        else:
            label.setText(label_text)
        label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;")
        col.addWidget(label)
        col.addWidget(widget)
        error = QLabel("")
        error.setObjectName("fieldError")
        error.hide()
        col.addWidget(error)
        return col, Field(widget, error)

    def add_field(self, label_text, widget, required=False) -> Field:
        col, field = self._make_field(label_text, widget, required)
        self.content.addLayout(col)
        return field

    def add_row(self, *specs) -> list:
        """Place several fields side by side. Each spec is (label, widget) or
        (label, widget, required). Returns the Fields in order."""
        row = QHBoxLayout()
        row.setSpacing(Spacing.MD)
        fields = []
        for spec in specs:
            label_text, widget = spec[0], spec[1]
            required = spec[2] if len(spec) > 2 else False
            col, field = self._make_field(label_text, widget, required)
            row.addLayout(col)
            fields.append(field)
        self.content.addLayout(row)
        return fields

    def add_widget(self, widget):
        self.content.addWidget(widget)
        return widget

    def build_buttons(self, save_text="حفظ", cancel_text="إلغاء"):
        self._root.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        cancel = IconButton(cancel_text, "cancel", variant="secondary")
        cancel.clicked.connect(self.reject)
        save = IconButton(save_text, "save", variant="primary")
        save.clicked.connect(self.on_save)
        row.addWidget(cancel)
        row.addWidget(save)
        self._root.addLayout(row)
        self.save_btn = save
        self.cancel_btn = cancel

    def on_save(self):  # pragma: no cover - abstract
        raise NotImplementedError
