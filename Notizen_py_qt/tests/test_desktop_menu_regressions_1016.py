from __future__ import annotations

from pathlib import Path

from notizen_py_qt.display_env import apply_graphical_session_environment


def test_graphical_session_repair_does_not_overwrite_good_menu_display() -> None:
    env = {
        "XDG_CURRENT_DESKTOP": "GNOME",
        "XDG_SESSION_DESKTOP": "gnome",
        "WAYLAND_DISPLAY": "wayland-0",
        "DISPLAY": ":0",
    }
    notes: list[str] = []
    changed = apply_graphical_session_environment(
        env,
        {
            "XDG_CURRENT_DESKTOP": "GNOME",
            "XDG_SESSION_DESKTOP": "gnome",
            "WAYLAND_DISPLAY": "wayland-0",
            "DISPLAY": ":1",
            "XDG_RUNTIME_DIR": "/run/user/1000",
        },
        notes,
    )
    assert changed is True  # XDG_RUNTIME_DIR is filled.
    assert env["DISPLAY"] == ":0"
    assert all("DISPLAY" not in note for note in notes)


def test_graphical_session_repair_still_fixes_known_stale_shell_display() -> None:
    env = {
        "XDG_CURRENT_DESKTOP": "GNOME",
        "WAYLAND_DISPLAY": "wayland-0",
        "DISPLAY": ":1",
    }
    notes: list[str] = []
    changed = apply_graphical_session_environment(env, {"DISPLAY": ":0", "XDG_SESSION_DESKTOP": "gnome"}, notes)
    assert changed is True
    assert env["DISPLAY"] == ":0"
    assert env["NOTIZEN_ORIGINAL_DISPLAY"] == ":1"
    assert any("DISPLAY" in note for note in notes)


def test_menu_launchers_preserve_gnome_supplied_display() -> None:
    project_desktop = Path("Notizen PyQt.desktop").read_text(encoding="utf-8")
    install_script = Path("scripts/install_linux_launcher.sh").read_text(encoding="utf-8")
    assert "NOTIZEN_KEEP_DISPLAY=1" in project_desktop
    assert "NOTIZEN_KEEP_DISPLAY=1" in install_script


def test_desktop_note_window_uses_qt_system_drag_for_wayland() -> None:
    text = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")
    assert "startSystemMove" in text
    assert "startSystemResize" in text
    assert "setGeometry`` drag can show the" in text
    assert "grabMouse" in text  # manual X11 fallback remains available
