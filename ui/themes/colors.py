"""Central color tokens for the CSCN_portal modern light theme.

This is the single source of truth for color. The QSS is generated from these
values (see ui/themes/stylesheet.py) and components read them directly. Legacy
attribute names (PRIMARY, SUCCESS, WARNING, DANGER, INFO, BORDER, TEXT,
TEXT_MUTED, BACKGROUND, SECONDARY) are kept as aliases so existing imports keep
working with the refreshed palette.

Palette: a cohesive teal / emerald scheme — calm and fitting for a healthcare /
nursing center, with a single hue family for primary + accent (so focus rings
and buttons agree instead of clashing).
"""


class Colors:
    # --- Brand / primary (teal) ---
    PRIMARY = "#0F766E"
    PRIMARY_HOVER = "#0D9488"
    PRIMARY_PRESSED = "#115E59"
    PRIMARY_DISABLED = "#9DC4C0"
    PRIMARY_SOFT = "#E6F3F1"
    PRIMARY_SOFT_TEXT = "#115E59"

    # --- Accent (bright teal): links, focus, progress ---
    ACCENT = "#0D9488"
    ACCENT_HOVER = "#0F766E"
    ACCENT_SOFT = "#D9F2EF"

    # --- Surfaces / backgrounds ---
    BG = "#F6F8F8"
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#F1F6F5"
    SURFACE_SUNKEN = "#E9F0EF"

    # --- Borders / dividers ---
    BORDER = "#E3E8E8"
    BORDER_STRONG = "#C7D2D0"
    GRIDLINE = "#EDF2F1"

    # --- Text ---
    TEXT = "#14201E"
    TEXT_SECONDARY = "#4F5E5B"
    TEXT_MUTED = "#84938F"
    TEXT_ON_PRIMARY = "#FFFFFF"

    # --- Semantic: base / soft background / text-on-soft ---
    SUCCESS = "#16A34A"
    SUCCESS_BG = "#E4F6EA"
    SUCCESS_TEXT = "#166534"

    WARNING = "#D97706"
    WARNING_BG = "#FCEFD9"
    WARNING_TEXT = "#92580B"

    DANGER = "#DC2626"
    DANGER_BG = "#FBE3E3"
    DANGER_TEXT = "#991B1B"

    INFO = "#0E7490"
    INFO_BG = "#DEF1F5"
    INFO_TEXT = "#0B5566"

    # --- KPI accents (decorative) ---
    KPI_BLUE = "#0E7490"
    KPI_GREEN = "#16A34A"
    KPI_AMBER = "#D97706"
    KPI_PURPLE = "#6D5BD0"

    # --- Sidebar ---
    SIDEBAR_BG_TOP = "#134E4A"
    SIDEBAR_BG_BOTTOM = "#0F766E"
    SIDEBAR_TEXT = "#FFFFFF"
    SIDEBAR_TEXT_MUTED = "rgba(255, 255, 255, 0.58)"
    SIDEBAR_ACTIVE_BG = "rgba(255, 255, 255, 0.16)"
    SIDEBAR_ACTIVE_BAR = "#2DD4BF"
    SIDEBAR_HOVER_BG = "rgba(255, 255, 255, 0.10)"
    SIDEBAR_LOGOUT = "#FCA5A5"

    # --- Legacy aliases (kept so old imports don't break) ---
    SECONDARY = SURFACE_ALT
    BACKGROUND = SURFACE
