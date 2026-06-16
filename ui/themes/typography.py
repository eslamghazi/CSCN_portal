"""Typography tokens. Single source of truth for font families and sizes.

FAMILY_STACK is used by the generated QSS global rule; the size scale is used by
components and the stylesheet builder. Legacy size names (H1_SIZE..SMALL_SIZE)
are kept as aliases.
"""


class Typography:
    # Font families (in preference order). Cairo/Tajawal activate automatically
    # if their .ttf files are dropped into ui/resources/fonts (see app._load_fonts).
    PRIMARY_FONT = "Cairo"
    SECONDARY_FONT = "Tajawal"
    SYSTEM_FALLBACK = "Segoe UI"
    LAST_RESORT = "Arial"

    # QSS font-family stack string.
    FAMILY_STACK = '"Cairo", "Tajawal", "Segoe UI", "Arial", sans-serif'

    # Size scale (px)
    XS = 11
    SM = 12
    BASE = 14
    MD = 16
    LG = 18
    XL = 20
    XXL = 24
    DISPLAY = 28

    # Weights
    REGULAR = 400
    MEDIUM = 600
    BOLD = 700

    # --- Legacy aliases ---
    H1_SIZE = XXL
    H2_SIZE = XL
    H3_SIZE = LG
    BODY_SIZE = BASE
    SMALL_SIZE = SM
