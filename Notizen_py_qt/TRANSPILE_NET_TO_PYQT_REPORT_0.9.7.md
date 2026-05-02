# Transpilationsbericht Notizen.NET → Python/Qt 0.9.7

Stand: 2026-04-30

## Ziel dieser Runde

Diese Runde setzt den Stand 0.9.6 fort. Nach der Reparatur der sichtbaren Hauptansicht wurden weitere sichtbare Befehle aus der alten WinForms-Anwendung und aus dem aktuellen Qt-Zwischenstand angeschlossen: Import, HTML-Export, Statistik, Knotenbewegung, Auf-/Zu-Befehle, Scrollleistenwechsel und Alt-Konfigurationsimport.

## Neu portiert / weiter angenähert

### TXT- und RTF-Import in die aktuelle Notiz

Für die aktuelle Notiz gibt es jetzt zwei direkte Importpfade:

- **TXT importieren** liest Textdateien mit UTF-8/UTF-16/Windows-1252-Fallback und schreibt daraus gültiges RTF in den aktuellen Knoten.
- **RTF importieren** übernimmt echte RTF-Dateien direkt. Falls die Datei kein RTF ist, wird sie defensiv als Plaintext importiert.
- Nach dem Import werden Editor, Desktop-Notizfenster und Änderungsstatus synchronisiert.
- Das zuletzt verwendete Verzeichnis wird in den Einstellungen gespeichert.

### HTML-Export ergänzt

Zusätzlich zu RTF, UTF-8-TXT, ANSI-TXT und Unicode-TXT kann jetzt exportiert werden:

- aktueller Teilbaum als eigenständige UTF-8-HTML-Datei,
- ganzer Baum als eigenständige UTF-8-HTML-Datei.

Der HTML-Export verwendet die bestehende RTF→HTML-Brücke, übernimmt die alte Teilbaum-Nummerierung (`1.`, `1.1.` usw.) und erhält eingebettete PNG/JPEG-Bilder als `data:image/...`-URIs, soweit sie bereits über die 0.9.3-RTF-Bildbrücke unterstützt werden. In derselben Runde wurde die gemeinsame Export-Nummerierung für mehrere Geschwisterknoten korrigiert, damit auf `1.` korrekt `2.`, `3.` usw. folgt.

### Statistikdialog

Ein neuer Statistikdialog zählt für aktuellen Teilbaum und Gesamtbaum:

- Knoten,
- Blätter,
- maximale Tiefe,
- Desktop-Notizen,
- Zeichen,
- Zeichen ohne Leerraum,
- Wörter,
- Zeilen,
- RTF-Bytes,
- eingebettete RTF-Bilder.

Die Zählung liegt in einem Qt-unabhängigen Modul `stats.py`, damit sie testbar bleibt und später auch für Statusleisten oder Exportberichte genutzt werden kann.

### Knoten nach oben/unten verschieben

Die Baumfunktionen wurden weiter an die WinForms-Bedienung angenähert:

- **Nach oben** verschiebt den aktuellen Knoten innerhalb seiner Geschwisterliste eine Position nach oben.
- **Nach unten** verschiebt ihn eine Position nach unten.
- Root-Knoten und nicht mögliche Bewegungen bleiben deaktiviert beziehungsweise ohne Effekt.
- Nach der Bewegung wird der Knoten wieder ausgewählt und der Editor korrekt neu geladen.

### Auf-/Zu-Befehle sichtbar gemacht

Die alten sichtbaren Baumaktionen sind jetzt angebunden:

- **Auf-/Zu** für den aktuellen Knoten,
- **Alle auf** für den ganzen Baum,
- **Alle zu** für den ganzen Baum.

Die Expansion wird zurück ins Datenmodell geschrieben, sodass Speichern/Laden die Baumansicht weiter mitnimmt.

### Scrollleistenwechsel wie im alten Menü

Der alte `ToolStrip_whatscroll_Click`-Gedanke ist als sichtbare Aktion zurück:

- Der Editor wechselt zyklisch zwischen keiner, horizontaler, vertikaler und beider Scrollleisten.
- Die Einstellung wird gespeichert und sofort angewendet.

### Alt-Config importieren

Alte `notizen.config.xml`-Dateien können jetzt über die Oberfläche importiert werden. Der Parser wurde dafür aus `AppSettings.load()` in eine wiederverwendbare Methode verlagert:

- `apply_xml_root(...)`,
- `apply_from_file(...)`.

Importiert werden unter anderem Scrollleisten, Sicherungsanzahl, Autostart-Flags, FTP-Daten, zuletzt geöffnete Dateien, Sprache, Fensterdaten, Taskleistenverhalten, Desktop-Notiz-Ränder und Autosave-Intervall. Das aktuelle Plattform-Konfigurationsverzeichnis bleibt dabei erhalten.

### Wartung der Validierungswerkzeuge

Die Shell-Prüfskripte und der Runtime-Probe wurden robuster für diese Umgebung gemacht, indem Python-Unterprozesse bei Bedarf ebenfalls ohne `site`-Initialisierung laufen. Dadurch hängen die Prüfungen hier nicht mehr nach erfolgreicher Ausgabe.

## Neue Tests

Ergänzt wurden Tests für:

- HTML-Export als eigenständiges Dokument,
- Nummerierung im HTML- und RTF/TXT-Export auch bei mehreren Geschwisterknoten,
- Erhalt eingebetteter Bilder im HTML-Export,
- Statistikzählung inklusive Desktop-Notizen und Bildern,
- Import beliebiger Legacy-Konfigurationsdateien,
- statische Verdrahtung der neuen Hauptfensteraktionen.

## Weiterhin bestehende Grenze

Die GUI konnte in dieser Umgebung weiterhin nicht live gestartet werden, weil keine Qt-Bindung installiert ist. Der Code kompiliert, die Qt-unabhängigen Pfade sind getestet, und der Runtime-Probe bricht ohne Qt sauber mit Installationshinweis ab. Ein echter visueller Praxistest sollte weiterhin auf einem System mit PySide6 oder PyQt6 erfolgen.
