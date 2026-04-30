# Validierungsbericht Notizen.NET → Python/Qt 0.9.4

Stand: 2026-04-30

## Ergebnis

Der Stand 0.9.4 wurde syntaktisch und funktional ohne installierte Qt-GUI-Bindung validiert.

```text
compileall: OK
pytest: 20 passed, 2 skipped
shell syntax: OK
check_no_slint.sh: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt: erwarteter Abbruch mit Installationshinweis
legacy help parser: OK
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
20 passed, 2 skipped in 0.41s
```

Die beiden Skips sind erwartbar:

- optionale Crypto-Abhängigkeit nicht installiert,
- alte Fixture-Datei nicht im aktuellen Paketarchiv enthalten.

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

Ergebnis:

```text
OK: no old UI-framework references found in active source/build files
```

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

### Legacy-Hilfeparameter

```bash
PYTHONPATH=src python -m notizen_py_qt /?
```

Ergebnis: OK, Hilfeausgabe mit Exitcode `0`.

## Neue Testabdeckung in 0.9.4

Neu hinzugefügt wurde `tests/test_legacy_behaviour_094.py` mit Tests für:

- WinForms-nahe Einfügelogik `legacy_paste_clone()`,
- Einfügen vor dem markierten Geschwisterknoten,
- Einfügen als erster Root-Unterknoten,
- TXT-Export in UTF-8, ANSI/Windows-1252 und Unicode/UTF-16,
- CRLF-Zeilenenden im TXT-Export,
- Sprachauflösung `Auto`,
- alte Sprachkeys,
- legacy Startparameter `/min`, `/?`, lokale `.alx` und `ftp://`,
- alte helle Desktop-Notiz-Farbpalette als signierte ARGB-Werte.

## Hinweis zur Umgebung

Während einiger Python-Prozesse gab die Notebook-/Artifact-Umgebung eine externe `artifact_tool`-Warmup-Warnung auf `stderr` aus. Die Projektprüfungen selbst hatten trotzdem erfolgreiche Rückgabecodes. Diese Warnung stammt nicht aus `notizen_py_qt`.
