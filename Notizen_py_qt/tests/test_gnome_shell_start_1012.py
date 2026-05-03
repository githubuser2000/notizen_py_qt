from __future__ import annotations

import os
import subprocess
from pathlib import Path

from notizen_py_qt.display_env import normalize_qt_display_environment


def test_shell_env_from_report_switches_to_known_visible_menu_display() -> None:
    env = {
        "XDG_CURRENT_DESKTOP": "GNOME",
        "XDG_SESSION_DESKTOP": "gnome",
        "WAYLAND_DISPLAY": "wayland-0",
        "DISPLAY": ":1",
        "GDK_BACKEND": "x11",
        "QT_QPA_PLATFORM": "wayland;xcb",
    }
    decision = normalize_qt_display_environment(["--no-tray", "--show"], env)
    assert decision.changed is True
    assert env["QT_QPA_PLATFORM"] == "wayland;xcb"
    assert "GDK_BACKEND" not in env
    assert env["DISPLAY"] == ":0"
    assert env["NOTIZEN_ORIGINAL_DISPLAY"] == ":1"
    assert "DISPLAY" in decision.summary()


def test_smoke_start_never_inherits_visible_display() -> None:
    env = {
        "XDG_CURRENT_DESKTOP": "GNOME",
        "WAYLAND_DISPLAY": "wayland-0",
        "DISPLAY": ":1",
        "GDK_BACKEND": "x11",
        "QT_QPA_PLATFORM": "wayland;xcb",
        "NOTIZEN_QT_SMOKE_TEST": "1",
    }
    normalize_qt_display_environment(["--smoke-test"], env)
    assert env["QT_QPA_PLATFORM"] == "offscreen"
    assert "DISPLAY" not in env
    assert "WAYLAND_DISPLAY" not in env
    assert "GDK_BACKEND" not in env


def test_build_script_does_not_start_gui_by_default() -> None:
    text = Path("scripts/build_python_qt.sh").read_text(encoding="utf-8")
    assert "WITH_SMOKE=0" in text
    assert "Skipping GUI smoke test by default" in text
    assert "--with-smoke" in text
    assert "timeout -k 2s 10s" in text
    assert "-u DISPLAY" in text
    assert "QT_QPA_PLATFORM=offscreen" in text


def test_diagnose_script_is_bounded_and_does_not_launch_gui_by_default() -> None:
    text = Path("notizen-diagnose.sh").read_text(encoding="utf-8")
    assert "run_with_timeout" in text
    assert "--launch-visible" in text
    assert "Hinweis: Diagnose startet die GUI nicht mehr dauerhaft" in text
    assert "offscreen smoke test" in text
    assert "systemd user display environment" in text


def test_launcher_logs_repaired_display_and_preserves_menu_compatible_display() -> None:
    text = Path("notizen-starten.sh").read_text(encoding="utf-8")
    assert "repair_display_from_session" in text
    assert "systemctl --user show-environment" in text
    assert "wayland;xcb" in text
    assert "GDK_BACKEND" in text
    assert "DISPLAY_REPAIRED" in text
    assert "PACKAGE_VERSION" in text
    assert "PACKAGE_FILE" in text


def test_scripts_are_syntax_valid_after_shell_start_fix() -> None:
    for script in (
        Path("notizen-starten.sh"),
        Path("Notizen starten.sh"),
        Path("notizen-diagnose.sh"),
        Path("scripts/build_python_qt.sh"),
    ):
        subprocess.run(["bash", "-n", str(script)], check=True)
