from __future__ import annotations

from notizen_py_qt import (
    LegacyDeskNoteCursor,
    LegacyDeskNoteMouseAction,
    LegacyDeskNoteRect,
    legacy_desknote_clamp_to_work_area,
    legacy_desknote_cursor_for_move_action,
    legacy_desknote_editor_rect,
    legacy_desknote_hidden_border_geometry,
    legacy_desknote_hover_geometry,
    legacy_desknote_label_geometry,
    legacy_desknote_mouse_down_action,
    legacy_desknote_mouse_move_action,
    legacy_desknote_move_geometry,
    legacy_desknote_point_outside,
    legacy_desknote_resize_geometry,
    legacy_desknote_show2_geometry,
)


def test_desknote_show2_uses_old_compact_geometry() -> None:
    saved = LegacyDeskNoteRect(100, 200, 200, 200)
    shown = legacy_desknote_show2_geometry(saved)
    assert shown == LegacyDeskNoteRect(112, 232, 174, 152)
    assert legacy_desknote_hover_geometry(shown) == saved
    assert legacy_desknote_hidden_border_geometry(saved) == shown


def test_desknote_editor_geometry_matches_idle_and_hover_richtextbox() -> None:
    assert legacy_desknote_editor_rect(174, 152, expanded=False) == LegacyDeskNoteRect(0, 0, 174, 152)
    assert legacy_desknote_editor_rect(200, 200, expanded=True) == LegacyDeskNoteRect(12, 32, 174, 152)


def test_desknote_title_label_is_centered_but_never_under_buttons() -> None:
    assert legacy_desknote_label_geometry(200, 80).x == 60
    assert legacy_desknote_label_geometry(100, 80).x == 37
    assert legacy_desknote_label_geometry(100, 200).width == 30


def test_desknote_mouse_down_title_zones_match_vb() -> None:
    assert legacy_desknote_mouse_down_action(10, 10, 240) is LegacyDeskNoteMouseAction.HIDE
    assert legacy_desknote_mouse_down_action(230, 10, 240) is LegacyDeskNoteMouseAction.CLOSE
    assert legacy_desknote_mouse_down_action(100, 10, 240) is LegacyDeskNoteMouseAction.MOVE
    assert legacy_desknote_mouse_down_action(230, 80, 240) is LegacyDeskNoteMouseAction.MOVE
    assert legacy_desknote_mouse_down_action(10, 10, 240, left_button=False) is LegacyDeskNoteMouseAction.MOVE


def test_desknote_mouse_move_hot_zones_and_cursors_match_vb() -> None:
    assert legacy_desknote_mouse_move_action(230, 190, 240, 200) is LegacyDeskNoteMouseAction.RESIZE
    assert legacy_desknote_cursor_for_move_action(LegacyDeskNoteMouseAction.RESIZE) is LegacyDeskNoteCursor.RESIZE
    assert legacy_desknote_mouse_move_action(10, 10, 240, 200) is LegacyDeskNoteMouseAction.HIDE_ZONE
    assert legacy_desknote_cursor_for_move_action(LegacyDeskNoteMouseAction.HIDE_ZONE) is LegacyDeskNoteCursor.HIDE
    assert legacy_desknote_mouse_move_action(230, 10, 240, 200) is LegacyDeskNoteMouseAction.CLOSE_ZONE
    assert legacy_desknote_cursor_for_move_action(LegacyDeskNoteMouseAction.CLOSE_ZONE) is LegacyDeskNoteCursor.ARROW
    assert legacy_desknote_mouse_move_action(120, 60, 240, 200) is LegacyDeskNoteMouseAction.MOVE
    assert legacy_desknote_cursor_for_move_action(LegacyDeskNoteMouseAction.MOVE) is LegacyDeskNoteCursor.MOVE


def test_desknote_move_resize_and_initial_screen_clamp_match_vb_math() -> None:
    assert legacy_desknote_move_geometry(300, 400, 20, 30, 174, 152) == LegacyDeskNoteRect(280, 370, 174, 152)
    assert legacy_desknote_resize_geometry(100, 200, 350, 480) == LegacyDeskNoteRect(100, 200, 250, 280)
    assert legacy_desknote_clamp_to_work_area(LegacyDeskNoteRect(2000, 900, 200, 200), 1920, 1080) == LegacyDeskNoteRect(1840, 900, 200, 200)
    assert legacy_desknote_clamp_to_work_area(LegacyDeskNoteRect(100, 2000, 200, 200), 1920, 1080) == LegacyDeskNoteRect(100, 1000, 200, 200)


def test_desknote_three_pixel_outside_tolerance() -> None:
    rect = LegacyDeskNoteRect(100, 100, 200, 100)
    assert legacy_desknote_point_outside(rect, 97, 150) is True
    assert legacy_desknote_point_outside(rect, 150, 100) is True
    assert legacy_desknote_point_outside(rect, 150, 150) is False
    assert legacy_desknote_point_outside(rect, 300, 150) is True
