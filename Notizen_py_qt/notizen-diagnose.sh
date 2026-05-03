#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
LOG_DIR="$STATE_HOME/notizen-py-qt"
LOG_FILE="$LOG_DIR/diagnose.log"
START_LOG="$LOG_DIR/startup.log"
mkdir -p "$LOG_DIR"

PYTHON_BIN="${PYTHON:-}"
if [[ -z "$PYTHON_BIN" ]]; then
    if [[ -x "$APPDIR/.venv/bin/python" ]]; then
        PYTHON_BIN="$APPDIR/.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python)"
    else
        PYTHON_BIN="python3"
    fi
fi

run_with_timeout() {
    local seconds="$1"
    shift
    if command -v timeout >/dev/null 2>&1; then
        timeout -k 2s "$seconds" "$@"
    else
        "$@"
    fi
}

launch_visible=0
args=()
for arg in "$@"; do
    case "$arg" in
        --launch|--launch-visible)
            launch_visible=1
            ;;
        *)
            args+=("$arg")
            ;;
    esac
done

set +e
{
    printf '%s\n' "--- Notizen PyQt Diagnose $(date -Is 2>/dev/null || date) ---"
    printf 'PWD=%s\nAPPDIR=%s\n' "$PWD" "$APPDIR"
    printf 'XDG_CURRENT_DESKTOP=%s\nXDG_SESSION_DESKTOP=%s\nWAYLAND_DISPLAY=%s\nDISPLAY=%s\nGDK_BACKEND=%s\n' \
        "${XDG_CURRENT_DESKTOP:-}" "${XDG_SESSION_DESKTOP:-}" "${WAYLAND_DISPLAY:-}" "${DISPLAY:-}" "${GDK_BACKEND:-}"
    printf 'QT_QPA_PLATFORM=%s\nQT_QPA_PLATFORMTHEME=%s\nPYTHON=%s\n' "${QT_QPA_PLATFORM:-}" "${QT_QPA_PLATFORMTHEME:-}" "$PYTHON_BIN"
    if command -v systemctl >/dev/null 2>&1; then
        printf '\n## systemd user display environment\n'
        systemctl --user show-environment 2>/dev/null | grep -E '^(DISPLAY|WAYLAND_DISPLAY|XDG_CURRENT_DESKTOP|XDG_SESSION_DESKTOP|XDG_RUNTIME_DIR)=' || true
    fi
    "$PYTHON_BIN" --version || true
    printf '\n## package import\n'
    run_with_timeout 10s env \
        PYTHONPATH="$APPDIR/src${PYTHONPATH:+:$PYTHONPATH}" \
        "$PYTHON_BIN" -c 'import importlib; pkg=importlib.import_module("notizen_py_qt"); print("notizen_py_qt", getattr(pkg,"__version__","?"), getattr(pkg,"__file__","?"))' || true
    printf '\n## display normalization dry run\n'
    run_with_timeout 10s env \
        PYTHONPATH="$APPDIR/src${PYTHONPATH:+:$PYTHONPATH}" \
        "$PYTHON_BIN" - <<'PY' || true
import os
from notizen_py_qt.display_env import normalize_qt_display_environment
env = dict(os.environ)
result = normalize_qt_display_environment(["--show", "--no-tray", "--reset-window"], env)
print(result.summary())
print("after DISPLAY=", env.get("DISPLAY", ""))
print("after WAYLAND_DISPLAY=", env.get("WAYLAND_DISPLAY", ""))
print("after GDK_BACKEND=", env.get("GDK_BACKEND", ""))
PY
    printf '\n## Qt binding import\n'
    run_with_timeout 10s env \
        PYTHONPATH="$APPDIR/src${PYTHONPATH:+:$PYTHONPATH}" \
        "$PYTHON_BIN" -c 'from notizen_py_qt.qt_compat import load_qt; binding, QtCore, QtGui, QtWidgets = load_qt(); print(binding); print(QtCore.qVersion())' || true
    printf '\n## offscreen smoke test, bounded and headless\n'
    run_with_timeout 10s env \
        -u DISPLAY \
        -u WAYLAND_DISPLAY \
        -u GDK_BACKEND \
        -u QT_QPA_PLATFORMTHEME \
        PYTHONPATH="$APPDIR/src${PYTHONPATH:+:$PYTHONPATH}" \
        QT_QPA_PLATFORM=offscreen \
        QT_STYLE_OVERRIDE=Fusion \
        NOTIZEN_QT_SMOKE_TEST=1 \
        NOTIZEN_NO_GUI_ERROR=1 \
        NOTIZEN_STARTUP_LOG="$START_LOG" \
        "$PYTHON_BIN" -m notizen_py_qt --smoke-test
    smoke_status=$?
    printf 'offscreen_smoke_status=%s\n' "$smoke_status"
    if [[ "$launch_visible" == 1 ]]; then
        printf '\n## visible launch requested, this will stay running until the app exits\n'
        "$APPDIR/notizen-starten.sh" "${args[@]}"
    fi
} >"$LOG_FILE" 2>&1
status=$?
set -e
printf 'Diagnoseprotokoll: %s\n' "$LOG_FILE"
printf 'Startprotokoll: %s\n' "$START_LOG"
if [[ "$launch_visible" != 1 ]]; then
    printf 'Hinweis: Diagnose startet die GUI nicht mehr dauerhaft. Für einen sichtbaren Test: %s --launch\n' "$0"
fi
exit "$status"
