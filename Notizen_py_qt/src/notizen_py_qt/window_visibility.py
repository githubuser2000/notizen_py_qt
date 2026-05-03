from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

_TRUE_VALUES = {"1", "true", "yes", "on", "ja"}


@dataclass(frozen=True, slots=True)
class VisibleWindowGeometry:
    """Sanitized main-window geometry that should be reachable on screen."""

    x: int
    y: int
    width: int
    height: int
    reset: bool = False


def _as_int(value: object, fallback: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return fallback


def _env_flag(env: Mapping[str, str] | None, name: str) -> bool:
    if env is None:
        import os

        env = os.environ
    return str(env.get(name, "")).strip().casefold() in _TRUE_VALUES


def env_requests_window_reset(env: Mapping[str, str] | None = None) -> bool:
    """Return True when the launcher/user requests a fresh visible position."""

    return _env_flag(env, "NOTIZEN_RESET_WINDOW") or _env_flag(env, "NOTIZEN_FORCE_VISIBLE")


def sanitize_legacy_window_geometry(
    *,
    x: object,
    y: object,
    width: object,
    height: object,
    screen_left: int = 0,
    screen_top: int = 0,
    screen_width: int = 1280,
    screen_height: int = 800,
    default_x_offset: int = 60,
    default_y_offset: int = 60,
    default_width: int = 1000,
    default_height: int = 700,
    min_width: int = 640,
    min_height: int = 420,
    force_reset: bool = False,
) -> VisibleWindowGeometry:
    """Clamp old Notizen.NET window settings to a visible desktop area.

    The legacy config stores absolute coordinates.  On GNOME, especially after
    monitor changes, Wayland/X11 differences, or a previously used second
    monitor, these values can place the window outside the current work area.
    Older PyQt port versions only handled coordinates too far to the right or
    bottom.  This helper also fixes negative/off-left/off-top positions and
    absurd sizes, and it gives the launcher a hard reset path.
    """

    left = _as_int(screen_left, 0)
    top = _as_int(screen_top, 0)
    sw = max(320, _as_int(screen_width, 1280))
    sh = max(240, _as_int(screen_height, 800))
    right = left + sw
    bottom = top + sh

    dw = min(max(min_width, _as_int(default_width, 1000)), sw)
    dh = min(max(min_height, _as_int(default_height, 700)), sh)
    default_x = min(max(left, left + default_x_offset), max(left, right - dw))
    default_y = min(max(top, top + default_y_offset), max(top, bottom - dh))

    if force_reset:
        return VisibleWindowGeometry(default_x, default_y, dw, dh, reset=True)

    w = max(min_width, _as_int(width, dw))
    h = max(min_height, _as_int(height, dh))
    w = min(w, sw)
    h = min(h, sh)
    px = _as_int(x, default_x)
    py = _as_int(y, default_y)

    # Require at least a small part of the title bar/client area to be reachable.
    visible_margin = 50
    offscreen = (
        px < left - (w - visible_margin)
        or py < top - (h - visible_margin)
        or px > right - visible_margin
        or py > bottom - visible_margin
    )
    if offscreen:
        return VisibleWindowGeometry(default_x, default_y, w, h, reset=True)

    clamped_x = min(max(px, left), max(left, right - visible_margin))
    clamped_y = min(max(py, top), max(top, bottom - visible_margin))
    # If the window is larger than the available area, put it at the work-area
    # origin after size capping so GNOME can decorate and manage it normally.
    if clamped_x + w > right:
        clamped_x = max(left, right - w)
    if clamped_y + h > bottom:
        clamped_y = max(top, bottom - h)

    return VisibleWindowGeometry(clamped_x, clamped_y, w, h, reset=(clamped_x != px or clamped_y != py))


def legacy_window_state_is_restorable(x: object, y: object) -> bool:
    """Return whether Notizen.NET would apply stored main-form state.

    The old VB.NET constructor only restored size/location/windowstate when both
    coordinates were non-zero.  The default config contains x=0, y=0 and
    windowstate=minimized; treating that as a real minimized request makes the
    Python port start invisibly on first launch.
    """

    return _as_int(x, 0) != 0 and _as_int(y, 0) != 0


def should_start_minimized(
    *,
    explicit_minimized: bool = False,
    legacy_minimized: bool = False,
    stored_window_state: str = "Normal",
    force_visible: bool = False,
    reset_window: bool = False,
    stored_state_restorable: bool = True,
) -> bool:
    """Return whether startup should begin minimized/hidden.

    ``--show`` and ``--reset-window`` are stronger than the legacy saved
    ``Minimized`` state because on GNOME that state can make the app look dead.
    """

    if force_visible or reset_window:
        return False
    stored_minimized = stored_state_restorable and str(stored_window_state).casefold() == "minimized"
    return bool(explicit_minimized or legacy_minimized or stored_minimized)
