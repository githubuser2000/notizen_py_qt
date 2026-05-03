from __future__ import annotations

from notizen_py_qt.display_env import normalize_qt_display_environment, visible_start_requested


def test_visible_start_flags_include_show_reset_and_no_tray() -> None:
    assert visible_start_requested(["--show"], {}) is True
    assert visible_start_requested(["--reset-window"], {}) is True
    assert visible_start_requested(["--no-tray"], {}) is True
    assert visible_start_requested([], {"NOTIZEN_FORCE_VISIBLE": "yes"}) is True


def test_gnome_wayland_terminal_prefers_wayland_over_xcb() -> None:
    env = {
        "XDG_CURRENT_DESKTOP": "GNOME",
        "WAYLAND_DISPLAY": "wayland-0",
        "DISPLAY": ":1",
        "QT_QPA_PLATFORM": "xcb",
    }
    decision = normalize_qt_display_environment(["--show", "--no-tray"], env)
    assert decision.changed is True
    assert env["QT_QPA_PLATFORM"] == "wayland;xcb"
    assert "xcb" in decision.platform_before


def test_offscreen_platform_is_removed_for_visible_start() -> None:
    env = {
        "WAYLAND_DISPLAY": "wayland-0",
        "QT_QPA_PLATFORM": "offscreen",
    }
    decision = normalize_qt_display_environment(["--show"], env)
    assert decision.changed is True
    assert env["QT_QPA_PLATFORM"] == "wayland;xcb"


def test_gtk_platform_theme_is_unset_on_gnome_wayland_visible_start() -> None:
    env = {
        "XDG_SESSION_DESKTOP": "gnome",
        "WAYLAND_DISPLAY": "wayland-0",
        "DISPLAY": ":1",
        "QT_QPA_PLATFORMTHEME": "gtk3",
    }
    decision = normalize_qt_display_environment(["--show"], env)
    assert decision.changed is True
    assert "QT_QPA_PLATFORMTHEME" not in env
    assert "unset" in "; ".join(decision.notes)


def test_keep_qt_env_opt_out_preserves_user_values() -> None:
    env = {
        "NOTIZEN_KEEP_QT_ENV": "1",
        "WAYLAND_DISPLAY": "wayland-0",
        "QT_QPA_PLATFORM": "xcb",
        "QT_QPA_PLATFORMTHEME": "gtk3",
    }
    decision = normalize_qt_display_environment(["--show"], env)
    assert decision.changed is False
    assert env["QT_QPA_PLATFORM"] == "xcb"
    assert env["QT_QPA_PLATFORMTHEME"] == "gtk3"


def test_unpacked_project_supports_python_m_from_root() -> None:
    import subprocess
    proc = subprocess.run(["python3", "-m", "notizen_py_qt", "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    assert "Notizen.NET Python/Qt port" in proc.stdout
    assert "--no-tray" in proc.stdout


def test_root_python_m_shim_points_to_src_package() -> None:
    from pathlib import Path
    shim = Path("notizen_py_qt/__init__.py").read_text(encoding="utf-8")
    main = Path("notizen_py_qt/__main__.py").read_text(encoding="utf-8")
    assert "src" in shim
    assert "notizen_py_qt" in shim
    assert "from .app import main" in main
