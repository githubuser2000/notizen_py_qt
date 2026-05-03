# Validierungsbericht Notizen.NET → Python/Qt 0.10.8

## Prüfumfang

Der Stand 0.10.8 wurde aus dem entpackten Archiv 0.10.7 weitergeführt. Geprüft wurden die neue Drag-and-drop-Modellregel nach `Baum_MouseUp`, die Bullet-Einfügefolge nach `ToolStrip_dot_Click`, die Startup-Zielprüfung aus `ApplicationEvents.vb`, die bisherigen Regressionstests, der paketweite Import und die ZIP-Berechtigungen.

Die GUI konnte in dieser Umgebung weiterhin nicht visuell gestartet werden, weil keine Qt-Bindung installiert ist. Die neue Drop-Regel ist aber als reine Modellfunktion getestet; die Qt-Oberfläche verwendet diese Regel über `LegacyTreeWidget`.

## Ausgeführte Prüfungen

```text
PYTHONPATH=src pytest -q
python3 -m compileall -q src tests scripts
bash -n scripts/*.sh *.sh
bash scripts/check_no_slint_strict.sh
PYTHONPATH=src python3 -c "import notizen_py_qt; print(notizen_py_qt.__version__)"
PYTHONPATH=src python3 scripts/probe_python_qt_runtime.py --skip-qt
python3 scripts/package_zip.py . /mnt/data/notizenPyQt_0.10.8.zip --root-name Notizen_py_qt
ZIP permission check
package recheck
```

## Ergebnis

```text
pytest: 84 passed, 2 skipped
compileall: OK
bash -n scripts/*.sh *.sh: OK
check_no_slint_strict.sh: OK
API probe: OK, Version 0.10.8
Qt binding import: erwarteter Hinweis, weil PySide6/PyQt6 in dieser Umgebung nicht installiert ist
ZIP permission check: OK
package recheck: OK
```

## Neue Tests in 0.10.8

`tests/test_legacy_drag_startup_bullet_108.py` prüft:

- Root-Knoten können nicht per Drag-and-drop verschoben werden.
- Drops auf die Wurzel, auf sich selbst oder in einen eigenen Nachfahren werden abgelehnt.
- Ein gezogener Knoten landet als Geschwister direkt vor dem Zielknoten.
- Same-parent-Indexverschiebungen behalten die korrekte Reihenfolge.
- Cross-parent-Moves behalten das bestehende `NoteNode`-Objekt und seine Unterstruktur.
- Der alte Bullet-Clipboard-Text ist `\r•   ` und wird für Qt zu `\n•   ` normalisiert.
- Fehlende lokale `.alx`-Startziele werden verworfen; existierende lokale Dateien und FTP-Ziele bleiben erhalten.

## ZIP-Rechte

Das Archiv wird weiter mit `scripts/package_zip.py` erstellt. Geprüfte Regeln:

```text
Verzeichnisse: 755
Shell-Skripte: 755
aktive Python-Hilfsskripte direkt unter `scripts/`: 755
.desktop-Dateien: 755
archivierte Legacy-Migrationsskripte unter `legacy_build_metadata`: 644
normale Dateien: 644
keine __pycache__/.pytest_cache/.pyc im Archiv
```

## Offene visuelle Prüfung

Lokal sollte zusätzlich geprüft werden:

```bash
python3 -m pip install --user "PySide6>=6.6,<7"
unzip notizenPyQt_0.10.8.zip
cd Notizen_py_qt
./Notizen\ starten.sh
```

Praktisch zu prüfen: Mehrere Geschwisterknoten anlegen und einen Knoten per Maus auf einen anderen ziehen. Der gezogene Knoten sollte vor dem Ziel-Geschwisterknoten erscheinen und nicht als Kind darunter. Zusätzlich den Bullet-Button im Editor testen: Er sollte immer einen neuen Bullet-Absatz einfügen.
