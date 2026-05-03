from __future__ import annotations

from dataclasses import dataclass


LEGACY_DESKNOTE_BORDER_LEFT = 12
LEGACY_DESKNOTE_BORDER_TOP = 32
LEGACY_DESKNOTE_BORDER_WIDTH_PAD = 26
LEGACY_DESKNOTE_BORDER_HEIGHT_PAD = 48
LEGACY_DESKNOTE_HEADER_HEIGHT = 40
LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH = 36
LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT = 111


@dataclass(frozen=True, slots=True)
class LegacyDeskNoteRect:
    """Small geometry record for the old frameless ``desknote.vb`` behavior."""

    x: int
    y: int
    width: int
    height: int


def legacy_opacity_percent_for_transparency_percent(transparency_percent: int | str | None) -> int:
    """Convert the old transparency menu value to a Qt opacity percentage.

    ``desknote_kontext_opacy.vb`` labels the entries as transparency values:
    ``90 %`` means very transparent and maps to window opacity ``0.1``;
    ``0 %`` means fully opaque and maps to opacity ``1.0``.
    """

    try:
        transparency = int(transparency_percent) if transparency_percent is not None else 0
    except (TypeError, ValueError):
        transparency = 0
    transparency = max(0, min(90, transparency))
    return max(10, min(100, 100 - transparency))


def legacy_transparency_menu_options() -> tuple[tuple[str, int], ...]:
    """Return ``(label, opacity_percent)`` pairs from the WinForms desk note menu."""

    return tuple(
        (f"{transparency} %", legacy_opacity_percent_for_transparency_percent(transparency))
        for transparency in range(90, -1, -10)
    )


def legacy_desknote_hover_geometry(rect: LegacyDeskNoteRect) -> LegacyDeskNoteRect:
    """Return the expanded border geometry used while a desk note is active.

    The old borderless form shrank itself when idle and expanded around the text
    editor on hover/focus by subtracting 12/32 pixels from x/y and adding 26/48
    pixels to width/height.  The Qt port does not blindly resize user windows on
    hover, but exposing the exact math keeps this old behavior documented and
    testable.
    """

    return LegacyDeskNoteRect(
        rect.x - LEGACY_DESKNOTE_BORDER_LEFT,
        rect.y - LEGACY_DESKNOTE_BORDER_TOP,
        rect.width + LEGACY_DESKNOTE_BORDER_WIDTH_PAD,
        rect.height + LEGACY_DESKNOTE_BORDER_HEIGHT_PAD,
    )


def legacy_desknote_hidden_border_geometry(rect: LegacyDeskNoteRect) -> LegacyDeskNoteRect:
    """Return the contracted geometry from the old idle/hidden-border state."""

    return LegacyDeskNoteRect(
        rect.x + LEGACY_DESKNOTE_BORDER_LEFT,
        rect.y + LEGACY_DESKNOTE_BORDER_TOP,
        max(1, rect.width - LEGACY_DESKNOTE_BORDER_WIDTH_PAD),
        max(1, rect.height - LEGACY_DESKNOTE_BORDER_HEIGHT_PAD),
    )


def _clamp_opacity(value: float | int | str | None) -> float:
    try:
        opacity = float(value) if value is not None else 0.85
    except (TypeError, ValueError):
        opacity = 0.85
    return max(0.1, min(1.0, opacity))


def legacy_desknote_opacity_for_active(stored_opacity: float | int | str | None) -> float:
    """Return the old active/focused opacity.

    ``desknote.vb`` made the note fully visible while it was being used.  The
    stored menu opacity is restored again on focus/hover loss.
    """

    _clamp_opacity(stored_opacity)
    return 1.0


def legacy_desknote_opacity_for_inactive(stored_opacity: float | int | str | None) -> float:
    """Return the old inactive opacity from the transparency menu setting."""

    return _clamp_opacity(stored_opacity)


def legacy_desknote_title_hit_action(local_x: int, local_y: int, width: int) -> str:
    """Classify old title-strip clicks from ``desknote.vb``.

    Left title button hides the note, right title button closes/removes it and
    the remaining title region starts a move.  Outside the title strip the old
    form still prepared move state, so ``move`` is the safe default.
    """

    if local_y < LEGACY_DESKNOTE_HEADER_HEIGHT:
        if local_x < LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH:
            return "hide"
        if local_x > max(0, width - LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH):
            return "close"
    return "move"
