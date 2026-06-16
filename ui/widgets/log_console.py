"""A read-only, terminal-styled log viewer with per-level syntax colouring.

The application log lines follow loguru's file format:

    2026-06-15 10:21:37 | INFO     | module.path:function:line - message

`LogHighlighter` parses that structure and colours each field; lines that do
not match (wrapped output, tracebacks) are shown in the default console colour.
The dark palette is intentionally self-contained — a deliberate "console" accent
that does not depend on the app's light theme tokens."""
import re

from qtpy.QtCore import Qt
from qtpy.QtGui import (
    QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextCursor,
)
from qtpy.QtWidgets import QPlainTextEdit


# Dark "terminal" palette for the console.
class _C:
    BG = "#0F172A"          # slate-900 background
    BORDER = "#1E293B"
    TEXT = "#E2E8F0"        # default message text
    MUTED = "#64748B"       # separators / punctuation
    TIME = "#7C93B0"        # timestamp
    LOCATION = "#5EEAD4"    # logger name:function:line (teal)
    SELECTION = "#1D4ED8"
    SCROLL = "#334155"
    SCROLL_HOVER = "#475569"


# Per-level accent colours (loguru levels).
LEVEL_COLORS = {
    "TRACE": "#7C93B0",
    "DEBUG": "#94A3B8",
    "INFO": "#38BDF8",
    "SUCCESS": "#4ADE80",
    "WARNING": "#FBBF24",
    "ERROR": "#F87171",
    "CRITICAL": "#FB7185",
}

# Levels whose message text is tinted so they stand out at a glance.
_LOUD_LEVELS = {"WARNING", "ERROR", "CRITICAL"}


def _fmt(color: str, bold: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Bold)
    return f


class LogHighlighter(QSyntaxHighlighter):
    """Colours a loguru-formatted log document field by field."""

    _LINE = re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
        r"(?P<s1>\s*\|\s*)"
        r"(?P<level>[A-Z]+)\s*"
        r"(?P<s2>\|\s*)"
        r"(?P<loc>\S+)"
        r"(?P<dash>\s-\s)"
        r"(?P<msg>.*)$"
    )

    def __init__(self, document):
        super().__init__(document)
        self._time = _fmt(_C.TIME)
        self._sep = _fmt(_C.MUTED)
        self._loc = _fmt(_C.LOCATION)
        self._msg = _fmt(_C.TEXT)
        self._level_fmt = {lvl: _fmt(c, bold=True) for lvl, c in LEVEL_COLORS.items()}
        self._msg_fmt = {lvl: _fmt(c) for lvl, c in LEVEL_COLORS.items()}

    def highlightBlock(self, text: str):
        m = self._LINE.match(text)
        if not m:
            # Continuation lines (tracebacks, wrapped output): plain console text.
            self.setFormat(0, len(text), self._msg)
            return
        level = m.group("level")
        self._apply(m, "ts", self._time)
        self._apply(m, "s1", self._sep)
        self._apply(m, "level", self._level_fmt.get(level, _fmt(_C.TEXT, bold=True)))
        self._apply(m, "s2", self._sep)
        self._apply(m, "loc", self._loc)
        self._apply(m, "dash", self._sep)
        msg_fmt = self._msg_fmt[level] if level in _LOUD_LEVELS else self._msg
        self._apply(m, "msg", msg_fmt)

    def _apply(self, m, group: str, fmt: QTextCharFormat):
        start = m.start(group)
        self.setFormat(start, m.end(group) - start, fmt)


class LogConsole(QPlainTextEdit):
    """Read-only, monospaced, dark log console with level-based colouring."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        # Logs read left-to-right; force LTR so timestamps/levels align even in
        # the app's RTL layout.
        self.setLayoutDirection(Qt.LeftToRight)

        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {_C.BG};
                color: {_C.TEXT};
                border: 1px solid {_C.BORDER};
                border-radius: 10px;
                padding: 10px 12px;
                selection-background-color: {_C.SELECTION};
                selection-color: #FFFFFF;
            }}
            QScrollBar:vertical {{
                background: transparent; width: 10px; margin: 4px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {_C.SCROLL}; border-radius: 5px; min-height: 32px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {_C.SCROLL_HOVER}; }}
            QScrollBar:horizontal {{
                background: transparent; height: 10px; margin: 2px 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {_C.SCROLL}; border-radius: 5px; min-width: 32px;
            }}
            QScrollBar::handle:horizontal:hover {{ background: {_C.SCROLL_HOVER}; }}
            QScrollBar::add-line, QScrollBar::sub-line {{
                height: 0; width: 0; background: none; border: none;
            }}
            QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
        """)

        self._highlighter = LogHighlighter(self.document())

    def set_log_text(self, text: str):
        """Replace the content and scroll to the newest (bottom) entries."""
        self.setPlainText(text)
        self.moveCursor(QTextCursor.End)
