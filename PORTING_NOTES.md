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
- Sticky-Metadaten-Editor für `visible`, `x`, `y`, `width`, `height`, `opacity`, `argb`
- Knotenfarben `bgcolor` und `fgcolor` werden wie im Original geschrieben und können bearbeitet werden
- FTP/FTPS-Transport mit `ftp://`/`ftps://`-URLs, `.netrc`-Fallback und migrierbarer Standardverbindung
- CLI erweitert um Statistik, Suche, XML-Dump/Pack, Einzelnotiz-RTF-Export, Notizinhalt ersetzen, Bewegung, Duplizieren, strukturelles Einfügen/Löschen/Umbenennen, Bild einfügen, Datum/Bullet anhängen und FTP-Konfiguration
- HTML-Export als portabler Ersatz für Drucken/Vorschau-Zusammenfassungen
- einfache Ganznotiz-Formatierung (`bold`, `italic`, `underline`, `strike`, Vorder-/Hintergrundfarbe, Schriftfamilie/-größe)
- RichTextBox-Toolbar-Buttons `B`, `I`, `U`, `S` und `Normal` aus der alten UI als Ganznotiz-Aktionen in Slint und als CLI-Befehl `style-note`
- globale RTF-Stilerkennung, damit vorhandene einfache RichTextBox-RTF-Dokumente beim Umformatieren Schriftfamilie/Schriftgröße/Stil sinnvoll weitertragen
- Ctrl+Plus/Ctrl+Minus aus `Notizen.vb` als RTF-weite Textgrößenänderung (`font-size`, A+/A-) portiert
- Suchoptionen aus der alten Dialog-/Suchlogik als UI-Checkboxen: Groß-/Kleinschreibung, Ganzwortsuche, nur aktueller Teilbaum
- Sticky-Autogröße und Sticky-HTML-Board als portabler Ersatz für Teile von `desknote.vb`
- alte `notizen.config.xml` aus `xml_kram.vb` lesen, in die neue JSON-Konfiguration übernehmen und diagnostisch wieder als alte XML-Struktur schreiben
- Autostart portabel nachgebaut: `.desktop` unter Linux, `.cmd` im Windows-Startup-Ordner, LaunchAgent unter macOS
- Autosave-Timer aus der Konfiguration für lokale Dateien
- Wecker-Regeln mit einmaliger, täglicher, wöchentlicher, monatlicher und jährlicher Wiederholung als speicherbare Python-Logik plus CLI/UI-Hooks
- fällige Wecker (`alarm-due`) und eine einfache dauernde Wecker-Schleife (`alarm-watch`) als portabler Ersatz für die alte Popup-Auslösung
- native Best-Effort-Benachrichtigung ohne externe Pakete: `notify-send` unter Linux/BSD, `osascript` unter macOS, PowerShell-MessageBox unter Windows

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

Der Port schreibt weiterhin UTF-16-XML, komprimiert mit GZip. Bei gesetztem Passwort wird anschließend die historische dreifache DES-CBC-Kaskade verwendet. Zusätzlich kann der Python-Kern lesbares Roh-XML direkt laden/speichern und per CLI mit `dump-xml`/`pack-xml` zwischen XML und `.alx` wechseln.

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

Damit bleiben alte formatierte Inhalte erreichbar, auch wenn die neue UI keine vollständige Rich-Text-Bearbeitung bietet. Zusätzlich kann der Port Bilder aus `\pict`-Gruppen extrahieren und PNG/JPEG/BMP wieder als `\pict`-Gruppen anhängen. Die alten Auswahlformatierungen werden nicht Zeichen-für-Zeichen nachgebildet; `format-note`, `style-note` und die Slint-Buttons wenden Stiländerungen bewusst auf die ganze Notiz an. Das ist ehrlich begrenzt, aber stabil und ohne native RichTextBox-Abhängigkeit.

## Alte Konfiguration, FTP und Autostart

`xml_kram.vb` schrieb die alte `notizen.config.xml` unter anderem mit Backup-Anzahl, Autosave-Sekunden, zuletzt geöffneten Dateien, Sprache, Fensterposition, Sticky-Rahmen, Autostart-Werten und FTP-Feldern. Der Port migriert diese Felder nach `~/.config/notizen-py-slint/config.json` beziehungsweise unter Windows nach `%APPDATA%`.

Die alte FTP-Konfiguration aus `ftpkram.vb` (`name`, `pass`, `host`, `path`) wird in die neue Konfiguration übernommen und kann als Standard-Remote-URL genutzt werden. Der eigentliche Transport nutzt nur die Standardbibliothek (`ftplib`) und unterstützt:

- `ftp://user:pass@host/path/file.alx`
- `ftps://user:pass@host/path/file.alx`
- Zugangsdaten aus `~/.netrc`, wenn sie nicht in der URL stehen

Backups werden nur lokal erzeugt. Bei Remote-Speichern wird direkt hochgeladen.

Der alte Windows-spezifische Autostart wurde nicht per Registry/COM 1:1 übernommen. Stattdessen erzeugt der Port plattformübliche Starterdateien und akzeptiert `--minimized` als kompatibles, aber momentan nicht fensterzustandswirksames Startargument.

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
- separate borderlose Desktop-Sticky-Fenster (der Port hat stattdessen Sticky-Metadaten, Autogröße und HTML-Board)
- native TreeView-Drag-and-drop-Gesten
- Druckdialog; HTML-Export dient als portabler Ersatz
- vollständige mehrsprachige Menülogik aus den `.resx`-/`languages.vb`-Dateien
- echte RichTextBox-Auswahlformatierung mit gemischten Fonts/Farben pro Zeichenbereich
- permanenter OS-Hintergrunddienst für Wecker/Tray

Diese Punkte sind entweder stark Windows-/WinForms-spezifisch oder passen nicht sauber zu Python/Slint. Die zugrunde liegenden Daten werden aber so weit wie möglich erhalten.
