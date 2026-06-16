"""Reusable busy/loading helper. Usage:

    from ui.widgets.busy import busy
    with busy(self, "جاري التحميل..."):
        ... slow work ...

Shows a LoadingOverlay over `widget` (reusing one per widget) and processes
events so it actually paints during synchronous work.
"""
from contextlib import contextmanager

from qtpy.QtWidgets import QApplication

from ui.widgets.loading_overlay import LoadingOverlay


@contextmanager
def busy(widget, message: str = "جاري التحميل..."):
    overlay = getattr(widget, "_busy_overlay", None)
    if overlay is None:
        overlay = LoadingOverlay(widget)
        widget._busy_overlay = overlay
    overlay.start(message)
    QApplication.processEvents()
    try:
        yield
    finally:
        overlay.stop()
