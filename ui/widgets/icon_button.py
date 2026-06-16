from qtpy.QtWidgets import QPushButton
from qtpy.QtCore import Qt, QSize

from ui.themes.colors import Colors
from ui.themes.tokens import Radius
from ui.themes.icons import icon


# Soft tinted fills for icon-only (table row action) buttons: (background, icon).
_ICON_ONLY_FILL = {
    "primary": (Colors.PRIMARY_SOFT, Colors.PRIMARY),
    "danger": (Colors.DANGER_BG, Colors.DANGER),
    "secondary": (Colors.SURFACE, Colors.PRIMARY),
}


def _icon_only_css(variant: str) -> str:
    """A soft, rounded, tinted square button for table row actions (cleaner than
    a heavy solid fill; the icon keeps its accent colour, hover shows a ring)."""
    bg, _fg = _ICON_ONLY_FILL.get(variant, _ICON_ONLY_FILL["secondary"])
    ring = Colors.DANGER if variant == "danger" else Colors.PRIMARY
    border = Colors.BORDER_STRONG if variant == "secondary" else "transparent"
    return (
        f"QPushButton {{ background-color: {bg}; border: 1px solid {border}; "
        f"border-radius: {Radius.SM}px; padding: 6px; }}"
        f"QPushButton:hover {{ border: 1px solid {ring}; }}"
    )


def _variant_css(variant: str, compact: bool, icon_only: bool = False) -> str:
    if icon_only:
        return _icon_only_css(variant)
    if compact:
        pad = "6px 14px"
    else:
        pad = "9px 18px"
    fs = 13 if compact else 14
    base = (
        f"border-radius: {Radius.SM}px; padding: {pad}; "
        f"font-weight: 600; font-size: {fs}px;"
    )
    if variant == "primary":
        return (
            f"QPushButton {{ background-color: {Colors.PRIMARY}; "
            f"color: {Colors.TEXT_ON_PRIMARY}; border: none; {base} }}"
            f"QPushButton:hover {{ background-color: {Colors.PRIMARY_HOVER}; }}"
            f"QPushButton:pressed {{ background-color: {Colors.PRIMARY_PRESSED}; }}"
            f"QPushButton:disabled {{ background-color: {Colors.PRIMARY_DISABLED}; }}"
        )
    if variant == "danger":
        return (
            f"QPushButton {{ background-color: {Colors.DANGER}; "
            f"color: {Colors.TEXT_ON_PRIMARY}; border: none; {base} }}"
            f"QPushButton:hover {{ background-color: {Colors.DANGER_TEXT}; }}"
        )
    # secondary (default)
    return (
        f"QPushButton {{ background-color: {Colors.SURFACE}; color: {Colors.PRIMARY}; "
        f"border: 1px solid {Colors.BORDER_STRONG}; {base} }}"
        f"QPushButton:hover {{ background-color: {Colors.PRIMARY_SOFT}; "
        f"border-color: {Colors.PRIMARY}; }}"
    )


class IconButton(QPushButton):
    """A QPushButton with a leading qtawesome icon and a self-contained variant
    style. The style is applied as an instance stylesheet (not via a global
    `class` selector) so the button always renders correctly regardless of
    parent graphics effects or font/metrics quirks.

    variant: "primary" | "secondary" | "danger". compact: smaller padding.
    """

    def __init__(self, text="", icon_name=None, variant="secondary",
                 compact=False, parent=None, tooltip=None, icon_only=False):
        # icon_only buttons show just the glyph (square), with the label as tooltip.
        label = "" if icon_only else text
        super().__init__(label, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(_variant_css(variant, compact, icon_only))
        if tooltip or (icon_only and text):
            self.setToolTip(tooltip or text)
        if icon_name:
            if icon_only:
                color = _ICON_ONLY_FILL.get(variant, _ICON_ONLY_FILL["secondary"])[1]
            elif variant in ("primary", "danger"):
                color = Colors.TEXT_ON_PRIMARY
            else:
                color = Colors.PRIMARY
            self.setIcon(icon(icon_name, color=color))
            self.setIconSize(QSize(16, 16))
        if icon_only:
            self.setFixedSize(QSize(34, 32))
