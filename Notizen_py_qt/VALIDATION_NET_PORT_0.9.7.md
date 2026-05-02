# Validierungsbericht Notizen.NET → Python/Qt 0.9.7

Stand: 2026-04-30

## Ergebnis

Der Stand 0.9.7 wurde syntaktisch und funktional ohne installierte Qt-GUI-Bindung validiert.

```text
compileall: OK
pytest: 31 passed, 2 skipped
shell syntax: OK
check_no_slint.sh: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt-Import: OK (--skip-qt)
runtime probe mit Qt-Import: erwarteter sauberer Abbruch mit Installationshinweis
legacy UI source checks: OK
Archiv extrahiert und erneut getestet: OK
```

## Ausgeführte Prüfungen

### Python-Kompilierung

```bash
python3 -S -m compileall -q src tests scripts/probe_python_qt_runtime.py
```

Ergebnis: OK.

### Tests

```bash
env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONPATH="src:/opt/pyvenv/lib64/python3.13/site-packages:/opt/pyvenv/lib/python3.13/site-packages" \
  python3 -S -m pytest -q
```

Ergebnis:

```text
31 passed, 2 skipped
```

Die beiden Skips sind erwartbar:

- optionale Crypto-Abhängigkeit nicht installiert,
- alte Legacy-Fixture-Datei nicht im aktuellen Paketarchiv enthalten.

Neu geprüft werden in 0.9.7:

- HTML-Export mit Dokumenthülle, Nummerierung und Bildern,
- korrigierte Geschwister-Nummerierung im HTML- und RTF/TXT-Export,
- Statistikzählung für Notizbäume,
- Import einer beliebigen alten `notizen.config.xml`,
- Quellverdrahtung der neuen Aktionen und Methoden.

### Shell-Skripte

```bash
bash -n scripts/*.sh
scripts/check_no_slint.sh
scripts/check_no_slint_strict.sh
```

Ergebnis: OK.

### Runtime-Probe ohne Qt

```bash
PYTHONPATH=src python3 -S scripts/probe_python_qt_runtime.py --skip-qt
```

Ergebnis: OK.

### Runtime-Probe mit Qt-Import

```bash
PYTHONPATH=src python3 -S scripts/probe_python_qt_runtime.py --skip-smoke
```

Ergebnis: erwarteter Exitcode `1`, weil in dieser Umgebung weder PySide6 noch PyQt6 installiert ist. Die Anwendung meldet sauber:

```text
No Qt binding is installed. Install one of:
  python -m pip install 'PySide6>=6.6,<7'
  python -m pip install 'PyQt6>=6.6,<7'
```

### CLI-Smoke ohne Qt

```bash
PYTHONPATH=src python3 -S -m notizen_py_qt --smoke-test
```

Ergebnis: erwarteter Exitcode `2` mit Installationshinweis für PySide6/PyQt6.

## Nicht ausgeführt

Ein echter visueller GUI-Test mit geöffnetem Fenster konnte hier nicht durchgeführt werden, weil PySide6/PyQt6 fehlt. Die neue Funktionalität ist deshalb über reine Python-Tests, statische MainWindow-Quellprüfungen und Runtime-Probes abgesichert.
