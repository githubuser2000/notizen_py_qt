# Validierungsbericht Notizen.NET → Python/Qt 0.9.9

Datum: 2026-05-01

## Zusammenfassung

Der Stand 0.9.9 wurde syntaktisch, funktional und strukturell geprüft. Die GUI konnte in dieser Umgebung nicht visuell gestartet werden, weil weder PySide6 noch PyQt6 installiert ist. Die erwartete Fehlermeldung des Runtime-Probes wurde geprüft.

## Durchgeführte Prüfungen

### Python-Compile

```bash
/usr/bin/python3 -m compileall -q src tests scripts
```

Ergebnis: erfolgreich.

### Pytest

Wegen störender globaler pytest-Plugins wurde die automatische Plugin-Ladung für die Validierung deaktiviert:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /usr/bin/python3 - <<'PY'
import sys
sys.path.append('/opt/pyvenv/lib/python3.13/site-packages')
import pytest
raise SystemExit(pytest.main(['-q']))
PY
```

Ergebnis:

```text
40 passed, 2 skipped
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
OK: no old UI-framework references found in active source/build files under /mnt/data/notizen_work_099/pyqt/Notizen_py_qt.
```

### Runtime-Probe ohne Qt-Import

```bash
PYTHONPATH=src /usr/bin/python3 scripts/probe_python_qt_runtime.py --skip-qt
```

Ergebnis:

```text
RESULT: Python/Qt runtime probe passed.
```

### Runtime-Probe mit Qt-Import, aber ohne Smoke-Test

```bash
PYTHONPATH=src /usr/bin/python3 scripts/probe_python_qt_runtime.py --skip-smoke
```

Ergebnis: erwarteter Fehler, da auf dem Validierungssystem keine Qt-Bindung installiert ist.

```text
Qt binding import failed: No Qt binding is installed. Install one of:
  python -m pip install 'PySide6>=6.6,<7'
  python -m pip install 'PyQt6>=6.6,<7'
RESULT: 1 problem(s) found.
```

## In 0.9.9 zusätzlich validiert

- Backup-Hilfsfunktionen erzeugen den alten `saftycopies`-Ordner ohne `.alx`-Suffix.
- Backup-Dateien verwenden das alte Muster `Name-YYYY-MM-DD-HH-MM-SS-ms.alx`.
- Backup-Rotation löscht ältere Sicherungen oberhalb des konfigurierten Limits.
- `keep=0` entfernt vorhandene Sicherungen wie deaktivierte Sicherheitskopien.
- UI-Aktionen `backup_now_action` und `open_backup_action` sind im Menü und in der Werkzeugleiste verdrahtet.
- Neue Desktop-Notizen nutzen Mausposition, 200×200 Pixel, 85 % Deckkraft und helle Legacy-Farbe.
