#!/usr/bin/env bash
set -euo pipefail

APPDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
XDG_DATA_HOME_VALUE="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DESKTOP_DIR="$XDG_DATA_HOME_VALUE/applications"
ICON_DIR="$XDG_DATA_HOME_VALUE/icons/hicolor/256x256/apps"
DESKTOP_TARGET="$APP_DESKTOP_DIR/notizen-py-qt.desktop"
ICON_TARGET="$ICON_DIR/notizen-py-qt.png"
INSTALL_DESKTOP_SHORTCUT=0

for arg in "$@"; do
    case "$arg" in
        --desktop|--schreibtisch)
            INSTALL_DESKTOP_SHORTCUT=1
            ;;
        -h|--help)
            cat <<'NOTIZEN_LAUNCHER_HELP'
Installiert einen GNOME/Linux-Starter für Notizen PyQt.

Aufruf:
  scripts/install_linux_launcher.sh [--desktop]

Ohne Option wird ein Eintrag im Anwendungsmenü installiert.
Mit --desktop wird zusätzlich eine anklickbare Datei auf dem Desktop/Schreibtisch abgelegt.
NOTIZEN_LAUNCHER_HELP
            exit 0
            ;;
        *)
            printf 'Unbekannte Option: %s\n' "$arg" >&2
            exit 2
            ;;
    esac
done

escape_desktop_arg() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    printf '"%s"' "$value"
}

mkdir -p "$APP_DESKTOP_DIR" "$ICON_DIR"
cp "$APPDIR/src/notizen_py_qt/resources/notizen.png" "$ICON_TARGET"

EXEC_PATH="$(escape_desktop_arg "$APPDIR/notizen-starten.sh")"
cat > "$DESKTOP_TARGET" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Notizen PyQt
GenericName=Notizenverwaltung
Comment=Notizen.NET Python/Qt-Port sichtbar starten
Exec=$EXEC_PATH --show --no-tray %f
Icon=notizen-py-qt
Terminal=false
Categories=Utility;TextEditor;Office;
StartupNotify=true
MimeType=application/x-notizen-alx;
EOF
chmod 0644 "$DESKTOP_TARGET"
chmod 0755 "$APPDIR/notizen-starten.sh" "$APPDIR/Notizen starten.sh"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DESKTOP_DIR" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q "$XDG_DATA_HOME_VALUE/icons/hicolor" >/dev/null 2>&1 || true
fi

if [[ "$INSTALL_DESKTOP_SHORTCUT" == 1 ]]; then
    DESKTOP_DIR="${XDG_DESKTOP_DIR:-}"
    if [[ -z "$DESKTOP_DIR" ]]; then
        if [[ -d "$HOME/Schreibtisch" ]]; then
            DESKTOP_DIR="$HOME/Schreibtisch"
        else
            DESKTOP_DIR="$HOME/Desktop"
        fi
    fi
    mkdir -p "$DESKTOP_DIR"
    DESKTOP_SHORTCUT="$DESKTOP_DIR/Notizen PyQt.desktop"
    cp "$DESKTOP_TARGET" "$DESKTOP_SHORTCUT"
    chmod 0755 "$DESKTOP_SHORTCUT"
    if command -v gio >/dev/null 2>&1; then
        gio set "$DESKTOP_SHORTCUT" metadata::trusted true >/dev/null 2>&1 || true
    fi
    printf 'Desktop-Starter installiert: %s\n' "$DESKTOP_SHORTCUT"
fi

printf 'Anwendungsstarter installiert: %s\n' "$DESKTOP_TARGET"
printf 'Direktstartdatei: %s\n' "$APPDIR/Notizen starten.sh"
