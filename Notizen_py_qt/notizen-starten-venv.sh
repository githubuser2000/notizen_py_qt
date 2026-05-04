#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BOOTSTRAP="${PYTHON_BOOTSTRAP:-python3}"
VENV_DIR="${NOTIZEN_VENV_DIR:-$APPDIR/.venv}"
VENV_PYTHON="$VENV_DIR/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Erstelle lokale Python-Umgebung: $VENV_DIR" >&2
    "$PYTHON_BOOTSTRAP" -m venv "$VENV_DIR"
    "$VENV_PYTHON" -m pip install --upgrade pip
    "$VENV_PYTHON" -m pip install -e "$APPDIR[crypto]"
fi

export PYTHON="$VENV_PYTHON"
exec "$APPDIR/notizen-starten.sh" "$@"
