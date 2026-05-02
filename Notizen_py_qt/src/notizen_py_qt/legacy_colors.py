from __future__ import annotations

import random

# System.Drawing.KnownColor values used by Notizen.NET get_lightcolor().
# Stored as signed ARGB integers because ALX serializes Color.ToArgb().
#
# VB.NET detail: Random.Next(0, 14) returns values 0..13.  Case 14
# (Magenta) and the Else branch (LightGray) were present in the source but are
# unreachable for automatically chosen desktop-note colors.  They remain listed
# for source documentation, while legacy_light_color_argb() chooses only the
# reachable 0..13 range.
LIGHT_COLOR_RGB: tuple[str, ...] = (
    "#f08080",  # 0 LightCoral
    "#e0ffff",  # 1 LightCyan
    "#90ee90",  # 2 LightGreen
    "#87cefa",  # 3 LightSkyBlue
    "#ffffe0",  # 4 LightYellow
    "#b0c4de",  # 5 LightSteelBlue
    "#ffa07a",  # 6 LightSalmon
    "#fafad2",  # 7 LightGoldenrodYellow
    "#add8e6",  # 8 LightBlue
    "#87ceeb",  # 9 SkyBlue
    "#ffff00",  # 10 Yellow
    "#ffffff",  # 11 White
    "#adff2f",  # 12 GreenYellow
    "#00ffff",  # 13 Cyan
    "#ff00ff",  # 14 Magenta, unreachable in the old Random.Next(0, 14) call
    "#d3d3d3",  # Else LightGray, unreachable in the old Random.Next(0, 14) call
)
LEGACY_RANDOM_LIGHT_COLOR_COUNT = 14


def rgb_to_signed_argb(rgb: str, alpha: int = 255) -> int:
    text = rgb.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError(f"Expected #RRGGBB color, got {rgb!r}")
    value = ((alpha & 0xFF) << 24) | int(text, 16)
    if value >= 2**31:
        value -= 2**32
    return value


LIGHT_COLOR_ARGB: tuple[int, ...] = tuple(rgb_to_signed_argb(color) for color in LIGHT_COLOR_RGB)
LEGACY_RANDOM_LIGHT_COLOR_ARGB: tuple[int, ...] = LIGHT_COLOR_ARGB[:LEGACY_RANDOM_LIGHT_COLOR_COUNT]


def legacy_light_color_argb(rng: random.Random | None = None) -> int:
    """Return a reachable light Notizen.NET desktop-note background color."""
    chooser = rng.choice if rng is not None else random.choice
    return int(chooser(LEGACY_RANDOM_LIGHT_COLOR_ARGB))
