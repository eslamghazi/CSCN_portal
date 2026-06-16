"""Shared visual effects. apply_shadow() replaces the QGraphicsDropShadowEffect
blocks that were copy-pasted across many pages."""
from qtpy.QtWidgets import QGraphicsDropShadowEffect, QWidget
from qtpy.QtGui import QColor

from ui.themes.tokens import Elevation


def apply_shadow(widget: QWidget, preset=Elevation.CARD) -> QGraphicsDropShadowEffect:
    """Apply a soft drop shadow to a widget from an (blur, y_offset, alpha) preset."""
    blur, dy, alpha = preset
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setColor(QColor(15, 23, 42, alpha))  # slate-900 tint
    effect.setOffset(0, dy)
    widget.setGraphicsEffect(effect)
    return effect
