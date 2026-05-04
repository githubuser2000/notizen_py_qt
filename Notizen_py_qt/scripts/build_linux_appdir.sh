#!/usr/bin/env bash
set -euo pipefail
APPDIR_INPUT="${1:-NotizenPyQt.AppDir}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
APPDIR="$(python3 - <<'PY' "$APPDIR_INPUT"
from pathlib import Path
import sys
print(Path(sys.argv[1]).expanduser().resolve())
PY
)"
PYTHON_BIN="${PYTHON:-python3}"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/src/notizen-py-qt" "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"
python3 - <<'PY_COPY' "$PROJECT_ROOT" "$APPDIR/usr/src/notizen-py-qt"
from pathlib import Path
import shutil
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
ignore_names = {'.git', '.venv', '__pycache__', '.pytest_cache'}
ignore_suffixes = {'.pyc', '.pyo'}
for item in src.rglob('*'):
    rel = item.relative_to(src)
    if any(part in ignore_names for part in rel.parts) or item.suffix in ignore_suffixes:
        continue
    target = dst / rel
    if item.is_dir():
        target.mkdir(parents=True, exist_ok=True)
    elif item.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
PY_COPY
cat > "$APPDIR/usr/share/applications/notizen-py-qt.desktop" <<'APPDIR_DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=Notizen PyQt
GenericName=Notizenverwaltung
Comment=Notizen.NET Python/Qt-Port sichtbar starten
Exec=AppRun %f
Icon=notizen-py-qt
Terminal=false
Categories=Utility;TextEditor;Office;
StartupNotify=true
StartupWMClass=notizen-py-qt
NoDisplay=false
DBusActivatable=false
MimeType=application/x-notizen-alx;
APPDIR_DESKTOP
cp "$PROJECT_ROOT/src/notizen_py_qt/resources/notizen.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/notizen-py-qt.png"
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
APPDIR_PROJECT="$HERE/usr/src/notizen-py-qt"
export PYTHONPATH="$APPDIR_PROJECT/src${PYTHONPATH:+:$PYTHONPATH}"
export NOTIZEN_KEEP_DISPLAY="${NOTIZEN_KEEP_DISPLAY:-1}"
export NOTIZEN_MENU_LAUNCH="${NOTIZEN_MENU_LAUNCH:-1}"
export NOTIZEN_FORCE_VISIBLE="${NOTIZEN_FORCE_VISIBLE:-1}"
export NOTIZEN_RESET_WINDOW="${NOTIZEN_RESET_WINDOW:-1}"
exec python3 -m notizen_py_qt --show --reset-window --no-tray "$@"
APPRUN
chmod 0755 "$APPDIR/AppRun"
ln -sf AppRun "$APPDIR/notizen-py-qt"
cat > "$APPDIR/README-AppDir.txt" <<'README'
Portable Notizen PyQt AppDir
============================

Start:
  ./AppRun

Dieses AppDir ist kein fertiges AppImage, sondern eine vorbereitete portable
Ordnerstruktur. Mit appimagetool kann daraus auf einem Zielsystem ein AppImage
gebaut werden. Die GNOME-sichtbaren Startargumente bleiben unverändert:
--show --reset-window --no-tray.
README
printf 'AppDir vorbereitet: %s\n' "$APPDIR"
printf 'Start: %s/AppRun\n' "$APPDIR"
printf 'Optional AppImage bauen: appimagetool %s\n' "$APPDIR"
