#!/usr/bin/env bash
set -euo pipefail

APPDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
XDG_DATA_HOME_VALUE="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DESKTOP_DIR="$XDG_DATA_HOME_VALUE/applications"
ICON_DIR="$XDG_DATA_HOME_VALUE/icons/hicolor/256x256/apps"
MIME_PACKAGE_DIR="$XDG_DATA_HOME_VALUE/mime/packages"
MIME_TARGET="$MIME_PACKAGE_DIR/notizen-py-qt.xml"
DESKTOP_TARGET="$APP_DESKTOP_DIR/notizen-py-qt.desktop"
STALE_DESKTOP_TARGET="$APP_DESKTOP_DIR/Notizen PyQt.desktop"
ICON_TARGET="$ICON_DIR/notizen-py-qt.png"
INSTALL_DESKTOP_SHORTCUT=0
for arg in "$@"; do
    case "$arg" in
        --desktop|--schreibtisch)
            INSTALL_DESKTOP_SHORTCUT=1
            ;;
        --venv)
            # Kompatibilitätsoption: der GNOME-Menüeintrag startet jetzt bewusst
            # direkt per python3 -m notizen_py_qt, weil Shell-Wrapper mit
            # Anführungszeichen im GNOME-Menü unzuverlässig waren.
            ;;
        -h|--help)
            cat <<'NOTIZEN_LAUNCHER_HELP'
Installiert einen GNOME/Linux-Starter für Notizen PyQt.

Aufruf:
  scripts/install_linux_launcher.sh [--desktop]

Ohne Option wird ein Eintrag im Anwendungsmenü installiert.
Mit --desktop wird zusätzlich eine anklickbare Datei auf dem Desktop/Schreibtisch abgelegt.
Der GNOME-Starter nutzt einen direkten python3-Modulstart ohne Shell-Wrapper.
NOTIZEN_LAUNCHER_HELP
            exit 0
            ;;
        *)
            printf 'Unbekannte Option: %s\n' "$arg" >&2
            exit 2
            ;;
    esac
done

mkdir -p "$APP_DESKTOP_DIR" "$ICON_DIR" "$MIME_PACKAGE_DIR"
cp "$APPDIR/src/notizen_py_qt/resources/notizen.png" "$ICON_TARGET"

cat > "$MIME_TARGET" <<'EOF_MIME'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-notizen-alx">
    <comment>Notizen ALX document</comment>
    <comment xml:lang="de">Notizen-ALX-Datei</comment>
    <glob pattern="*.alx"/>
    <glob pattern="*.ALX"/>
  </mime-type>
</mime-info>
EOF_MIME
chmod 0644 "$MIME_TARGET"

APPDIR_REAL="$(readlink -f "$APPDIR")"
cat > "$DESKTOP_TARGET" <<EOF_DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Notizen PyQt
GenericName=Notizenverwaltung
Comment=Notizen.NET Python/Qt-Port sichtbar starten
Exec=env NOTIZEN_RESET_WINDOW=1 python3 -m notizen_py_qt --show --no-tray --reset-window %f
Path=$APPDIR_REAL
Icon=notizen-py-qt
Terminal=false
Categories=Utility;TextEditor;Office;
StartupNotify=true
StartupWMClass=notizen-py-qt
NoDisplay=false
DBusActivatable=false
MimeType=application/x-notizen-alx;
EOF_DESKTOP
chmod 0644 "$DESKTOP_TARGET"
chmod 0755 "$APPDIR/notizen-starten.sh" "$APPDIR/Notizen starten.sh"
if [[ -f "$APPDIR/notizen-starten-venv.sh" ]]; then
    chmod 0755 "$APPDIR/notizen-starten-venv.sh"
fi

# Der Projektordner enthielt früher eine zweite Menü-Datei mit Leerzeichen im
# Namen. GNOME kann diese stale Kopie weiter anzeigen und dann den falschen
# Exec-Pfad starten. Der Installer entfernt sie bewusst und registriert nur den
# kanonischen Starter.
if [[ "$STALE_DESKTOP_TARGET" != "$DESKTOP_TARGET" ]]; then
    rm -f "$STALE_DESKTOP_TARGET"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DESKTOP_DIR" >/dev/null 2>&1 || true
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database "$XDG_DATA_HOME_VALUE/mime" >/dev/null 2>&1 || true
fi
if command -v xdg-mime >/dev/null 2>&1; then
    xdg-mime default notizen-py-qt.desktop application/x-notizen-alx >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q "$XDG_DATA_HOME_VALUE/icons/hicolor" >/dev/null 2>&1 || true
fi
if command -v gio >/dev/null 2>&1; then
    gio set "$DESKTOP_TARGET" metadata::trusted true >/dev/null 2>&1 || true
fi
touch "$APP_DESKTOP_DIR" >/dev/null 2>&1 || true

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
printf 'Entfernte alte Menü-Kopie (falls vorhanden): %s\n' "$STALE_DESKTOP_TARGET"
printf 'ALX-Dateizuordnung: application/x-notizen-alx\n'
printf 'GNOME Exec: env NOTIZEN_RESET_WINDOW=1 python3 -m notizen_py_qt --show --no-tray --reset-window %%f\n'
printf 'Direktstartdatei: %s\n' "$APPDIR/Notizen starten.sh"
printf 'Diagnoseprotokoll bei Menüstart: %s\n' "${XDG_STATE_HOME:-$HOME/.local/state}/notizen-py-qt/startup.log"
