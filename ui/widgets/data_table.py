import math
from typing import List

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QLineEdit, QComboBox
)
from qtpy.QtCore import Qt, Signal, QSize

from ui.themes.colors import Colors
from ui.themes.icons import icon
from ui.widgets.status_badge import StatusBadge
from ui.widgets.icon_button import IconButton
from ui.widgets.cell import cell_widget


class Badge:
    """A status-pill cell value."""
    def __init__(self, text: str, kind: str = "info"):
        self.text = text
        self.kind = kind


class Widget:
    """An arbitrary-widget cell value; `factory` is a callable returning a QWidget
    (rebuilt on each render, e.g. a progress bar)."""
    def __init__(self, factory):
        self.factory = factory


class Action:
    """A row action -> icon-only button in the actions column."""
    def __init__(self, icon_name, tooltip, callback, variant="secondary"):
        self.icon_name = icon_name
        self.tooltip = tooltip
        self.callback = callback
        self.variant = variant


class Row:
    """One table row.

    cells: list of str | Badge for the non-action columns.
    actions: list[Action] rendered in the last ("إجراءات") column.
    search: text matched against the search box.
    sort: per-column sort keys (parallel to cells); falls back to cell text.
    tags: {filter_title: value} matched against filter combos.
    """
    def __init__(self, cells, actions=None, search="", sort=None, tags=None):
        self.cells = cells
        self.actions = actions or []
        self.search = search
        self.sort = sort or []
        self.tags = tags or {}


def _norm(value):
    """Type-stable sort key so str/number/None never compare-clash."""
    if value is None:
        return (2, "")
    if isinstance(value, (int, float)):
        return (0, value)
    return (1, str(value).lower())


class DataTable(QWidget):
    """Reusable table with client-side search, filtering, column sorting,
    pagination and dual empty states. Feed it Row models via set_records()."""

    page_changed = Signal(int)        # kept for backward compatibility
    search_requested = Signal(str)    # kept for backward compatibility
    row_action_requested = Signal(int, str)

    def __init__(self, columns: List[str], page_size: int = 25):
        super().__init__()
        self.columns = columns
        self._all_rows: List[Row] = []
        self._query = ""
        self._filters = []  # list of {"title": str, "combo": QComboBox}
        self._sort_col = None
        self._sort_desc = False
        self._page = 1
        self._page_size = page_size
        self.setup_ui()

    # ------------------------------------------------------------------ UI
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.toolbar = QHBoxLayout()
        search_icon = QLabel()
        si = icon("search", color=Colors.TEXT_MUTED)
        if not si.isNull():
            search_icon.setPixmap(si.pixmap(QSize(16, 16)))
        self.toolbar.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.toolbar.addWidget(self.search_input)
        self.toolbar.addStretch()
        layout.addLayout(self.toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.horizontalHeader().sectionClicked.connect(self._on_sort)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet(
            f"QTableWidget::item:hover {{ background-color: {Colors.PRIMARY_SOFT}; }}"
        )
        layout.addWidget(self.table)

        self.empty_label = QLabel("لا توجد بيانات لعرضها")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(
            f"font-size: 16px; color: {Colors.TEXT_MUTED}; margin: 24px;"
        )
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        pagination = QHBoxLayout()
        self.prev_btn = IconButton("السابق", variant="secondary", compact=True)
        self.prev_btn.clicked.connect(self.prev_page)
        self.page_label = QLabel("صفحة 1 من 1")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.next_btn = IconButton("التالي", variant="secondary", compact=True)
        self.next_btn.clicked.connect(self.next_page)
        pagination.addStretch()
        pagination.addWidget(self.next_btn)
        pagination.addWidget(self.page_label)
        pagination.addWidget(self.prev_btn)
        pagination.addStretch()
        layout.addLayout(pagination)

    def add_filter(self, title: str, options: list):
        """Add a filter combo. options: list of (label, value); a leading
        "الكل" (value None) is added automatically. Rows are matched on
        row.tags[title] == selected value."""
        label = QLabel(title)
        combo = QComboBox()
        combo.addItem("الكل", None)
        for opt_label, value in options:
            combo.addItem(opt_label, value)
        combo.currentIndexChanged.connect(self._on_filter_changed)
        # insert before the trailing stretch
        self.toolbar.insertWidget(self.toolbar.count() - 1, label)
        self.toolbar.insertWidget(self.toolbar.count() - 1, combo)
        self._filters.append({"title": title, "combo": combo})

    # --------------------------------------------------------------- data
    def set_records(self, rows: list):
        self._all_rows = rows or []
        self._page = 1
        self._render()

    def set_data(self, data: list):
        """Backward-compatible: list of list[str] -> plain text rows."""
        rows = [Row(cells=list(r), search=" ".join(str(c) for c in r), sort=list(r))
                for r in data]
        self.set_records(rows)

    # ------------------------------------------------------------- filters
    def _visible(self) -> list:
        rows = self._all_rows
        if self._query:
            q = self._query.lower()
            rows = [r for r in rows if q in (r.search or "").lower()]
        for f in self._filters:
            value = f["combo"].currentData()
            if value is not None:
                rows = [r for r in rows if r.tags.get(f["title"]) == value]
        if self._sort_col is not None:
            col = self._sort_col

            def key(r):
                if col < len(r.sort) and r.sort[col] is not None:
                    return _norm(r.sort[col])
                cell = r.cells[col] if col < len(r.cells) else ""
                return _norm(cell.text if isinstance(cell, Badge) else cell)

            rows = sorted(rows, key=key, reverse=self._sort_desc)
        return rows

    def _render(self):
        visible = self._visible()
        total = len(visible)

        if not self._all_rows:
            self._show_empty("لا توجد بيانات لعرضها")
            return
        if total == 0:
            self._show_empty("لا توجد نتائج مطابقة لبحثك")
            return

        self.table.show()
        self.empty_label.hide()
        self._set_pagination_visible(True)

        pages = max(1, math.ceil(total / self._page_size))
        self._page = min(self._page, pages)
        start = (self._page - 1) * self._page_size
        page_rows = visible[start:start + self._page_size]

        action_col = len(self.columns) - 1
        self.table.setRowCount(len(page_rows))
        for r_idx, row in enumerate(page_rows):
            for c_idx, cell in enumerate(row.cells):
                if c_idx >= len(self.columns):
                    break
                if isinstance(cell, Badge):
                    self.table.setItem(r_idx, c_idx, QTableWidgetItem(""))
                    self.table.setCellWidget(
                        r_idx, c_idx, StatusBadge.for_cell(cell.text, cell.kind))
                elif isinstance(cell, Widget):
                    self.table.setItem(r_idx, c_idx, QTableWidgetItem(""))
                    self.table.setCellWidget(r_idx, c_idx, cell.factory())
                else:
                    item = QTableWidgetItem(str(cell))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r_idx, c_idx, item)
            if row.actions:
                buttons = [
                    self._make_action_button(a) for a in row.actions
                ]
                self.table.setCellWidget(r_idx, action_col, cell_widget(*buttons))

        self.page_label.setText(f"صفحة {self._page} من {pages}")
        self.prev_btn.setEnabled(self._page > 1)
        self.next_btn.setEnabled(self._page < pages)

    @staticmethod
    def _make_action_button(action: Action) -> IconButton:
        btn = IconButton(icon_name=action.icon_name, variant=action.variant,
                         tooltip=action.tooltip, icon_only=True)
        btn.clicked.connect(lambda _checked=False, cb=action.callback: cb())
        return btn

    def _show_empty(self, message: str):
        self.table.hide()
        self.empty_label.setText(message)
        self.empty_label.show()
        self._set_pagination_visible(False)

    def _set_pagination_visible(self, visible: bool):
        self.prev_btn.setVisible(visible)
        self.next_btn.setVisible(visible)
        self.page_label.setVisible(visible)

    # ------------------------------------------------------------- events
    def _on_search_changed(self, text: str):
        self._query = text.strip()
        self._page = 1
        self._render()

    def _on_filter_changed(self, _index: int):
        self._page = 1
        self._render()

    def _on_sort(self, col: int):
        if self._sort_col == col:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col = col
            self._sort_desc = False
        order = Qt.DescendingOrder if self._sort_desc else Qt.AscendingOrder
        self.table.horizontalHeader().setSortIndicator(col, order)
        self._render()

    def prev_page(self):
        if self._page > 1:
            self._page -= 1
            self._render()

    def next_page(self):
        self._page += 1
        self._render()
