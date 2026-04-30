from __future__ import annotations

import random

# System.Drawing.KnownColor values used by Notizen.NET get_lightcolor().
# Stored as signed ARGB integers because ALX serializes Color.ToArgb().
LIGHT_COLOR_RGB: tuple[str, ...] = (
    "#f08080",  # LightCoral
    "#e0ffff",  # LightCyan
    "#90ee90",  # LightGreen
    "#87cefa",  # LightSkyBlue
    "#ffffe0",  # LightYellow
    "#b0c4de",  # LightSteelBlue
    "#ffa07a",  # LightSalmon
    "#fafad2",  # LightGoldenrodYellow
    "#add8e6",  # LightBlue
    "#87ceeb",  # SkyBlue
    "#ffff00",  # Yellow
    "#ffffff",  # White
    "#adff2f",  # GreenYellow
    "#00ffff",  # Cyan
    "#ff00ff",  # Magenta
    "#d3d3d3",  # LightGray fallback from the old Select Case Else branch
)


def rgb_to_signed_argb(rgb: str, alpha: int = 255) -> int:
    text = rgb.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError(f"Expected #RRGGBB color, got {rgb!r}")
    value = ((alpha & 0xFF) << 24) | int(text, 16)
    if value >= 2**31:
        value -= 2**32
    return value


LIGHT_COLOR_ARGB: tuple[int, ...] = tuple(rgb_to_signed_argb(color) for color in LIGHT_COLOR_RGB)


def legacy_light_color_argb(rng: random.Random | None = None) -> int:
    """Return a light Notizen.NET desktop-note background color."""
    chooser = rng.choice if rng is not None else random.choice
    return int(chooser(LIGHT_COLOR_ARGB))
