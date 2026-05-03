from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence
import os
import subprocess
import sys

_TRUE_VALUES = {"1", "true", "yes", "on", "ja"}
_DANGEROUS_QPA_ROOTS = {"offscreen", "minimal", "minimalegl", "vnc", "eglfs", "linuxfb", "directfb", "webgl"}
_GTK_PLATFORM_THEMES = {"gtk2", "gtk3"}
_GNOME_MENU_COMPAT_QPA = "wayland;xcb"
_VISIBLE_FLAGS = {"--show", "--visible", "--reset-window", "--no-tray"}
_SMOKE_FLAGS = {"--smoke-test"}
_SESSION_ENV_KEYS = {"DISPLAY", "WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "XDG_RUNTIME_DIR"}


@dataclass(frozen=True, slots=True)
class DisplayEnvironmentDecision:
    """Qt/GNOME display-environment changes made before importing Qt.

    GNOME menu starts and shell starts can inherit different display variables.
    The failing user log showed exactly this split: the menu launch was visible
    with ``DISPLAY=:0``, while the shell inherited ``DISPLAY=:1`` and
    ``GDK_BACKEND=x11`` although the session was GNOME/Wayland.  The decision is
    intentionally testable and runs before PySide/PyQt is imported.
    """

    changed: bool
    platform_before: str
    platform_after: str
    theme_before: str
    theme_after: str
    display_before: str = ""
    display_after: str = ""
    wayland_before: str = ""
    wayland_after: str = ""
    gdk_before: str = ""
    gdk_after: str = ""
    notes: tuple[str, ...] = ()

    def summary(self) -> str:
        items = [
            f"changed={int(self.changed)}",
            f"QT_QPA_PLATFORM={self.platform_after or '<unset>'}",
            f"QT_QPA_PLATFORMTHEME={self.theme_after or '<unset>'}",
            f"DISPLAY={self.display_after or '<unset>'}",
            f"WAYLAND_DISPLAY={self.wayland_after or '<unset>'}",
            f"GDK_BACKEND={self.gdk_after or '<unset>'}",
        ]
        if self.notes:
            items.append("notes=" + "; ".join(self.notes))
        return " | ".join(items)


def _truthy(value: object) -> bool:
    return str(value or "").strip().casefold() in _TRUE_VALUES


def _root(value: str) -> str:
    # Qt allows values such as "wayland;xcb" and "xcb:some-option".
    return value.strip().casefold().split(";", 1)[0].split(":", 1)[0]


def _desktop_is_gnome(env: MutableMapping[str, str]) -> bool:
    desktop = " ".join([env.get("XDG_CURRENT_DESKTOP", ""), env.get("XDG_SESSION_DESKTOP", "")]).casefold()
    return "gnome" in desktop


def _smoke_start_requested(argv: Sequence[str] | None = None, env: MutableMapping[str, str] | None = None) -> bool:
    env = env if env is not None else os.environ
    args = list(sys.argv[1:] if argv is None else argv)
    return any(arg in _SMOKE_FLAGS for arg in args) or _truthy(env.get("NOTIZEN_QT_SMOKE_TEST"))


def visible_start_requested(argv: Sequence[str] | None = None, env: MutableMapping[str, str] | None = None) -> bool:
    """Return whether startup must prefer a real visible window."""

    env = env if env is not None else os.environ
    args = list(sys.argv[1:] if argv is None else argv)
    if any(arg in _VISIBLE_FLAGS for arg in args):
        return True
    return _truthy(env.get("NOTIZEN_FORCE_VISIBLE")) or _truthy(env.get("NOTIZEN_RESET_WINDOW")) or _truthy(env.get("NOTIZEN_SAFE_DISPLAY"))


def _read_systemd_user_environment() -> dict[str, str]:
    """Best-effort copy of the graphical session environment from systemd."""

    try:
        proc = subprocess.run(
            ["systemctl", "--user", "show-environment"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=1.0,
            check=False,
        )
    except Exception:
        return {}
    if proc.returncode != 0:
        return {}
    result: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in _SESSION_ENV_KEYS and value:
            result[key] = value
    return result


def apply_graphical_session_environment(
    env: MutableMapping[str, str],
    session: Mapping[str, str],
    notes: list[str] | None = None,
) -> bool:
    """Clone the graphical session variables used by the GNOME menu launcher.

    The user's failing log showed two different environments: the GNOME menu
    launch used ``DISPLAY=:0`` and showed a window, while the interactive shell
    inherited ``DISPLAY=:1`` and hung in GTK.  The safest default is therefore
    not to delete ``DISPLAY``.  Instead, clone the display variables from the
    desktop session when they are available.
    """

    changed = False
    notes = notes if notes is not None else []
    for key in ("XDG_RUNTIME_DIR", "WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DISPLAY"):
        value = session.get(key, "")
        if not value:
            continue
        old = env.get(key, "")
        if old != value:
            env[key] = value
            changed = True
            notes.append(f"{key} {old or '<unset>'!r} -> {value!r} from graphical session")
    return changed


def _repair_display_from_systemd(env: MutableMapping[str, str], notes: list[str]) -> None:
    """Repair stale shell display variables using the desktop session env.

    This is only used for the real process environment.  Unit tests pass a plain
    dict and must not depend on the host's systemd state.
    """

    if env is not os.environ:
        return
    if _truthy(env.get("NOTIZEN_KEEP_QT_ENV")) or _truthy(env.get("NOTIZEN_KEEP_DISPLAY")):
        return
    session = _read_systemd_user_environment()
    if session:
        apply_graphical_session_environment(env, session, notes)


def _set_or_unset(env: MutableMapping[str, str], key: str, value: str | None, notes: list[str]) -> None:
    old = env.get(key, "")
    if value is None:
        if key in env:
            env.pop(key, None)
            notes.append(f"{key} {old!r} unset")
    elif old != value:
        env[key] = value
        notes.append(f"{key} {old or '<unset>'!r} -> {value!r}")


def normalize_qt_display_environment(
    argv: Sequence[str] | None = None,
    env: MutableMapping[str, str] | None = None,
) -> DisplayEnvironmentDecision:
    """Sanitize Qt display variables before importing PySide/PyQt.

    The 0.10.13 policy deliberately mirrors the GNOME menu launch that was
    observed to work on the user's machine: clone the graphical session
    variables from systemd when available, keep the repaired ``DISPLAY`` and use
    ``wayland;xcb`` instead of deleting X11 entirely.  Users can still opt out
    with ``NOTIZEN_KEEP_QT_ENV=1`` or set ``NOTIZEN_QPA_PLATFORM`` explicitly.
    """

    env = env if env is not None else os.environ
    platform_before = env.get("QT_QPA_PLATFORM", "")
    theme_before = env.get("QT_QPA_PLATFORMTHEME", "")
    display_before = env.get("DISPLAY", "")
    wayland_before = env.get("WAYLAND_DISPLAY", "")
    gdk_before = env.get("GDK_BACKEND", "")
    notes: list[str] = []

    if _truthy(env.get("NOTIZEN_KEEP_QT_ENV")):
        return DisplayEnvironmentDecision(
            False,
            platform_before,
            platform_before,
            theme_before,
            theme_before,
            display_before,
            display_before,
            wayland_before,
            wayland_before,
            gdk_before,
            gdk_before,
            ("kept by NOTIZEN_KEEP_QT_ENV",),
        )

    smoke = _smoke_start_requested(argv, env)
    if smoke:
        # Validation must be bounded and headless.  Do not inherit a user's stale
        # DISPLAY/GDK variables into the smoke QApplication constructor.
        _set_or_unset(env, "QT_QPA_PLATFORM", "offscreen", notes)
        _set_or_unset(env, "DISPLAY", None, notes)
        _set_or_unset(env, "WAYLAND_DISPLAY", None, notes)
        _set_or_unset(env, "GDK_BACKEND", None, notes)
        if _root(theme_before) in _GTK_PLATFORM_THEMES:
            _set_or_unset(env, "QT_QPA_PLATFORMTHEME", None, notes)
    else:
        _repair_display_from_systemd(env, notes)
        wants_visible = visible_start_requested(argv, env)
        gnome = _desktop_is_gnome(env)
        has_wayland = bool(env.get("WAYLAND_DISPLAY"))
        if (
            gnome
            and has_wayland
            and wants_visible
            and env.get("DISPLAY", "") in {":1", ":1.0"}
            and not _truthy(env.get("NOTIZEN_KEEP_DISPLAY"))
            and not _truthy(env.get("NOTIZEN_KEEP_SHELL_DISPLAY"))
        ):
            env.setdefault("NOTIZEN_ORIGINAL_DISPLAY", env.get("DISPLAY", ""))
            _set_or_unset(env, "DISPLAY", ":0", notes)
        has_x11 = bool(env.get("DISPLAY"))
        platform_root = _root(env.get("QT_QPA_PLATFORM", ""))

        if has_wayland and (wants_visible or gnome):
            # 0.10.13 deliberately mirrors the GNOME menu launch again.  The
            # menu path was confirmed visible by the user with DISPLAY=:0 and
            # QT_QPA_PLATFORM=wayland;xcb.  Earlier pure-Wayland forcing could
            # make shell starts worse on systems where the shell had a stale
            # DISPLAY but the session manager had the right one.
            desired_platform = env.get("NOTIZEN_QPA_PLATFORM") or _GNOME_MENU_COMPAT_QPA
            if not env.get("QT_QPA_PLATFORM") or platform_root in _DANGEROUS_QPA_ROOTS or env.get("QT_QPA_PLATFORM") != desired_platform:
                _set_or_unset(env, "QT_QPA_PLATFORM", desired_platform, notes)
            if _root(env.get("GDK_BACKEND", "")) == "x11":
                _set_or_unset(env, "GDK_BACKEND", None, notes)
        elif has_x11 and platform_root in _DANGEROUS_QPA_ROOTS and wants_visible:
            _set_or_unset(env, "QT_QPA_PLATFORM", "xcb", notes)

        theme_root = _root(env.get("QT_QPA_PLATFORMTHEME", ""))
        if has_wayland and (wants_visible or gnome) and theme_root in _GTK_PLATFORM_THEMES:
            _set_or_unset(env, "QT_QPA_PLATFORMTHEME", None, notes)

    platform_after = env.get("QT_QPA_PLATFORM", "")
    theme_after = env.get("QT_QPA_PLATFORMTHEME", "")
    display_after = env.get("DISPLAY", "")
    wayland_after = env.get("WAYLAND_DISPLAY", "")
    gdk_after = env.get("GDK_BACKEND", "")
    changed = any(
        before != after
        for before, after in (
            (platform_before, platform_after),
            (theme_before, theme_after),
            (display_before, display_after),
            (wayland_before, wayland_after),
            (gdk_before, gdk_after),
        )
    )
    if notes:
        env["NOTIZEN_DISPLAY_ENV_NOTES"] = "; ".join(notes)
    return DisplayEnvironmentDecision(
        changed,
        platform_before,
        platform_after,
        theme_before,
        theme_after,
        display_before,
        display_after,
        wayland_before,
        wayland_after,
        gdk_before,
        gdk_after,
        tuple(notes),
    )


def default_startup_log_path(env: MutableMapping[str, str] | None = None) -> Path:
    env = env if env is not None else os.environ
    state_home = env.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state_home) / "notizen-py-qt" / "startup.log"


def append_startup_log(message: str, env: MutableMapping[str, str] | None = None) -> None:
    """Best-effort append for launcher/app diagnostics."""

    env = env if env is not None else os.environ
    target = env.get("NOTIZEN_STARTUP_LOG") or str(default_startup_log_path(env))
    try:
        path = Path(target).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip("\n") + "\n")
    except Exception:
        pass
