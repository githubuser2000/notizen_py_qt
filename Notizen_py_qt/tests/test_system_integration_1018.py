from __future__ import annotations

from pathlib import Path

from notizen_py_qt import __version__
from notizen_py_qt.system_integration import (
    LEGACY_ALX_EXTENSION,
    LEGACY_ALX_PROG_ID,
    build_linux_desktop_exec,
    build_windows_module_open_command,
    build_windows_script_open_command,
    legacy_windows_alx_registry_entries,
    windows_association_preview_lines,
)


def test_version_1022() -> None:
    assert __version__ == "0.10.22"


def test_windows_module_open_command_quotes_percent_one() -> None:
    command = build_windows_module_open_command(python_executable=r"C:\Program Files\Python\python.exe")
    assert command.startswith('"C:\\Program Files\\Python\\python.exe" -m notizen_py_qt')
    assert "--show" in command
    assert "--no-tray" in command
    assert "--reset-window" in command
    assert command.endswith(' "%1"')


def test_windows_script_open_command_quotes_launcher_and_file() -> None:
    command = build_windows_script_open_command(Path(r"C:\Tools\Notizen starten.cmd"))
    assert command.startswith('"C:\\Tools\\Notizen starten.cmd"')
    assert command.endswith(' "%1"')


def test_legacy_windows_registry_entries_mirror_old_hkcr_layout() -> None:
    entries = legacy_windows_alx_registry_entries(
        open_command='"python" -m notizen_py_qt "%1"',
        icon_path=r"C:\Python\python.exe",
    )
    assert LEGACY_ALX_EXTENSION == ".alx"
    assert LEGACY_ALX_PROG_ID == "notizenfile"
    by_key_name = {(entry.key, entry.name): entry for entry in entries}
    assert by_key_name[(r"Software\Classes\.alx", "")].value == "Notizenfile"
    assert by_key_name[(r"Software\Classes\.alx\OpenWithList\Notizen.exe", "")].write_if_missing
    assert by_key_name[(r"Software\Classes\.alx\OpenWithProgIds", "notizenfile")].write_if_missing
    assert by_key_name[(r"Software\Classes\notizenfile\Shell", "")].value == "Open"
    assert by_key_name[(r"Software\Classes\notizenfile\Shell\Open\Command", "")].value == '"python" -m notizen_py_qt "%1"'
    assert not by_key_name[(r"Software\Classes\notizenfile\Shell\Open\Command", "")].write_if_missing


def test_registry_preview_is_stable_and_human_readable() -> None:
    entries = legacy_windows_alx_registry_entries(open_command="cmd %1", icon_path="icon")
    lines = windows_association_preview_lines(entries)
    assert lines[0].startswith(r"if-missing Software\Classes\.alx [(Default)]")
    assert any(r"set Software\Classes\notizenfile\Shell\Open\Command [(Default)] = cmd %1" == line for line in lines)


def test_linux_desktop_exec_keeps_visible_direct_module_flags() -> None:
    line = build_linux_desktop_exec()
    assert line == "env NOTIZEN_RESET_WINDOW=1 RESOURCE_NAME=notizen-py-qt python3 -m notizen_py_qt --show --no-tray --reset-window %f"


def test_new_installation_scripts_are_present() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "Notizen starten.cmd").read_text(encoding="utf-8").startswith("@echo off")
    assert "HKCU:\\Software\\Classes" in (root / "scripts" / "install_windows_file_association.ps1").read_text(encoding="utf-8")
    assert (root / "scripts" / "uninstall_linux_launcher.sh").read_text(encoding="utf-8").startswith("#!/usr/bin/env bash")
    assert (root / "scripts" / "build_linux_appdir.sh").read_text(encoding="utf-8").startswith("#!/usr/bin/env bash")
