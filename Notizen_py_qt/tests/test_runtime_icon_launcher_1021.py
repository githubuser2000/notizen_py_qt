from __future__ import annotations

from pathlib import Path


def test_qt_runtime_identity_matches_desktop_file_for_taskbar_icon() -> None:
    source = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")

    assert 'APP_DESKTOP_ID = "notizen-py-qt"' in source
    assert 'os.environ.setdefault("RESOURCE_NAME", APP_DESKTOP_ID)' in source
    assert "setDesktopFileName(APP_DESKTOP_ID)" in source
    assert "setApplicationDisplayName(APP_DISPLAY_NAME)" in source
    assert "QApplication([APP_DESKTOP_ID])" in source
    assert "self.setWindowIcon(icon)" in source


def test_linux_menu_launcher_keeps_direct_module_exec_and_resource_name() -> None:
    installer = Path("scripts/install_linux_launcher.sh").read_text(encoding="utf-8")
    desktop = Path("Notizen PyQt.desktop").read_text(encoding="utf-8")

    expected_exec = (
        "Exec=env NOTIZEN_RESET_WINDOW=1 RESOURCE_NAME=notizen-py-qt "
        "python3 -m notizen_py_qt --show --no-tray --reset-window %f"
    )
    for source in (installer, desktop):
        assert expected_exec in source
        assert "Icon=notizen-py-qt" in source
        assert "StartupWMClass=notizen-py-qt" in source
        assert "Exec=sh " not in source
        assert "Exec=bash " not in source
        assert "notizen-starten.sh --show" not in source
