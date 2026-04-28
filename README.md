# Notizen Py Slint

Das ist ein Python-orientierter Port von **Notizen.NET** aus dem gelieferten VB.NET/WinForms-Projekt. Der alte Code wurde nicht nur zeilenweise umgeschrieben: Dateiformat, Notizbaum, RTF-Textinhalt, Sicherheitskopien, Konfiguration, FTP-Transport, Wecker-Logik und die historische DES-Kaskadenverschlüsselung wurden als pure-Python-Kern neu aufgebaut. Die Oberfläche liegt als Slint-Datei plus Python-Controller vor.

## Status

Funktioniert im Port:

- `.alx` laden und speichern
- GZip-komprimiertes UTF-16-XML-Format `<notizen-alx2>` lesen/schreiben
- verschlüsselte `.alx`-Dateien lesen/schreiben, kompatibel zur alten dreifachen DES-CBC-Kaskade mit den alten Passwort-Slicing-Eigenheiten
- Notizbaum anzeigen, Kind-/Nachbarnotizen anlegen, löschen, duplizieren, kopieren/ausschneiden/einfügen
- Knoten hoch/runter verschieben, einrücken, ausrücken, alle auf-/zuklappen
- Suche über Titel und Text, einmalig oder als Trefferliste; in der UI jetzt mit Groß-/Kleinschreibung, Ganzwortsuche und Suche nur im aktuellen Teilbaum
- TXT-, RTF-, Markdown-, JSON- und HTML-Export für ganze Datei oder ausgewählten Teilbaum
- Roh-RTF einer einzelnen Notiz exportieren, Text/RTF in aktuelle Notiz importieren
- PNG/JPEG/BMP als RTF-`\pict` an Notizen anhängen
- eingebettete RichTextBox-/RTF-Bilder aus alten Notizen extrahieren
- Datum/Uhrzeit und Aufzählungszeichen an Notizen anhängen
- einfache Ganznotiz-Formatierung als portabler Ersatz für RichTextBox-Auswahlformatierung
- auswahlbezogene RichTextBox-Aktionen als Plain-Text-Range-Operationen im Python-Kern und in der CLI: Text einfügen, Bereich löschen und Bereich formatieren
- RichTextBox-Toolbar-Stile `B`, `I`, `U`, `S` und `Normal` als Ganznotiz-Aktionen in UI und CLI sowie als Bereichsformatierung per `style-range`
- Textgröße per A+/A- beziehungsweise CLI wie im alten Ctrl+Plus/Ctrl+Minus-Workflow ändern
- Raw-RTF-Modus in der UI, damit alte RichTextBox-Inhalte notfalls direkt bearbeitet werden können
- alte Intellibit-`notes_doc`-Dateien importieren
- Sticky/Desktop-Notiz-Metadaten lesen, speichern, sichtbar/unsichtbar schalten, Geometrie/Farbe bearbeiten, automatisch grob dimensionieren, als HTML-Board exportieren und optional als kleine Tk-Fenster öffnen
- Knotenfarben (`bgcolor`, `fgcolor`) lesen, speichern, löschen, per alter heller Notizen.NET-Palette setzen und wieder als WinForms-kompatible signed ARGB-Werte schreiben
- Sicherheitskopien beim lokalen Speichern und Autosave-Timer aus der Konfiguration
- alte `notizen.config.xml` lesen/importieren/exportieren, inklusive Backup-Anzahl, Autosave, Autostart, Fensterdaten, Sticky-Rahmen und FTP-Feldern
- portabler Autostart-Stub für Linux, Windows und macOS aus der neuen Konfiguration
- FTP/FTPS laden und speichern über `ftp://`/`ftps://`-URLs, inklusive `.netrc`-Fallback und migrierbarem Standardziel
- Wecker-/Erinnerungsregeln mit einmaliger, täglicher, wöchentlicher, monatlicher und jährlicher Wiederholung
- fällige Wecker prüfen beziehungsweise als dauernde CLI-Schleife beobachten, optional mit nativer Best-Effort-Desktop-Benachrichtigung über Plattformwerkzeuge
- alte Sprachtexte aus `languages.vb` als Python-Tabelle mit CLI-Abfrage, About-Text und UI-Info-Hook
- alte Tastenkürzel aus `Notizen.tastendruck` als dokumentiertes Manifest mit CLI-Ausgabe und UI-Kurzhinweis
- allgemeine Konfigurationsschalter per `config-set`/`config-path`, damit Teile des alten Einstellungsdialogs auch ohne GUI skriptbar sind
- Feedback-Dialog als lokaler GZip-/UTF-16-Draft kompatibel zum alten Payloadformat, aber ohne automatischen Upload zu alten Servern
- erweiterte Kommandozeile ohne GUI als Fallback

Bewusst vereinfacht oder nicht vollständig portiert:

- Slints `TextEdit` ist Plain-Text. Vorhandenes RTF wird im Textmodus als Text angezeigt und nach Bearbeitung als schlichtes RTF neu gespeichert. Der Raw-RTF-Modus erlaubt aber direkten Zugriff auf das gespeicherte RTF.
- Sticky/Desktop-Notizen bleiben in der Slint-Hauptoberfläche Metadaten. Zusätzlich gibt es `sticky-run` als optionalen Python/Tk-Ersatz für kleine separate Fenster. In headless Umgebungen oder ohne Tk fällt das sauber mit einer lesbaren Meldung zurück.
- Wecker-Benachrichtigungen sind bewusst best-effort: Linux nutzt `notify-send`, macOS `osascript`, Windows PowerShell/MessageBox. Wenn das jeweilige Werkzeug fehlt oder die Umgebung headless ist, läuft die CLI trotzdem weiter und gibt den Grund aus.
- Trayicon, native Drag-and-drop-Mauslogik und Druckdialog sind nicht 1:1 in der neuen UI enthalten. Die alten Sprachtexte sind als Daten/CLI-Hooks portiert, aber nicht als vollständige dynamische Menüumschaltung jeder Slint-Beschriftung. Autostart, HTML-Export und RTF-Bildzugriff sind portabel nachgebaut, aber nicht identisch mit WinForms.
- Die alte Verschlüsselung ist absichtlich nur kompatibel, nicht sicher. Für echte Sicherheit die `.alx` zusätzlich mit einem modernen Werkzeug verschlüsseln.

## Installation

Für Kern und CLI reicht die editierbare Installation ohne externe Laufzeitpakete:

```bash
cd notizen_py_slint
python3 -m pip install -e .
```

Für die Slint-Oberfläche die UI-Extra-Abhängigkeit installieren:

```bash
cd notizen_py_slint
python3 -m pip install -e ".[slint]"
```

Hinweis: Das Projekt ist ein normales Python-Projekt. Die alte Pinning-Logik für PyPy wurde entfernt. Die Slint-Extra-Abhängigkeit nutzt aktuelle Slint-Python-Versionen (`slint>=1.16.1b1`); Kern und CLI bleiben bewusst ohne Slint lauffähig.

## Starten

GUI:

```bash
python3 -m notizen_py_slint
python3 -m notizen_py_slint pfad/zur/datei.alx
python3 -m notizen_py_slint pfad/zur/datei.alx --password geheim
python3 -m notizen_py_slint 'ftp://user:pass@example.org/notizen.alx'
python3 -m notizen_py_slint /min        # alter Autostart-Alias für --minimized
```

Kompatibilität: `python3 -m notizen_pypy_slint` funktioniert weiterhin als alter Alias, damit vorhandene lokale Aufrufe nicht sofort brechen. Neu bevorzugt ist `python3 -m notizen_py_slint`.

CLI-Fallback ohne Slint:

```bash
notizen-alx tree tests/fixtures/test.alx
notizen-alx stats tests/fixtures/test.alx
notizen-alx search tests/fixtures/test.alx test
notizen-alx export-txt tests/fixtures/test.alx /tmp/notizen.txt --numbered
notizen-alx export-rtf tests/fixtures/test.alx /tmp/notizen.rtf --title "PC" --numbered
notizen-alx export-html tests/fixtures/test.alx /tmp/notizen.html
notizen-alx export-sticky-html tests/fixtures/test.alx /tmp/sticky.html --all
notizen-alx export-note-rtf tests/fixtures/test.alx /tmp/notiz.rtf --title "todo"
notizen-alx dump-xml input.alx /tmp/notizen.xml
notizen-alx pack-xml /tmp/notizen.xml output.alx --password geheim
notizen-alx extract-images input.alx /tmp/notizen-bilder
notizen-alx insert-image input.alx output.alx --title "todo" --image /tmp/bild.png
notizen-alx append-date input.alx output.alx --title "todo"
notizen-alx append-bullet input.alx output.alx --title "todo"
notizen-alx change-password input.alx output.alx --old-password alt --new-password neu
notizen-alx set-note input.alx output.alx --title "todo" --input /tmp/neuer-text.txt
notizen-alx format-note input.alx output.alx --title "todo" --bold --fg-color '#112233'
notizen-alx color-palette
notizen-alx color-note input.alx output.alx --title "todo" --bg-name LightYellow --show
notizen-alx color-note input.alx output.alx --title "todo" --random-bg --random-index 4
notizen-alx style-note input.alx output.alx --title "todo" --style bold
notizen-alx style-note input.alx output.alx --title "todo" --font-family "Arial" --font-size 22 --show
notizen-alx font-size input.alx output.alx --title "todo" --bigger
notizen-alx sticky input.alx output.alx --title "todo" --show --autosize --x 100 --y 100
notizen-alx sticky-list input.alx --all --json
notizen-alx sticky-run input.alx --readonly
notizen-alx rename input.alx output.alx --title "todo" --new-title "erledigen"
notizen-alx add-note input.alx output.alx --title "todo" --new-title "Unterpunkt" --where child
notizen-alx move input.alx output.alx --title "todo" --action down
notizen-alx move-under input.alx output.alx --title "todo" --target-title "Archiv"
notizen-alx duplicate input.alx output.alx --title "todo"
notizen-alx config-read-legacy /pfad/notizen.config.xml
notizen-alx config-import-legacy /pfad/notizen.config.xml
notizen-alx config-set-ftp --host example.org --user name --password geheim --path /pfad/notizen.alx --tls
notizen-alx autostart --enable
notizen-alx alarm-add --name "Review" --at "2026-04-27 09:00" --repeat weekly --weekday mo,mi --message "prüfen"
notizen-alx alarm-list
notizen-alx alarm-next
notizen-alx alarm-due --now "2026-04-27 09:00" --grace-seconds 60 --notify --dry-run
notizen-alx alarm-watch --poll-seconds 30
notizen-alx alarm-remove --name "Review"
notizen-alx config-path
notizen-alx config-set --backup-count 9 --autosave-seconds 60 --language en --autorun --autorun-minimized
notizen-alx config-set --recent /tmp/a.alx --recent /tmp/b.alx --window 50 60 1000 700
notizen-alx lang-list
notizen-alx lang-get Strip1_1 --language en
notizen-alx lang-dump --language de
notizen-alx shortcuts
notizen-alx about --language de
notizen-alx feedback-draft /tmp/feedback.txt.gz --text "Das ist ein lokaler Feedback-Entwurf"
```

FTP/FTPS in der CLI:

```bash
notizen-alx tree 'ftp://user:pass@example.org/pfad/notizen.alx'
notizen-alx change-password local.alx 'ftps://user:pass@example.org/pfad/notizen.alx' --new-password geheim
```

Benutzername/Passwort können in der URL stehen, aus der neuen Konfiguration kommen oder über `~/.netrc` gelesen werden. Ohne Angaben wird anonymes FTP versucht.


### Auswahlnachbau / Plain-Text-Bereiche

Die alte WinForms-RichTextBox arbeitete oft mit der aktuellen Markierung. Slint stellt diese RichTextBox-Markierung nicht nativ bereit; der Port bildet sie deshalb über Klartext-Zeichenbereiche nach. Die Zeichenpositionen beziehen sich immer auf den durch `rtf_to_text` sichtbaren Text der Notiz.

```bash
notizen-alx insert-text input.alx output.alx --title "Todo" --at 6 --text "neuer Text"
notizen-alx insert-text input.alx output.alx --title "Todo" --at 0 --date
notizen-alx delete-range input.alx output.alx --title "Todo" --start 6 --length 4
notizen-alx style-range input.alx output.alx --title "Todo" --start 6 --length 4 --style bold --font-size 24
```

## Tests

```bash
cd notizen_py_slint
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Im Erstellungscontainer wurden die Kern-Tests mit CPython ausgeführt. Slint selbst war dort nicht installiert, daher wurde die GUI nicht gestartet, aber Kern, CLI und Dateiformatpfade wurden geprüft:

```text
Ran 62 tests
OK
```

Getestet wurden:

- DES-Known-Vector
- Notizen-DES-Kaskaden-Roundtrip
- RTF Plain-Text-Konvertierung, RTF-Erkennung, Unicode-Surrogates, Ganznotiz-Formatierung, Toolbar-Stilerkennung, Plain-Text-Range-Ersetzen/-Formatieren, Textgrößenänderung, RTF-Bildextraktion und RTF-Bildeinfügen
- Laden der originalen `test.alx`-Fixture mit 65 Knoten
- Speichern/Laden unverschlüsselt
- Speichern/Laden verschlüsselt
- Speichern/Laden aus Bytes inklusive Sticky-/Farbmetadaten und WinForms-kompatibler signed-ARGB-Ausgabe
- direktes Laden/Speichern von lesbarem XML und Raw-XML-Dump/Pack-Roundtrip
- Kopieren/verschieben/einrücken/ausrücken/duplizieren im Baum
- Suche, Statistik, alte helle Notizen.NET-Farbpalette, `color-note`, `sticky-list` und Legacy-Argumentnormalisierung
- HTML-Export, Sticky-HTML-Export, Bildexport, Bildimport und Notiz-Anhänge
- alte Konfigurationsmigration inklusive FTP-Feldern
- Wecker-Wiederholungen, Wecker-Store, fällige Wecker, Benachrichtigungs-Dry-Run und CLI-Weckerpfade
- CLI-Integrationspfade inklusive XML-Dump/Pack, `style-note`, `insert-text`, `delete-range`, `style-range`, Font-Size, Sticky-Bearbeitung und FTP/FTPS-URL-Parsing
- Sprach-/Übersetzungstabelle aus `languages.vb`, Tastenkürzelmanifest, `config-set`/`config-path`, About-Ausgabe und lokaler Feedback-Draft

## Projektstruktur

```text
src/notizen_py_slint/
  app.py              Slint-Controller
  ui/app-window.slint Slint-Oberfläche
  model.py            Notizbaum-Datenmodell und Baumoperationen
  storage.py          .alx/.xml Laden, Speichern, Export, Import
  remote.py           FTP/FTPS-Transport
  legacy_config.py    alte notizen.config.xml migrieren
  autostart.py        portable Autostart-Einträge
  alarm.py            Wecker-/Erinnerungsregeln
  notify.py           native Best-Effort-Benachrichtigungen ohne externe Pakete
  legacy_colors.py    alte Notizen.NET-Farbpalette und signed-ARGB-Kompatibilität
  sticky_runtime.py   optionale Tk-Sticky-Fenster und normalisierte Sticky-Spezifikationen
  translations.py     alte languages.vb-Texte und Sprachschlüssel
  shortcuts.py        alte Tastenkürzel aus Notizen.tastendruck
  feedback.py         lokales GZip-/UTF-16-Feedback-Draftformat
  des_compat.py       pure-Python DES/CBC-Kompatibilität
  rtf.py              RTF<->Text-Konvertierung, einfache Formatierung, Bildzugriff
  cli.py              CLI-Fallback ohne Slint
  config.py           JSON-Konfiguration
  dialogs.py          Tkinter-/Konsolen-Dialoge
```

## Lizenz

Der Ursprungscode steht unter GPL-3.0. Dieser Port behält die GPL-Lizenz bei; siehe `LICENSE`.
