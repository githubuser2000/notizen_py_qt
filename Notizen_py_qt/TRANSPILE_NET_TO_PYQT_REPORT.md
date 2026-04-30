# Notizen.NET → Python/Qt Weitertranspilierung

Stand: 2026-04-30  
Version: 0.9.3

## Ausgangspunkt

- Weitergeführt wurde der vorhandene Python/Qt-Port **0.9.2**.
- Als Referenz diente weiterhin das originale VB.NET/WinForms-Projekt aus `notizen.net.tar.bz2`.
- Der aktive Zielpfad bleibt ein Python-Paket unter `src/notizen_py_qt/`.
- Frühere Projektentscheidung bleibt erhalten: PySide6 ist das bevorzugte Qt-for-Python-Ziel; PyQt6 bleibt als Fallback im Kompatibilitätslayer.

## In dieser Runde weiter transpilierte .NET-Funktionen

### Editor-Kontextmenü aus `kontext_inhalt.vb`

Der Qt-Editor hat jetzt die im alten RichTextBox-Kontextmenü fehlenden Aktionen:

- Ausschneiden,
- Kopieren,
- Einfügen,
- Text löschen,
- Bild einfügen,
- Datum einfügen,
- Suchen,
- Formatierungsaktionen im Editor-Kontextbereich.

`Datum einfügen` verwendet bewusst das alte Notizen.NET-Schema mit Leerzeichen davor/danach und der einfachen deutschen Punktnotation: `Tag.Monat.Jahr Stunde:Minute`.

`Bild einfügen` lädt ein Bild über den Qt-Dateidialog. Das Bild wird über `QImage` normalisiert und als PNG-Data-URI in den Qt-Editor eingefügt, damit es beim Speichern vollständig in den ALX-/RTF-Inhalt gelangt und nicht nur als lokaler Dateipfad erhalten bleibt.

### Echter RTF-Bild-Roundtrip

Der größte technische Fortschritt gegenüber 0.9.2 ist der Bildpfad in `rtf_utils.py`:

- HTML-`img` mit Data-URI oder lokalem Datei-`src` wird zu RTF-`{\pict ...}`.
- PNG wird als `\pngblip` gespeichert.
- JPEG wird als `\jpegblip` gespeichert.
- Bildbreite/-höhe werden aus HTML-Attributen oder CSS gelesen und als `\picwgoal`/`\pichgoal` geschrieben.
- RTF-`\pict`-Gruppen werden beim Laden wieder zu HTML-`img src="data:image/...;base64,..."`.
- Plaintext-Extraktion überspringt Bilder weiterhin sauber, statt Rohdaten oder Hexblöcke in Notiztext zu leaken.
- Eingebettete Bildgruppen in `\shppict`/`\nonshppict` werden praktisch erkannt, wenn sie einen inneren `\pict`-Block enthalten.

Damit ist der frühere 0.9.2-Kompromiss entfernt, bei dem HTML-Bilder nur als `[Bild]`-Marker gespeichert wurden.

### Schriftfamilie und Schriftgröße näher an `ToolStrip_fonts`/`fontsize.vb`

Der Port hat jetzt eine Qt-Schriftleiste mit:

- `QFontComboBox` für Schriftfamilien,
- direkter Schriftgrößen-Eingabe per `QSpinBox`,
- Synchronisation der Anzeige beim Bewegen des Cursors im Editor,
- Speicherung von Schriftfamilien über RTF-Fonttables,
- Rücklesen von RTF-`\fonttbl` und `\fN` in Qt-HTML-`font-family`.

Die Formatierungslogik wurde außerdem an das alte RichTextBox-Verhalten angepasst: Wenn keine Textauswahl existiert, wird bei Formatierungsbefehlen die ganze aktuelle Notiz formatiert. Das entspricht dem alten `font_set`-Pfad, der bei leerer Auswahl `SelectAll()` verwendete.

### RTF-Fonttable im Export

Der Teilbaum-RTF-Export bewahrt jetzt zusätzlich zu Fett/Kursiv/Unterstrichen/Durchgestrichen, Schriftgröße, Textfarbe und Highlight auch die Schriftfamilie der unterstützten Textsegmente.

Dafür wurden ergänzt:

- Font-Familien in `RtfTextStyle`,
- Font-Familien-Sammlung im Export,
- RTF-Fonttable-Erzeugung mit `\f0` als Standard und zusätzlichen `\fN`-Einträgen,
- `\fN`-Präfixe in formatierten Segmenten.

### Desktop-Notizen näher an `desknote.vb` und Kontextklassen

Desktop-Notizen wurden erweitert:

- eigenes Kontextmenü im Desktop-Notizfenster und im darin liegenden Editor,
- Ausschneiden/Kopieren/Einfügen im Desktop-Editor,
- Hintergrundfarbe pro Desktop-Notiz,
- Transparenzmenü von 10 % bis 100 %,
- Ausblenden,
- Desktop-Notiz schließen/entfernen,
- Doppelklick öffnet den zugehörigen Knoten im Hauptfenster,
- gespeicherte Rand-Einstellung wird beim Erzeugen des Fensters berücksichtigt; ohne Rand wird ein frameless Qt-Fenster verwendet.

### Kleinere Stabilisierung

- `insert_image` verwendet jetzt die Qt6-kompatible `QStandardPaths.StandardLocation.PicturesLocation`-Auflösung über den vorhandenen Enum-Kompatibilitätshelfer.
- Version wurde in `pyproject.toml` und `src/notizen_py_qt/__init__.py` auf **0.9.3** gesetzt.
- Tests wurden um RTF-Bild-Roundtrip und Schriftfamilien-Roundtrip erweitert.

## Aktive Python/Qt-Struktur

- `src/notizen_py_qt/app.py` – Qt-Hauptfenster, Baum, Editor, Menüs, Toolbars, Tray, Desktop-Notizen, FTP-Dialog, Wecker.
- `src/notizen_py_qt/models.py` – `NoteDocument`, `NoteNode`, `DesktopNoteState`.
- `src/notizen_py_qt/alx_io.py` – ALX-Dateiformat, GZip, UTF-16-XML, Legacy-DES-Passwortmodus, Backups.
- `src/notizen_py_qt/rtf_utils.py` – RTF↔HTML↔Plaintext-Brücke inklusive Fonttable und PNG/JPEG-`\pict`-Bildern.
- `src/notizen_py_qt/exporters.py` – Teilbaum-Export und Zusammenfassung.
- `src/notizen_py_qt/settings.py` – kompatible `notizen.config.xml`-Konfiguration.
- `src/notizen_py_qt/search_logic.py` – Suchlogik.
- `src/notizen_py_qt/ftp_sync.py` – FTP-Zielnormalisierung, Download und Upload per `ftplib`.
- `src/notizen_py_qt/qt_compat.py` – PySide6 bevorzugt, PyQt6 als Fallback.
- `src/notizen_py_qt/resources/` – Notizen-Icon und `.qrc`.

## Bekannte Grenzen

- Der RTF-Bildpfad unterstützt jetzt praxisrelevante PNG/JPEG-`\pict`-Blöcke. Exotische RTF-Bildarten wie WMF/EMF, OLE-Objekte, `\bin`-Payloads oder Tabellen sind weiterhin nicht vollständig portiert.
- RichText ist funktional deutlich näher am Original, aber nicht bytegenau WinForms-identisch.
- Die Oberfläche ist funktional nachgebaut, nicht pixelgenau WinForms-identisch.
- Die Spracharrays aus `languages.vb` sind weiterhin nicht vollständig 1:1 als Lokalisierungssystem portiert.
- FTP ist wie im Original unverschlüsselt. Für vertrauliche Notizen sollte die ALX-Datei selbst mit Passwort gespeichert werden.
- In dieser Container-Umgebung ist kein PySide6/PyQt6 installiert; GUI-Smoke-Test kann deshalb nur bis zur sauberen Fehlermeldung geprüft werden.

## Start

```bash
python -m pip install -e ".[crypto]"
notizen-py-qt /pfad/zur/datei.alx
```

Ohne verschlüsselte ALX-Dateien genügt:

```bash
python -m pip install -e .
```

Smoke-Test auf einem Rechner mit Qt-Binding:

```bash
python -m notizen_py_qt --smoke-test
```
