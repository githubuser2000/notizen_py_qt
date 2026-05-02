# Validierungsbericht Notizen.NET → Python/Qt 0.10.5

## Prüfumfang

Der Stand 0.10.5 wurde aus dem entpackten Archiv 0.10.4 weitergeführt. Geprüft wurden die neue Suchergebnislisten-Parität, die historische Ganzwort-Tokenisierung aus `suche.vb`, die bisherigen Regressionstests und die ZIP-Berechtigungen.

Die GUI konnte in dieser Umgebung weiterhin nicht visuell gestartet werden, weil keine Qt-Bindung installiert ist. Die Qt-unabhängige Kernlogik, die Starter-/Packaging-Logik und der paketweite Import wurden geprüft.

## Ausgeführte Prüfungen

```text
PYTHONPATH=src pytest -q
python3 -m compileall -q src tests scripts
bash -n scripts/*.sh *.sh
bash scripts/check_no_slint_strict.sh
PYTHONPATH=src python3 -c "import notizen_py_qt; print(notizen_py_qt.__version__)"
PYTHONPATH=src python3 scripts/probe_python_qt_runtime.py
python3 scripts/package_zip.py . /mnt/data/notizenPyQt_0.10.5.zip --root-name Notizen_py_qt
ZIP permission check
```

## Ergebnis

```text
pytest: 70 passed, 2 skipped
compileall: OK
bash -n scripts/*.sh *.sh: OK
check_no_slint_strict.sh: OK
API probe: OK, Version 0.10.5
package/data roundtrip probe: OK
Qt binding import: erwarteter Hinweis, weil PySide6/PyQt6 in dieser Umgebung nicht installiert ist
ZIP permission check: OK
```

## Neue Tests in 0.10.5

`tests/test_search_results_105.py` prüft:

- Legacy-Ganzwortsuche trennt nur bei Leerzeichen und CR/LF.
- Satzzeichen und Tabs bleiben wie in `suche.vb` Teil eines Such-Tokens.
- Suchtreffer werden als Knotenreferenz plus `SelectionStart` geführt.
- `build_search_hit_views(...)` erzeugt Knotenpfad, Vorschautext und Listenlabel.
- Snippets komprimieren Zeilenumbrüche und markieren abgeschnittene Ränder.
- Der Qt-Suchdialog enthält eine sichtbare Ergebnisliste `Suchliste` mit Aktivierung und Rückwärtsnavigation.

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
unzip notizenPyQt_0.10.5.zip
cd Notizen_py_qt
./Notizen\ starten.sh
```

Im Suchdialog sollte bei aktivierter Option **Alle Knoten durchsuchen** eine Trefferliste erscheinen. Ein Treffer sollte per Doppelklick/Enter den passenden Knoten öffnen und den Treffer im Editor markieren.
