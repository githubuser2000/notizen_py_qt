# Validierungsbericht Notizen.NET → Python/Qt 0.10.2

Datum: 2026-05-02

## Zusammenfassung

Der Stand 0.10.2 wurde syntaktisch, funktional, strukturell und mit Blick auf ZIP-Berechtigungen geprüft. Die GUI konnte in dieser Umgebung nicht visuell gestartet werden, weil weder PySide6 noch PyQt6 installiert ist. Die Runtime-Prüfung ohne Qt-Import ist erfolgreich; die echte Qt-Bindung muss lokal installiert werden.

## Durchgeführte Prüfungen

### Python-Compile

```bash
python -m compileall -q src scripts tests
```

Ergebnis: erfolgreich.

### Pytest

```bash
python -m pytest -q
```

Ergebnis:

```text
58 passed, 1 skipped
```

Der übersprungene Test betrifft eine optionale externe Bedingung beziehungsweise nicht mitgelieferte Legacy-Fixtures.

### Shell-Syntax

```bash
bash -n scripts/*.sh
```

Ergebnis: erfolgreich.

### Strenger aktiver Pfad-Scanner

```bash
bash scripts/check_no_slint_strict.sh
```

Ergebnis: erfolgreich; keine alten Slint-/QML-/Rust-UI-Verweise im aktiven Projektpfad.

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

### ZIP-Berechtigungen

Das neu erzeugte Archiv wurde per `zipinfo -l` und zusätzlichem Python-Check geprüft:

- Verzeichnisse: `755`
- Shell-/Python-Build-Skripte: `755`
- normale Dateien: `644`
- keine `drw-------`-Verzeichnisse mehr

## In 0.10.2 zusätzlich validiert

- GNOME-Sitzungen werden über Desktop-Umgebungsvariablen erkannt.
- Bekannte AppIndicator/KStatusNotifier-Erweiterungen werden anhand ihrer GNOME-Shell-Extension-UUIDs erkannt.
- Unter GNOME ohne erkannte Tray-Erweiterung startet Notizen bei minimiertem Start sichtbar statt unsichtbar im Tray.
- `--force-tray-start` kann das alte versteckte Tray-Verhalten erzwingen.
- `--no-tray` deaktiviert den Traypfad.
- `<tray gnome-safe-start="..." />` wird gespeichert und wieder geladen.
- Die ZIP-Verpackungshilfe setzt portable Unix-Rechte.
