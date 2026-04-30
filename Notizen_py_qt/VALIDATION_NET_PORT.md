# Validierung: Notizen.NET-Python/Qt-Port 0.9.2

Stand: 2026-04-30

## Ausgeführt

```bash
python3 -m py_compile src/notizen_py_qt/*.py scripts/*.py tests/*.py
bash -n scripts/*.sh
bash scripts/check_no_slint.sh .
python3 scripts/probe_python_qt_runtime.py . --skip-smoke --skip-qt
```

Ergebnis:

```text
py_compile: OK
shell syntax: OK
check_no_slint: OK: no old UI-framework references found in active source/build files under /mnt/data/next_work/py_next.
probe_python_qt_runtime: RESULT: Python/Qt runtime probe passed.
```

## Manuelle Assertions ohne GUI

Zusätzlich wurde ein pytest-unabhängiger Validierungslauf mit echten Python-Assertions ausgeführt. Geprüft wurden:

- ALX-Byte-Roundtrip über `dump_alx_bytes`/`load_alx_bytes`.
- ALX-Datei-Roundtrip über `save_alx`/`load_alx`.
- Desktop-Notiz-Zustand in ALX-Struktur.
- RTF→HTML→RTF-/Plaintext-Verhalten mit Fett, Kursiv, Unterstrichen, Durchgestrichen, Textfarbe, Highlight und Emoji.
- Teilbaum-Export nach TXT/RTF mit Nummerierung `1.` und `1.1.`.
- Formatierter Teilbaum-RTF-Export mit Kursiv, Textfarbe und Highlight.
- Erzeugen einer zusammengefassten Notiz.
- Suche über einen kompletten Knotenbaum.
- FTP-Zielnormalisierung.
- Lesen und Schreiben erweiterter Legacy-Konfiguration (`scrolls`, `autorun`, Sprache, Taskleisten- und Desktop-Notiz-Optionen).

Ergebnis:

```text
manual validation OK
```

## GUI-Smoke-Test in dieser Umgebung

```bash
PYTHONPATH=src python3 -m notizen_py_qt --smoke-test
```

Ergebnis:

```text
No Qt binding is installed. Install one of:
  python -m pip install 'PySide6>=6.6,<7'
  python -m pip install 'PyQt6>=6.6,<7'
status: 2
```

Das ist für diesen Container erwartbar, weil weder PySide6 noch PyQt6 installiert ist. Der Code bricht dabei sauber mit Installationshinweis ab.

## pytest-Hinweis

Die aktive Testsammlung besteht jetzt aus den Notizen-Port-Tests unter `tests/`. In dieser Sandbox meldete `pytest` für die neue RichText-/Export-/Settings-Testdatei zwar `5 passed`, der Python-Prozess kehrte nach dem Import von `pytest` hier aber nicht zuverlässig zur Shell zurück. Deshalb wird die Validierung in diesem Paketbericht nicht als vollständiger `pytest`-Lauf behauptet, sondern über `py_compile`, Shell-Prüfung, den Runtime-Probe und explizite Python-Assertions dokumentiert.
