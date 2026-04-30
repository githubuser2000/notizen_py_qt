from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
import subprocess
import sys


@dataclass(slots=True, frozen=True)
class NotificationResult:
    """Result of a best-effort desktop notification attempt."""

    delivered: bool
    backend: str
    message: str = ""


def notify(title: str, body: str = "", *, dry_run: bool = False) -> NotificationResult:
    """Send a small desktop notification using only platform tools.

    The original WinForms app opened a modal/alarm dialog.  This Python port keeps
    the core dependency-free and therefore talks to the common OS helpers instead
    of adding a notification package.  When no helper is available, callers still
    receive a useful fallback result and can print the message.
    """
    title = str(title or "Notizen")
    body = str(body or "")
    if dry_run:
        return NotificationResult(True, "dry-run", f"{title}: {body}".strip())

    try:
        if sys.platform.startswith("linux") or "bsd" in sys.platform:
            return _notify_linux(title, body)
        if sys.platform == "darwin":
            return _notify_macos(title, body)
        if sys.platform.startswith("win"):
            return _notify_windows(title, body)
    except Exception as exc:  # noqa: BLE001 - notification must never crash alarms
        return NotificationResult(False, "error", str(exc))
    return NotificationResult(False, "unsupported", "Keine Desktop-Benachrichtigung für diese Plattform implementiert.")


def _notify_linux(title: str, body: str) -> NotificationResult:
    exe = shutil.which("notify-send")
    if exe is None:
        return NotificationResult(False, "notify-send", "notify-send nicht gefunden")
    env = os.environ.copy()
    # notify-send fails in many headless test containers. Return the reason rather
    # than treating it as a fatal error.
    completed = subprocess.run([exe, title, body], env=env, text=True, capture_output=True, timeout=10, check=False)
    if completed.returncode == 0:
        return NotificationResult(True, "notify-send")
    return NotificationResult(False, "notify-send", (completed.stderr or completed.stdout or "notify-send fehlgeschlagen").strip())


def _notify_macos(title: str, body: str) -> NotificationResult:
    exe = shutil.which("osascript")
    if exe is None:
        return NotificationResult(False, "osascript", "osascript nicht gefunden")
    script = f'display notification {_apple_quote(body)} with title {_apple_quote(title)}'
    completed = subprocess.run([exe, "-e", script], text=True, capture_output=True, timeout=10, check=False)
    if completed.returncode == 0:
        return NotificationResult(True, "osascript")
    return NotificationResult(False, "osascript", (completed.stderr or completed.stdout or "osascript fehlgeschlagen").strip())


def _notify_windows(title: str, body: str) -> NotificationResult:
    exe = shutil.which("powershell") or shutil.which("powershell.exe") or shutil.which("pwsh")
    if exe is None:
        return NotificationResult(False, "powershell", "PowerShell nicht gefunden")
    # MessageBox is deliberately simple and dependency-free. Toast notifications
    # require more OS-specific setup and are not consistently available from scripts.
    script = (
        "Add-Type -AssemblyName PresentationFramework;"
        f"[System.Windows.MessageBox]::Show({_ps_quote(body)}, {_ps_quote(title)}) | Out-Null"
    )
    completed = subprocess.run([exe, "-NoProfile", "-NonInteractive", "-Command", script], text=True, capture_output=True, timeout=20, check=False)
    if completed.returncode == 0:
        return NotificationResult(True, "powershell-messagebox")
    return NotificationResult(False, "powershell-messagebox", (completed.stderr or completed.stdout or "PowerShell-Benachrichtigung fehlgeschlagen").strip())


def _apple_quote(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
