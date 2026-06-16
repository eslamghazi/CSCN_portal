from qtpy.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel
from qtpy.QtCore import Qt, QSize

from ui.themes.colors import Colors
from ui.themes.icons import icon
from ui.widgets.icon_button import IconButton


def confirm(parent, message: str, title: str = "تأكيد",
            yes_text: str = "نعم", danger: bool = None) -> bool:
    """Show a styled Yes/Cancel confirmation dialog (Arabic). Returns True if
    confirmed. Used before destructive/important actions (delete, logout, ...).

    `danger` switches to the red/warning style; when left as None it is inferred
    from the message (delete actions render in red automatically)."""
    if danger is None:
        danger = "حذف" in message
    dialog = _ConfirmDialog(parent, message, title, yes_text, danger)
    return dialog.exec() == QDialog.Accepted


class _ConfirmDialog(QDialog):
    def __init__(self, parent, message, title, yes_text, danger):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(430)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.SURFACE}; }}")

        accent = Colors.DANGER if danger else Colors.PRIMARY
        accent_bg = Colors.DANGER_BG if danger else Colors.INFO_BG
        icon_name = "warning" if danger else "info"

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 20)
        root.setSpacing(16)

        # Header: a soft colored icon badge + the title.
        head = QHBoxLayout()
        head.setSpacing(14)
        badge = QLabel()
        badge.setFixedSize(46, 46)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"background-color: {accent_bg}; border-radius: 23px;")
        glyph = icon(icon_name, color=accent)
        if not glyph.isNull():
            badge.setPixmap(glyph.pixmap(QSize(24, 24)))
        head.addWidget(badge)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"font-size: 17px; font-weight: bold; color: {Colors.TEXT};"
            f" background: transparent;")
        head.addWidget(title_lbl)
        head.addStretch()
        root.addLayout(head)

        # Message.
        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet(
            f"font-size: 14px; color: {Colors.TEXT_SECONDARY}; background: transparent;")
        root.addWidget(msg)

        # Buttons.
        root.addSpacing(4)
        btns = QHBoxLayout()
        btns.addStretch()
        cancel = IconButton("إلغاء", "cancel", variant="secondary")
        cancel.clicked.connect(self.reject)
        ok = IconButton(yes_text, "delete" if danger else "save",
                        variant="danger" if danger else "primary")
        ok.clicked.connect(self.accept)
        ok.setDefault(True)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        root.addLayout(btns)

        ok.setFocus()
