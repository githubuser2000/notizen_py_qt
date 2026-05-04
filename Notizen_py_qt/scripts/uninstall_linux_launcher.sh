#!/usr/bin/env bash
set -euo pipefail
XDG_DATA_HOME_VALUE="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DESKTOP_DIR="$XDG_DATA_HOME_VALUE/applications"
ICON_DIR="$XDG_DATA_HOME_VALUE/icons/hicolor/256x256/apps"
MIME_PACKAGE_DIR="$XDG_DATA_HOME_VALUE/mime/packages"
DESKTOP_TARGET="$APP_DESKTOP_DIR/notizen-py-qt.desktop"
MIME_TARGET="$MIME_PACKAGE_DIR/notizen-py-qt.xml"
ICON_TARGET="$ICON_DIR/notizen-py-qt.png"
rm -f "$DESKTOP_TARGET" "$MIME_TARGET" "$ICON_TARGET"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DESKTOP_DIR" >/dev/null 2>&1 || true
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database "$XDG_DATA_HOME_VALUE/mime" >/dev/null 2>&1 || true
fi
if command -v gio >/dev/null 2>&1; then
    gio mime application/x-notizen-alx >/dev/null 2>&1 || true
fi
printf 'Notizen-PyQt-Starter/MIME-Dateien entfernt, soweit vorhanden.\n'
printf 'Entfernt: %s\n' "$DESKTOP_TARGET"
printf 'Entfernt: %s\n' "$MIME_TARGET"
printf 'Entfernt: %s\n' "$ICON_TARGET"
