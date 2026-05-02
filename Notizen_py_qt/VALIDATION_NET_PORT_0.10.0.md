# Validierungsbericht Notizen.NET → Python/Qt 0.10.0

Datum: 2026-05-01

## Zusammenfassung

Der Stand 0.10.0 wurde syntaktisch, funktional und strukturell geprüft. Die GUI konnte in dieser Umgebung nicht visuell gestartet werden, weil weder PySide6 noch PyQt6 installiert ist. Die Qt-Importprüfung liefert deshalb erwartungsgemäß den Installationshinweis.

Während der Python-Unterprozesse gibt die Containerumgebung eine `artifact_tool`-/Spreadsheet-Warmupwarnung auf stderr aus. Sie stammt nicht aus dem Notizen-Projekt; die relevanten Prüfungen hatten trotzdem den erwarteten Returncode.

## Durchgeführte Prüfungen

### Python-Compile

```bash
PYTHONPATH=src python -m compileall -q src tests scripts
```

Ergebnis: erfolgreich.

### Pytest

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q
```

Ergebnis:

```text
44 passed, 2 skipped
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
OK: no old UI-framework references found in active source/build files under /mnt/data/notizen_validate_0100/Notizen_py_qt.
```

### Runtime-Probe ohne Qt-Import

```bash
PYTHONPATH=src python scripts/probe_python_qt_runtime.py --skip-qt
```

Ergebnis:

```text
RESULT: Python/Qt runtime probe passed.
```

### Qt-Bindung

```bash
PYTHONPATH=src python -c "from notizen_py_qt.qt_compat import load_qt; load_qt()"
```

Ergebnis: erwarteter Fehler, da auf dem Validierungssystem keine Qt-Bindung installiert ist.

```text
Qt binding import failed: No Qt binding is installed. Install one of:
  python -m pip install 'PySide6>=6.6,<7'
  python -m pip install 'PyQt6>=6.6,<7'
```

## In 0.10.0 zusätzlich validiert

- Legacy-Config liest und speichert `open/once-opened`.
- Legacy-Config liest und speichert `tool-stripes`-Positionen.
- Autosave folgt der WinForms-Regel: `0` aus, aktivierte Werte unter fünf Sekunden werden zu fünf Sekunden, Standard ist 60 Sekunden.
- Autostart-Helfer wählen die jüngste Recent-Datei, setzen optional `-min` und schreiben/entfernen das Startup-Skript.
- RTF-Tabellensteuerwörter `\cell`, `\nestcell` und `\row` bleiben in Plain-Text-/Exportpfaden als Tabulatoren und Zeilenumbrüche lesbar.
