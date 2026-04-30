# Validierung: Notizen.NET-Python/Qt-Port 0.9.3

Stand: 2026-04-30

## Ausgeführt

```bash
PYTHONPATH=src /usr/bin/python3 -m compileall -q src tests scripts
bash -n scripts/*.sh
PYTHON=/usr/bin/python3 bash scripts/check_no_slint.sh .
PYTHON=/usr/bin/python3 bash scripts/check_no_slint_strict.sh .
PYTHONPATH=src /usr/bin/python3 scripts/probe_python_qt_runtime.py --skip-qt --skip-smoke
```

Ergebnis:

```text
py_compile/compileall: OK
shell syntax: OK
check_no_slint: OK
check_no_slint_strict: OK
probe_python_qt_runtime --skip-qt --skip-smoke: RESULT: Python/Qt runtime probe passed.
```

## Testfunktionen

Zusätzlich wurde die aktive Testsammlung direkt über Python-Testfunktionen ausgeführt. Das ist in dieser Sandbox zuverlässiger als der normale `pytest`-Prozess, weil der installierte virtuelle Python-Runner hier nach `pytest`-Importen nicht zuverlässig zur Shell zurückkehrt. Die Testfunktionen selbst laufen mit echten Assertions.

Ergebnis:

```text
SUMMARY passed=13 skipped=2 failed=0
```

Geprüft wurden unter anderem:

- ALX-Byte-Roundtrip über `dump_alx_bytes`/`load_alx_bytes`.
- UTF-16/GZip-Kompatibilität der gespeicherten Dokument-XML-Struktur.
- Legacy-Passwortnormalisierung.
- Legacy-Notiz-XML-Parsing.
- V2-Nested-XML-Roundtrip.
- Suche über einen Knotenbaum.
- FTP-Zielnormalisierung.
- RTF→HTML→RTF-/Plaintext-Verhalten mit Fett, Kursiv, Unterstrichen, Durchgestrichen, Schriftgröße, Schriftfamilie, Textfarbe, Highlight und Emoji.
- RTF-Bild-Roundtrip für HTML-Data-URI → RTF-`\pict\pngblip` → HTML-Data-URI.
- Teilbaum-Export nach TXT/RTF mit Nummerierung `1.` und `1.1.`.
- Formatierter Teilbaum-RTF-Export mit Kursiv, Schriftfamilie, Textfarbe und Highlight.
- Erzeugen einer zusammengefassten Notiz.
- Lesen und Schreiben erweiterter Legacy-Konfiguration (`scrolls`, `autorun`, Sprache, Taskleisten- und Desktop-Notiz-Optionen).

Übersprungene Tests:

```text
pycryptodome not installed
legacy fixture not included
```

## GUI-Smoke-Test in dieser Umgebung

Ohne `--skip-qt` ergibt der Runtime-Probe erwartungsgemäß:

```text
Qt binding import failed: No Qt binding is installed. Install one of:
  python -m pip install 'PySide6>=6.6,<7'
  python -m pip install 'PyQt6>=6.6,<7'
RESULT: 1 problem(s) found.
```

Das ist für diesen Container erwartbar, weil weder PySide6 noch PyQt6 installiert ist. Der Code bricht dabei sauber mit Installationshinweis ab. Auf einem Rechner mit installiertem PySide6 oder PyQt6 sollte zusätzlich ausgeführt werden:

```bash
python -m notizen_py_qt --smoke-test
```
