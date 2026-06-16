"""Builds the global application stylesheet from design tokens.

This replaces the static ui/themes/base_theme.qss. Colors/typography/radii all
come from the token modules so there is one source of truth. Note: literal QSS
braces are doubled ({{ }}) because this is an f-string.
"""
from ui.themes.colors import Colors as C
from ui.themes.typography import Typography as T
from ui.themes.tokens import Radius as R
from ui.themes.icon_assets import ensure_qss_assets


def build_stylesheet() -> str:
    _assets = ensure_qss_assets()

    def _img(name: str) -> str:
        # Quote the path — temp/user dirs can contain spaces, which break url().
        path = _assets.get(name)
        return f'image: url("{path}");' if path else ""

    down_arrow = _img("chevron_down")
    caret_up = _img("caret_up")
    caret_down = _img("caret_down")
    calendar = _img("calendar")
    check = _img("check")

    return f"""
/* ============ Global ============ */
* {{
    font-family: {T.FAMILY_STACK};
    color: {C.TEXT};
    font-size: {T.BASE}px;
}}

QMainWindow, QDialog {{
    background-color: {C.BG};
}}
QWidget#centralWidget {{
    background-color: {C.BG};
}}
QDialog#appDialog {{
    background-color: {C.SURFACE};
}}

QLabel {{
    border: none;
    background: transparent;
}}

/* ============ Buttons ============ */
QPushButton {{
    background-color: {C.SURFACE_SUNKEN};
    color: {C.TEXT_SECONDARY};
    border: 1px solid {C.BORDER};
    border-radius: {R.SM}px;
    padding: 8px 16px;
}}
QPushButton:hover {{
    background-color: {C.BORDER};
}}
QPushButton:disabled {{
    color: {C.TEXT_MUTED};
    background-color: {C.SURFACE_SUNKEN};
    border-color: {C.BORDER};
}}

QPushButton.primary {{
    background-color: {C.PRIMARY};
    color: {C.TEXT_ON_PRIMARY};
    border: none;
    border-radius: {R.SM}px;
    padding: 10px 20px;
    font-weight: 600;
}}
QPushButton.primary:hover {{
    background-color: {C.PRIMARY_HOVER};
}}
QPushButton.primary:pressed {{
    background-color: {C.PRIMARY_PRESSED};
}}
QPushButton.primary:disabled {{
    background-color: {C.PRIMARY_DISABLED};
}}

QPushButton.secondary {{
    background-color: {C.SURFACE};
    color: {C.PRIMARY};
    border: 1px solid {C.BORDER_STRONG};
    border-radius: {R.SM}px;
    padding: 10px 20px;
    font-weight: 600;
}}
QPushButton.secondary:hover {{
    background-color: {C.PRIMARY_SOFT};
    border-color: {C.PRIMARY};
}}

QPushButton.danger {{
    background-color: {C.DANGER};
    color: {C.TEXT_ON_PRIMARY};
    border: none;
    border-radius: {R.SM}px;
    padding: 10px 20px;
    font-weight: 600;
}}
QPushButton.danger:hover {{
    background-color: {C.DANGER_TEXT};
}}

QPushButton#compact {{
    padding: 5px 12px;
    font-size: {T.SM}px;
}}

/* ============ Inputs ============ */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background-color: {C.SURFACE};
    border: 1px solid {C.BORDER};
    border-radius: {R.SM}px;
    padding: 10px 12px;
    min-height: 20px;
    color: {C.TEXT};
    selection-background-color: {C.PRIMARY_SOFT};
    selection-color: {C.PRIMARY_SOFT_TEXT};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover,
QDateEdit:hover, QTextEdit:hover {{
    border: 1px solid {C.BORDER_STRONG};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border: 2px solid {C.ACCENT};
    padding: 9px 11px;
}}
QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled {{
    background-color: {C.SURFACE_SUNKEN};
    color: {C.TEXT_MUTED};
}}
QLineEdit::placeholder {{
    color: {C.TEXT_MUTED};
}}

/* Error state (set widget property error=true) */
QLineEdit[error="true"], QTextEdit[error="true"], QComboBox[error="true"],
QSpinBox[error="true"], QDoubleSpinBox[error="true"], QDateEdit[error="true"] {{
    border: 1px solid {C.DANGER};
}}
QLabel#fieldError {{
    color: {C.DANGER_TEXT};
    font-size: {T.SM}px;
}}

/* Spin box buttons + arrows */
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top left;
    width: 28px;
    border: none;
    border-right: 1px solid {C.BORDER};
    border-bottom: 1px solid {C.BORDER};
    background: {C.SURFACE_ALT};
    border-top-left-radius: {R.SM}px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom left;
    width: 28px;
    border: none;
    border-right: 1px solid {C.BORDER};
    background: {C.SURFACE_ALT};
    border-bottom-left-radius: {R.SM}px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {C.PRIMARY_SOFT};
}}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
    background: {C.BORDER_STRONG};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    {caret_up}
    width: 14px;
    height: 14px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    {caret_down}
    width: 14px;
    height: 14px;
}}
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled,
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled {{
    width: 14px;
    height: 14px;
}}

/* ComboBox / DateEdit dropdown (RTL: arrow on the left) */
QComboBox::drop-down, QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top left;
    width: 28px;
    border-top-left-radius: {R.SM}px;
    border-bottom-left-radius: {R.SM}px;
    border-right: 1px solid {C.BORDER};
}}
QComboBox::down-arrow {{
    {down_arrow}
    width: 12px;
    height: 12px;
}}
QDateEdit::down-arrow {{
    {calendar}
    width: 15px;
    height: 15px;
}}
/* Dropdown popup: a padded, rounded menu with generous, clearly-separated
   options and a prominent highlight on the hovered/selected one. */
QComboBox QAbstractItemView, QDateEdit QAbstractItemView {{
    border: 1px solid {C.BORDER_STRONG};
    border-radius: {R.MD}px;
    background-color: {C.SURFACE};
    selection-background-color: {C.PRIMARY_SOFT};
    selection-color: {C.PRIMARY_SOFT_TEXT};
    outline: none;
    padding: 6px;
}}
QComboBox QAbstractItemView::item, QDateEdit QAbstractItemView::item {{
    min-height: 38px;
    padding: 9px 16px;
    margin: 2px 3px;
    border-radius: 8px;
    color: {C.TEXT};
    font-size: {T.BASE}px;
}}
QComboBox QAbstractItemView::item:hover, QDateEdit QAbstractItemView::item:hover {{
    background-color: {C.SURFACE_ALT};
    color: {C.TEXT};
}}
QComboBox QAbstractItemView::item:selected, QDateEdit QAbstractItemView::item:selected {{
    background-color: {C.PRIMARY_SOFT};
    color: {C.PRIMARY_SOFT_TEXT};
    font-weight: 700;
}}

/* ============ Checkable ============ */
QCheckBox, QRadioButton {{
    spacing: 8px;
    color: {C.TEXT};
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {C.BORDER_STRONG};
    background: {C.SURFACE};
}}
QCheckBox::indicator {{
    border-radius: 4px;
}}
QRadioButton::indicator {{
    border-radius: 9px;
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {C.PRIMARY};
    border-color: {C.PRIMARY};
}}
QCheckBox::indicator:checked {{
    {check}
}}

/* ============ Tables ============ */
QTableWidget, QTableView {{
    background-color: {C.SURFACE};
    border: 1px solid {C.BORDER};
    border-radius: {R.MD}px;
    gridline-color: {C.GRIDLINE};
    selection-background-color: {C.PRIMARY_SOFT};
    selection-color: {C.PRIMARY_SOFT_TEXT};
    alternate-background-color: {C.SURFACE_ALT};
}}
QTableView::item {{
    padding: 8px 10px;
}}
/* Header: sunken band, bold dark labels, and a primary accent underline. No
   vertical separators for a cleaner, more modern look. */
QHeaderView {{
    background-color: transparent;
    border: none;
}}
QHeaderView::section {{
    background-color: {C.SURFACE_SUNKEN};
    color: {C.TEXT};
    padding: 12px 14px;
    border: none;
    border-bottom: 2px solid {C.PRIMARY};
    font-weight: 700;
    font-size: {T.SM}px;
}}
QHeaderView::section:hover {{
    background-color: {C.PRIMARY_SOFT};
}}
QTableCornerButton::section {{
    background-color: {C.SURFACE_ALT};
    border: none;
}}

/* ============ Trees / Lists ============ */
QTreeWidget, QTreeView, QListWidget, QListView {{
    background-color: {C.SURFACE};
    border: 1px solid {C.BORDER};
    border-radius: {R.MD}px;
    outline: none;
}}
QTreeView::item, QListView::item {{
    padding: 6px;
}}
QTreeView::item:selected, QListView::item:selected {{
    background: {C.PRIMARY_SOFT};
    color: {C.PRIMARY_SOFT_TEXT};
}}

/* ============ Scrollbars ============ */
QScrollBar:vertical {{
    border: none;
    background: {C.SURFACE_SUNKEN};
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {C.BORDER_STRONG};
    min-height: 24px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C.TEXT_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    border: none;
    background: {C.SURFACE_SUNKEN};
    height: 10px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {C.BORDER_STRONG};
    min-width: 24px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {C.TEXT_MUTED};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ============ Tabs ============ */
/* Modern underline tabs: flat labels with a primary indicator bar under the
   active tab, sitting above a clean card content pane. */
QTabWidget::pane {{
    border: 1px solid {C.BORDER};
    background: {C.SURFACE};
    border-radius: {R.MD}px;
    top: 2px;
}}
QTabBar::tab {{
    background: transparent;
    color: {C.TEXT_SECONDARY};
    border: none;
    border-bottom: 3px solid transparent;
    padding: 11px 24px;
    margin-right: 6px;
    font-weight: 600;
    font-size: {T.BASE}px;
}}
QTabBar::tab:selected {{
    color: {C.PRIMARY};
    border-bottom: 3px solid {C.PRIMARY};
}}
QTabBar::tab:hover:!selected {{
    color: {C.TEXT};
    border-bottom: 3px solid {C.BORDER_STRONG};
}}

/* ============ Group Box ============ */
QGroupBox {{
    background-color: {C.SURFACE};
    border: 1px solid {C.BORDER};
    border-radius: {R.MD}px;
    margin-top: 1.6ex;
    padding-top: 6px;
    font-weight: 600;
    color: {C.PRIMARY};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 8px;
    color: {C.PRIMARY};
}}

/* ============ Progress ============ */
QProgressBar {{
    border: 1px solid {C.BORDER};
    border-radius: {R.SM}px;
    text-align: center;
    color: {C.TEXT};
    background-color: {C.SURFACE_SUNKEN};
    min-height: 10px;
}}
QProgressBar::chunk {{
    background-color: {C.ACCENT};
    border-radius: 5px;
}}

/* ============ Menus ============ */
QMenu {{
    background-color: {C.SURFACE};
    border: 1px solid {C.BORDER};
    border-radius: {R.SM}px;
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {C.PRIMARY_SOFT};
    color: {C.PRIMARY_SOFT_TEXT};
}}

/* ============ Message Box ============ */
QMessageBox {{
    background-color: {C.SURFACE};
}}
QMessageBox QLabel {{
    color: {C.TEXT};
    font-size: {T.BASE}px;
}}
QMessageBox QPushButton {{
    background-color: {C.PRIMARY};
    color: {C.TEXT_ON_PRIMARY};
    border: none;
    border-radius: {R.SM}px;
    padding: 7px 16px;
    min-width: 84px;
}}
QMessageBox QPushButton:hover {{
    background-color: {C.PRIMARY_HOVER};
}}

/* ============ ToolTip ============ */
QToolTip {{
    background-color: {C.TEXT};
    color: {C.SURFACE};
    border: none;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: {T.SM}px;
}}

/* ============ Calendar popup ============ */
QCalendarWidget QWidget {{
    alternate-background-color: {C.SURFACE_ALT};
}}
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {C.PRIMARY};
    border-top-left-radius: {R.SM}px;
    border-top-right-radius: {R.SM}px;
}}
QCalendarWidget QToolButton {{
    color: {C.TEXT_ON_PRIMARY};
    background-color: transparent;
    border: none;
    border-radius: {R.SM}px;
    padding: 4px 10px;
    font-weight: 600;
}}
QCalendarWidget QToolButton:hover {{
    background-color: {C.PRIMARY_HOVER};
}}
QCalendarWidget QMenu {{
    background-color: {C.SURFACE};
    border: 1px solid {C.BORDER};
}}
QCalendarWidget QAbstractItemView {{
    background-color: {C.SURFACE};
    selection-background-color: {C.PRIMARY};
    selection-color: {C.TEXT_ON_PRIMARY};
    outline: none;
    gridline-color: {C.GRIDLINE};
}}
QCalendarWidget QAbstractItemView:enabled {{
    color: {C.TEXT};
}}
QCalendarWidget QAbstractItemView:disabled {{
    color: {C.TEXT_MUTED};
}}

/* ============ Card surface ============ */
QFrame#card {{
    background-color: {C.SURFACE};
    border-radius: {R.LG}px;
}}
"""
