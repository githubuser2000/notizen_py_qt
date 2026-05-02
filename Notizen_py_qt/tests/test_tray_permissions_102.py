from __future__ import annotations

import importlib.util
import stat
from pathlib import Path
from xml.etree import ElementTree as ET

from notizen_py_qt.settings import AppSettings
from notizen_py_qt.tray_support import (
    decide_startup_tray_visibility,
    has_known_gnome_tray_extension,
    is_gnome_session,
    parse_gnome_extension_list,
)


def test_gnome_session_and_appindicator_detection_are_pure_helpers() -> None:
    env = {"XDG_CURRENT_DESKTOP": "GNOME"}
    assert is_gnome_session(env) is True
    assert is_gnome_session({"XDG_CURRENT_DESKTOP": "KDE"}) is False

    parsed = parse_gnome_extension_list("appindicatorsupport@rgcjonas.gmail.com\nother@example\n")
    assert parsed == ("appindicatorsupport@rgcjonas.gmail.com", "other@example")
    assert has_known_gnome_tray_extension(parsed) is True
    assert has_known_gnome_tray_extension(("other@example",)) is False


def test_gnome_safe_start_does_not_hide_without_known_extension() -> None:
    decision = decide_startup_tray_visibility(
        tray_icon_created=True,
        show_in_taskbar_when_minimized=False,
        gnome_safe_start=True,
        env={"XDG_CURRENT_DESKTOP": "GNOME"},
        enabled_gnome_extensions=(),
    )

    assert decision.hide_to_tray is False
    assert decision.gnome_session is True
    assert "GNOME" in decision.reason


def test_gnome_safe_start_keeps_window_visible_even_when_extension_is_enabled() -> None:
    decision = decide_startup_tray_visibility(
        tray_icon_created=True,
        show_in_taskbar_when_minimized=False,
        gnome_safe_start=True,
        env={"XDG_CURRENT_DESKTOP": "GNOME"},
        enabled_gnome_extensions=("appindicatorsupport@rgcjonas.gmail.com",),
    )

    assert decision.hide_to_tray is False
    assert decision.tray_extension_detected is True
    assert "force-tray-start" in decision.reason


def test_tray_decision_respects_taskbar_and_force_flags() -> None:
    assert decide_startup_tray_visibility(
        tray_icon_created=True,
        show_in_taskbar_when_minimized=True,
        env={"XDG_CURRENT_DESKTOP": "KDE"},
    ).hide_to_tray is False
    forced = decide_startup_tray_visibility(
        tray_icon_created=True,
        show_in_taskbar_when_minimized=False,
        env={"XDG_CURRENT_DESKTOP": "GNOME"},
        enabled_gnome_extensions=(),
        force_hide_to_tray=True,
    )
    assert forced.hide_to_tray is True
    assert forced.gnome_session is True
    assert decide_startup_tray_visibility(
        tray_icon_created=False,
        show_in_taskbar_when_minimized=False,
    ).hide_to_tray is False


def test_settings_roundtrip_preserves_gnome_safe_tray_start(tmp_path: Path) -> None:
    settings = AppSettings(config_dir=tmp_path)
    settings.gnome_safe_tray_start = False
    settings.save()

    root = ET.parse(tmp_path / "notizen.config.xml").getroot()
    assert root.find("./tray").get("gnome-safe-start") == "no"  # type: ignore[union-attr]

    loaded = AppSettings.load(tmp_path)
    assert loaded.gnome_safe_tray_start is False


def test_zip_permission_policy_for_future_packaging(tmp_path: Path) -> None:
    project = tmp_path / "Project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "run.sh"
    script.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    py_script = scripts / "probe.py"
    py_script.write_text("#!/usr/bin/env python3\nprint('ok')\n", encoding="utf-8")
    module_file = project / "src" / "notizen_py_qt" / "module.py"
    module_file.parent.mkdir(parents=True)
    module_file.write_text("print('library')\n", encoding="utf-8")
    readme = project / "README.md"
    readme.write_text("ok\n", encoding="utf-8")

    spec = importlib.util.spec_from_file_location("package_zip", Path("scripts/package_zip.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    unix_zip_mode_for_path = module.unix_zip_mode_for_path

    assert stat.S_IMODE(unix_zip_mode_for_path(project)) == 0o755
    assert stat.S_IMODE(unix_zip_mode_for_path(scripts)) == 0o755
    assert stat.S_IMODE(unix_zip_mode_for_path(script)) == 0o755
    desktop = project / "Notizen PyQt.desktop"
    desktop.write_text("[Desktop Entry]\nType=Application\n", encoding="utf-8")
    assert stat.S_IMODE(unix_zip_mode_for_path(py_script)) == 0o755
    assert stat.S_IMODE(unix_zip_mode_for_path(desktop)) == 0o755
    assert stat.S_IMODE(unix_zip_mode_for_path(module_file)) == 0o644
    assert stat.S_IMODE(unix_zip_mode_for_path(readme)) == 0o644
