# Validierungsbericht Notizen.NET → Python/Qt 0.10.13

Geprüft wurde der weitertranspilierte Stand 0.10.13 aus 0.10.12. Schwerpunkt dieser Runde: sichtbaren GNOME-Startpfad konservieren, Sprach-Parität aus `languages.vb`, datenschutzbewusste ALX-Fixtures, Recent-Files-Rotation, RTF-WMF/EMF und weitere Desktop-Notiz-Parität.

## Ausgeführte Prüfungen

```text
PYTHONPATH=src pytest -q
python -m compileall -q src notizen_py_qt
bash -n scripts/*.sh *.sh
./scripts/check_no_slint_strict.sh
python scripts/probe_python_qt_runtime.py . --skip-smoke --skip-qt
PYTHONPATH=src python - <<'PY'
import notizen_py_qt
print(notizen_py_qt.__version__)
PY
```

## Ergebnis

```text
pytest: 133 passed, 2 skipped
compileall: OK
bash -n: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt-Import: OK
API probe: OK, Version 0.10.13
ZIP permission check: OK
package recheck via unzip: 133 passed, 2 skipped
```

## Neue Tests in 0.10.13

- `tests/test_legacy_languages_1013.py`
  - prüft 118 alte Sprachschlüssel,
  - prüft vollständige Schlüsselmenge je Sprache,
  - prüft, dass keine generischen `key_###`-Fallbacks mehr vorhanden sind,
  - prüft Französisch/Spanisch/Russisch gegen konkrete alte `languages.vb`-Positionen,
  - prüft Aliaswerte aus alten Configs.

- `tests/test_legacy_alx_fixtures_1013.py`
  - lädt die echte alte leere `unbenannt.alx`-Fixture,
  - lädt eine kleine sanitisierte Legacy-Desktop-Notiz-Fixture,
  - prüft Wurzel, Knoten, Desktop-Notiz-Zustände und Roundtrip-Erhalt ohne persönliche Altinhalte.

- `tests/test_recent_desktop_1013.py`
  - prüft alte Recent-Datei-Slots `a/b/c/d`,
  - prüft Rotation beim Wiederöffnen,
  - prüft `AppSettings`-Integration,
  - prüft Desktop-Notiz-Randgeometrie, Opacity und Titelstreifen-Klickzonen.

- `tests/test_legacy_keyboard_1013.py`
  - prüft globale Ctrl-Shortcuts aus `Notizen.vb/tastendruck`,
  - prüft Editor-spezifische Ctrl+Plus/Ctrl+Minus-Schriftgrößenregeln,
  - prüft baumbezogene Insert/Delete/Enter- und Shift+Insert/Shift+Delete-Regeln.

- `tests/test_wecker_legacy_1013.py`
  - prüft alte Wochentags-Checkboxnamen und Reihenfolge aus `wecker.Designer.vb`,
  - prüft Intervall-Einheiten aus `wecker.vb`,
  - prüft deaktivierte Wecker-Spezifikationen.

- `tests/test_legacy_config_rtf_1013.py`
  - prüft unbekannte Legacy-Config-Root-Attribute und Zusatz-Elemente,
  - prüft WMF- und EMF-Bilder in RTF-Parsing, HTML-Brücke und kombiniertem RTF-Export.

## Nicht visuell geprüft

In dieser Umgebung ist weiterhin keine echte GNOME-/Wayland-Sitzung mit installierter Qt-Bindung vorhanden. Der Startpfad wurde deshalb per Code und Tests abgesichert, aber die entscheidende visuelle Prüfung bleibt auf dem Zielsystem:

```bash
./Notizen\ starten.sh
./notizen-starten.sh
python3 -m notizen_py_qt --no-tray --show --reset-window
```

Wichtig: 0.10.13 setzt den Start bewusst wieder auf den Menü-kompatiblen sichtbaren Pfad (`wayland;xcb`, kein pauschales Entfernen von `DISPLAY`) zurück.
