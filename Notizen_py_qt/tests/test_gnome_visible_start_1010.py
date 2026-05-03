from __future__ import annotations

import os
import subprocess
from pathlib import Path

from notizen_py_qt.window_visibility import (
    env_requests_window_reset,
    legacy_window_state_is_restorable,
    sanitize_legacy_window_geometry,
    should_start_minimized,
)


def test_legacy_default_minimized_state_is_not_restorable_at_zero_zero() -> None:
    assert legacy_window_state_is_restorable(0, 0) is False
    assert legacy_window_state_is_restorable("0", "60") is False
    assert legacy_window_state_is_restorable(60, 60) is True
    assert should_start_minimized(stored_window_state="Minimized", stored_state_restorable=False) is False
    assert should_start_minimized(stored_window_state="Minimized", stored_state_restorable=True) is True


def test_force_visible_and_reset_override_minimized_requests() -> None:
    assert should_start_minimized(explicit_minimized=True, force_visible=True) is False
    assert should_start_minimized(legacy_minimized=True, reset_window=True) is False
    assert env_requests_window_reset({"NOTIZEN_RESET_WINDOW": "yes"}) is True
    assert env_requests_window_reset({"NOTIZEN_FORCE_VISIBLE": "1"}) is True


def test_window_geometry_is_clamped_back_into_current_work_area() -> None:
    negative = sanitize_legacy_window_geometry(
        x=-5000,
        y=-3000,
        width=900,
        height=600,
        screen_left=0,
        screen_top=0,
        screen_width=1920,
        screen_height=1080,
    )
    assert negative.reset is True
    assert negative.x >= 0 and negative.y >= 0

    too_far = sanitize_legacy_window_geometry(
        x=5000,
        y=3000,
        width=900,
        height=600,
        screen_left=0,
        screen_top=0,
        screen_width=1920,
        screen_height=1080,
    )
    assert too_far.reset is True
    assert 0 <= too_far.x <= 1920 - 50
    assert 0 <= too_far.y <= 1080 - 50

    forced = sanitize_legacy_window_geometry(
        x=400,
        y=300,
        width=900,
        height=600,
        screen_left=10,
        screen_top=20,
        screen_width=1280,
        screen_height=800,
        force_reset=True,
    )
    assert forced.reset is True
    assert forced.x >= 10 and forced.y >= 20


def test_start_scripts_force_visible_reset_and_have_diagnostics() -> None:
    script = Path("notizen-starten.sh")
    text = script.read_text(encoding="utf-8")
    assert "prefix+=(--show)" in text
    assert "prefix+=(--reset-window)" in text
    assert "--no-tray" in text
    assert "startup.log" in text
    assert "NOTIZEN_FORCE_VISIBLE=1" in text
    assert "QT_QPA_PLATFORM=\"wayland;xcb\"" in text
    assert ">>\"$LOG_FILE\" 2>&1" in text

    diagnose = Path("notizen-diagnose.sh")
    assert diagnose.exists()
    assert os.access(diagnose, os.X_OK)
    assert "diagnose.log" in diagnose.read_text(encoding="utf-8")


def test_desktop_installers_pass_reset_window() -> None:
    root_desktop = Path("Notizen PyQt.desktop").read_text(encoding="utf-8")
    installer = Path("scripts/install_linux_launcher.sh").read_text(encoding="utf-8")
    assert "--show --no-tray --reset-window" in root_desktop
    assert "--show --no-tray --reset-window" in installer


def test_visible_start_shell_scripts_are_syntax_valid() -> None:
    for script in (
        Path("notizen-starten.sh"),
        Path("Notizen starten.sh"),
        Path("notizen-diagnose.sh"),
        Path("scripts/install_linux_launcher.sh"),
    ):
        subprocess.run(["bash", "-n", str(script)], check=True)
