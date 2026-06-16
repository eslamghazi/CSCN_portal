from qtpy.QtWidgets import QWidget, QHBoxLayout
from qtpy.QtCore import Qt


def cell_widget(*widgets, spacing: int = 6) -> QWidget:
    """Wrap one or more widgets centered in a container suitable for
    QTableWidget.setCellWidget (e.g. action buttons in a table row)."""
    wrap = QWidget()
    layout = QHBoxLayout(wrap)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(spacing)
    layout.setAlignment(Qt.AlignCenter)
    for widget in widgets:
        layout.addWidget(widget)
    return wrap
