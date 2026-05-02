#!/usr/bin/env bash
set -euo pipefail

show_error() {
    local message="$1"
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --title="Notizen PyQt" --text="$message" || true
    elif command -v kdialog >/dev/null 2>&1; then
        kdialog --error "$message" --title "Notizen PyQt" || true
    elif command -v notify-send >/dev/null 2>&1; then
        notify-send "Notizen PyQt" "$message" || true
    fi
    printf '%s\n' "$message" >&2
}

APPDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

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
        *)
            args+=("$arg")
            ;;
    esac
done

prefix=()
if [[ "$force_visible" == 1 ]]; then
    prefix+=(--show)
fi
if [[ "$force_no_tray" == 1 ]]; then
    prefix+=(--no-tray)
fi

exec "$PYTHON_BIN" -m notizen_py_qt "${prefix[@]}" "${args[@]}"
