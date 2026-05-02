from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from notizen_py_qt import (
    LEGACY_DEFAULT_FILENAME,
    legacy_documents_notizen_dir,
    legacy_opacity_percent_for_transparency_percent,
    legacy_transparency_menu_options,
    normalize_window_state,
    split_legacy_file_location,
)
from notizen_py_qt.settings import AppSettings


def test_legacy_default_directory_matches_datei_vb_convention(tmp_path: Path) -> None:
    assert legacy_documents_notizen_dir(tmp_path) == tmp_path / "Documents" / "Notizen"
    assert LEGACY_DEFAULT_FILENAME == "unbenannt.alx"


def test_split_legacy_file_location_handles_windows_paths_on_non_windows() -> None:
    directory, file_name = split_legacy_file_location(r"C:\Users\me\Notizen\demo.alx")
    assert directory == r"C:\Users\me\Notizen"
    assert file_name == "demo.alx"


def test_split_legacy_file_location_handles_posix_and_empty_values(tmp_path: Path) -> None:
    directory, file_name = split_legacy_file_location("/home/me/Notizen/demo.alx")
    assert directory == "/home/me/Notizen"
    assert file_name == "demo.alx"

    default_dir = tmp_path / "Documents" / "Notizen"
    directory, file_name = split_legacy_file_location("", default_dir)
    assert directory == str(default_dir)
    assert file_name == "unbenannt.alx"


def test_app_settings_defaults_and_remember_file_keep_legacy_split(tmp_path: Path) -> None:
    settings = AppSettings(config_dir=tmp_path)
    assert settings.last_file == "unbenannt.alx"
    assert settings.last_directory.endswith(str(Path("Documents") / "Notizen"))

    settings.remember_file(r"C:\Users\me\Notizen\demo.alx")
    assert settings.last_directory == r"C:\Users\me\Notizen"
    assert settings.last_file == "demo.alx"
    assert settings.recent_files[-1] == r"C:\Users\me\Notizen\demo.alx"


def test_legacy_open_config_empty_directory_falls_back_to_documents_notizen(tmp_path: Path) -> None:
    settings = AppSettings(config_dir=tmp_path)
    root = ET.fromstring('<notizen-alx><open file="" directory=""><once-opened file="once.alx" timestamp="123" /></open></notizen-alx>')
    settings.apply_xml_root(root)
    assert settings.last_file == "unbenannt.alx"
    assert settings.last_directory.endswith(str(Path("Documents") / "Notizen"))
    assert settings.open_once_file == "once.alx"
    assert settings.open_once_timestamp == "123"


def test_desktop_note_transparency_menu_uses_old_transparency_semantics() -> None:
    options = legacy_transparency_menu_options()
    assert options[0] == ("90 %", 10)
    assert options[-1] == ("0 %", 100)
    assert legacy_opacity_percent_for_transparency_percent(80) == 20
    assert legacy_opacity_percent_for_transparency_percent(0) == 100
    assert legacy_opacity_percent_for_transparency_percent(200) == 10


def test_window_state_normalization_accepts_legacy_config_values() -> None:
    assert normalize_window_state("minimized") == "Minimized"
    assert normalize_window_state("MAXIMIZED") == "Maximized"
    assert normalize_window_state("weird") == "Normal"
