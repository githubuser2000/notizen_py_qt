# Validierungsbericht Notizen.NET → Python/Qt 0.10.1

Datum: 2026-05-02

## Zusammenfassung

Der Stand 0.10.1 wurde syntaktisch, funktional und strukturell geprüft. Die GUI konnte in dieser Umgebung nicht visuell gestartet werden, weil weder PySide6 noch PyQt6 installiert ist. Die Runtime-Prüfung ohne Qt-Import ist erfolgreich; die echte Qt-Bindung muss lokal installiert werden.

## Durchgeführte Prüfungen

### Python-Compile

```bash
python -m compileall -q src tests
```

Ergebnis: erfolgreich.

### Pytest

```bash
python -m pytest -q
```

Ergebnis:

```text
51 passed, 2 skipped
```

Die beiden übersprungenen Tests betreffen optionale externe Bedingungen, insbesondere nicht mitgelieferte Legacy-Fixtures beziehungsweise optionale Kryptografiebedingungen je nach Host.

### Shell-Syntax

```bash
bash -n scripts/*.sh
```

Ergebnis: erfolgreich.

### Strenger aktiver Pfad-Scanner

```bash
bash scripts/check_no_slint_strict.sh
```

Ergebnis:

```text
OK: no old UI-framework references found in active source/build files under /mnt/data/work_0101/Notizen_py_qt.
```

### Runtime-Probe ohne Qt-Import

```bash
python scripts/probe_python_qt_runtime.py --skip-qt
```

Ergebnis:

```text
RESULT: Python/Qt runtime probe passed.
```

### Qt-Bindung

In dieser Umgebung ist keine Qt-Bindung installiert. Erwarteter lokaler Installationspfad:

```bash
python -m pip install "PySide6>=6.6,<7"
# oder
python -m pip install "PyQt6>=6.6,<7"
```

## In 0.10.1 zusätzlich validiert

- `Datei.vb`-Standardname `unbenannt.alx` ist als Konstante abgebildet.
- Der alte Standardordner `MyDocuments\\Notizen` ist als `Documents/Notizen`-Fallback portiert.
- Windows-Backslash-Pfade werden auch auf Linux/macOS korrekt in Verzeichnis und Dateiname getrennt.
- Leere `open`-Configwerte fallen auf den Legacy-Standard zurück.
- `AppSettings.remember_file(...)` nutzt das robuste Legacy-Splitting.
- Desktop-Notiz-Transparenz aus `desknote_kontext_opacy.vb` wird als Transparenz, nicht als Deckkraft, interpretiert.
- `minimized`-/`maximized`-Fensterzustände aus `xml_kram.vb` werden normalisiert und in der Startlogik berücksichtigt.
