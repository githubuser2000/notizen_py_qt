#!/usr/bin/env bash
set -euo pipefail

APPDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
LOG_DIR="$STATE_HOME/notizen-py-qt"
LOG_FILE="$LOG_DIR/startup.log"
mkdir -p "$LOG_DIR"
export NOTIZEN_STARTUP_LOG="$LOG_FILE"
export NOTIZEN_FORCE_VISIBLE=1
export NOTIZEN_RESET_WINDOW=1

show_error() {
    local message="$1"
    # In an interactive terminal the text error is clearer and avoids misleading
    # Gtk "cannot open display" warnings from zenity/kdialog.  GUI dialogs are
    # only tried for menu/desktop starts where there is no terminal output.
    if [[ ! -t 2 && -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" && -z "${NOTIZEN_NO_GUI_ERROR:-}" ]]; then
        if command -v zenity >/dev/null 2>&1; then
            GDK_BACKEND="${GDK_BACKEND:-wayland,x11}" zenity --error --title="Notizen PyQt" --text="$message" || true
        elif command -v kdialog >/dev/null 2>&1; then
            kdialog --error "$message" --title "Notizen PyQt" || true
        elif command -v notify-send >/dev/null 2>&1; then
            notify-send "Notizen PyQt" "$message" || true
        fi
    fi
    printf '%s\n' "$message" >&2
}

sanitize_qt_env() {
    if [[ "${NOTIZEN_KEEP_QT_ENV:-}" =~ ^(1|true|TRUE|yes|YES|on|ON|ja|JA)$ ]]; then
        return 0
    fi

    local current="${QT_QPA_PLATFORM:-}"
    local current_lc="${current,,}"
    current_lc="${current_lc%%;*}"
    current_lc="${current_lc%%:*}"

    if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
        case "$current_lc" in
            ""|xcb|offscreen|minimal|minimalegl|vnc|eglfs|linuxfb|directfb|webgl)
                export QT_QPA_PLATFORM="wayland;xcb"
                ;;
        esac
        local theme="${QT_QPA_PLATFORMTHEME:-}"
        local theme_lc="${theme,,}"
        theme_lc="${theme_lc%%;*}"
        theme_lc="${theme_lc%%:*}"
        case "$theme_lc" in
            gtk2|gtk3)
                unset QT_QPA_PLATFORMTHEME
                ;;
        esac
    elif [[ -n "${DISPLAY:-}" ]]; then
        case "$current_lc" in
            offscreen|minimal|minimalegl|vnc|eglfs|linuxfb|directfb|webgl)
                export QT_QPA_PLATFORM="xcb"
                ;;
        esac
    fi
}

if [[ -n "${PYTHON:-}" ]]; then
    PYTHON_BIN="$PYTHON"
elif [[ -x "$APPDIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$APPDIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    show_error "Python wurde nicht gefunden. Installiere Python 3.10 oder neuer und starte diese Datei erneut."
    exit 127
fi

export PYTHONPATH="$APPDIR/src${PYTHONPATH:+:$PYTHONPATH}"
sanitize_qt_env

{
    printf '%s\n' "--- Notizen PyQt startup $(date -Is 2>/dev/null || date) ---"
    printf 'APPDIR=%s\nPYTHON=%s\n' "$APPDIR" "$PYTHON_BIN"
    printf 'PWD=%s\nXDG_CURRENT_DESKTOP=%s\nXDG_SESSION_DESKTOP=%s\nWAYLAND_DISPLAY=%s\nDISPLAY=%s\n' \
        "$PWD" "${XDG_CURRENT_DESKTOP:-}" "${XDG_SESSION_DESKTOP:-}" "${WAYLAND_DISPLAY:-}" "${DISPLAY:-}"
    printf 'QT_QPA_PLATFORM=%s\nQT_QPA_PLATFORMTHEME=%s\nPYTHONPATH=%s\n' \
        "${QT_QPA_PLATFORM:-}" "${QT_QPA_PLATFORMTHEME:-}" "$PYTHONPATH"
} >>"$LOG_FILE" 2>&1

if ! "$PYTHON_BIN" - <<'NOTIZEN_QT_CHECK' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if (importlib.util.find_spec("PySide6") or importlib.util.find_spec("PyQt6")) else 1)
NOTIZEN_QT_CHECK
then
    missing_qt_message="$(cat <<EOF
Qt für Python fehlt. Installiere es mit:

$PYTHON_BIN -m pip install --user 'PySide6>=6.6,<7'

Optional für alte verschlüsselte ALX-Dateien:
$PYTHON_BIN -m pip install --user pycryptodome
EOF
)"
    show_error "$missing_qt_message"
    exit 2
fi

force_visible=1
force_no_tray=1
args=()
for arg in "$@"; do
    case "$arg" in
        --allow-tray|--tray)
            force_no_tray=0
            ;;
        --keep-start-state|--keep-window-state)
            force_visible=0
            ;;
        --show|--visible|--reset-window|--no-tray)
            # Added below once.  Repeating them is harmless, but clean logs make
            # diagnosing GNOME starts easier.
            ;;
        *)
            args+=("$arg")
            ;;
    esac
done

prefix=()
if [[ "$force_visible" == 1 ]]; then
    prefix+=(--show)
    prefix+=(--reset-window)
fi
if [[ "$force_no_tray" == 1 ]]; then
    prefix+=(--no-tray)
fi

{
    printf 'ARGS='
    printf '%q ' "${prefix[@]}" "${args[@]}"
    printf '\n'
} >>"$LOG_FILE" 2>&1

if [[ -t 1 ]]; then
    exec "$PYTHON_BIN" -m notizen_py_qt "${prefix[@]}" "${args[@]}"
fi

set +e
"$PYTHON_BIN" -m notizen_py_qt "${prefix[@]}" "${args[@]}" >>"$LOG_FILE" 2>&1
status=$?
set -e
if [[ "$status" != 0 ]]; then
    show_error "Notizen PyQt konnte nicht gestartet werden. Diagnoseprotokoll: $LOG_FILE"
fi
exit "$status"
