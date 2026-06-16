"""Non-color design tokens: spacing, radii, and elevation (shadow) presets."""


class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


class Radius:
    SM = 6
    MD = 10
    LG = 14
    PILL = 999


class Elevation:
    """Drop-shadow presets as (blur_radius, y_offset, alpha) consumed by
    ui.themes.effects.apply_shadow."""
    CARD = (24, 6, 22)
    CARD_LOW = (14, 2, 16)
    DIALOG = (32, 10, 40)
    TOPBAR = (15, 2, 15)
