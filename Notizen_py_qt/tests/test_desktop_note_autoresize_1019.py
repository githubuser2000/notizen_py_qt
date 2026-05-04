from __future__ import annotations

from pathlib import Path

from notizen_py_qt import (
    LEGACY_DESKNOTE_AUTORESIZE_SCROLL_PAD,
    LEGACY_DESKNOTE_AUTORESIZE_STEP,
    LEGACY_DESKNOTE_AUTORESIZE_WORK_AREA_PAD,
    LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT,
    LegacyDeskNoteRect,
    legacy_desknote_auto_resize_can_grow,
    legacy_desknote_auto_resize_grow_both_step,
    legacy_desknote_auto_resize_grow_width_step,
    legacy_desknote_auto_resize_shrink_step,
)


def test_legacy_desknote_autoresize_numbers_match_vb_set_clientsizes() -> None:
    assert LEGACY_DESKNOTE_AUTORESIZE_STEP == 10
    assert LEGACY_DESKNOTE_AUTORESIZE_SCROLL_PAD == 6
    assert LEGACY_DESKNOTE_AUTORESIZE_WORK_AREA_PAD == 11
    assert LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT == 111


def test_legacy_desknote_autoresize_step_helpers_match_work_area_guards() -> None:
    rect = LegacyDeskNoteRect(100, 50, 200, 120)
    assert legacy_desknote_auto_resize_can_grow(rect, 400, 300) is True
    assert legacy_desknote_auto_resize_can_grow(LegacyDeskNoteRect(100, 50, 289, 120), 400, 300) is False

    shrunk = legacy_desknote_auto_resize_shrink_step(rect)
    assert shrunk == LegacyDeskNoteRect(100, 50, 190, 111)

    grown_both = legacy_desknote_auto_resize_grow_both_step(rect, 400, 300)
    assert grown_both == LegacyDeskNoteRect(100, 50, 210, 130)

    grown_width = legacy_desknote_auto_resize_grow_width_step(rect, 400, 300)
    assert grown_width == LegacyDeskNoteRect(100, 50, 210, 120)


def test_desktop_note_window_ports_vb_set_clientsizes_scroll_triggers() -> None:
    source = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")
    assert "def _set_clientsizes" in source
    assert "_scroll_manual" in source
    assert "contentsChanged.connect(self._schedule_auto_resize_from_content)" in source
    assert "verticalScrollBar().rangeChanged" in source
    assert "horizontalScrollBar().rangeChanged" in source
    assert "LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT" in source
    assert "legacy_desknote_hover_geometry(geo)" in source


def test_gnome_menu_launcher_hardened_against_stale_desktop_copy() -> None:
    root_desktop = Path("Notizen PyQt.desktop").read_text(encoding="utf-8")
    installer = Path("scripts/install_linux_launcher.sh").read_text(encoding="utf-8")
    appdir = Path("scripts/build_linux_appdir.sh").read_text(encoding="utf-8")

    assert "Exec=env NOTIZEN_RESET_WINDOW=1 python3 -m notizen_py_qt --show --no-tray --reset-window %f" in root_desktop
    assert "DBusActivatable=false" in root_desktop
    assert "STALE_DESKTOP_TARGET" in installer
    assert 'rm -f "$STALE_DESKTOP_TARGET"' in installer
    assert "Exec=env NOTIZEN_RESET_WINDOW=1 python3 -m notizen_py_qt" in installer
    assert "Exec=AppRun %f" in appdir
