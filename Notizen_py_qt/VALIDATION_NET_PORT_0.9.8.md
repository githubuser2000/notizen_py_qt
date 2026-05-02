# Validierungsbericht Notizen.NET → Python/Qt 0.9.8

Datum: 2026-05-01

## Zusammenfassung

Der Stand 0.9.8 wurde syntaktisch, funktional und strukturell geprüft. Die GUI konnte in dieser Umgebung nicht visuell gestartet werden, weil weder PySide6 noch PyQt6 installiert ist. Die erwartete Fehlermeldung des Runtime-Probes wurde geprüft.

## Durchgeführte Prüfungen

### Python-Compile

```bash
python3 -m compileall -q src tests scripts
```

Ergebnis: erfolgreich.

### Pytest

```bash
python3 -m pytest -q
```

Ergebnis:

```text
34 passed, 2 skipped
```

Die beiden übersprungenen Tests betreffen optionale externe Bedingungen, insbesondere nicht mitgelieferte Legacy-Fixtures beziehungsweise optionale Kryptografiebedingungen je nach Host.

### Shell-Syntax

```bash
bash -n scripts/*.sh
```

Ergebnis: erfolgreich.

### Strenger aktiver Pfad-Scanner

```bash
bash scripts/check_no_slint_strict.sh .
```

Ergebnis:

```text
OK: no old UI-framework references found in active source/build files under /mnt/data/work_notizen/pyqt/Notizen_py_qt.
```

### Runtime-Probe ohne Qt-Import

```bash
PYTHONPATH=src python3 scripts/probe_python_qt_runtime.py --skip-qt
```

Ergebnis:

```text
RESULT: Python/Qt runtime probe passed.
```

### Runtime-Probe mit Qt-Import, aber ohne Smoke-Test

```bash
PYTHONPATH=src python3 scripts/probe_python_qt_runtime.py --skip-smoke
```

Ergebnis: erwarteter Fehler, da auf dem Validierungssystem keine Qt-Bindung installiert ist.

```text
Qt binding import failed: No Qt binding is installed. Install one of:
  python -m pip install 'PySide6>=6.6,<7'
  python -m pip install 'PyQt6>=6.6,<7'
RESULT: 1 problem(s) found.
```

### Modul-Smoke-Test

```bash
PYTHONPATH=src python3 -m notizen_py_qt --smoke-test
```

Ergebnis: erwarteter Exit-Code 2 mit Installationshinweis für PySide6/PyQt6, weil keine Qt-Bindung installiert ist.

## In 0.9.8 zusätzlich validiert

- `unify_root_action` ist in der UI-Quelle verdrahtet.
- `unify_root_tree()` nutzt die Dokumentwurzel und denselben Append-Pfad wie die Teilbaum-Zusammenfassung.
- `open_recent_file()` prüft fehlende Dateien und ruft vor dem Laden `maybe_save_changes()` auf.
- Such- und Exportpfade enthalten `save_current_editor_to_node()` vor der Modellauswertung.
- Alte UI-Migrationsdateien liegen nicht mehr im aktiven Source-/Build-Pfad.
