#!/usr/bin/env bash
set -euo pipefail

APPDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
LOG_DIR="$STATE_HOME/notizen-py-qt"
LOG_FILE="$LOG_DIR/startup.log"
mkdir -p "$LOG_DIR"
export NOTIZEN_STARTUP_LOG="$LOG_FILE"

SMOKE_TEST=0
for arg in "$@"; do
    if [[ "$arg" == "--smoke-test" ]]; then
        SMOKE_TEST=1
        break
    fi
done

if [[ "$SMOKE_TEST" == 1 ]]; then
    export NOTIZEN_QT_SMOKE_TEST=1
    unset NOTIZEN_FORCE_VISIBLE || true
    unset NOTIZEN_RESET_WINDOW || true
else
    export NOTIZEN_FORCE_VISIBLE=1
    export NOTIZEN_RESET_WINDOW=1
fi

show_error() {
    local message="$1"
    # Interactive terminals should receive text only.  Starting zenity/kdialog
    # from a terminal with a stale DISPLAY is exactly what produced misleading
    # Gtk "cannot open display" warnings in the GNOME bug report.
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

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES|on|ON|ja|JA) return 0 ;;
        *) return 1 ;;
    esac
}

repair_display_from_session() {
    if is_truthy "${NOTIZEN_KEEP_QT_ENV:-}" || is_truthy "${NOTIZEN_KEEP_DISPLAY:-}"; then
        return 0
    fi
    command -v systemctl >/dev/null 2>&1 || return 0

    local session_env
    session_env="$(systemctl --user show-environment 2>/dev/null || true)"
    [[ -n "$session_env" ]] || return 0

    local line key value old notes=""
    while IFS= read -r line; do
        [[ "$line" == *=* ]] || continue
        key="${line%%=*}"
        value="${line#*=}"
        [[ -n "$value" ]] || continue
        case "$key" in
            DISPLAY|WAYLAND_DISPLAY|XDG_CURRENT_DESKTOP|XDG_SESSION_DESKTOP|XDG_RUNTIME_DIR)
                case "$key" in
                    DISPLAY) old="${DISPLAY:-}" ;;
                    WAYLAND_DISPLAY) old="${WAYLAND_DISPLAY:-}" ;;
                    XDG_CURRENT_DESKTOP) old="${XDG_CURRENT_DESKTOP:-}" ;;
                    XDG_SESSION_DESKTOP) old="${XDG_SESSION_DESKTOP:-}" ;;
                    XDG_RUNTIME_DIR) old="${XDG_RUNTIME_DIR:-}" ;;
                esac
                if [[ "$old" != "$value" ]]; then
                    export "$key=$value"
                    notes+="$key:${old:-<unset>}->$value "
                fi
                ;;
        esac
    done <<<"$session_env"
    if [[ -n "$notes" ]]; then
        export NOTIZEN_DISPLAY_REPAIRED="$notes"
    fi
}

sanitize_qt_env() {
    if is_truthy "${NOTIZEN_KEEP_QT_ENV:-}"; then
        return 0
    fi

    local current="${QT_QPA_PLATFORM:-}"
    local current_lc="${current,,}"
    current_lc="${current_lc%%;*}"
    current_lc="${current_lc%%:*}"

    local theme="${QT_QPA_PLATFORMTHEME:-}"
    local theme_lc="${theme,,}"
    theme_lc="${theme_lc%%;*}"
    theme_lc="${theme_lc%%:*}"

    if [[ "$SMOKE_TEST" == 1 ]]; then
        export QT_QPA_PLATFORM="offscreen"
        unset DISPLAY || true
        unset WAYLAND_DISPLAY || true
        unset GDK_BACKEND || true
        case "$theme_lc" in
            gtk2|gtk3) unset QT_QPA_PLATFORMTHEME || true ;;
        esac
        return 0
    fi

    if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
        # 0.10.13 mirrors the GNOME menu launch that was confirmed visible:
        # keep the repaired session DISPLAY (usually :0) and use wayland;xcb.
        # The earlier pure-wayland/unset-DISPLAY path could regress shell
        # starts on systems where systemd already knew the correct display.
        export QT_QPA_PLATFORM="${NOTIZEN_QPA_PLATFORM:-wayland;xcb}"
        case "$theme_lc" in
            gtk2|gtk3) unset QT_QPA_PLATFORMTHEME || true ;;
        esac
        case "${GDK_BACKEND,,}" in
            x11) unset GDK_BACKEND || true ;;
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
if [[ "$SMOKE_TEST" != 1 ]]; then
    repair_display_from_session
fi
if [[ "$SMOKE_TEST" != 1 && -n "${WAYLAND_DISPLAY:-}" && "${XDG_CURRENT_DESKTOP,,}${XDG_SESSION_DESKTOP,,}" == *gnome* && ( "${DISPLAY:-}" == ":1" || "${DISPLAY:-}" == ":1.0" ) ]]; then
    if ! is_truthy "${NOTIZEN_KEEP_DISPLAY:-}" && ! is_truthy "${NOTIZEN_KEEP_SHELL_DISPLAY:-}"; then
        export NOTIZEN_ORIGINAL_DISPLAY="${NOTIZEN_ORIGINAL_DISPLAY:-$DISPLAY}"
        export DISPLAY=":0"
        export NOTIZEN_DISPLAY_REPAIRED="${NOTIZEN_DISPLAY_REPAIRED:-} DISPLAY:${NOTIZEN_ORIGINAL_DISPLAY}->:0"
    fi
fi
sanitize_qt_env

{
    printf '%s\n' "--- Notizen PyQt startup $(date -Is 2>/dev/null || date) ---"
    printf 'APPDIR=%s\nPYTHON=%s\n' "$APPDIR" "$PYTHON_BIN"
    printf 'PWD=%s\nXDG_CURRENT_DESKTOP=%s\nXDG_SESSION_DESKTOP=%s\nWAYLAND_DISPLAY=%s\nDISPLAY=%s\nORIGINAL_DISPLAY=%s\nGDK_BACKEND=%s\nDISPLAY_REPAIRED=%s\n' \
        "$PWD" "${XDG_CURRENT_DESKTOP:-}" "${XDG_SESSION_DESKTOP:-}" "${WAYLAND_DISPLAY:-}" "${DISPLAY:-}" "${NOTIZEN_ORIGINAL_DISPLAY:-}" "${GDK_BACKEND:-}" "${NOTIZEN_DISPLAY_REPAIRED:-}"
    printf 'QT_QPA_PLATFORM=%s\nQT_QPA_PLATFORMTHEME=%s\nPYTHONPATH=%s\n' \
        "${QT_QPA_PLATFORM:-}" "${QT_QPA_PLATFORMTHEME:-}" "$PYTHONPATH"
} >>"$LOG_FILE" 2>&1

# Log exactly which local package will be used. This catches old editable
# installs or mixed source folders without importing Qt.
"$PYTHON_BIN" - <<'NOTIZEN_VERSION_LOG' >>"$LOG_FILE" 2>&1 || true
import importlib, os, sys
try:
    mod = importlib.import_module("notizen_py_qt")
    print("PACKAGE_VERSION=%s" % getattr(mod, "__version__", "?"))
    print("PACKAGE_FILE=%s" % getattr(mod, "__file__", "?"))
    print("PYTHON_EXECUTABLE=%s" % sys.executable)
except Exception as exc:
    print("PACKAGE_IMPORT_FOR_LOG_FAILED=%s" % exc)
NOTIZEN_VERSION_LOG

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
            # Added below once. Clean logs make diagnosing GNOME starts easier.
            ;;
        *)
            args+=("$arg")
            ;;
    esac
done

prefix=()
if [[ "$SMOKE_TEST" != 1 && "$force_visible" == 1 ]]; then
    prefix+=(--show)
    prefix+=(--reset-window)
fi
if [[ "$SMOKE_TEST" != 1 && "$force_no_tray" == 1 ]]; then
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
