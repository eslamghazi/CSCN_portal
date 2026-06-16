import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont, QFontDatabase

from ui.themes.stylesheet import build_stylesheet
from ui.themes.typography import Typography
from ui.themes.colors import Colors
from ui.themes.icons import icon


class CSCN_portalApp(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)

        # Setup High DPI scaling
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            self.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            self.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # Set RTL layout for Arabic
        self.setLayoutDirection(Qt.RightToLeft)

        self.setApplicationName("CSCN Portal")
        self.setApplicationVersion("1.1.0")
        self.setOrganizationName("Faculty of Nursing - Kafrelsheikh University")

        self._load_fonts()
        self._load_theme()

        # Application/taskbar icon (generated from qtawesome, no asset file needed).
        app_icon = icon("app", color=Colors.PRIMARY)
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

    @staticmethod
    def _resource_base() -> Path:
        """Project root in dev, or the PyInstaller bundle dir when frozen."""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(__file__).resolve().parent.parent

    def _load_fonts(self):
        """Load any bundled Arabic fonts from ui/resources/fonts, then choose a
        font family that is actually installed. Crucially, we never force a
        family that isn't available — a substituted family can report broken
        (zero-width) metrics for Arabic text, which collapses button sizes. If
        no preferred family is present we keep the platform default family
        (which shapes Arabic correctly) and only set the size."""
        fonts_dir = self._resource_base() / "ui" / "resources" / "fonts"
        if fonts_dir.exists():
            for font_file in fonts_dir.iterdir():
                if font_file.suffix.lower() in (".ttf", ".otf"):
                    QFontDatabase.addApplicationFont(str(font_file))

        # QFontDatabase.families() is a static method on Qt6/PySide6 but an
        # instance method on Qt5/PySide2 (whose QFontDatabase can't be the Qt6
        # static one). Support both bindings.
        try:
            available = set(QFontDatabase.families())
        except TypeError:
            available = set(QFontDatabase().families())
        chosen = next(
            (f for f in (Typography.PRIMARY_FONT, Typography.SECONDARY_FONT,
                         Typography.SYSTEM_FALLBACK) if f in available),
            None,
        )
        font = QFont(chosen) if chosen else QFont()  # keep default family if none
        font.setPointSize(10)
        self.setFont(font)

    def _load_theme(self):
        """Apply the token-generated global stylesheet."""
        self.setStyleSheet(build_stylesheet())
