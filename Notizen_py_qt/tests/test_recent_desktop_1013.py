from __future__ import annotations

from xml.etree import ElementTree as ET

from notizen_py_qt import (
    LegacyDeskNoteRect,
    legacy_activate_recent_file,
    legacy_desknote_hidden_border_geometry,
    legacy_desknote_hover_geometry,
    legacy_desknote_opacity_for_active,
    legacy_desknote_opacity_for_inactive,
    legacy_desknote_title_hit_action,
    legacy_recent_files_from_slots,
    legacy_recent_slots_from_files,
    legacy_remember_recent_file,
)
from notizen_py_qt.settings import AppSettings


def test_legacy_recent_slots_are_read_and_written_in_four_file_order() -> None:
    element = ET.fromstring('<files a="a.alx" b="" c="c.alx" d="d.alx" />')
    assert legacy_recent_files_from_slots(element) == ["a.alx", "c.alx", "d.alx"]
    assert legacy_recent_slots_from_files(["one.alx", "two.alx", "three.alx", "four.alx", "five.alx"]) == {
        "a": "two.alx",
        "b": "three.alx",
        "c": "four.alx",
        "d": "five.alx",
    }


def test_legacy_recent_remember_and_activation_rotate_to_newest_slot() -> None:
    assert legacy_remember_recent_file(["a", "b", "c", "d"], "b") == ["a", "c", "d", "b"]
    selected, recent = legacy_activate_recent_file(["a", "b", "c", "d"], 1)
    assert selected == "b"
    assert recent == ["a", "c", "d", "b"]
    selected, recent = legacy_activate_recent_file(recent, "a")
    assert selected == "a"
    assert recent == ["c", "d", "b", "a"]


def test_app_settings_recent_helpers_use_legacy_slots(tmp_path) -> None:
    settings = AppSettings(config_dir=tmp_path)
    settings.recent_files = ["a", "b", "c", "d"]
    settings.remember_file("b")
    assert settings.recent_files == ["a", "c", "d", "b"]
    assert settings.activate_recent_file(0) == "a"
    assert settings.recent_files == ["c", "d", "b", "a"]


def test_desknote_legacy_geometry_and_opacity_helpers() -> None:
    rect = LegacyDeskNoteRect(100, 200, 300, 400)
    expanded = legacy_desknote_hover_geometry(rect)
    assert expanded == LegacyDeskNoteRect(88, 168, 326, 448)
    assert legacy_desknote_hidden_border_geometry(expanded) == rect
    assert legacy_desknote_opacity_for_active(0.35) == 1.0
    assert legacy_desknote_opacity_for_inactive("0.35") == 0.35
    assert legacy_desknote_opacity_for_inactive(0) == 0.1
    assert legacy_desknote_opacity_for_inactive(9) == 1.0


def test_desknote_legacy_title_hit_actions() -> None:
    assert legacy_desknote_title_hit_action(10, 10, 240) == "hide"
    assert legacy_desknote_title_hit_action(230, 10, 240) == "close"
    assert legacy_desknote_title_hit_action(100, 10, 240) == "move"
    assert legacy_desknote_title_hit_action(10, 70, 240) == "move"
