from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


LEGACY_DESKNOTE_BORDER_LEFT = 12
LEGACY_DESKNOTE_BORDER_TOP = 32
LEGACY_DESKNOTE_BORDER_WIDTH_PAD = 26
LEGACY_DESKNOTE_BORDER_HEIGHT_PAD = 48
LEGACY_DESKNOTE_HEADER_HEIGHT = 40
LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH = 36
LEGACY_DESKNOTE_BOTTOM_HOTZONE_HEIGHT = 40
LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT = 111
LEGACY_DESKNOTE_SCREEN_EDGE_MARGIN = 80
LEGACY_DESKNOTE_MOUSE_TOLERANCE = 3


class LegacyDeskNoteMouseAction(str, Enum):
    """Actions from the old frameless ``desknote.vb`` mouse handlers."""

    MOVE = "move"
    RESIZE = "resize"
    HIDE = "hide"
    CLOSE = "close"
    HIDE_ZONE = "hide-zone"
    CLOSE_ZONE = "close-zone"


class LegacyDeskNoteCursor(str, Enum):
    """Cursor hints used by ``desknote_MouseMove`` in the WinForms form."""

    MOVE = "size-all"
    RESIZE = "size-nwse"
    ARROW = "arrow"
    HIDE = "pan-south"


@dataclass(frozen=True, slots=True)
class LegacyDeskNoteRect:
    """Small geometry record for the old frameless ``desknote.vb`` behavior."""

    x: int
    y: int
    width: int
    height: int


def _clamp_positive(value: int, minimum: int = 1) -> int:
    return max(minimum, int(value))


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

    ``mouse_over_all`` subtracted 12/32 pixels from the window origin, enlarged
    the form by 26/48 pixels, moved the RichTextBox to 12/32 and showed the
    title strip.  This is the expanded custom-border rectangle.
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
        _clamp_positive(rect.width - LEGACY_DESKNOTE_BORDER_WIDTH_PAD),
        _clamp_positive(rect.height - LEGACY_DESKNOTE_BORDER_HEIGHT_PAD),
    )


def legacy_desknote_show2_geometry(saved_window: LegacyDeskNoteRect) -> LegacyDeskNoteRect:
    """Return the geometry shown by ``desknote.show2`` after construction.

    The VB constructor remembered the logical ``window`` rectangle and kept the
    RichTextBox invisible.  ``show2`` then showed a compact text-only note by
    applying the same +12/+32 and -26/-48 transform as the hidden-border state.
    """

    return legacy_desknote_hidden_border_geometry(saved_window)


def legacy_desknote_editor_rect(window_width: int, window_height: int, *, expanded: bool) -> LegacyDeskNoteRect:
    """Return the RichTextBox rectangle inside the legacy form.

    Idle notes fill the whole compact form.  Expanded notes reserve the old
    title/border strip and place the editor at ``(12, 32)``.
    """

    if expanded:
        return LegacyDeskNoteRect(
            LEGACY_DESKNOTE_BORDER_LEFT,
            LEGACY_DESKNOTE_BORDER_TOP,
            _clamp_positive(window_width - LEGACY_DESKNOTE_BORDER_WIDTH_PAD),
            _clamp_positive(window_height - LEGACY_DESKNOTE_BORDER_HEIGHT_PAD),
        )
    return LegacyDeskNoteRect(0, 0, _clamp_positive(window_width), _clamp_positive(window_height))


def legacy_desknote_label_geometry(window_width: int, label_width: int, label_height: int = 22) -> LegacyDeskNoteRect:
    """Return the title-label placement from the WinForms ``Paint`` handler."""

    x = int(window_width / 2) - int(label_width / 2)
    if x < LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH + 1:
        x = LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH + 1
    max_width = max(1, window_width - 70)
    return LegacyDeskNoteRect(x, 10, min(max_width, max(1, label_width)), max(1, label_height))


def legacy_desknote_title_hit_action(local_x: int, local_y: int, width: int) -> str:
    """Classify old title-strip clicks from ``desknote.vb``.

    Left title button hides the note, right title button closes/removes it and
    the remaining title region starts a move.  Outside the title strip the old
    form still prepared move state, so ``move`` is the safe default.
    """

    action = legacy_desknote_mouse_down_action(local_x, local_y, width, left_button=True)
    return action.value if isinstance(action, LegacyDeskNoteMouseAction) else str(action)


def legacy_desknote_mouse_down_action(
    local_x: int,
    local_y: int,
    width: int,
    *,
    left_button: bool = True,
) -> LegacyDeskNoteMouseAction:
    """Return the old action for ``desknote_MouseDown``.

    On a left click in the first 40 pixels of the title strip: left 36 pixels
    hide, right 36 pixels close, center moves.  All other clicks start moving.
    """

    if left_button and local_y < LEGACY_DESKNOTE_HEADER_HEIGHT:
        if local_x > max(0, width - LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH):
            return LegacyDeskNoteMouseAction.CLOSE
        if local_x < LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH:
            return LegacyDeskNoteMouseAction.HIDE
    return LegacyDeskNoteMouseAction.MOVE


def legacy_desknote_mouse_move_action(
    local_x: int,
    local_y: int,
    width: int,
    height: int,
) -> LegacyDeskNoteMouseAction:
    """Classify the active hot zone from ``desknote_MouseMove``.

    The lower-right 36x40 area resizes.  Other lower/middle areas move.  In the
    top strip the left and right button areas are visible hot zones but do not
    start resizing.
    """

    if local_y > height - LEGACY_DESKNOTE_BOTTOM_HOTZONE_HEIGHT:
        if local_x > width - LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH:
            return LegacyDeskNoteMouseAction.RESIZE
        return LegacyDeskNoteMouseAction.MOVE
    if local_y < LEGACY_DESKNOTE_HEADER_HEIGHT:
        if local_x > width - LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH:
            return LegacyDeskNoteMouseAction.CLOSE_ZONE
        if local_x < LEGACY_DESKNOTE_HEADER_BUTTON_WIDTH:
            return LegacyDeskNoteMouseAction.HIDE_ZONE
    return LegacyDeskNoteMouseAction.MOVE


def legacy_desknote_cursor_for_move_action(action: LegacyDeskNoteMouseAction | str) -> LegacyDeskNoteCursor:
    """Map a move-zone action to the old WinForms cursor hint."""

    value = LegacyDeskNoteMouseAction(action)
    if value is LegacyDeskNoteMouseAction.RESIZE:
        return LegacyDeskNoteCursor.RESIZE
    if value is LegacyDeskNoteMouseAction.CLOSE_ZONE:
        return LegacyDeskNoteCursor.ARROW
    if value is LegacyDeskNoteMouseAction.HIDE_ZONE:
        return LegacyDeskNoteCursor.HIDE
    return LegacyDeskNoteCursor.MOVE


def legacy_desknote_move_geometry(mouse_x: int, mouse_y: int, offset_x: int, offset_y: int, width: int, height: int) -> LegacyDeskNoteRect:
    """Return the geometry used by ``mouse_inelement_move`` while dragging."""

    return LegacyDeskNoteRect(mouse_x - offset_x, mouse_y - offset_y, _clamp_positive(width), _clamp_positive(height))


def legacy_desknote_resize_geometry(window_x: int, window_y: int, mouse_x: int, mouse_y: int) -> LegacyDeskNoteRect:
    """Return the resize geometry from the old lower-right drag handle."""

    return LegacyDeskNoteRect(window_x, window_y, _clamp_positive(mouse_x - window_x), _clamp_positive(mouse_y - window_y))


def legacy_desknote_clamp_to_work_area(
    rect: LegacyDeskNoteRect,
    work_area_width: int,
    work_area_height: int,
) -> LegacyDeskNoteRect:
    """Clamp initial note placement like the VB constructor.

    Notizen.NET only moved notes that started beyond the screen minus 80px; it
    did not fully center or resize them.  Width and height are preserved.
    """

    max_x = max(0, int(work_area_width) - LEGACY_DESKNOTE_SCREEN_EDGE_MARGIN)
    max_y = max(0, int(work_area_height) - LEGACY_DESKNOTE_SCREEN_EDGE_MARGIN)
    return LegacyDeskNoteRect(min(rect.x, max_x), min(rect.y, max_y), rect.width, rect.height)


def legacy_desknote_point_outside(rect: LegacyDeskNoteRect, point_x: int, point_y: int) -> bool:
    """Return the old three-pixel-tolerant outside check from ``mouse_is_outside``."""

    return (
        point_x + LEGACY_DESKNOTE_MOUSE_TOLERANCE >= rect.x + rect.width
        or point_x - LEGACY_DESKNOTE_MOUSE_TOLERANCE <= rect.x
        or point_y + LEGACY_DESKNOTE_MOUSE_TOLERANCE >= rect.y + rect.height
        or point_y - LEGACY_DESKNOTE_MOUSE_TOLERANCE <= rect.y
    )


def legacy_desknote_opacity_for_active(stored_opacity: float | int | str | None) -> float:
    """Return the old active/focused opacity.

    The production VB code had the assignment commented out in later snapshots,
    but the surrounding semantics and menu class still model active notes as
    fully visible.  The stored opacity is restored on focus/hover loss.
    """

    _clamp_opacity(stored_opacity)
    return 1.0


def legacy_desknote_opacity_for_inactive(stored_opacity: float | int | str | None) -> float:
    """Return the old inactive opacity from the transparency menu setting."""

    return _clamp_opacity(stored_opacity)


def _clamp_opacity(value: float | int | str | None) -> float:
    try:
        opacity = float(value) if value is not None else 0.85
    except (TypeError, ValueError):
        opacity = 0.85
    return max(0.1, min(1.0, opacity))
