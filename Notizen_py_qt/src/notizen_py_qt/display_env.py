from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import MutableMapping, Sequence
import os
import sys

_TRUE_VALUES = {"1", "true", "yes", "on", "ja"}
_DANGEROUS_QPA_ROOTS = {"offscreen", "minimal", "minimalegl", "vnc", "eglfs", "linuxfb", "directfb", "webgl"}
_GTK_PLATFORM_THEMES = {"gtk2", "gtk3"}
_VISIBLE_FLAGS = {"--show", "--visible", "--reset-window", "--no-tray"}


@dataclass(frozen=True, slots=True)
class DisplayEnvironmentDecision:
    """Qt display-environment changes made before importing Qt.

    The shell problem reported for GNOME was not a tray problem anymore: the
    menu launcher showed a window, but terminal starts inherited a display
    environment that could make Qt use an invisible/broken backend.  This
    structure is intentionally tiny and testable so the decision can run before
    PySide/PyQt is imported.
    """

    changed: bool
    platform_before: str
    platform_after: str
    theme_before: str
    theme_after: str
    notes: tuple[str, ...] = ()

    def summary(self) -> str:
        items = [
            f"changed={int(self.changed)}",
            f"QT_QPA_PLATFORM={self.platform_after or '<unset>'}",
            f"QT_QPA_PLATFORMTHEME={self.theme_after or '<unset>'}",
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


def visible_start_requested(argv: Sequence[str] | None = None, env: MutableMapping[str, str] | None = None) -> bool:
    """Return whether startup must prefer a real visible window.

    ``--no-tray`` is included because a terminal user who disables the tray must
    not end up with a headless/offscreen Qt platform.  The launcher also sets
    ``NOTIZEN_FORCE_VISIBLE`` so shell scripts and direct module starts share the
    same safety path.
    """

    env = env if env is not None else os.environ
    args = list(sys.argv[1:] if argv is None else argv)
    if any(arg in _VISIBLE_FLAGS for arg in args):
        return True
    return _truthy(env.get("NOTIZEN_FORCE_VISIBLE")) or _truthy(env.get("NOTIZEN_RESET_WINDOW")) or _truthy(env.get("NOTIZEN_SAFE_DISPLAY"))


def normalize_qt_display_environment(
    argv: Sequence[str] | None = None,
    env: MutableMapping[str, str] | None = None,
) -> DisplayEnvironmentDecision:
    """Sanitize Qt display variables before importing PySide/PyQt.

    GNOME menu launches and terminal launches can inherit different environment
    variables.  A terminal can contain ``QT_QPA_PLATFORM=xcb`` while only the
    Wayland socket is usable, or ``QT_QPA_PLATFORM=offscreen/minimal`` from a
    previous debug session.  Either case makes ``--show`` powerless because Qt
    never creates a visible platform window.  The old Notizen.NET application had
    no equivalent backend choice, so the Python port should choose the visible
    GNOME backend unless the user explicitly opts out with ``NOTIZEN_KEEP_QT_ENV``.
    """

    env = env if env is not None else os.environ
    platform_before = env.get("QT_QPA_PLATFORM", "")
    theme_before = env.get("QT_QPA_PLATFORMTHEME", "")
    notes: list[str] = []

    if _truthy(env.get("NOTIZEN_KEEP_QT_ENV")):
        return DisplayEnvironmentDecision(False, platform_before, platform_before, theme_before, theme_before, ("kept by NOTIZEN_KEEP_QT_ENV",))

    wants_visible = visible_start_requested(argv, env)
    gnome = _desktop_is_gnome(env)
    has_wayland = bool(env.get("WAYLAND_DISPLAY"))
    has_x11 = bool(env.get("DISPLAY"))
    platform_root = _root(platform_before)

    if has_wayland and (wants_visible or gnome):
        if not platform_before or platform_root in _DANGEROUS_QPA_ROOTS or platform_root == "xcb":
            env["QT_QPA_PLATFORM"] = "wayland;xcb"
            if platform_before:
                notes.append(f"QT_QPA_PLATFORM {platform_before!r} -> 'wayland;xcb'")
            else:
                notes.append("QT_QPA_PLATFORM set to 'wayland;xcb'")
    elif has_x11 and platform_root in _DANGEROUS_QPA_ROOTS and wants_visible:
        env["QT_QPA_PLATFORM"] = "xcb"
        notes.append(f"QT_QPA_PLATFORM {platform_before!r} -> 'xcb'")

    theme_root = _root(theme_before)
    if has_wayland and (wants_visible or gnome) and theme_root in _GTK_PLATFORM_THEMES:
        env.pop("QT_QPA_PLATFORMTHEME", None)
        notes.append(f"QT_QPA_PLATFORMTHEME {theme_before!r} unset")

    platform_after = env.get("QT_QPA_PLATFORM", "")
    theme_after = env.get("QT_QPA_PLATFORMTHEME", "")
    changed = platform_before != platform_after or theme_before != theme_after
    if notes:
        env["NOTIZEN_DISPLAY_ENV_NOTES"] = "; ".join(notes)
    return DisplayEnvironmentDecision(changed, platform_before, platform_after, theme_before, theme_after, tuple(notes))


def default_startup_log_path(env: MutableMapping[str, str] | None = None) -> Path:
    env = env if env is not None else os.environ
    state_home = env.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state_home) / "notizen-py-qt" / "startup.log"


def append_startup_log(message: str, env: MutableMapping[str, str] | None = None) -> None:
    """Best-effort append for launcher/app diagnostics.

    The function is intentionally silent on failure; startup logging must never
    be the reason the notes window does not open.
    """

    env = env if env is not None else os.environ
    target = env.get("NOTIZEN_STARTUP_LOG") or str(default_startup_log_path(env))
    try:
        path = Path(target).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip("\n") + "\n")
    except Exception:
        pass
