from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / "src" / "notizen_py_qt" / "app.py").read_text(encoding="utf-8")
ALX_SOURCE = (ROOT / "src" / "notizen_py_qt" / "alx_io.py").read_text(encoding="utf-8")


def test_backup_actions_are_wired_like_legacy_safety_copies() -> None:
    assert "backup_now_action" in APP_SOURCE
    assert "open_backup_action" in APP_SOURCE
    assert "def create_manual_backup" in APP_SOURCE
    assert "def open_backup_dialog" in APP_SOURCE
    assert "self.file_menu.addAction(self.backup_now_action)" in APP_SOURCE
    assert "backup_directory_for(self.document.path)" in APP_SOURCE
    assert "list_backups(self.document.path)" in APP_SOURCE


def test_backup_helpers_preserve_notizennet_name_scheme() -> None:
    assert "def backup_directory_for" in ALX_SOURCE
    assert "return Path(path).with_suffix(\"\")" in ALX_SOURCE
    assert "def parse_legacy_backup_timestamp" in ALX_SOURCE
    assert "YYYY-MM-DD-HH-MM-SS-ms" in ALX_SOURCE
    assert "f\"{target.stem}-{stamp}{suffix}\"" in ALX_SOURCE


def test_new_desktop_note_defaults_match_winforms_context_menu() -> None:
    assert "def default_desktop_note_state" in APP_SOURCE
    assert "QtGui.QCursor.pos()" in APP_SOURCE
    assert "width=200" in APP_SOURCE
    assert "height=200" in APP_SOURCE
    assert "opacity=0.85" in APP_SOURCE
    assert "legacy_light_color_argb()" in APP_SOURCE
