# Weitertranspilierung Notizen.NET → Python/Qt 0.10.13

Ausgangspunkt war der große Gap-Audit nach 0.10.12. Die wichtigste Vorgabe des Nutzers war: den zuletzt sichtbar funktionierenden Startpfad nicht wieder verschlimmbessern. Deshalb wurde in dieser Runde keine neue aggressive GNOME-/Tray-/Display-Strategie eingebaut. Stattdessen bleibt der Start sichtbar-first und orientiert sich am GNOME-Menüstart, der auf dem Zielsystem zwischenzeitlich sichtbar funktioniert hatte.

## 1. Startpfad konservativ gehalten

0.10.12 hatte für Shellstarts reines Wayland und gelöschtes `DISPLAY` erzwungen. Das war als Diagnoseversuch nachvollziehbar, aber der Nutzer meldete ausdrücklich, dass es zwischendurch sichtbar war und so bleiben soll. In 0.10.13 wurde der Pfad deshalb wieder konservativer gehalten:

- sichtbarer GNOME/Wayland-Start nutzt `QT_QPA_PLATFORM=wayland;xcb`,
- `DISPLAY` wird nicht pauschal entfernt,
- grafische Sitzungswerte aus `systemctl --user show-environment` werden übernommen,
- ein offensichtlich falsches Shell-`DISPLAY=:1` kann auf den bekannten sichtbaren Menüwert `:0` korrigiert werden,
- `GDK_BACKEND=x11` wird bei GNOME/Wayland entfernt,
- GTK-Platform-Themes `gtk2`/`gtk3` werden entfernt,
- Startdateien bleiben bei `--show --reset-window --no-tray`,
- Startlogs schreiben Paketversion, Paketdatei und Python-Executable.

Betroffene Dateien:

- `src/notizen_py_qt/display_env.py`
- `notizen-starten.sh`
- `Notizen starten.sh`
- `notizen-diagnose.sh`
- `scripts/build_python_qt.sh`

## 2. Sprach-Parität aus `languages.vb`

Der Audit hatte Französisch, Spanisch und Russisch als echte Lücke markiert. Diese Sprachen waren zuvor teilweise über generische `key_###`-Fallbacks abgebildet und damit nicht sauber mit `lang_keys` verbunden.

In 0.10.13 wurde die alte Sprachstruktur positionsgenau übernommen:

- alle 118 `lang_keys`-Positionen sind als semantische Schlüssel vorhanden,
- Deutsch, Englisch, Französisch, Spanisch, Russisch und Chinesisch haben jeweils dieselbe vollständige Schlüsselmenge,
- generische `key_###`-Schlüssel wurden entfernt,
- Legacy-Aliaswerte wie `french`, `spanish`, `russian` und `Chinese` bleiben akzeptiert,
- `legacy_language_key_for_index(...)` macht die alte Enum-/Array-Position testbar,
- `legacy_language_translations(...)` liefert eine Sprache wieder in alter Array-Reihenfolge.

Betroffene Datei:

- `src/notizen_py_qt/i18n.py`

Neuer Test:

- `tests/test_legacy_languages_1013.py`

## 3. Echte alte `.alx`-Dateien als Fixtures

Der Audit hatte ausdrücklich festgestellt, dass reine synthetische Tests nicht ausreichen. Gleichzeitig enthalten die großen alten Debug-ALX-Dateien im Originalprojekt persönliche Notizinhalte. 0.10.13 geht deshalb bewusst zweigleisig vor:

- `tests/fixtures/legacy_unbenannt.alx` bleibt als echte alte leere Notizen.NET-Minimalfixture enthalten,
- `tests/fixtures/legacy_sanitized_desktop.alx` ist eine kleine sanitisierte Legacy-ALX-Datei mit Desktop-Notiz-Attributen, aber ohne persönliche Altinhalte.

Geprüft wird insbesondere:

- der alte Ein-Knoten-Standardbaum `start` lädt aus der echten `unbenannt.alx`,
- die sanitisierte Legacy-Fixture lädt mit Wurzel `Notes`,
- verschachtelte Knoten und zwei Desktop-Notizzustände werden erkannt,
- ein Dump/Load-Roundtrip erhält Titelreihenfolge und Desktop-Notiz-Zustände.

Neuer Test:

- `tests/test_legacy_alx_fixtures_1013.py`

## 4. Recent-Files-Parität aus `xml_kram.vb`

Der Audit nannte die alte Vierer-Rotation der zuletzt geöffneten Dateien als noch nicht exakt genug abgebildet. 0.10.13 ergänzt dafür reine, testbare Helfer:

- `LEGACY_RECENT_FILE_SLOTS`
- `legacy_recent_files_from_slots(...)`
- `legacy_recent_slots_from_files(...)`
- `legacy_remember_recent_file(...)`
- `legacy_activate_recent_file(...)`

`AppSettings.remember_file(...)` und `AppSettings.save(...)` nutzen diese Helfer. Beim Öffnen über das Recent-Menü wird der ausgewählte Eintrag wieder in Richtung neuester Slot rotiert.

Betroffene Dateien:

- `src/notizen_py_qt/settings.py`
- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/__init__.py`

Neuer Test:

- `tests/test_recent_desktop_1013.py`

## 5. Desktop-Notizen weiter aus `desknote.vb` abgeleitet

Desktop-Notizen waren im Audit als großer Block markiert. Die komplette WinForms-Paint-/Mouse-/Resize-Logik ist noch nicht vollständig identisch, aber 0.10.13 portiert weitere konkrete Regeln:

- Legacy-Randmaße der alten borderlosen Notiz werden als Konstanten dokumentiert,
- Hover-/Fokus-Geometrie ist als reine Funktion testbar,
- die alte kontrahierte Randgeometrie ist testbar,
- Titelstreifen-Klickzonen für Hide/Close/Move sind testbar,
- aktive Desktop-Notizen werden wieder voll sichtbar,
- nach Fokus-/Hoververlust wird die gespeicherte Opacity wiederhergestellt,
- temporäre Vollsichtbarkeit wird nicht mehr als dauerhafte Transparenz gespeichert.

Betroffene Dateien:

- `src/notizen_py_qt/desktop_note_legacy.py`
- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/__init__.py`

Neuer Test:

- `tests/test_recent_desktop_1013.py`

## 6. Alter Info-/Hilfe-Text

Der alte `aboutinfotext` aus `languages.vb` wird im Info-/Hilfe-Dialog wieder verwendet. Dadurch ist der alte Hilfeinhalt zumindest als lesbarer Dialog zurück im Port, auch wenn die alte Feedback-Sendefunktion weiterhin nicht als Netzwerkfunktion nachgebaut wurde.

Betroffene Datei:

- `src/notizen_py_qt/app.py`

## 7. Tastaturbedienung aus `Notizen.vb/tastendruck`

Der Audit hatte die alte WinForms-Tastaturbedienung als Restparitätsblock markiert. 0.10.13 ergänzt eine Qt-unabhängige Zuordnung, damit die alten Tasten nicht nur in QAction-Shortcuts verstreut sind:

- Ctrl+Space → Wecker,
- Ctrl+S/O/N/Q → Speichern/Öffnen/Neue Datei/Beenden,
- Ctrl+C/V/X → kontextabhängige Zwischenablage,
- Ctrl+U → Knoten umbenennen,
- Ctrl+F → Suche,
- Ctrl+Plus/Ctrl+Minus → Schriftgröße im Editor,
- Shift+Insert/Shift+Delete → Knoten einfügen/ausschneiden im Baum,
- Insert/Delete/Enter im Baum → Unterknoten, Löschen, neuer Geschwisterknoten.

Betroffene Dateien:

- `src/notizen_py_qt/keyboard_legacy.py`
- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/__init__.py`

Neuer Test:

- `tests/test_legacy_keyboard_1013.py`

## 8. RTF-WMF/EMF und Config-Erhalt

Zusätzlich zu PNG/JPEG/BMP werden alte RichTextBox-`\wmetafileN`- und `\emfblip`-Bilder erkannt, in HTML als Data-URI erhalten und beim kombinierten RTF-Export wieder als passende `\pict`-Gruppen geschrieben. Außerdem bleiben unbekannte Root-Attribute und unbekannte direkte Config-Elemente beim Speichern erhalten.

Betroffene Dateien:

- `src/notizen_py_qt/rtf_utils.py`
- `src/notizen_py_qt/exporters.py`
- `src/notizen_py_qt/settings.py`

Neuer Test:

- `tests/test_legacy_config_rtf_1013.py`

## 9. Wecker-Details aus `wecker.vb`

Zusätzlich wurden weitere alte Wecker-Details testbar gemacht:

- die alte Checkbox-Reihenfolge aus `wecker.Designer.vb`,
- Wochentagszuordnung Montag bis Sonntag,
- alte Intervall-Einheiten für täglich/wöchentlich/monatlich/jährlich,
- deaktivierte Wecker-Spezifikationen erzeugen keine nächste Auslösung.

Betroffene Dateien:

- `src/notizen_py_qt/alarms.py`
- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/__init__.py`

Neuer Test:

- `tests/test_wecker_legacy_1013.py`

## Noch offen nach 0.10.13

Diese Punkte bleiben aus der großen Restanalyse offen oder nur teilweise erledigt:

- echte verschlüsselte alte `.alx`-Fixtures,
- Realtest auf dem Nutzer-GNOME-System,
- vollständige WinForms-artige Desktop-Notiz-Paint-/Resize-/MouseLeave-Logik,
- komplexe RTF-Fidelity mit echten Altdateien,
- FTP-Realtest mit Server,
- Installer/AppImage/venv-Paketierung,
- vollständige alte Feedback-Sendefunktion, falls sie wirklich noch gebraucht wird.

0.10.13 schließt damit bewusst mehrere Audit-Blöcke, ohne den sichtbaren Startpfad wieder experimentell umzubauen.
