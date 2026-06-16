"""Generate the application icon (ui/resources/icons/app.ico) from qtawesome.

Run once (or whenever the brand changes):  python tools/make_app_icon.py
Produces a brand-colored rounded tile with a white nurse glyph, saved as a
multi-size .ico used by PyInstaller (--icon) for the exe/taskbar.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QPixmap, QPainter, QColor
from qtpy.QtCore import Qt, QRectF
import qtawesome as qta
from PIL import Image

PRIMARY = "#2B4C7E"
OUT_DIR = Path(__file__).resolve().parent.parent / "ui" / "resources" / "icons"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PNG_PATH = OUT_DIR / "app.png"
ICO_PATH = OUT_DIR / "app.ico"


def main():
    app = QApplication(sys.argv)  # noqa: F841 - needed for qtawesome rendering
    size = 256
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(PRIMARY))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(QRectF(8, 8, size - 16, size - 16), 48, 48)
    glyph = qta.icon("fa5s.user-nurse", color="#FFFFFF").pixmap(150, 150)
    painter.drawPixmap((size - 150) // 2, (size - 150) // 2, glyph)
    painter.end()
    pm.save(str(PNG_PATH), "PNG")

    Image.open(PNG_PATH).save(
        ICO_PATH,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Wrote {ICO_PATH}")


if __name__ == "__main__":
    main()
