# Validierungsbericht Notizen.NET → Python/Qt 0.10.7

## Prüfumfang

Der Stand 0.10.7 wurde aus dem entpackten Archiv 0.10.6 weitergeführt. Geprüft wurden die neue `neu_neben_knoten`-Parität, die exakt erreichbare `get_lightcolor()`-Zufallspalette, die bisherigen Regressionstests, die paketweite API und die ZIP-Berechtigungen.

Die GUI konnte in dieser Umgebung weiterhin nicht visuell gestartet werden, weil keine Qt-Bindung installiert ist. Die Qt-unabhängige Kernlogik, die Starter-/Packaging-Logik und der paketweite Import wurden geprüft.

## Ausgeführte Prüfungen

```text
PYTHONPATH=src pytest -q
python3 -m compileall -q src tests scripts
bash -n scripts/*.sh *.sh
bash scripts/check_no_slint_strict.sh
PYTHONPATH=src python3 -c "import notizen_py_qt; print(notizen_py_qt.__version__)"
PYTHONPATH=src python3 scripts/probe_python_qt_runtime.py --skip-qt
python3 scripts/package_zip.py . /mnt/data/notizenPyQt_0.10.7.zip --root-name Notizen_py_qt
ZIP permission check
package recheck
```

## Ergebnis

```text
pytest: 76 passed, 2 skipped
compileall: OK
bash -n scripts/*.sh *.sh: OK
check_no_slint_strict.sh: OK
API probe: OK, Version 0.10.7
Qt binding import: erwarteter Hinweis, weil PySide6/PyQt6 in dieser Umgebung nicht installiert ist
ZIP permission check: OK
package recheck: OK
```

## Neue Tests in 0.10.7

`tests/test_legacy_new_next_colors_107.py` prüft:

- `legacy_new_next_parent(...)` liefert für Nicht-Wurzelknoten den Elternknoten und den Endindex der Elternebene.
- `legacy_new_next_node(...)` hängt neue Geschwister wie `neu_neben_knoten` ans Ende der Elternebene.
- Bei markierter Wurzel wird der neue Knoten als Kind der Wurzel am Ende angelegt.
- `legacy_light_color_argb(...)` nutzt nur die von `Random.Next(0, 14)` erreichbaren Farben 0 bis 13.
- Die alten, aber automatisch unerreichbaren Fälle `Case 14`/Magenta und `Else`/LightGray bleiben außerhalb der Zufallspalette.

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
unzip notizenPyQt_0.10.7.zip
cd Notizen_py_qt
./Notizen\ starten.sh
```

Praktisch zu prüfen: Mehrere Geschwisterknoten anlegen, den mittleren markieren und Enter beziehungsweise **Neu daneben** auslösen. Der neue Knoten sollte wie im alten Notizen.NET am Ende derselben Elternebene erscheinen, nicht direkt hinter dem markierten Knoten.
