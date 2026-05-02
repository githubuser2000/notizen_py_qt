# Notizen Python/Qt Port

Dies ist die Weitertranspilierung des alten VB.NET/WinForms-Projekts **Notizen.NET** nach Python/Qt.

Aktueller Stand dieses Archivs: **0.10.1**.

## Start

```bash
python -m pip install -e ".[crypto]"
notizen-py-qt /pfad/zur/datei.alx
```

PySide6 ist die bevorzugte Qt-Bindung. PyQt6 wird vom Kompatibilitätslayer ebenfalls akzeptiert, falls PyQt6 installiert oder lokal bevorzugt wird.

## Enthalten

- ALX-Dateiformat mit GZip, UTF-16-XML und Legacy-DES-Passwortmodus.
- Baumansicht, Editor, Knotenoperationen, Drag-and-drop, Suche, Export und Notizen.NET-kompatible Sicherheitskopien.
- WinForms-nahe Hauptansicht mit sichtbarem Baumfeld `txt1` über dem Baum, Titel-Textfeld `txt2` über dem Editor und dauerhaft sichtbarem RichText-Editor `Inhalt`.
- RTF-zu-HTML-Bridge für den Qt-Editor mit Fett/Kursiv/Unterstrichen/Durchgestrichen, Schriftgröße, Schriftfamilie, Textfarbe, Markierung und Unicode.
- RTF-Bild-Roundtrip für übliche WinForms/Qt-`\pict`-Bilder mit PNG/JPEG-Hexdaten sowie HTML-`img`-Data-URIs.
- Editor-Kontextfunktionen aus Notizen.NET: Text löschen, Bild einfügen, Datum einfügen, Suche und Zwischenablageaktionen.
- Teilbaum-Export nach RTF/TXT mit alter Notizen.NET-Nummerierung sowie „Teilbaum zusammenfassen“ und „Ganzen Baum zusammenfassen“ als neue Notiz.
- Fokusabhängiges Ausschneiden/Kopieren/Einfügen/Löschen wie im alten WinForms-Programm.
- Desktop-Notizen mit Kontextmenü, Hintergrundfarbe, Transparenz, Ausblenden/Schließen und Doppelklick zurück zum Hauptfenster; neue Desktop-Notizen starten wie im WinForms-Kontextmenü an der Mausposition mit 200×200 px und 85 % Deckkraft.
- Das Desktop-Notiz-Transparenzmenü nutzt jetzt die alte WinForms-Semantik aus `desknote_kontext_opacy.vb`: „90 %“ bedeutet 90 % Transparenz und wird intern zu 10 % Qt-Deckkraft.
- System-Tray, Wecker per `Ctrl+Space`, Grundeinstellungen und zuletzt geöffnete Dateien; Recent-Einträge prüfen fehlende Dateien und fragen bei ungespeicherten Änderungen nach.
- FTP-Öffnen/Speichern wie im alten `ftpkram.vb`.
- Importiertes Notizen-Icon als Paketressource plus `.qrc`.
- Importierte Sprachdateien aus `languages.vb` für Deutsch, English, Chinese, français, spanish und russian; Menü-/Aktionsbeschriftungen werden zur Laufzeit umgeschaltet.
- Legacy-Startparameter aus `ApplicationEvents.vb`: `/min`, `-min`, `min`, Hilfe-Flags und direkte `ftp://...alx`-Startziele.
- WinForms-nahe Knoten-Einfügelogik: Kopierte/ausgeschnittene Teilbäume werden wie in `paste_anything(False)` vor dem markierten Geschwisterknoten bzw. als erster Root-Unterknoten eingefügt.
- Erweiterte Export-Parität: aktueller Teilbaum oder ganzer Baum als RTF, UTF-8-TXT, ANSI-TXT oder Unicode-TXT sowie Roh-RTF des aktuellen Knotens.
- Desktop-Notizen synchronisieren laufende Editoränderungen jetzt live und erhalten bei fehlender Alt-Farbe eine zufällige helle Legacy-Farbe.
- Knoten-Kopieren/Ausschneiden nutzt zusätzlich zur internen Ablage ein eigenes systemweites XML-MIME-Format, damit Teilbäume zwischen zwei laufenden Programmfenstern eingefügt werden können.
- Der Wecker aus `wecker.vb` unterstützt jetzt einmalige, tägliche, wöchentliche, monatliche und jährliche Wiederholungen mit Intervall und Wochentagen.
- Drucken über QtPrintSupport für aktuelle Notiz, aktuellen Teilbaum oder ganzen Baum ist angebunden.
- Legacy-Tastaturvarianten `Shift+Insert` und `Shift+Delete` sind ergänzt.
- TXT- und RTF-Import in die aktuelle Notiz sind angebunden.
- HTML-Export für aktuellen Teilbaum und ganzen Baum erzeugt eine eigenständige UTF-8-HTML-Datei mit Nummerierung und eingebetteten Bildern.
- Statistikdialog zählt Knoten, Blätter, Tiefe, Desktop-Notizen, Textmengen und eingebettete Bilder für aktuellen Teilbaum und Gesamtbaum.
- Knoten können per Aktion nach oben/unten verschoben werden; Auf-/Zu, Alle auf und Alle zu sind wieder als sichtbare Befehle vorhanden.
- Alte `notizen.config.xml`-Dateien können aus der Oberfläche importiert werden; Scrollleisten können wie im WinForms-Menü zyklisch umgeschaltet werden.
- Suche, Schnell-Suche und alle Exportpfade synchronisieren den sichtbaren Editorinhalt vor der Auswertung zurück ins Modell.
- Sicherheitskopien folgen der alten `saftycopies`-Logik aus Notizen.NET: Backup-Ordner neben der `.alx`-Datei, Dateinamen `Name-YYYY-MM-DD-HH-MM-SS-ms.alx`, konfigurierbare Rotation und neue Aktionen „Jetzt Sicherung erstellen“/„Sicherung öffnen“.
- Legacy-Config-Parität weitergeführt: `open/once-opened`, alte `tool-stripes`-Positionen und der WinForms-Autosave-Schutz aus `einstellungen.vb` werden übernommen und beim Speichern erhalten; frische Configs starten wie Notizen.NET mit 60 Sekunden Autosave.
- Die alte Datei-Startlogik aus `Datei.vb` ist präzisiert: Standardname `unbenannt.alx`, Standardordner `Documents/Notizen` und Windows-Backslash-Pfade aus alten Configs werden auch auf Linux/macOS korrekt in Verzeichnis und Dateiname getrennt.
- Autostart-Einstellung aus `xml_kram.setshortcut` ist als Windows-Startup-`.cmd`-Adapter portiert: jüngste zuletzt geöffnete Datei wird bevorzugt, `-min` wird bei minimiertem Autostart vorangestellt.
- Fensterzustände aus `xml_kram.vb` werden robuster normalisiert; gespeicherte `minimized`-/`maximized`-Werte werden beim Start ausgewertet, und offensichtlich außerhalb des Arbeitsbereichs liegende Hauptfensterpositionen werden abgefangen.
- RTF-Tabellenzellen aus alten RichTextBox-Inhalten werden in Suche, Statistik und Exporten nicht mehr zusammengeschoben, sondern als Tabulatoren und Zeilenumbrüche erhalten.

Historische Qt-/QML-Migrationsskripte aus früheren Zwischenschritten liegen nicht mehr im aktiven Projektpfad, sondern unter `legacy_build_metadata/`.

Details stehen in [`TRANSPILE_NET_TO_PYQT_REPORT.md`](TRANSPILE_NET_TO_PYQT_REPORT.md). Validierung steht in [`VALIDATION_NET_PORT.md`](VALIDATION_NET_PORT.md).
