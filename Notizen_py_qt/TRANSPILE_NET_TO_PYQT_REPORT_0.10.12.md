# Weitertranspilierung Notizen.NET → Python/Qt 0.10.13

Ausgangsstand war 0.10.12. Diese Runde folgt der großen Rest-Transpilierungsuntersuchung, aber mit einer wichtigen Korrektur der Priorität: Der Startpfad bleibt jetzt bewusst so konservativ, dass das Fenster sichtbar bleibt. Der zwischenzeitlich funktionierende GNOME-Menüstart wurde als Referenz genommen. Deshalb erzwingt 0.10.13 nicht mehr reines Wayland und löscht `DISPLAY` nicht mehr hart.

## Schwerpunkt 1: sichtbarer GNOME-/Shell-Start konservativ gehalten

Die Nutzerdiagnose zeigte zwei Dinge:

- Der GNOME-Menüstart konnte sichtbar funktionieren.
- Shellstarts waren empfindlich gegenüber geerbten Anzeigevariablen.

0.10.12 hatte daraufhin sehr hart auf reines Wayland umgeschaltet. Das war als Schutz nachvollziehbar, konnte aber genau den Startpfad verschlechtern, der zwischendurch funktionierte. 0.10.13 nimmt deshalb die menu-kompatible Variante wieder auf:

- sichtbarer GNOME/Wayland-Start nutzt wieder `QT_QPA_PLATFORM=wayland;xcb`,
- `DISPLAY` wird nicht pauschal entfernt,
- wenn `systemctl --user show-environment` eine brauchbare GNOME-Sitzungsumgebung liefert, werden `DISPLAY`, `WAYLAND_DISPLAY`, `XDG_CURRENT_DESKTOP`, `XDG_SESSION_DESKTOP` und `XDG_RUNTIME_DIR` daraus übernommen,
- ein offensichtlich falsches `DISPLAY=:1` kann auf den vom Menüstart bekannten Wert `:0` korrigiert werden, statt es leer zu setzen,
- `GDK_BACKEND=x11` wird bei sichtbarem GNOME/Wayland-Start entfernt, aber nicht durch eine harte neue Einstellung ersetzt,
- `QT_QPA_PLATFORMTHEME=gtk2/gtk3` wird weiterhin entfernt, weil diese Werte GTK-Displayfehler auslösen können,
- `NOTIZEN_KEEP_QT_ENV=1`, `NOTIZEN_KEEP_DISPLAY=1`, `NOTIZEN_KEEP_SHELL_DISPLAY=1` und `NOTIZEN_QPA_PLATFORM=...` bleiben als Notfall-/Diagnose-Overrides erhalten.

Damit bleibt das Fenster-Sichtbarkeitsziel wichtiger als eine theoretisch sauberere, aber auf dem Zielsystem riskante Backend-Erzwingung.

## Schwerpunkt 2: Startdateien und Diagnose bleiben sichtbar-first

Die Startdateien bleiben absichtlich einfach:

```text
--show --reset-window --no-tray
```

Dadurch werden alte minimierte Fensterzustände, Offscreen-Positionen und Tray-Verstecken weiterhin überstimmt. `notizen-starten.sh` protokolliert jetzt zusätzlich die Paketversion und die tatsächlich verwendete Paketdatei. Dadurch ist im Log leichter zu erkennen, ob wirklich die frisch entpackte Version oder noch eine alte Installation gestartet wurde.

`build_python_qt.sh` startet weiterhin keine dauerhafte GUI mehr. `notizen-diagnose.sh` bleibt bounded und startet die sichtbare Anwendung nur mit `--launch`.

## Schwerpunkt 3: Sprachen aus `languages.vb` vollständig positionsgenau übernommen

Die große Untersuchung hatte die Mehrsprachigkeit als echte Transpilierungslücke markiert. In 0.10.13 wurde deshalb `languages.vb` erneut gegen `Notizen.vb Enum lang_keys` ausgewertet und in den Python/Qt-Port übertragen.

Umgesetzt:

- alle 118 Legacy-Sprachschlüssel werden als semantische Namen geführt,
- Deutsch, Englisch, Französisch, Spanisch, Russisch und Chinesisch besitzen jetzt denselben vollständigen Schlüsselraum,
- die früheren generischen `key_###`-Fallbacks für Französisch/Spanisch/Russisch wurden entfernt,
- die Positionen aus dem alten VB-Array bleiben erhalten,
- Groß-/Kleinschreibungsabweichungen alter Keys werden beim Übersetzen tolerant behandelt,
- neue testbare Helfer wurden ergänzt:
  - `LEGACY_LANGUAGE_KEYS`,
  - `LEGACY_LANGUAGE_KEY_ORDER`,
  - `LEGACY_LANGUAGE_INDEX`,
  - `legacy_language_key_for_index(...)`,
  - `legacy_language_index_for_key(...)`,
  - `legacy_language_values(...)`,
  - `legacy_language_translations(...)`.

Das schließt einen der wichtigsten P1-Punkte aus der Restuntersuchung: Die Spracharrays sind nicht mehr nur teilweise oder generisch übernommen, sondern aus dem alten VB.NET-Code abgeleitet.

## Aktualisierte Dateien

- `src/notizen_py_qt/display_env.py`
- `src/notizen_py_qt/i18n.py`
- `src/notizen_py_qt/__init__.py`
- `notizen-starten.sh`
- `README.md`
- `docs/MAPPING.md`
- `docs/PROJECT_CONTEXT_IMPORTED.md`
- `pyproject.toml`
- `tests/test_display_env_1011.py`
- `tests/test_gnome_shell_start_1012.py`
- `tests/test_legacy_languages_1013.py`
- `TRANSPILE_NET_TO_PYQT_REPORT.md`
- `VALIDATION_NET_PORT.md`

## Weiterhin offen

0.10.13 schließt nicht die gesamte große Audit-Liste. Vorrangig erledigt wurden der konservative sichtbare Startpfad und die vollständige Spracharray-Portierung. Weiter offen bleiben vor allem echte alte `.alx`-Fixtures, komplexe RTF-/RichTextBox-Fälle, Desktop-Notiz-Verhalten, FTP-Realtests, Wecker-Sonderfälle, Toolbar-/Recent-Files-Feinschliff und ein robuster Installer.

## Nicht visuell geprüft

In dieser Ausführungsumgebung gibt es keine echte GNOME-/Wayland-Sitzung mit installierter Qt-Bindung. Der Startpfad wurde daher über die gelieferte Nutzerdiagnose, Shell-Skripte, frühe Display-Umgebungslogik und Regressionstests abgesichert. Der entscheidende Praxistest bleibt auf dem Zielsystem.
