from qtpy.QtWidgets import QFrame, QVBoxLayout

from ui.themes.effects import apply_shadow
from ui.themes.tokens import Elevation, Spacing


class Card(QFrame):
    """A white rounded surface with a soft shadow. Replaces the copy-pasted
    QFrame + QGraphicsDropShadowEffect blocks across pages. Styled via the
    `QFrame#card` rule in the generated stylesheet."""

    def __init__(self, padding: int = Spacing.XL, elevation=Elevation.CARD, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        apply_shadow(self, elevation)
        self._body = QVBoxLayout(self)
        self._body.setContentsMargins(padding, padding, padding, padding)
        self._body.setSpacing(Spacing.LG)

    @property
    def body(self) -> QVBoxLayout:
        return self._body

    def add(self, widget):
        self._body.addWidget(widget)
        return widget

    def add_layout(self, layout):
        self._body.addLayout(layout)
        return layout
