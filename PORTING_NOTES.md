# Portierungsnotizen

## Herkunft

Der Ausgangscode ist das gelieferte VB.NET/WinForms-Projekt **Notizen.NET**. Relevante alte Dateien:

- `Notizen.vb`: Hauptformular, Speichern/Laden, Verschlüsselung, Export, Tastatur-/Toolbar-Logik
- `Baum.vb`: TreeView-Operationen, Anlegen/Löschen, Verschieben per Drag-and-drop
- `CText.vb` und `inhalt.vb`: Knoteninhalt als RichTextBox-RTF
- `desknote.vb`: Desktop-/Sticky-Notizen
- `xml_kram.vb`: Konfigurations-/Autostart-Fragmente
- `ftpkram.vb`: FTP-Konfiguration der alten Anwendung
- `kontext_inhalt.vb`: Kontextmenü für Kopieren/Ausschneiden/Einfügen, Bild einfügen, Datum, Löschen und Suchen
- `wecker.vb`: Wecker-/Wiederholungsdialog

## Weiterer Transpilationsstand

Diese Runde baut auf dem Python-Stand auf und zieht weitere alte Bedienlogik in portable Python-/Slint-Form:

- Baumoperationen: kopieren, ausschneiden, einfügen, duplizieren, hoch/runter, einrücken, ausrücken
- alte Drag-and-drop-Verschiebeidee als explizite Buttons/Methoden, weil Slint/Python hier portabler ist als native Maus-TreeView-Draglogik
- Teilbaum-Export ähnlich der alten „Einheit/Zusammenfassen“-Funktion, jetzt als nummerierter TXT-/RTF-Export
- Roh-RTF-Modus, damit RichTextBox-Daten nicht nur nach Plain-Text konvertiert werden müssen
- Text-/RTF-Import in die aktuelle Notiz
- RichTextBox-Kontextfunktionen als portable Aktionen: Datum anhängen, Aufzählungszeichen anhängen, Bild anhängen
- PNG/JPEG/BMP als RTF-`\pict`-Gruppen an Notizen anhängen
- RTF-Bilder aus alten `\pict`-Gruppen extrahieren
- Sticky-Metadaten-Editor für `visible`, `x`, `y`, `width`, `height`, `opacity`, `argb` plus normalisierte Sticky-Fenster-Spezifikationen für CLI, HTML und den optionalen Tk-Laufzeitmodus
- Knotenfarben `bgcolor` und `fgcolor` werden wie im Original als signed `Color.ToArgb()`-Werte geschrieben, können bearbeitet werden und nutzen auf Wunsch die alte helle Zufallspalette aus `get_lightcolor()`
- FTP/FTPS-Transport mit `ftp://`/`ftps://`-URLs, `.netrc`-Fallback und migrierbarer Standardverbindung
- CLI erweitert um Statistik, Suche, XML-Dump/Pack, Einzelnotiz-RTF-Export, Notizinhalt ersetzen, Bewegung, Duplizieren, strukturelles Einfügen/Löschen/Umbenennen, Bild einfügen, Datum/Bullet anhängen und FTP-Konfiguration
- HTML-Export als portabler Ersatz für Drucken/Vorschau-Zusammenfassungen
- einfache Ganznotiz-Formatierung (`bold`, `italic`, `underline`, `strike`, Vorder-/Hintergrundfarbe, Schriftfamilie/-größe)
- RichTextBox-Toolbar-Buttons `B`, `I`, `U`, `S` und `Normal` aus der alten UI als Ganznotiz-Aktionen in Slint und als CLI-Befehl `style-note`
- globale RTF-Stilerkennung, damit vorhandene einfache RichTextBox-RTF-Dokumente beim Umformatieren Schriftfamilie/Schriftgröße/Stil sinnvoll weitertragen
- Ctrl+Plus/Ctrl+Minus aus `Notizen.vb` als RTF-weite Textgrößenänderung (`font-size`, A+/A-) portiert
- Suchoptionen aus der alten Dialog-/Suchlogik als UI-Checkboxen: Groß-/Kleinschreibung, Ganzwortsuche, nur aktueller Teilbaum; zusätzlich gibt es eine globale Ersetzen-Aktion für den gefundenen Textbereich
- Sticky-Autogröße, Sticky-HTML-Board und optionales `sticky-run` mit kleinen Tk-Fenstern als portabler Ersatz für Teile von `desknote.vb`
- alte `notizen.config.xml` aus `xml_kram.vb` lesen, in die neue JSON-Konfiguration übernehmen und diagnostisch wieder als alte XML-Struktur schreiben
- Autostart portabel nachgebaut: `.desktop` unter Linux, `.cmd` im Windows-Startup-Ordner, LaunchAgent unter macOS
- Autosave-Timer aus der Konfiguration für lokale Dateien
- Wecker-Regeln mit einmaliger, täglicher, wöchentlicher, monatlicher und jährlicher Wiederholung als speicherbare Python-Logik plus CLI/UI-Hooks
- fällige Wecker (`alarm-due`) und eine einfache dauernde Wecker-Schleife (`alarm-watch`) als portabler Ersatz für die alte Popup-Auslösung
- native Best-Effort-Benachrichtigung ohne externe Pakete: `notify-send` unter Linux/BSD, `osascript` unter macOS, PowerShell-MessageBox unter Windows
- alte `languages.vb`-Tabelle plus `lang_keys`-Enum als `translations.py` portiert; die CLI kann einzelne Schlüssel, ganze Sprachlisten und den alten About-Text ausgeben
- alte Tastaturbelegung aus `Notizen.tastendruck` als Manifest in `shortcuts.py` portiert, inklusive Ctrl+S/O/N/Q, Ctrl+F, Ctrl+Plus/Minus und TreeView-Tasten
- weitere Felder des alten Einstellungsdialogs sind per `config-set` skriptbar: Sprache, Backup/Autosave, Autostart, Fensterposition, Taskbar-/Sticky-Rahmen-Optionen und zuletzt geöffnete Dateien
- Feedback aus `info_help_and_feedback.vb` wird als lokales GZip-/UTF-16LE-Draftformat erzeugt; der alte harte FTP-Upload wurde bewusst nicht automatisiert
- Auswahl-/Kontextmenülogik aus `kontext_inhalt.vb` und den RichTextBox-Toolbar-Handlern wird weiter nachgezogen: Text kann an einer Klartextposition eingefügt, ein Klartextbereich gelöscht und ein Klartextbereich lokal als RTF-Gruppe formatiert werden
- `document_to_xml_bytes` schreibt wieder genau einen Top-Level-Root-Knoten; zusätzliche Top-Level-Notizen werden nur noch defensiv beim Laden malformed/alter Dateien zusammengeführt

## Dateiformat

Das alte Hauptformat ist:

```xml
<notizen-alx2>
  <Notiz name="..." isexpanded="True" bgcolor="0" fgcolor="0">RTF...</Notiz>
</notizen-alx2>
```

Desktop-/Sticky-Notizen hängen als Attribute am selben `Notiz`-Element:

```xml
visible="True" x="100" y="100" width="260" height="180" opacity="0.85" argb="-1"
```

Der Port schreibt weiterhin UTF-16-XML, komprimiert mit GZip. Farbwerte werden beim Schreiben auf signed 32-Bit-ARGB normalisiert, weil WinForms `Color.ToArgb()` im alten Code ebenfalls signed Integer in XML serialisierte. Bei gesetztem Passwort wird anschließend die historische dreifache DES-CBC-Kaskade verwendet. Zusätzlich kann der Python-Kern lesbares Roh-XML direkt laden/speichern und per CLI mit `dump-xml`/`pack-xml` zwischen XML und `.alx` wechseln.

## Verschlüsselung

Die alte Anwendung verwendet drei DES-Provider mit überlappenden 8-Byte-Schlüsseln:

- `p.Substring(0, 8)`
- `p.Substring(7, 8)`
- `p.Substring(15, 8)`

Key und IV sind jeweils identisch. Das ist kryptographisch schwach, wird aber zur Dateikompatibilität nachgebaut. Der Port implementiert DES und CBC vollständig in Python, damit der Kern ohne OpenSSL-/Crypto-Abhängigkeit unter Python läuft.

## RTF und Bilder

Slints `TextEdit` ist kein RichTextBox-Ersatz. Deshalb gibt es zwei Modi:

- Textmodus: gespeichertes RTF wird best-effort zu Plain-Text konvertiert; Änderungen werden als schlichtes RTF gespeichert.
- Raw-RTF-Modus: der gespeicherte RTF-String wird direkt editiert/exportiert/importiert.

Damit bleiben alte formatierte Inhalte erreichbar, auch wenn die neue UI keine vollständige Rich-Text-Bearbeitung bietet. Zusätzlich kann der Port Bilder aus `\pict`-Gruppen extrahieren und PNG/JPEG/BMP wieder als `\pict`-Gruppen anhängen. Die alten gemischten RichTextBox-Formatierungen werden nicht vollständig wie in WinForms nachgebildet; `format-note`, `style-note` und die Slint-Buttons arbeiten bewusst stabil auf Ganznotizebene. Für gezielte Bearbeitung gibt es zusätzlich die Plain-Text-Range-Funktionen `insert-text`, `delete-range` und `style-range`.

## Alte Konfiguration, FTP und Autostart

`xml_kram.vb` schrieb die alte `notizen.config.xml` unter anderem mit Backup-Anzahl, Autosave-Sekunden, zuletzt geöffneten Dateien, Sprache, Fensterposition, Sticky-Rahmen, Autostart-Werten und FTP-Feldern. Der Port migriert diese Felder nach `~/.config/notizen-py-slint/config.json` beziehungsweise unter Windows nach `%APPDATA%`.

Die alte FTP-Konfiguration aus `ftpkram.vb` (`name`, `pass`, `host`, `path`) wird in die neue Konfiguration übernommen und kann als Standard-Remote-URL genutzt werden. Der eigentliche Transport nutzt nur die Standardbibliothek (`ftplib`) und unterstützt:

- `ftp://user:pass@host/path/file.alx`
- `ftps://user:pass@host/path/file.alx`
- Zugangsdaten aus `~/.netrc`, wenn sie nicht in der URL stehen

Backups werden nur lokal erzeugt. Bei Remote-Speichern wird direkt hochgeladen.

Der alte Windows-spezifische Autostart wurde nicht per Registry/COM 1:1 übernommen. Stattdessen erzeugt der Port plattformübliche Starterdateien und akzeptiert `--minimized` sowie die alten Kürzel `/min`, `-min`, `min`, `/h` und `/?` als kompatible Startargumente. `--minimized` ist momentan ein akzeptierter, aber nicht fensterzustandswirksamer Startmodus.

## Sprache, Tastenkürzel und Feedback

`languages.vb` enthält eine aktive sechsspaltige Übersetzungstabelle für Deutsch, Englisch, Chinesisch, Französisch, Spanisch und Russisch. Der Port hat diese Tabelle mit den `lang_keys` aus `Notizen.vb` in `translations.py` übernommen. Damit sind alte Menü-/Dialogtexte nicht mehr verloren, auch wenn die Slint-Oberfläche noch keine vollständige Live-Umschaltung aller sichtbaren Labels macht. Über `lang-list`, `lang-get`, `lang-dump` und `about` lassen sich die Daten prüfen und weiterverwenden.

Die alte globale Tastaturbehandlung aus `Notizen.tastendruck` wurde als Manifest portiert. Slint/Python bildet nicht jede WinForms-Accelerator-Route identisch nach, aber die Zuordnung ist dokumentiert, testbar und kann von CLI/UI-Teilen genutzt werden.

Der alte Feedback-Dialog packte Text als GZip über .NET `Encoding.Unicode` und lud ihn zu einem fest verdrahteten FTP-Ziel hoch. Der Port erzeugt denselben Payload lokal (`feedback-draft`), sendet aber nichts automatisch. Das ist die richtige Grenze: Dateikompatibilität ja, ungefragter Upload an historische Server nein.

## Wecker

`wecker.vb` war stark WinForms-Dialoglogik: Auswahl von Wiederholungsart, Intervall und Wochentagen. Der Port übersetzt diesen Teil als Datenmodell in `alarm.py`. Regeln werden als JSON gespeichert und können per CLI/UI angelegt, entfernt und abgefragt werden.

Neu ist ein tatsächlicher Auslösepfad ohne externe Pakete:

- `notizen-alx alarm-due` prüft fällige Alarme in einem Zeitfenster.
- `notizen-alx alarm-watch` läuft dauerhaft, prüft periodisch und meldet Treffer.
- `notify.py` versucht Desktop-Benachrichtigungen über vorhandene Plattformwerkzeuge.

Das ist kein vollständiger Dienst/Daemon und kein WinForms-Popup mit eigener Dialogoberfläche, aber es schließt die wichtigste funktionale Lücke: gespeicherte Erinnerungen können jetzt auslösen.

## Nicht 1:1 portiert

Nicht sinnvoll 1:1 übernommen wurden:

- WinForms-Trayicon als natives System-Tray-Objekt
- separate borderlose WinForms-Desktop-Sticky-Fenster; `sticky-run` bietet einen optionalen Tk-Nachbau, ist aber bewusst kein 1:1-WinForms-Fenster mit identischem Verhalten
- native TreeView-Drag-and-drop-Gesten
- Druckdialog; HTML-Export dient als portabler Ersatz
- vollständige Live-Umschaltung jeder Slint-Menübeschriftung; die alten Sprachdaten selbst sind aber portiert und per CLI/UI-Hook verfügbar
- echte RichTextBox-Auswahlformatierung mit gemischten Fonts/Farben pro Zeichenbereich
- permanenter OS-Hintergrunddienst für Wecker/Tray
- automatischer Feedback-Upload zum alten FTP-Ziel

Diese Punkte sind entweder stark Windows-/WinForms-spezifisch oder passen nicht sauber zu Python/Slint. Die zugrunde liegenden Daten werden aber so weit wie möglich erhalten.

## v11: TreeView-Zwischenablage, relative Baumoperationen und Legacy-Exporte

Der nächste Portierungsschritt zieht weitere WinForms-TreeView-Aktionen nach. Ganze Teilbäume können jetzt in eine portable JSON-Zwischenablage geschrieben, als Text angezeigt, optional in die System-Zwischenablage gelegt und relativ zu einem Zielknoten wieder eingefügt werden. Das bildet die alten `Ctrl+C`/`Ctrl+X`/`Ctrl+V`- und `Shift+Insert`/`Shift+Delete`-Arbeitsweisen ohne native TreeView-Abhängigkeit ab.

Zusätzlich gibt es `move-relative` und `copy-relative` für die alten Kontext-/Drag-Zielpositionen Kind, davor und danach. Ungültige Strukturen werden verhindert: die Wurzel wird nicht verschoben, ein Knoten kann nicht in seinen eigenen Unterbaum verschoben werden und Geschwisterpositionen um die Wurzel herum sind nicht erlaubt.

Der alte Exportpfad aus `Notizen.vb` wurde weiter angenähert: `export-legacy-txt` normalisiert auf CRLF und schreibt mit wählbarem Encoding, standardmäßig `cp1252`; `export-unity-rtf` erzeugt einen RTF-Outline-Export im Geist der alten Einheit/Zusammenfassen-Funktion. Für Desktop-Notizen ist außerdem die alte Transparenzauswahl `90 %` bis `0 %` als `sticky-opacity` beziehungsweise `--opacity-choice` portiert.

Ergänzt wurde außerdem die alte Suchergebnisform aus `suche.vb`/`suchergebnisse.vb`: `find_occurrences` und `search --occurrences` liefern jetzt genaue sichtbare Textpositionen für Titel und Inhalt, also den funktionalen Ersatz für `SelectionStart`. Die WinForms-Kontextmenüs aus `kontext_inhalt.vb`, `Baum_Kontext_.vb`, `desknote_kontext.vb` und `desknote_kontext_opacy.vb` liegen als `context_menus.py` vor und sind per `notizen-alx context-menus` sowie im Slint-Infofeld abrufbar.


## v12: OPML, Teilbaum-ALX, sichtbare Treffer und Schriftliste

Dieser Schritt ergänzt Export-/Importpfade, die früher in mehreren WinForms-Menüs verteilt waren. Ganze Dateien oder ausgewählte Teilbäume können jetzt als eigenständige `.alx` exportiert werden. Zusätzlich gibt es OPML-Export und -Import. OPML ist absichtlich als portables Outline-Format gehalten; optionale private `_notizen_*`-Attribute bewahren RTF, Klartext, Farben, Sticky-Metadaten und den Auf-/Zu-Zustand, ohne fremde OPML-Leser zu blockieren.

Die Suchlogik wurde um einen eigenen `search-occurrences`-Befehl erweitert. Er liefert Treffer nicht nur pro Notiz, sondern mit Feld, Start-/Endposition, Trefferindex, Pfad und Snippet. Das ist der robustere Python-Ersatz für die alten `SelectionStart`-basierten Suchergebnislisten.

`expand-state` macht gespeicherte Baumzustände per CLI setzbar, inklusive einer Option, die Wurzel beim Massenlauf nicht zu schließen. `font-list` scannt installierte Systemschriften ohne externe Pakete über Font-Dateien und nutzt bei unlesbaren Dateien einen Dateinamen-Fallback. Damit sind alte Font-Dialog-/Toolbar-Arbeitsweisen besser skriptbar, auch wenn Slint weiterhin keinen WinForms-Fontdialog nachbildet.

## v13: Datei.vb-Standardpfade, notes_doc-Export und Kompatibilitätsbericht

Dieser Schritt schließt weitere alte Randlogik aus dem WinForms-Projekt. `paths.py` bildet das frühere `Datei.vb`-Verhalten nach: Der alte Standardordner liegt unter `Documents/Notizen`, die Standarddatei heißt `unbenannt.alx`, und `notizen-alx default-paths` beziehungsweise `notizen-alx init-file` machen diesen Workflow auch ohne GUI nutzbar.

Die alte Intellibit-Struktur wurde bisher gelesen, aber nicht wieder geschrieben. Mit `intellibit.py` und `export-notes-doc` kann der Port nun wieder `notes_doc`-XML mit `node`/`leaf` und `leaf_text`/`p` erzeugen. Damit ist ein zusätzlicher Roundtrip-Pfad für sehr alte oder fremde Notizen-Dateien vorhanden, auch wenn das bevorzugte neue Format weiterhin `notizen-alx2` bleibt.

Neu ist außerdem `compat.py`: `notizen-alx compat-report` analysiert lokale `.alx`- und `.xml`-Dateien und meldet Format, vermutete Verschlüsselung, Strukturgrößen, RTF-/Plain-Anteile, Bilder, Farben, Sticky-Metadaten, zugeklappte Knoten und konkrete Warnungen. Dadurch lassen sich Migrationen gezielter prüfen, bevor Dateien im neuen Port weiterbearbeitet werden.

In der Slint-Datei wurden passende Hooks ergänzt: `NotesDoc` exportiert den aktuellen Teilbaum in das alte XML-Format, `Compat` zeigt die Diagnose im Infofeld, und `Pfade` zeigt die alten Standardpfade. Nebenbei wurde die doppelte `Import OPML`-Schaltfläche bereinigt.


## v14: Passwortdialog, ToolStrip-Positionen und Reparaturlauf

Die alte Verschlüsselung hatte eine leicht ungewöhnliche Passwortaufbereitung: der Dialog arbeitete effektiv mit 24 Zeichen, füllte kürzere Eingaben mit Leerzeichen auf und schnitt längere Werte ab. Zusätzlich entstehen die drei DES-Schlüsselbereiche nicht als saubere 8/8/8-Aufteilung, sondern mit dem historischen Überlappungsversatz aus dem Originalcode. `passwords.py` macht diese Regeln explizit und prüfbar, ohne Passwörter versehentlich im Klartext auszugeben.

`xml_kram.vb` speicherte neben Fenster- und FTP-Daten auch ToolStrip-Koordinaten. Diese Werte haben in Slint keine direkte Layoutwirkung, werden aber jetzt migriert, im neuen JSON erhalten und über `toolstrips` beziehungsweise `config-set --toolstrip` bearbeitbar gemacht. Damit gehen alte Layoutdaten bei Migrationen nicht verloren.

`repair.py` ergänzt eine vorsichtige Normalisierungsschicht für reale Altdateien: Plain-Text-Knoten werden in RTF gewandelt, leere Titel markiert, vollständig transparente Farben entfernt, Sticky-Fenster auf sinnvolle Mindestgrößen gebracht und ARGB-Werte in das alte signed-WinForms-Format gebracht. Der Reparaturlauf ist als Bericht testbar und kann per CLI als Dry-Run ausgeführt werden.

Weil die CLI inzwischen sehr viele alte Menü- und Dialogpfade abbildet, wird der große Argumentparser pro Prozess gecacht. Das ändert die Kommandozeilenoberfläche nicht, macht aber wiederholte Aufrufe aus Tests, Skripten und der Slint-Schicht deutlich robuster.


## v17: Textbereich-Kontextmenü, dickere Toolbar und resizebares Fenster

v17 entfernt weiterhin `ContextMenuArea`, `Menu`, `MenuItem` und `MenuSeparator`, damit die UI mit den Slint-Versionen kompiliert, die diese nativen Menüelemente noch nicht kennen. Das Baum-Kontextmenü bleibt als eigenes Overlay aus normalen Slint-Elementen erhalten; Rechtsklick auf eine Zeile wählt die Notiz aus und zeigt die alten Kernaktionen. Der Callback `rename-row(int)` bleibt dafür erhalten.

Der Editor ist jetzt einen Schritt näher am alten RichTextBox-Verhalten: Der eigentliche Textbereich wird von einer `TouchArea` umschlossen, die Rechtsklicks erkennt und das RTF-Kontextpanel öffnet. Die sichtbare `☰`-Leiste und der `RTF Kontext`-Button bleiben nur als alternative Auslöser. Clipboard-Aktionen laufen weiterhin über `TextEdit.copy()`, `cut()`, `paste()` und `select-all()`.

Die obere Werkzeugleiste wurde erneut deutlich vergrößert: `540px` Höhe und zwölf thematische Reihen statt weniger überladener Zeilen. Damit haben die vielen portierten Datei-, Export-, Import-, Baum-, RTF-, Sticky- und Diagnoseaktionen sichtbar Platz, ohne dass der Benutzer die Fensterbreite sofort erhöhen muss.

Das Fenster ist jetzt nicht mehr durch feste `width`/`height`-Angaben fixiert. `app-window.slint` nutzt `preferred-width: 1360px`, `preferred-height: 1080px`, `min-width: 980px` und `min-height: 760px`. Nach Slints Layoutmodell sind feste `width`/`height` am Root-Fenster eine harte Geometrie-Vorgabe; mit Preferred-/Minimum-Werten kann der Fenstermanager wieder normal resizen und maximieren. Zusätzlich gibt es einen Best-Effort-Button `Max` für Slint-Python-Bindings mit Maximize-API und einen portablen `Vollbild`-Fallback über die Slint-Property `full-screen`.
