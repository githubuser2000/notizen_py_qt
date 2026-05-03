# Validierungsbericht Notizen.NET → Python/Qt 0.10.11

Geprüft wurde der weitertranspilierte Stand 0.10.11 aus 0.10.10. Schwerpunkt war der Unterschied zwischen sichtbarem GNOME-Menüstart und unsichtbarem Shell-/Modulstart.

## Prüfumgebung

- Keine installierte Qt-Bindung in dieser Ausführungsumgebung.
- Keine echte GNOME-/Wayland-Sitzung verfügbar.
- Validierung daher über reine Logiktests, Syntaxchecks, Kompilierung, Paketprüfung und ZIP-Rechte.

## Ausgeführte Prüfungen

```text
python3 -m pytest -q
python3 -m compileall -q src tests
bash -n notizen-starten.sh "Notizen starten.sh" notizen-diagnose.sh scripts/*.sh
scripts/check_no_slint_strict.sh
python3 scripts/package_zip.py . /mnt/data/notizenPyQt_0.10.11.zip --root-name Notizen_py_qt
```

Ergebnis:

```text
pytest: 103 passed, 2 skipped
compileall: OK
bash -n: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt-Import: OK
API probe: OK, Version 0.10.11
ZIP permission check: OK
package recheck via unzip: OK
```

## Neue Tests in 0.10.11

`tests/test_display_env_1011.py` prüft:

- `--show`, `--reset-window`, `--no-tray` und `NOTIZEN_FORCE_VISIBLE` lösen sichtbaren Start aus.
- GNOME/Wayland mit geerbtem `QT_QPA_PLATFORM=xcb` wird auf `wayland;xcb` normalisiert.
- `QT_QPA_PLATFORM=offscreen` wird bei sichtbarem Start entfernt.
- `QT_QPA_PLATFORMTHEME=gtk3` wird bei sichtbarem GNOME/Wayland-Start entfernt.
- `NOTIZEN_KEEP_QT_ENV=1` lässt absichtlich gesetzte Werte unangetastet.
- `python3 -m notizen_py_qt --help` funktioniert aus dem entpackten Projektordner über den neuen Root-Shim.

`tests/test_gnome_visible_start_1010.py` wurde erweitert und prüft nun zusätzlich:

- Startdateien setzen `NOTIZEN_FORCE_VISIBLE=1`.
- Startdateien enthalten die `wayland;xcb`-Bereinigung.
- Diagnose- und Startskripte bleiben Bash-syntaxvalide.

## Erwarteter Test auf dem Zielsystem

Nach dem Entpacken direkt im neuen Ordner:

```bash
cd Notizen_py_qt
./notizen-diagnose.sh
./Notizen\ starten.sh
```

Direkter Modulstart aus dem entpackten Projektordner funktioniert jetzt ohne manuelles `PYTHONPATH`:

```bash
python3 -m notizen_py_qt --no-tray --show --reset-window
```

Die relevante Diagnose steht danach in:

```bash
cat ~/.local/state/notizen-py-qt/startup.log
cat ~/.local/state/notizen-py-qt/diagnose.log
```

## ZIP-Rechte

Erwartete Rechte im Archiv:

```text
Verzeichnisse: 755
Shell-Starter: 755
.desktop-Starter: 755
aktive Python-Hilfsskripte direkt unter scripts/: 755
archivierte Legacy-Migrationsskripte: 644
normale Dateien: 644
keine __pycache__/.pytest_cache/.pyc im Archiv
```

## Nicht visuell geprüft

Der tatsächliche GNOME-Fensteraufbau kann in dieser Umgebung nicht geprüft werden. Der Fix wurde so früh wie möglich im Prozess platziert, damit er auch für `python3 -m notizen_py_qt --no-tray --show` greift, bevor Qt geladen wird.
