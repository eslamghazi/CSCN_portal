from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from qtpy.QtCore import Qt

from ui.themes.colors import Colors


class LoadingOverlay(QWidget):
    """A semi-transparent overlay with an indeterminate progress bar, sized to
    its parent. Usage (synchronous MVP):
        overlay.start(); QApplication.processEvents(); load(); overlay.stop()
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(244, 246, 250, 0.72);")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        self.label = QLabel("جاري التحميل...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 14px; font-weight: 600; "
            f"background: transparent;"
        )
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)  # indeterminate
        self.bar.setFixedWidth(180)
        self.bar.setTextVisible(False)

        layout.addWidget(self.label)
        layout.addWidget(self.bar, alignment=Qt.AlignCenter)
        self.hide()

    def start(self, text: str = "جاري التحميل..."):
        self.label.setText(text)
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()

    def stop(self):
        self.hide()
