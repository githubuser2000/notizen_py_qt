from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Iterable


@dataclass(frozen=True, slots=True)
class LegacyColor:
    """A color from Notizen.NET's old WinForms helper palette.

    WinForms wrote ``Color.ToArgb()`` as a signed 32-bit integer.  The Python
    model accepts both signed integers and common hex notation, but this module
    keeps a named palette so CLI/UI operations can reproduce the old random
    light desktop-note colors instead of inventing new ones.
    """

    name: str
    argb: int

    @property
    def signed_argb(self) -> int:
        return argb_to_signed(self.argb)

    @property
    def hex(self) -> str:
        return f"#{self.argb & 0xFFFFFFFF:08X}"


# Same order as the old get_lightcolor() Select Case in Notizen.vb.
LEGACY_LIGHT_COLORS: tuple[LegacyColor, ...] = (
    LegacyColor("LightCoral", 0xFFF08080),
    LegacyColor("LightCyan", 0xFFE0FFFF),
    LegacyColor("LightGreen", 0xFF90EE90),
    LegacyColor("LightSkyBlue", 0xFF87CEFA),
    LegacyColor("LightYellow", 0xFFFFFFE0),
    LegacyColor("LightSteelBlue", 0xFFB0C4DE),
    LegacyColor("LightSalmon", 0xFFFFA07A),
    LegacyColor("LightGoldenrodYellow", 0xFFFAFAD2),
    LegacyColor("LightBlue", 0xFFADD8E6),
    LegacyColor("SkyBlue", 0xFF87CEEB),
    LegacyColor("Yellow", 0xFFFFFF00),
    LegacyColor("White", 0xFFFFFFFF),
    LegacyColor("GreenYellow", 0xFFADFF2F),
    LegacyColor("Cyan", 0xFF00FFFF),
    LegacyColor("Magenta", 0xFFFF00FF),
)
_FALLBACK_LIGHT_GRAY = LegacyColor("LightGray", 0xFFD3D3D3)


def argb_to_signed(value: int | None) -> int | None:
    """Return the WinForms/Int32 representation for an ARGB value."""

    if value is None:
        return None
    unsigned = int(value) & 0xFFFFFFFF
    return unsigned - 0x100000000 if unsigned >= 0x80000000 else unsigned


def argb_to_unsigned(value: int | None) -> int | None:
    if value is None:
        return None
    return int(value) & 0xFFFFFFFF


def legacy_light_color(index: int | None = None) -> LegacyColor:
    """Return a light color from the original palette.

    ``index`` is accepted for deterministic tests/CLI runs.  Values outside the
    original ``0..14`` range return LightGray, matching the old ``Case Else``.
    """

    if index is None:
        return random.choice(LEGACY_LIGHT_COLORS)
    if 0 <= index < len(LEGACY_LIGHT_COLORS):
        return LEGACY_LIGHT_COLORS[index]
    return _FALLBACK_LIGHT_GRAY


def legacy_color_by_name(name: str) -> LegacyColor:
    key = (name or "").strip().replace(" ", "").replace("-", "").casefold()
    for color in (*LEGACY_LIGHT_COLORS, _FALLBACK_LIGHT_GRAY):
        if color.name.casefold() == key:
            return color
    raise ValueError(f"Unbekannte alte Notizen.NET-Farbe: {name}")


def legacy_palette_table() -> list[dict[str, object]]:
    return [
        {"index": index, "name": color.name, "argb": color.signed_argb, "hex": color.hex}
        for index, color in enumerate(LEGACY_LIGHT_COLORS)
    ]


def css_color(value: int | None, fallback: str = "transparent") -> str:
    if value is None:
        return fallback
    unsigned = int(value) & 0xFFFFFFFF
    # CSS ignores alpha in #RRGGBB.  Sticky opacity is represented separately.
    return f"#{unsigned & 0xFFFFFF:06X}"


def readable_color_lines(colors: Iterable[LegacyColor] = LEGACY_LIGHT_COLORS) -> str:
    return "\n".join(f"{i:02d} {color.name:24s} {color.hex} {color.signed_argb}" for i, color in enumerate(colors))
