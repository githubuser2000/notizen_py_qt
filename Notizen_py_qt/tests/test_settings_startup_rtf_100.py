from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from notizen_py_qt.rtf_utils import rtf_to_html, rtf_to_plain_text
from notizen_py_qt.settings import AppSettings, normalize_autosave_seconds
from notizen_py_qt.startup import (
    apply_windows_autostart_script,
    build_autostart_command,
    legacy_autostart_arguments,
    legacy_autostart_target_file,
)


def test_legacy_config_roundtrip_preserves_once_opened_toolstrips_and_autosave_floor(tmp_path: Path) -> None:
    config = tmp_path / "notizen.config.xml"
    config.write_text(
        """<?xml version="1.0" encoding="utf-16"?>
<notizen-alx>
  <open directory="C:\\Notizen" file="demo.alx">
    <once-opened file="C:\\Notizen\\demo.alx" timestamp="637000000000000000" />
  </open>
  <tool-stripes>
    <haupt x="10" y="2" />
    <elements x="20" y="3" />
    <font x="30" y="4" />
    <cutpastecopy x="40" y="5" />
  </tool-stripes>
  <x a="3" />
</notizen-alx>
""",
        encoding="utf-16",
    )

    settings = AppSettings.load(tmp_path)

    assert settings.last_directory == "C:\\Notizen"
    assert settings.last_file == "demo.alx"
    assert settings.open_once_file == "C:\\Notizen\\demo.alx"
    assert settings.open_once_timestamp == "637000000000000000"
    assert settings.toolstrip_positions["haupt"] == (10, 2)
    assert settings.toolstrip_positions["elements"] == (20, 3)
    assert settings.toolstrip_positions["font"] == (30, 4)
    assert settings.toolstrip_positions["cutpastecopy"] == (40, 5)
    assert settings.autosave_seconds == 5

    settings.toolstrip_positions["font"] = (33, 44)
    settings.save()

    root = ET.parse(config).getroot()
    once_opened = root.find("./open/once-opened")
    assert once_opened is not None
    assert once_opened.get("file") == "C:\\Notizen\\demo.alx"
    assert once_opened.get("timestamp") == "637000000000000000"
    assert root.find("./tool-stripes/font").get("x") == "33"  # type: ignore[union-attr]
    assert root.find("./tool-stripes/font").get("y") == "44"  # type: ignore[union-attr]
    assert root.find("./x").get("a") == "5"  # type: ignore[union-attr]


def test_autosave_normalization_matches_winforms_settings_guard() -> None:
    assert normalize_autosave_seconds(None) == 0
    assert normalize_autosave_seconds("not-a-number") == 0
    assert normalize_autosave_seconds(0) == 0
    assert normalize_autosave_seconds(1) == 5
    assert normalize_autosave_seconds("4") == 5
    assert normalize_autosave_seconds(5) == 5
    assert normalize_autosave_seconds(60) == 60
    assert AppSettings(config_dir=Path("/tmp/example")).autosave_seconds == 60


def test_legacy_autostart_helpers_choose_newest_recent_file_and_write_script(tmp_path: Path) -> None:
    recent = [
        r"C:\Users\me\old.alx",
        "",
        "ftp://example.invalid/notizen.alx",
        r"C:\Users\me\newest.alx",
    ]

    assert legacy_autostart_target_file(recent) == r"C:\Users\me\newest.alx"

    args = legacy_autostart_arguments(enabled=True, minimized=True, recent_files=recent)
    assert args == ("-min", r"C:\Users\me\newest.alx")

    command = build_autostart_command(python_executable=r"C:\Python311\python.exe", arguments=args)
    assert "notizen_py_qt" in command
    assert "-min" in command
    assert r"C:\Users\me\newest.alx" in command

    created = apply_windows_autostart_script(
        enabled=True,
        minimized=True,
        recent_files=recent,
        python_executable=r"C:\Python311\python.exe",
        startup_dir=tmp_path,
    )
    assert created.changed is True
    assert created.path is not None
    assert created.path.exists()
    script = created.path.read_text(encoding="utf-8")
    assert 'start ""' in script
    assert "notizen_py_qt" in script
    assert "-min" in script
    assert r"C:\Users\me\newest.alx" in script

    removed = apply_windows_autostart_script(
        enabled=False,
        minimized=False,
        recent_files=recent,
        startup_dir=tmp_path,
    )
    assert removed.changed is True
    assert created.path.exists() is False


def test_rtf_table_cell_and_row_controls_survive_plain_text_and_html_conversion() -> None:
    rtf = r"{\rtf1\ansi{\trowd A\cell B\cell\row C\cell D\cell\row}}"

    plain = rtf_to_plain_text(rtf)

    assert "A\tB" in plain
    assert "C\tD" in plain
    assert plain.count("\n") >= 1

    html = rtf_to_html(rtf)
    assert "A" in html
    assert "B" in html
    assert "C" in html
    assert "D" in html
