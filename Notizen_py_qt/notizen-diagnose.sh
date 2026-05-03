#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
LOG_DIR="$STATE_HOME/notizen-py-qt"
LOG_FILE="$LOG_DIR/diagnose.log"
mkdir -p "$LOG_DIR"
set +e
{
    printf '%s\n' "--- Notizen PyQt Diagnose $(date -Is 2>/dev/null || date) ---"
    printf 'PWD=%s\nAPPDIR=%s\n' "$PWD" "$APPDIR"
    printf 'XDG_CURRENT_DESKTOP=%s\nXDG_SESSION_DESKTOP=%s\nWAYLAND_DISPLAY=%s\nDISPLAY=%s\n' "${XDG_CURRENT_DESKTOP:-}" "${XDG_SESSION_DESKTOP:-}" "${WAYLAND_DISPLAY:-}" "${DISPLAY:-}"
    command -v python3 || true
    python3 --version || true
    "$APPDIR/notizen-starten.sh" --show --no-tray --reset-window "$@"
} >"$LOG_FILE" 2>&1
status=$?
set -e
printf 'Diagnoseprotokoll: %s\n' "$LOG_FILE"
exit "$status"
