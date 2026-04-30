# Notizen Py Slint

Das ist ein Python-orientierter Port von **Notizen.NET** aus dem gelieferten VB.NET/WinForms-Projekt. Der alte Code wurde nicht nur zeilenweise umgeschrieben: Dateiformat, Notizbaum, RTF-Textinhalt, Sicherheitskopien, Konfiguration, FTP-Transport, Wecker-Logik und die historische DES-Kaskadenverschlüsselung wurden als pure-Python-Kern neu aufgebaut. Die Oberfläche liegt als Slint-Datei plus Python-Controller vor.

## Status

Funktioniert im Port:

- `.alx` laden und speichern
- GZip-komprimiertes UTF-16-XML-Format `<notizen-alx2>` lesen/schreiben
- verschlüsselte `.alx`-Dateien lesen/schreiben, kompatibel zur alten dreifachen DES-CBC-Kaskade mit den alten Passwort-Slicing-Eigenheiten
- Notizbaum anzeigen, Kind-/Nachbarnotizen anlegen, löschen, duplizieren, kopieren/ausschneiden/einfügen
- portable Notizen-Zwischenablage für ganze Teilbäume, inklusive Datei-Zwischenablage und Best-Effort-Systemclipboard
- Knoten hoch/runter verschieben, einrücken, ausrücken, unter Zielknoten hängen sowie relativ als Kind/vor/nach Zielknoten verschieben oder kopieren
- Suche über Titel und Text, einmalig, als Trefferliste oder als exakte alte `suchergebnisse.SelectionStart`-Trefferpositionen; in der UI jetzt mit Groß-/Kleinschreibung, Ganzwortsuche und Suche nur im aktuellen Teilbaum
- OPML-Export und -Import mit optionalen privaten Notizen-Metadaten für RTF, Text, Farben, Sticky-Fenster und Auf-/Zu-Zustand
- TXT-, RTF-, Markdown-, JSON-, HTML-, OPML- und eigenständiger `.alx`-Export für ganze Datei oder ausgewählten Teilbaum
- Legacy-TXT-Export mit CRLF und wählbarem Windows-Codepage-Encoding sowie Einheit/Zusammenfassen-RTF-Export nach altem Workflow
- Roh-RTF einer einzelnen Notiz exportieren, Text/RTF in aktuelle Notiz importieren
- PNG/JPEG/BMP als RTF-`\pict` an Notizen anhängen
- eingebettete RichTextBox-/RTF-Bilder aus alten Notizen extrahieren
- Datum/Uhrzeit und Aufzählungszeichen an Notizen anhängen
- einfache Ganznotiz-Formatierung als portabler Ersatz für RichTextBox-Auswahlformatierung
- auswahlbezogene RichTextBox-Aktionen als Plain-Text-Range-Operationen im Python-Kern und in der CLI: Text einfügen, Bereich löschen und Bereich formatieren
- RichTextBox-Toolbar-Stile `B`, `I`, `U`, `S` und `Normal` als Ganznotiz-Aktionen in UI und CLI sowie als Bereichsformatierung per `style-range`
- Textgröße per A+/A- beziehungsweise CLI wie im alten Ctrl+Plus/Ctrl+Minus-Workflow ändern
- Raw-RTF-Modus in der UI, damit alte RichTextBox-Inhalte notfalls direkt bearbeitet werden können
- alte Intellibit-`notes_doc`-Dateien importieren und wieder als `notes_doc`/`node`/`leaf`-XML exportieren
- aufgeklappte/eingeklappte Baumzustände skriptbar setzen
- Sticky/Desktop-Notiz-Metadaten lesen, speichern, sichtbar/unsichtbar schalten, Geometrie/Farbe bearbeiten, alte Transparenz-Menüwerte abbilden, automatisch grob dimensionieren, als HTML-Board exportieren und optional als kleine Tk-Fenster öffnen
- Knotenfarben (`bgcolor`, `fgcolor`) lesen, speichern, löschen, per alter heller Notizen.NET-Palette setzen und wieder als WinForms-kompatible signed ARGB-Werte schreiben
- alte `Datei.vb`-Standardpfade (`~/Documents/Notizen/unbenannt.alx`) berechnen, bei Bedarf anlegen und neue Dateien dort initialisieren
- Kompatibilitätsbericht für `.alx`/`.xml`-Dateien mit Format-, Verschlüsselungs-, RTF-, Farb-, Sticky- und Strukturhinweisen
- Sicherheitskopien beim lokalen Speichern und Autosave-Timer aus der Konfiguration
- alte `notizen.config.xml` lesen/importieren/exportieren, inklusive Backup-Anzahl, Autosave, Autostart, Fensterdaten, Sticky-Rahmen und FTP-Feldern
- portabler Autostart-Stub für Linux, Windows und macOS aus der neuen Konfiguration
- FTP/FTPS laden und speichern über `ftp://`/`ftps://`-URLs, inklusive `.netrc`-Fallback und migrierbarem Standardziel
- Wecker-/Erinnerungsregeln mit einmaliger, täglicher, wöchentlicher, monatlicher und jährlicher Wiederholung
- fällige Wecker prüfen beziehungsweise als dauernde CLI-Schleife beobachten, optional mit nativer Best-Effort-Desktop-Benachrichtigung über Plattformwerkzeuge
- alte Sprachtexte aus `languages.vb` als Python-Tabelle mit CLI-Abfrage, About-Text und UI-Info-Hook
- alte Tastenkürzel aus `Notizen.tastendruck` als dokumentiertes Manifest mit CLI-Ausgabe und UI-Kurzhinweis
- alte WinForms-Kontextmenüs aus `kontext_inhalt.vb`, `Baum_Kontext_.vb`, `desknote_kontext.vb` und der Desktop-Notiz-Transparenzauswahl als Portierungsmanifest mit CLI- und UI-Hook
- allgemeine Konfigurationsschalter per `config-set`/`config-path`, damit Teile des alten Einstellungsdialogs auch ohne GUI skriptbar sind
- installierte Systemschriften portabel auflisten, damit alte Font-Dialog-/Toolbar-Arbeitsweisen besser nachbaubar sind
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
notizen-alx search tests/fixtures/test.alx test --occurrences --json
notizen-alx search-occurrences tests/fixtures/test.alx test --json
notizen-alx export-alx tests/fixtures/test.alx /tmp/teilbaum.alx --title "PC"
notizen-alx export-notes-doc tests/fixtures/test.alx /tmp/notizen-notes-doc.xml
notizen-alx export-opml tests/fixtures/test.alx /tmp/notizen.opml
notizen-alx import-opml input.alx output.alx --title "Archiv" --input /tmp/notizen.opml
notizen-alx expand-state input.alx output.alx --title "Archiv" --collapsed
notizen-alx font-list --contains Arial --limit 20
notizen-alx default-paths --json
notizen-alx init-file ~/Documents/Notizen/unbenannt.alx --title "Notes" --text "erste Notiz"
notizen-alx compat-report tests/fixtures/test.alx --json
notizen-alx export-txt tests/fixtures/test.alx /tmp/notizen.txt --numbered
notizen-alx export-rtf tests/fixtures/test.alx /tmp/notizen.rtf --title "PC" --numbered
notizen-alx export-html tests/fixtures/test.alx /tmp/notizen.html
notizen-alx export-legacy-txt tests/fixtures/test.alx /tmp/notizen-win.txt --encoding cp1252
notizen-alx export-unity-rtf tests/fixtures/test.alx /tmp/einheit.rtf
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
notizen-alx sticky input.alx output.alx --title "todo" --show --opacity-choice "90%"
notizen-alx sticky-opacity --json
notizen-alx sticky-list input.alx --all --json
notizen-alx sticky-run input.alx --readonly
notizen-alx rename input.alx output.alx --title "todo" --new-title "erledigen"
notizen-alx add-note input.alx output.alx --title "todo" --new-title "Unterpunkt" --where child
notizen-alx move input.alx output.alx --title "todo" --action down
notizen-alx move-under input.alx output.alx --title "todo" --target-title "Archiv"
notizen-alx move-relative input.alx output.alx --title "todo" --target-title "Archiv" --where after
notizen-alx copy-relative input.alx output.alx --title "todo" --target-title "Archiv" --where child
notizen-alx duplicate input.alx output.alx --title "todo"
notizen-alx copy-node input.alx --title "todo" --clipboard /tmp/notizen-clip.json
notizen-alx paste-node input.alx output.alx --target-title "Archiv" --where child --clipboard /tmp/notizen-clip.json
notizen-alx clipboard-show --clipboard /tmp/notizen-clip.json --json
notizen-alx context-menus --menu tree --include-opacity
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
Ran 83 tests
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
- CLI-Integrationspfade inklusive XML-Dump/Pack, `style-note`, `insert-text`, `delete-range`, `style-range`, `search --occurrences`, `search-occurrences`, `export-alx`, `export-opml`, `import-opml`, `expand-state`, `font-list`, `context-menus`, portable TreeView-Zwischenablage, Font-Size, Sticky-Bearbeitung und FTP/FTPS-URL-Parsing
- Sprach-/Übersetzungstabelle aus `languages.vb`, Tastenkürzelmanifest, `config-set`/`config-path`, ToolStrip-Positionsmigration, OPML-Roundtrip, Teilbaum-ALX-Export, Systemfont-Scanner, Passwort-Kompatibilitätsdiagnose, Reparaturlauf, About-Ausgabe und lokaler Feedback-Draft

## Projektstruktur

```text
src/notizen_py_slint/
  app.py              Slint-Controller
  ui/app-window.slint Slint-Oberfläche
  model.py            Notizbaum-Datenmodell und Baumoperationen
  storage.py          .alx/.xml Laden, Speichern, Export, Import
  remote.py           FTP/FTPS-Transport
  legacy_config.py    alte notizen.config.xml migrieren
  passwords.py        alte 24-Zeichen-Passwortnormalisierung und DES-Key-Segmente
  repair.py           Migrations-/Reparaturlauf für alte/metadatenfehlerhafte Dateien
  autostart.py        portable Autostart-Einträge
  alarm.py            Wecker-/Erinnerungsregeln
  notify.py           native Best-Effort-Benachrichtigungen ohne externe Pakete
  legacy_colors.py    alte Notizen.NET-Farbpalette und signed-ARGB-Kompatibilität
  legacy_sticky.py    alte Desktop-Notiz-Transparenzauswahl
  context_menus.py    alte WinForms-Kontextmenüs als Manifest
  clipboard.py        portable Teilbaum-Zwischenablage
  opml.py             OPML-Export/-Import mit privaten Notizen-Metadaten
  fonts.py            portable Systemfont-Erkennung
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

## Neu in v13 / 0.13.0

Dieser Schritt zieht drei alte Randbereiche nach, die im Alltag wichtig sind:

- `Datei.vb`-Verhalten: `default-paths` berechnet den alten Standardordner `Documents/Notizen` und `init-file` legt eine neue `.alx` mit Startnotiz an.
- Alte Intellibit-Kompatibilität: `export-notes-doc` schreibt wieder das historische `notes_doc`/`node`/`leaf`-XML, das der Port bereits lesen konnte.
- Migrationsprüfung: `compat-report` zeigt Format, Verschlüsselungsstatus, Strukturgrößen und Warnungen zu Plain-Text-Inhalten, transparenten Farben, Sticky-Geometrie und leeren Titeln.

In der Slint-Oberfläche sind dafür die Hooks `NotesDoc`, `Compat` und `Pfade` ergänzt.



## Neu in v14 / 0.14.0

Dieser Schritt zieht weitere alte Dialog- und Migrationsdetails nach:

- `password-info` und `password-normalize` bilden die alte Passwortdialog-Logik nach: Passwörter werden wie im Original auf 24 Zeichen gebracht, zu lange Werte werden abgeschnitten, zu kurze mit Leerzeichen gefüllt, und die drei alten DES-Schlüsselbereiche werden diagnostisch angezeigt. Standardmäßig werden sensible Werte maskiert; `--reveal` zeigt sie bewusst an.
- `repair` normalisiert alte oder malformierte Dateien: leere Titel werden ersetzt, Plain-Text-Inhalte werden als RTF gespeichert, transparente Farben werden bereinigt, Sticky-Größen und Deckkraft werden geklemmt und ARGB-Werte werden wieder WinForms-kompatibel als signed Integer geschrieben.
- Die alten `xml_kram.vb`-ToolStrip-Positionen werden aus `notizen.config.xml` migriert und mit `toolstrips` beziehungsweise `config-set --toolstrip NAME X Y` bearbeitbar.
- Die Slint-Oberfläche hat dafür neue Hooks `PwInfo`, `Reparieren` und `ToolStrips`.
- Der große CLI-Parser wird nun pro Prozess gecacht; dadurch bleiben wiederholte In-Process-Aufrufe wie in Tests, Skripten oder eingebetteten Workflows stabil und schneller. Der Sticky-Befehl hat zusätzlich einen kleinen Direktparser für den alten Desktop-Notiz-Hotpath.


## Neu in v17 / 0.17.0

Dieser Schritt greift die drei gemeldeten UI-Probleme gezielt an:

- Der Text-/RTF-Bereich hat jetzt ebenfalls eine Rechtsklick-Fläche über dem tatsächlichen Editorbereich. Rechtsklick im Text öffnet das RTF-Kontextpanel; die schmale `☰`-Leiste und der `RTF Kontext`-Button bleiben nur als Fallback erhalten.
- Die obere Buttonzone ist deutlich höher und stärker aufgeteilt: statt einer gedrängten Leiste gibt es zwölf thematische Zeilen für Datei, Fenster, Export, Import, Baum, RTF, Suche, Sticky/Farbe, Info und Extras. Die Toolbar ist jetzt `540px` hoch.
- Das Slint-Fenster verwendet keine feste `width`/`height` mehr. Die Startgröße läuft über `preferred-width`/`preferred-height`, die Mindestgröße über `min-width`/`min-height`. Dadurch kann der Fenstermanager das Fenster wieder normal resizen und maximieren.
- Zusätzlich gibt es oben eine kleine Fenster-Zeile mit `Max` und `Vollbild`. `Max` nutzt die Slint-Python-Maximize-API, falls die installierte Slint-Version sie anbietet; `Vollbild` nutzt die portable Slint-Property `full-screen`.
- `ContextMenuArea`, `Menu`, `MenuItem` und `MenuSeparator` bleiben weiterhin entfernt, damit die UI auch mit Slint-Versionen kompiliert, die diese nativen Menüelemente noch nicht kennen.
- Für das Baum-Kontextpanel bleibt der Callback `rename-row(int)` erhalten, damit Umbenennen direkt auf der rechtsgeklickten Zeile arbeitet.

## Neu in v18 / 0.18.0

Dieser Schritt repariert den von Slint gemeldeten Compilefehler `Unknown property full-screen in Window`:

- Die Slint-Datei nutzt keine `full-screen`-Property mehr. Der Button `Vollbild Start` bleibt vorhanden, aber die Umschaltung läuft nur noch über optionale Python-/Backend-APIs, wenn die installierte Slint-Version sie anbietet. Ohne passende API bleibt das Fenster normal nutzbar und zeigt eine Statusmeldung; Start-Vollbild kann zusätzlich mit `--fullscreen` beziehungsweise `/fullscreen` angefragt werden.
- Das Fenster bleibt resizable: am Root-`Window` stehen weiterhin keine festen `width`/`height`-Werte, sondern `preferred-width`, `preferred-height`, `min-width` und `min-height`.
- Die obere Buttonzone ist erneut höher und stärker aufgeteilt: `760px` Toolbar-Höhe, `preferred-height: 1360px`, `min-height: 900px` und zusätzliche Reihen für Datei, Export, Baum, Info und Extras. Dadurch laufen die langen Button-Gruppen nicht mehr so schnell ineinander. Zusätzlich akzeptiert der alte Kompatibilitätsstarter jetzt `/fullscreen`, `/fs`, `/max` und `--maximized`.
- Die Kontextmenüs im Baum und im Textbereich bleiben als Slint-kompatible Overlay-Panels aus normalen Elementen erhalten; es werden weiterhin keine `ContextMenuArea`-/`MenuItem`-Typen verwendet.

Start:

```bash
python3 -m notizen_py_slint
```

Die alte Weiterleitung bleibt ebenfalls erhalten:

```bash
python3 -m notizen_pypy_slint
```

## Neu in v19 / 0.19.0

- Obere Toolbar von 760px auf 184px zurückgebaut, aber horizontal in vier Gruppen aufgeteilt.
- Fenstergeometrie auf `preferred-width: 1280px`, `preferred-height: 860px`, `min-width: 760px`, `min-height: 520px` geändert, damit Resize/Maximieren praktikabler wird.
- Buttons, die bereits im Baum-Kontextmenü oder RTF/Text-Kontextmenü liegen, wurden aus der oberen Leiste entfernt.
- Baum-Kontextmenü zweispaltig erweitert: Bearbeiten, Ansicht/Ordnen, Sticky/Farben.
- RTF/Text-Kontextmenü zweispaltig erweitert: Bearbeiten/Suche links, Format/Roh-RTF rechts.
