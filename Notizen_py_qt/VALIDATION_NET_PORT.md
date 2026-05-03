# Validierungsbericht Notizen.NET → Python/Qt 0.10.14

Geprüft wurde der weitertranspilierte Stand 0.10.14 aus 0.10.13. Schwerpunkt: sichtbaren GNOME-Startpfad konservieren, ALX-Attributerhalt, sparse Desktop-Notiz-Roundtrips, Legacy-ALX-Validator und RTF-Codepage-Auswertung.

## Ausgeführte Prüfungen

```text
PYTHONPATH=src pytest -q
python3 -m compileall -q src notizen_py_qt scripts
bash -n notizen-starten.sh 'Notizen starten.sh' notizen-diagnose.sh scripts/*.sh
./scripts/check_no_slint_strict.sh
python3 scripts/probe_python_qt_runtime.py . --skip-smoke --skip-qt
PYTHONPATH=src scripts/validate_legacy_alx.py tests/fixtures/legacy_unbenannt.alx
PYTHONPATH=src scripts/validate_legacy_alx.py tests/fixtures/legacy_sanitized_desktop.alx
PYTHONPATH=src scripts/validate_legacy_alx.py <alte Notizen.NET unbenannt.alx> <alte Notizen.NET test.alx>
PYTHONPATH=src python3 - <<'PY'
import notizen_py_qt
print(notizen_py_qt.__version__)
PY
```

## Ergebnis

```text
pytest: 142 passed, 3 skipped
compileall: OK
bash -n: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt-Import: OK
Legacy ALX validator: OK für Paket-Fixtures
Legacy ALX validator: OK für alte Notizen.NET-Debug-Dateien ohne Inhaltsausgabe
API probe: OK, Version 0.10.14
```

Die Skip-Fälle bleiben erwartbar:

- echte verschlüsselte alte ALX-Fixture fehlt,
- visuelle Qt-/GNOME-Prüfung ist in dieser Umgebung nicht möglich,
- abhängig von lokaler Crypto-/Qt-Installation können einzelne optionale Tests übersprungen werden.

## Neue Tests in 0.10.14

- `tests/test_alx_roundtrip_attrs_1014.py`
  - prüft unbekannte `<Notiz>`-Attribute,
  - prüft sparse Desktop-Notizen ohne künstliches `opacity`/`argb`,
  - prüft gezieltes Schreiben moderner Desktop-Werte nach Änderung,
  - prüft dieselbe Logik im Teilbaum-Zwischenablagepfad.

- `tests/test_legacy_validation_1014.py`
  - prüft datenschutzarme Dokumentzusammenfassungen,
  - prüft ALX-Laden/Speichern/Laden-Roundtrip-Vergleich,
  - prüft das neue CLI-Werkzeug `scripts/validate_legacy_alx.py`.

- `tests/test_rtf_codepage_1014.py`
  - prüft `\ansicpg1251` mit hexadezimalen RTF-Escapes,
  - prüft Plaintext-/HTML-/Content-Parts-Decoding,
  - prüft Fallback auf `cp1252` bei unbekannter Codepage.

## Intern geprüfte echte alte ALX-Dateien

Aus dem alten Notizen.NET-Projekt wurden zwei Debug-ALX-Dateien nur intern gegen den neuen Validator geprüft. Der Validator gibt keine Titel und keine Notiztexte aus.

```text
alte unbenannt.alx: roundtrip=OK
alte test.alx: nodes=65, max_depth=3, desktop_notes=3, roundtrip=OK
```

Die große Debug-Datei wird nicht ins Paket gepackt.

## Startpfad

Der sichtbare GNOME-Startpfad wurde absichtlich nicht neu experimentell verändert. 0.10.14 behält 0.10.13 bei:

```text
--show --reset-window --no-tray
QT_QPA_PLATFORM=wayland;xcb
kein pauschales Entfernen von DISPLAY
```

Korrigiert wurde nur eine ungültige Bash-Bedingung in `notizen-starten.sh`, damit der vorhandene Startpfad syntaktisch sauber ausführbar bleibt.

## Nicht visuell geprüft

In dieser Umgebung gibt es keine echte GNOME-/Wayland-Sitzung mit sichtbarer Qt-Oberfläche. Die entscheidende visuelle Prüfung bleibt auf dem Zielsystem:

```bash
./Notizen\ starten.sh
./notizen-starten.sh
python3 -m notizen_py_qt --no-tray --show --reset-window
```
