"""Central color tokens for the CSCN_portal modern light theme.

This is the single source of truth for color. The QSS is generated from these
values (see ui/themes/stylesheet.py) and components read them directly. Legacy
attribute names (PRIMARY, SUCCESS, WARNING, DANGER, INFO, BORDER, TEXT,
TEXT_MUTED, BACKGROUND, SECONDARY) are kept as aliases so existing imports keep
working with the refreshed palette.
"""


class Colors:
    # --- Brand / primary (indigo) ---
    PRIMARY = "#2B4C7E"
    PRIMARY_HOVER = "#34598F"
    PRIMARY_PRESSED = "#22406B"
    PRIMARY_DISABLED = "#A9B8CE"
    PRIMARY_SOFT = "#EAF0F8"
    PRIMARY_SOFT_TEXT = "#22406B"

    # --- Accent (teal): links, focus, progress ---
    ACCENT = "#0E7C86"
    ACCENT_HOVER = "#0B6A72"
    ACCENT_SOFT = "#E0F2F3"

    # --- Surfaces / backgrounds ---
    BG = "#F4F6FA"
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#F8FAFC"
    SURFACE_SUNKEN = "#EEF2F7"

    # --- Borders / dividers ---
    BORDER = "#E2E8F0"
    BORDER_STRONG = "#CBD5E1"
    GRIDLINE = "#EDF1F6"

    # --- Text ---
    TEXT = "#1F2A37"
    TEXT_SECONDARY = "#566375"
    TEXT_MUTED = "#8A97A8"
    TEXT_ON_PRIMARY = "#FFFFFF"

    # --- Semantic: base / soft background / text-on-soft ---
    SUCCESS = "#1E8E5A"
    SUCCESS_BG = "#E3F4EC"
    SUCCESS_TEXT = "#136B43"

    WARNING = "#B7791F"
    WARNING_BG = "#FBF1DC"
    WARNING_TEXT = "#8A5B0E"

    DANGER = "#C53D3D"
    DANGER_BG = "#FBE6E6"
    DANGER_TEXT = "#9B2C2C"

    INFO = "#2B6CB0"
    INFO_BG = "#E4EFFA"
    INFO_TEXT = "#1F4F84"

    # --- KPI accents (decorative) ---
    KPI_BLUE = "#2B6CB0"
    KPI_GREEN = "#1E8E5A"
    KPI_AMBER = "#B7791F"
    KPI_PURPLE = "#6D5BD0"

    # --- Sidebar ---
    SIDEBAR_BG_TOP = "#22406B"
    SIDEBAR_BG_BOTTOM = "#2B4C7E"
    SIDEBAR_TEXT = "#FFFFFF"
    SIDEBAR_TEXT_MUTED = "rgba(255, 255, 255, 0.55)"
    SIDEBAR_ACTIVE_BG = "rgba(255, 255, 255, 0.16)"
    SIDEBAR_ACTIVE_BAR = "#37C5C9"
    SIDEBAR_HOVER_BG = "rgba(255, 255, 255, 0.09)"
    SIDEBAR_LOGOUT = "#FCA5A5"

    # --- Legacy aliases (kept so old imports don't break) ---
    SECONDARY = SURFACE_ALT
    BACKGROUND = SURFACE
