from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import sys

from .config import AppConfig


@dataclass(slots=True, frozen=True)
class AutostartStatus:
    supported: bool
    installed: bool
    path: Path | None
    message: str = ""


def default_autostart_path() -> Path | None:
    if os.name == "nt":
        startup = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup / "Notizen Python Slint.cmd"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "LaunchAgents" / "net.notizen-py-slint.plist"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart" / "notizen-py-slint.desktop"


def autostart_status() -> AutostartStatus:
    path = default_autostart_path()
    if path is None:
        return AutostartStatus(False, False, None, "Diese Plattform wird nicht unterstützt.")
    return AutostartStatus(True, path.exists(), path)


def install_autostart(config: AppConfig, *, command: list[str] | None = None) -> Path:
    path = default_autostart_path()
    if path is None:
        raise RuntimeError("Autostart wird auf dieser Plattform nicht unterstützt.")
    command = command or _default_command(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        path.write_text(_windows_cmd(command), encoding="utf-8")
    elif sys.platform == "darwin":
        path.write_text(_launch_agent_plist(command), encoding="utf-8")
    else:
        path.write_text(_linux_desktop_entry(command), encoding="utf-8")
        try:
            path.chmod(0o755)
        except OSError:
            pass
    return path


def remove_autostart() -> bool:
    path = default_autostart_path()
    if path is None or not path.exists():
        return False
    path.unlink()
    return True


def sync_autostart(config: AppConfig) -> AutostartStatus:
    if config.autorun:
        try:
            path = install_autostart(config)
        except Exception as exc:  # noqa: BLE001 - caller shows user-facing message
            return AutostartStatus(False, False, default_autostart_path(), str(exc))
        return AutostartStatus(True, True, path)
    removed = remove_autostart()
    status = autostart_status()
    return AutostartStatus(status.supported, status.installed, status.path, "entfernt" if removed else status.message)


def _default_command(config: AppConfig) -> list[str]:
    command = [sys.executable, "-m", "notizen_py_slint"]
    if config.autorun_minimized:
        command.append("--minimized")
    if config.last_file:
        command.append(config.last_file)
    return command


def _linux_desktop_entry(command: list[str]) -> str:
    quoted = " ".join(shlex.quote(part) for part in command)
    return "\n".join(
        [
            "[Desktop Entry]",
            "Type=Application",
            "Name=Notizen Python Slint",
            f"Exec={quoted}",
            "Terminal=false",
            "X-GNOME-Autostart-enabled=true",
            "",
        ]
    )


def _windows_cmd(command: list[str]) -> str:
    quoted = " ".join(_quote_windows(part) for part in command)
    return f"@echo off\r\nstart \"Notizen Python Slint\" {quoted}\r\n"


def _quote_windows(value: str) -> str:
    if not value or any(ch.isspace() for ch in value) or '"' in value:
        return '"' + value.replace('"', '\\"') + '"'
    return value


def _launch_agent_plist(command: list[str]) -> str:
    args = "\n".join(f"        <string>{_xml_escape(part)}</string>" for part in command)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>net.notizen-py-slint</string>
    <key>ProgramArguments</key>
    <array>
{args}
    </array>
    <key>RunAtLoad</key><true/>
</dict>
</plist>
'''


def _xml_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
