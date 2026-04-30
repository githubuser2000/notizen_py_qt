# Validierung: Notizen.NET-Python/Qt-Port

## Ausgeführt

```bash
python3 -m py_compile src/notizen_py_qt/*.py scripts/*.py
bash -n scripts/*.sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests
```

Ergebnis:

```text
20 passed in 1.98s
```

## Zusätzlich geprüft

```bash
PYTHONPATH=src python3 -m notizen_py_qt --smoke-test
```

Ergebnis in dieser Container-Umgebung:

```text
No Qt binding is installed. Install one of:
  python -m pip install 'PySide6>=6.6,<7'
  python -m pip install 'PyQt6>=6.6,<7'
```

Das ist erwartbar: PySide6/PyQt6 ist hier nicht installiert. Der Code importiert und testet deshalb bewusst die nicht-GUI-seitigen Module getrennt.

## Testabdeckung

- ALX-v2-XML-Roundtrip.
- Laden des originalen `unbenannt.alx`-Fixtures aus Notizen.NET.
- Legacy-`notes_doc`-Import.
- Passwortnormalisierung nach VB.NET-Regel mit 24 Zeichen.
- GZip/UTF-16-Kompatibilität.
- Byte-basierter ALX-Import/Export für FTP.
- Verschlüsselter DES-Roundtrip, wenn `pycryptodome` installiert ist.
- Suchmodi.
- FTP-Feldnormalisierung.
- Bestehende Qt-6.11-/no-Slint-Migrationsskripte aus dem hochgeladenen Zielarchiv.
