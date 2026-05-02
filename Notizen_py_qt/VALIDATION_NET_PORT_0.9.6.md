# Validierungsbericht Notizen.NET → Python/Qt 0.9.6

Stand: 2026-04-30

## Ergebnis

Der Stand 0.9.6 wurde syntaktisch und funktional ohne installierte Qt-GUI-Bindung validiert.

```text
compileall: OK
pytest: 26 passed, 2 skipped
shell syntax: OK
check_no_slint.sh: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt: erwarteter Abbruch mit Installationshinweis
legacy UI source check: OK
```

## Ausgeführte Prüfungen

### Python-Kompilierung

```bash
python -m compileall -q src tests
```

Ergebnis: OK.

### Tests

```bash
python -m pytest -q
```

Ergebnis:

```text
26 passed, 2 skipped
```

Die beiden Skips sind erwartbar:

- optionale Crypto-Abhängigkeit nicht installiert,
- alte Legacy-Fixture-Datei nicht im aktuellen Paketarchiv enthalten.

Neu hinzugekommen ist eine statische UI-Prüfung, die sicherstellt, dass die WinForms-nahen Objektbereiche im Hauptfenster-Quellcode vorhanden sind:

- `txt1`,
- `txt2`,
- `Baum`,
- `Inhalt`,
- Titel-Synchronisierung über `commit_title_box`,
- Kopffeld-Synchronisierung über `update_node_text_boxes`.

### Shell-Skripte

```bash
bash -n scripts/check_no_slint.sh
bash -n scripts/check_no_slint_strict.sh
bash -n scripts/verify_qt611_environment.sh
bash -n scripts/build_python_qt.sh
```

Ergebnis: OK.

### Keine alten UI-Framework-Referenzen im aktiven Pfad

```bash
bash scripts/check_no_slint.sh
bash scripts/check_no_slint_strict.sh
```

Ergebnis: OK.

### Runtime-Probe ohne Qt

```bash
PYTHONPATH=src python -m notizen_py_qt --smoke-test
```

Ergebnis: erwarteter Exitcode `2`, weil in dieser Umgebung weder PySide6 noch PyQt6 installiert ist.

Die Anwendung meldet sauber:

```text
No Qt binding is installed. Install one of:
  python -m pip install 'PySide6>=6.6,<7'
  python -m pip install 'PyQt6>=6.6,<7'
```

## Nicht ausgeführt

Ein echter visueller GUI-Test mit geöffnetem Fenster konnte hier nicht durchgeführt werden, weil PySide6/PyQt6 fehlt. Genau dafür wurden in 0.9.6 zusätzliche Mindestgrößen, Objekt-Namen und statische Prüfungen eingebaut, sodass der nächste Test auf einem lokalen Qt-System gezielt überprüfbar ist.
