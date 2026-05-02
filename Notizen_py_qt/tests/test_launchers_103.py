from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


def test_direct_start_script_is_visible_no_tray_launcher() -> None:
    script = Path("notizen-starten.sh")
    text = script.read_text(encoding="utf-8")

    assert script.exists()
    assert os.access(script, os.X_OK)
    assert "PYTHONPATH" in text
    assert "-m notizen_py_qt" in text
    assert "prefix+=(--show)" in text
    assert "prefix+=(--no-tray)" in text
    assert "PySide6" in text and "PyQt6" in text


def test_human_named_start_file_delegates_to_safe_launcher() -> None:
    script = Path("Notizen starten.sh")
    text = script.read_text(encoding="utf-8")

    assert os.access(script, os.X_OK)
    assert "notizen-starten.sh" in text


def test_desktop_launcher_uses_start_script_relative_to_desktop_file() -> None:
    launcher = Path("Notizen PyQt.desktop")
    text = launcher.read_text(encoding="utf-8")

    assert os.access(launcher, os.X_OK)
    assert "Type=Application" in text
    assert "notizen-starten.sh" in text
    assert "%k" in text
    assert "%f" in text


def test_linux_launcher_installer_writes_visible_no_tray_exec() -> None:
    script = Path("scripts/install_linux_launcher.sh")
    text = script.read_text(encoding="utf-8")

    assert os.access(script, os.X_OK)
    assert "notizen-py-qt.desktop" in text
    assert "--show --no-tray" in text
    assert "metadata::trusted" in text


def test_launcher_shell_scripts_are_syntax_valid() -> None:
    for script in (
        Path("notizen-starten.sh"),
        Path("Notizen starten.sh"),
        Path("scripts/install_linux_launcher.sh"),
    ):
        subprocess.run(["bash", "-n", str(script)], check=True)
