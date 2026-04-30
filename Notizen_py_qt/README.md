# Notizen Python/Qt Port

Dies ist die Weitertranspilierung des alten VB.NET/WinForms-Projekts **Notizen.NET** nach Python/Qt.

Aktueller Stand dieses Archivs: **0.9.4**.

## Start

```bash
python -m pip install -e ".[crypto]"
notizen-py-qt /pfad/zur/datei.alx
```

PySide6 ist die bevorzugte Qt-Bindung. PyQt6 wird vom Kompatibilitätslayer ebenfalls akzeptiert, falls PyQt6 installiert oder lokal bevorzugt wird.

## Enthalten

- ALX-Dateiformat mit GZip, UTF-16-XML und Legacy-DES-Passwortmodus.
- Baumansicht, Editor, Knotenoperationen, Drag-and-drop, Suche, Export und Backups.
- RTF-zu-HTML-Bridge für den Qt-Editor mit Fett/Kursiv/Unterstrichen/Durchgestrichen, Schriftgröße, Schriftfamilie, Textfarbe, Markierung und Unicode.
- RTF-Bild-Roundtrip für übliche WinForms/Qt-`\pict`-Bilder mit PNG/JPEG-Hexdaten sowie HTML-`img`-Data-URIs.
- Editor-Kontextfunktionen aus Notizen.NET: Text löschen, Bild einfügen, Datum einfügen, Suche und Zwischenablageaktionen.
- Teilbaum-Export nach RTF/TXT mit alter Notizen.NET-Nummerierung sowie „Teilbaum zusammenfassen“ als neue Notiz.
- Fokusabhängiges Ausschneiden/Kopieren/Einfügen/Löschen wie im alten WinForms-Programm.
- Desktop-Notizen mit Kontextmenü, Hintergrundfarbe, Transparenz, Ausblenden/Schließen und Doppelklick zurück zum Hauptfenster.
- System-Tray, Wecker per `Ctrl+Space`, Grundeinstellungen und zuletzt geöffnete Dateien.
- FTP-Öffnen/Speichern wie im alten `ftpkram.vb`.
- Importiertes Notizen-Icon als Paketressource plus `.qrc`.
- Importierte Sprachdateien aus `languages.vb` für Deutsch, English, Chinese, français, spanish und russian; Menü-/Aktionsbeschriftungen werden zur Laufzeit umgeschaltet.
- Legacy-Startparameter aus `ApplicationEvents.vb`: `/min`, `-min`, `min`, Hilfe-Flags und direkte `ftp://...alx`-Startziele.
- WinForms-nahe Knoten-Einfügelogik: Kopierte/ausgeschnittene Teilbäume werden wie in `paste_anything(False)` vor dem markierten Geschwisterknoten bzw. als erster Root-Unterknoten eingefügt.
- Erweiterte Export-Parität: aktueller Teilbaum oder ganzer Baum als RTF, UTF-8-TXT, ANSI-TXT oder Unicode-TXT sowie Roh-RTF des aktuellen Knotens.
- Desktop-Notizen synchronisieren laufende Editoränderungen jetzt live und erhalten bei fehlender Alt-Farbe eine zufällige helle Legacy-Farbe.

Historische Qt-/QML-Migrationsskripte aus früheren Zwischenschritten liegen nicht mehr im aktiven Projektpfad, sondern unter `legacy_build_metadata/`.

Details stehen in [`TRANSPILE_NET_TO_PYQT_REPORT.md`](TRANSPILE_NET_TO_PYQT_REPORT.md). Validierung steht in [`VALIDATION_NET_PORT.md`](VALIDATION_NET_PORT.md).
