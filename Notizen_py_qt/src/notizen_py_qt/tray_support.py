from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Mapping, Sequence

_TRUE_VALUES = {"1", "true", "yes", "on", "ja"}
_FALSE_VALUES = {"0", "false", "no", "off", "nein"}

# UUIDs used by the common GNOME Shell tray/AppIndicator extensions.  The first
# one is the widely packaged AppIndicator/KStatusNotifier extension.  Ubuntu
# sometimes ships a distribution-specific UUID, and the others are kept as
# compatibility hints for users who install alternate legacy-tray extensions.
KNOWN_GNOME_TRAY_EXTENSION_UUIDS = (
    "appindicatorsupport@rgcjonas.gmail.com",
    "ubuntu-appindicators@ubuntu.com",
    "trayIconsReloaded@selfmade.pl",
    "status-icons@gnome-shell-extensions.gcampax.github.com",
    "statusicons@gnome-shell-extensions.gcampax.github.com",
)


@dataclass(frozen=True, slots=True)
class TrayDecision:
    """Result of deciding whether a minimized start may be hidden in the tray."""

    hide_to_tray: bool
    reason: str
    gnome_session: bool = False
    tray_extension_detected: bool = False


def _env_value(env: Mapping[str, str] | None, name: str) -> str:
    source = os.environ if env is None else env
    return str(source.get(name, ""))


def _env_flag(env: Mapping[str, str] | None, name: str) -> bool | None:
    value = _env_value(env, name).strip().casefold()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    return None


def is_gnome_session(env: Mapping[str, str] | None = None) -> bool:
    """Return True when environment variables identify a GNOME session."""

    desktop = ":".join(
        _env_value(env, key)
        for key in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION", "GNOME_DESKTOP_SESSION_ID")
    ).casefold()
    return "gnome" in desktop


def parse_gnome_extension_list(output: str) -> tuple[str, ...]:
    """Parse ``gnome-extensions list --enabled`` output into UUIDs."""

    return tuple(line.strip() for line in output.splitlines() if line.strip())


def detect_enabled_gnome_extensions(timeout: float = 1.5) -> tuple[str, ...]:
    """Return enabled GNOME Shell extension UUIDs, or an empty tuple on failure."""

    if shutil.which("gnome-extensions") is None:
        return ()
    try:
        completed = subprocess.run(
            ["gnome-extensions", "list", "--enabled"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
        )
    except Exception:
        return ()
    return parse_gnome_extension_list(completed.stdout or "")


def has_known_gnome_tray_extension(enabled_extensions: Sequence[str] | None = None) -> bool:
    """Return True when a known tray/AppIndicator extension is enabled."""

    enabled = enabled_extensions if enabled_extensions is not None else detect_enabled_gnome_extensions()
    enabled_lower = {item.casefold() for item in enabled}
    return any(uuid.casefold() in enabled_lower for uuid in KNOWN_GNOME_TRAY_EXTENSION_UUIDS)


def decide_startup_tray_visibility(
    *,
    tray_icon_created: bool,
    show_in_taskbar_when_minimized: bool,
    gnome_safe_start: bool = True,
    env: Mapping[str, str] | None = None,
    enabled_gnome_extensions: Sequence[str] | None = None,
    force_hide_to_tray: bool = False,
) -> TrayDecision:
    """Decide whether a minimized startup should hide the main window.

    The legacy WinForms app could safely start hidden because Windows always had
    a notification area.  GNOME often does not expose legacy tray icons unless an
    AppIndicator/KStatusNotifier extension is enabled.  Starting hidden there can
    make the app look dead and leave no obvious way back to the main window.
    """

    if not tray_icon_created:
        return TrayDecision(False, "Kein Qt-Tray verfügbar.")
    if show_in_taskbar_when_minimized:
        return TrayDecision(False, "Einstellung zeigt minimierte Fenster in der Taskleiste.")
    if force_hide_to_tray or _env_flag(env, "NOTIZEN_FORCE_TRAY_START") is True:
        return TrayDecision(True, "Tray-Start wurde erzwungen.", is_gnome_session(env), False)
    env_override = _env_flag(env, "NOTIZEN_GNOME_SAFE_TRAY")
    if env_override is not None:
        gnome_safe_start = env_override

    gnome = is_gnome_session(env)
    if gnome and gnome_safe_start:
        # 0.10.3 deliberately keeps the main window visible in GNOME by
        # default, even if an AppIndicator extension appears to be enabled.
        # In real GNOME sessions the extension can still be installed but the
        # icon may be hidden, disabled for the user session, or otherwise not
        # reachable.  The old Windows tray behavior is therefore only used
        # when the user explicitly requests it with --force-tray-start or the
        # NOTIZEN_FORCE_TRAY_START environment flag.
        extension_detected = has_known_gnome_tray_extension(enabled_gnome_extensions)
        if extension_detected:
            return TrayDecision(
                False,
                "GNOME-Sitzung: Hauptfenster bleibt sichtbar; Tray-Start nur mit --force-tray-start.",
                gnome_session=True,
                tray_extension_detected=True,
            )
        return TrayDecision(
            False,
            "GNOME-Sitzung ohne erkannte Tray-/AppIndicator-Erweiterung; Hauptfenster bleibt sichtbar.",
            gnome_session=True,
            tray_extension_detected=False,
        )

    return TrayDecision(True, "Tray-Verbergen erlaubt.", gnome_session=gnome)


def gnome_tray_install_hint() -> str:
    """Short user-facing hint for enabling tray icons in GNOME."""

    return (
        "GNOME zeigt klassische Trayicons oft erst mit einer AppIndicator/KStatusNotifier-Erweiterung. "
        "Notizen startet dort standardmäßig mit sichtbarem Hauptfenster; Tray-Start nur bewusst per --force-tray-start."
    )
