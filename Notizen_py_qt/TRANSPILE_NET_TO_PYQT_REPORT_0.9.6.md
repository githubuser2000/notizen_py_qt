# Transpilationsbericht Notizen.NET → Python/Qt 0.9.6

Stand: 2026-04-30

## Ziel dieser Runde

Diese Runde setzt den Stand 0.9.5 fort und behebt gezielt das im Screenshot sichtbare Problem: In der Hauptansicht fehlten praktisch nutzbar der Baum und das Text-/Editorfeld beziehungsweise die beiden kleinen Notizen.NET-Kopffelder. Dafür wurde der zentrale WinForms-Aufbau aus `Notizen.Designer.vb` deutlicher in Qt nachgebaut.

## Neu portiert / weiter angenähert

### Hauptfenster-Layout wie im alten `Notizen.Designer.vb`

Der alte WinForms-Dialog bestand im Kern aus drei Splitter-Bereichen:

- links ein oberes Textfeld `txt1`,
- darunter der Baum `Baum`,
- rechts ein oberes Titel-Textfeld `txt2`,
- darunter der RichTextBox-Inhalt `Inhalt`.

Dieser Aufbau ist jetzt im Python/Qt-Hauptfenster explizit vorhanden:

- `QLineEdit` mit Objektname `txt1` über dem Baum,
- `QTreeWidget` mit Objektname `Baum`,
- `QLineEdit` mit Objektname `txt2` über dem Editor,
- `QTextEdit` mit Objektname `Inhalt`,
- nicht kollabierender `QSplitter`,
- Mindestgrößen für Baum und Editor,
- Startgrößen für den Splitter, damit der Baum nicht auf Breite/Höhe 0 zusammengedrückt wird.

Damit sollte genau der im Screenshot erkennbare Zustand, bei dem fast nur Toolbars und leere Fläche sichtbar waren, nicht mehr auftreten.

### Titel-Textfeld `txt2` funktionsfähig gemacht

Das neue rechte Kopffeld ist nicht nur optisch vorhanden:

- Beim Wechsel des markierten Knotens wird `txt2` mit dem Knotentitel synchronisiert.
- `Return`, Fokusverlust oder die Schaltfläche **Umbenennen** übernehmen den Titel zurück in den Baum.
- Der aktuelle Baumknoten, Desktop-Notiz-Titel und Tray-Menü werden anschließend aktualisiert.
- Leere Titel werden wie im alten Programm auf `...` normalisiert.

### Linkes Kopffeld `txt1` wieder vorhanden

Das alte `txt1` war ein gelb hinterlegtes, read-only Textfeld über dem Baum und zeigte den obersten Baumknoten. Diese Funktion ist portiert:

- `txt1` ist read-only,
- die alte hellgelbe WinForms-Anmutung ist per Qt-Stylesheet nachgebildet,
- bei neuen/geladenen Dokumenten und Knotenwechseln wird der Root-Titel angezeigt.

### Schnell-Suche direkt im Hauptfenster

Unter dem Baum gibt es jetzt zusätzlich eine kleine Suchzeile:

- Suchfeld mit Platzhalter **Suchen**,
- **Weiter** durchsucht zunächst die aktuelle Notiz und fällt bei keinem Treffer auf den ganzen Baum zurück,
- **Alle** durchsucht direkt den ganzen Baum,
- Treffer werden im Editor markiert und der zugehörige Knoten wird ausgewählt.

Der vorhandene ausführlichere Suchdialog über `Ctrl+F` bleibt weiterhin erhalten.

### Fokusverhalten für neue Textfelder korrigiert

Durch die neuen `QLineEdit`-Felder musste die Zwischenablagenlogik angepasst werden:

- `Ctrl+X`, `Ctrl+C` und `Ctrl+V` wirken in `txt2` und der Suchzeile jetzt auf den Text im Feld,
- sie schneiden/kopieren/einfügen nicht versehentlich Baumknoten,
- `Shift+Insert` und `Shift+Delete` wirken nur noch bei Baum-Fokus auf Knoten, damit Textfelder normales Editierverhalten behalten.

## Weiterhin bestehende Grenze

Die GUI konnte in dieser Umgebung weiterhin nicht live gestartet werden, weil keine Qt-Bindung installiert ist. Die Änderungen sind deshalb syntaktisch, über vorhandene Logiktests und über statische UI-Quellprüfung validiert. Der nächste echte Praxischeck sollte auf einem System mit PySide6 oder PyQt6 erfolgen.
