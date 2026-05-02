# Validierungsbericht Notizen.NET → Python/Qt 0.10.6

## Prüfumfang

Der Stand 0.10.6 wurde aus dem entpackten Archiv 0.10.5 weitergeführt. Geprüft wurden die neue Baum-Löschparität aus `Baum.element_loeschen`, das rekursive Schließen von Desktop-Notizen im betroffenen Teilbaum, die Autosave-Schutzbedingung aus `Autosavetimer_Tick`, die bisherigen Regressionstests und die ZIP-Berechtigungen.

Die GUI konnte in dieser Umgebung weiterhin nicht visuell gestartet werden, weil keine Qt-Bindung installiert ist. Die Qt-unabhängige Kernlogik, die Starter-/Packaging-Logik und der paketweite Import wurden geprüft.

## Ausgeführte Prüfungen

```text
PYTHONPATH=src pytest -q
python3 -m compileall -q src tests scripts
bash -n scripts/*.sh *.sh
bash scripts/check_no_slint_strict.sh
PYTHONPATH=src python3 -c "import notizen_py_qt; print(notizen_py_qt.__version__)"
PYTHONPATH=src python3 scripts/probe_python_qt_runtime.py
python3 scripts/package_zip.py . /mnt/data/notizenPyQt_0.10.6.zip --root-name Notizen_py_qt
ZIP permission check
```

## Ergebnis

```text
pytest: 73 passed, 2 skipped
compileall: OK
bash -n scripts/*.sh *.sh: OK
check_no_slint_strict.sh: OK
API probe: OK, Version 0.10.6
Qt binding import: erwarteter Hinweis, weil PySide6/PyQt6 in dieser Umgebung nicht installiert ist
ZIP permission check: OK
package recheck: 73 passed, 2 skipped; API Version 0.10.6
```

## Neue Tests in 0.10.6

`tests/test_tree_delete_autosave_106.py` prüft:

- `legacy_visible_walk(...)` bildet die sichtbare TreeView-Reihenfolge abhängig vom `expanded`-Status ab.
- `legacy_delete_fallback_node(...)` wählt denselben vorher sichtbaren Knoten wie das alte `SelectedNode.PrevVisibleNode`.
- Wurzel-Löschen liefert keinen Fallback, weil der alte Pfad das Dokument schließt.
- `legacy_autosave_should_save(...)` speichert nur bei existierender Datei, vorhandenem Baum und Änderungen.
- Eine entfernte `.alx` wird durch Autosave nicht still neu angelegt.

## ZIP-Rechte

Das Archiv wird weiter mit `scripts/package_zip.py` erstellt. Geprüfte Regeln:

```text
Verzeichnisse: 755
Shell-Skripte: 755
Python-Skripte in `scripts`-Pfaden: 755
.desktop-Dateien: 755
normale Dateien: 644
keine __pycache__/.pytest_cache/.pyc im Archiv
```

## Offene visuelle Prüfung

Lokal sollte zusätzlich geprüft werden:

```bash
python3 -m pip install --user "PySide6>=6.6,<7"
unzip notizenPyQt_0.10.6.zip
cd Notizen_py_qt
./Notizen\ starten.sh
```

Praktisch zu prüfen: Einen aufgeklappten Teilbaum mit Desktop-Notizen in Kindknoten löschen oder ausschneiden. Danach sollten keine verwaisten Desktop-Notizfenster sichtbar bleiben, und die Baum-Auswahl sollte auf den vorher sichtbaren Knoten springen.
