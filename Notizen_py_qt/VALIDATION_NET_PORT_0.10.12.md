# Validierungsbericht Notizen.NET → Python/Qt 0.10.13

Geprüft wurde der weitertranspilierte Stand 0.10.13 aus 0.10.12. Schwerpunkt war die Nutzeranforderung, den zwischenzeitlich sichtbaren GNOME-Startpfad nicht wieder zu verschlechtern, sowie die vollständige Übernahme der alten `languages.vb`-Spracharrays.

## Prüfumgebung

- Keine echte GNOME-/Wayland-Sitzung in dieser Ausführungsumgebung.
- Keine installierte Qt-Bindung für eine visuelle Prüfung.
- Validierung daher über reine Logiktests, Skriptprüfung, Kompilierung, API-Probes, Paketprüfung und ZIP-Rechte.

## Ausgeführte Prüfungen

```text
PYTHONPATH=src pytest -q
python3 -m compileall -q src notizen_py_qt
bash -n scripts/*.sh *.sh
bash scripts/check_no_slint_strict.sh
PYTHONPATH=src python3 -c "import notizen_py_qt; print(notizen_py_qt.__version__)"
python3 scripts/probe_python_qt_runtime.py . --skip-qt --skip-smoke
python3 scripts/package_zip.py . /mnt/data/notizenPyQt_0.10.13.zip --root-name Notizen_py_qt
```

Ergebnis im Arbeitsstand:

```text
pytest: 118 passed
compileall: OK
bash -n: OK
check_no_slint_strict.sh: OK
API probe: OK, Version 0.10.13
runtime probe ohne Qt-Import: OK
```

Nach dem Verpacken wurde das ZIP erneut entpackt und geprüft.

## Neue Tests in 0.10.13

`tests/test_legacy_languages_1013.py` prüft:

- alle sechs alten Sprachen besitzen exakt denselben Legacy-Schlüsselraum,
- Französisch, Spanisch und Russisch verwenden keine generischen `key_###`-Fallbacks mehr,
- positionsbasierte Schlüssel aus `Notizen.vb Enum lang_keys` bleiben abrufbar,
- alte Sprachwerte werden vollständig übernommen,
- die API-Exports für Sprachschlüssel und Übersetzungswerte funktionieren.

Aktualisierte Display-Tests prüfen, dass der sichtbare GNOME/Wayland-Start wieder menu-kompatibel arbeitet:

- `QT_QPA_PLATFORM=wayland;xcb`,
- keine harte Löschung von `DISPLAY`,
- `GDK_BACKEND=x11` wird entfernt,
- `QT_QPA_PLATFORMTHEME=gtk2/gtk3` wird entfernt,
- Smoke-/Buildstarts bleiben headless mit `QT_QPA_PLATFORM=offscreen`.

## Erwarteter Test auf dem Zielsystem

Nach sauberem Entpacken direkt im neuen Ordner:

```bash
cd Notizen_py_qt
./Notizen\ starten.sh
```

Direkter Modulstart:

```bash
python3 -m notizen_py_qt --no-tray --show --reset-window
```

Die relevante Diagnose steht danach in:

```bash
cat ~/.local/state/notizen-py-qt/startup.log
```

Bei 0.10.13 sollte das Log erkennen lassen, dass wirklich diese Version läuft:

```text
PACKAGE_VERSION=0.10.13
ARGS=--show --reset-window --no-tray
QT_QPA_PLATFORM=wayland;xcb
```

`DISPLAY` wird in dieser Version nicht absichtlich leergeräumt. Wenn `systemctl --user show-environment` den vom GNOME-Menü genutzten Wert liefert, darf `DISPLAY=:0` im Log stehen.

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

Der tatsächliche GNOME-Fensteraufbau kann in dieser Umgebung nicht geprüft werden. Der Port lässt den Startpfad in 0.10.13 aber wieder näher an dem GNOME-Menüpfad, der auf dem Zielsystem sichtbar war, und vermeidet die harte pure-Wayland-Änderung aus 0.10.12.
