# Validierungsbericht Notizen.NET → Python/Qt 0.9.5

Stand: 2026-04-30

## Ergebnis

Der Stand 0.9.5 wurde syntaktisch und funktional ohne installierte Qt-GUI-Bindung validiert.

```text
compileall: OK
pytest: 25 passed, 2 skipped
shell syntax: OK
check_no_slint.sh: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt: erwarteter Abbruch mit Installationshinweis
legacy help parser: OK
Archiv extrahiert und erneut getestet: OK
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
25 passed, 2 skipped in 0.57s
```

Die beiden Skips sind erwartbar:

- optionale Crypto-Abhängigkeit nicht installiert,
- alte Legacy-Fixture-Datei nicht im aktuellen Paketarchiv enthalten.

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

## Neue Testabdeckung in 0.9.5

Neu hinzugefügt wurde `tests/test_node_clipboard_alarms.py` mit Tests für:

- systemweites Knoten-Clipboard-XML,
- Roundtrip eines Teilbaums mit RTF-Inhalt,
- Farben und Expand-Zustand im Clipboard-XML,
- Eltern-/Kind-Beziehungen nach dem Laden,
- bewusstes Entfernen von Desktop-Notiz-Zustand beim Kopieren,
- optionaler Erhalt von Desktop-Notiz-Zustand,
- Standard-Einfügelogik ohne Desktop-Notiz-Duplikate,
- nächste Wecker-Termine für einmalige, tägliche, wöchentliche, monatliche und jährliche Wiederholungen,
- Monatsende- und Schaltjahrfälle.

### Archiv-Retest

Das erzeugte Archiv wurde nach `/mnt/data/validate_095` extrahiert und erneut geprüft:

```bash
python -m compileall -q src tests
python -m pytest -q
```

Ergebnis:

```text
25 passed, 2 skipped in 0.60s
```

Zusätzlich wurden `pyproject.toml` und `src/notizen_py_qt/__init__.py` auf Version `0.9.5` geprüft.

## Hinweis zur Umgebung

Die GUI selbst konnte hier weiterhin nicht gestartet werden, weil kein Qt-Binding installiert ist. Das ist keine Projekt-Regression; der Runtime-Probe bricht sauber mit Installationshinweis ab. Ein echter GUI-/Drucktest sollte auf einem Rechner mit PySide6 oder PyQt6 erfolgen.
