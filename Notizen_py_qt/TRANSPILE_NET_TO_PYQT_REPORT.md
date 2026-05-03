# Weitertranspilierung Notizen.NET → Python/Qt 0.10.11

Ausgangsstand war 0.10.10. Diese Runde behandelt die neue Nutzerdiagnose: Der Start über das GNOME-Menü zeigt ein Fenster, aber der Start aus der Shell über `python3 -m notizen_py_qt --no-tray --show`, `./notizen-starten.sh` und `./Notizen\ starten.sh` blieb unsichtbar beziehungsweise erzeugte `Gtk-WARNING: cannot open display: :1`.

## Diagnose

Das ist kein reiner Trayfehler mehr. Wenn der GNOME-Menüstarter sichtbar funktioniert, aber die Shell nicht, liegt der Unterschied typischerweise in der geerbten Startumgebung: `QT_QPA_PLATFORM`, `QT_QPA_PLATFORMTHEME`, `DISPLAY`, `WAYLAND_DISPLAY`, `PYTHONPATH` oder ein alter installierter Modulpfad.

Der Port behandelt sichtbaren GNOME-Start jetzt deshalb schon **vor dem Import von PySide6/PyQt6**. Dadurch greifen die Korrekturen auch beim direkten Modulstart mit `python3 -m notizen_py_qt --no-tray --show`.

## Umgesetzte Änderungen in 0.10.11

- Neues Modul `display_env.py`:
  - `DisplayEnvironmentDecision`
  - `visible_start_requested(...)`
  - `normalize_qt_display_environment(...)`
  - `append_startup_log(...)`
- Frühe Qt-Display-Normalisierung in `app.py`, bevor `qt_compat.load_qt()` PySide6/PyQt6 importiert.
- Sichtbarer GNOME/Wayland-Start setzt problematische Shell-Backends auf:
  - `QT_QPA_PLATFORM=wayland;xcb`
- Als problematisch gelten unter anderem:
  - leerer/unklarer Wert bei sichtbarem GNOME/Wayland-Start,
  - `xcb` bei vorhandener Wayland-Sitzung,
  - `offscreen`, `minimal`, `vnc`, `eglfs`, `linuxfb`, `directfb`, `webgl`.
- `QT_QPA_PLATFORMTHEME=gtk2`/`gtk3` wird für sichtbaren GNOME/Wayland-Start entfernt, weil genau solche geerbten Theme-Plugins zu `Gtk-WARNING: cannot open display: :1` führen können.
- Opt-out für absichtlich gesetzte Qt-Umgebung:
  - `NOTIZEN_KEEP_QT_ENV=1`
- `notizen-starten.sh` setzt jetzt:
  - `NOTIZEN_FORCE_VISIBLE=1`
  - `NOTIZEN_RESET_WINDOW=1`
  - `NOTIZEN_STARTUP_LOG=~/.local/state/notizen-py-qt/startup.log`
- Die Startdateien protokollieren jetzt auch Terminalstarts teilweise, vor allem:
  - `DISPLAY`
  - `WAYLAND_DISPLAY`
  - `QT_QPA_PLATFORM`
  - `QT_QPA_PLATFORMTHEME`
  - `PYTHONPATH`
  - tatsächlich übergebene Argumente
- Doppelte Argumente wie `--show --reset-window --no-tray --show --no-tray --reset-window` werden in den Startdateien bereinigt.
- `notizen-diagnose.sh` protokolliert zusätzlich `QT_QPA_PLATFORM`, `QT_QPA_PLATFORMTHEME` und `GDK_BACKEND`.
- GUI-Fehlerdialoge durch `zenity`/`kdialog` werden bei interaktivem Terminalstart vermieden, damit keine irreführenden GTK-Displaywarnungen die eigentliche Ausgabe überdecken.

## Bezug zu Notizen.NET

Das alte WinForms-Programm hatte keine Qt-Backendwahl. Diese Änderung ist deshalb keine fachliche Notizen.NET-Funktion, sondern eine notwendige Plattformanpassung des Python/Qt-Ports: Sichtbarer Start muss Vorrang vor geerbten Shell-/Wayland-/X11-Sonderfällen haben.

## Aktualisierte Dateien

- `src/notizen_py_qt/display_env.py`
- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/__init__.py`
- `notizen-starten.sh`
- `notizen-diagnose.sh`
- `README.md`
- `docs/MAPPING.md`
- `docs/PROJECT_CONTEXT_IMPORTED.md`
- `pyproject.toml`
- `notizen_py_qt/__init__.py`
- `notizen_py_qt/__main__.py`
- `tests/test_display_env_1011.py`
- `tests/test_gnome_visible_start_1010.py`

## Weiterhin nicht visuell geprüft

In dieser Umgebung ist keine echte GNOME-Sitzung mit Qt-Bindung verfügbar. Der Fix ist deshalb über reine Logik, Skriptprüfung, Import-/API-Probes und Regressionstests abgesichert. Der entscheidende Praxistest bleibt auf dem Zielsystem.
