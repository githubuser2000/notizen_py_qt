# Transpilationsbericht Notizen.NET → Python/Qt 0.9.5

Stand: 2026-04-30

## Ziel dieser Runde

Diese Runde setzt den Stand 0.9.4 fort und nimmt weitere WinForms-/VB.NET-Verhaltensdetails aus dem alten Projekt in den Python/Qt-Port auf. Schwerpunkte waren diesmal das alte Knoten-Clipboard, der Wecker aus `wecker.vb`, Druckpfade und weitere Tastatur-Parität aus `Notizen.vb`.

## Neu portiert / weiter angenähert

### Systemweites Knoten-Clipboard

Bis 0.9.4 war das Kopieren/Ausschneiden von Knoten vor allem ein interner Programmzustand. In 0.9.5 wurde daraus zusätzlich ein systemweites Clipboard-Format:

- neues Modul `notizen_py_qt.node_clipboard`,
- eigenes MIME-Format `application/x-notizen-pyqt-node+xml`,
- XML-Payload mit einem `Notiz`-Teilbaum nahe am ALX-Aufbau,
- Einfügen aus einem zweiten laufenden Notizen-Python/Qt-Fenster,
- Fallback über Plain-Text-XML, damit der Payload auch auf einfacheren Clipboard-Backends lesbar bleibt,
- optionales Lesen einzelner `Notiz`-Elemente oder ganzer `notizen-alx2`-Wurzeln.

Wie im alten Programm werden Desktop-Notizfenster beim Kopieren/Ausschneiden nicht verdoppelt: Desktop-Notiz-Geometrie und Sichtbarkeit werden standardmäßig aus kopierten Teilbäumen entfernt.

### Einfügen als Unterknoten

Neben dem WinForms-nahen Standard-Einfügen aus 0.9.4 gibt es jetzt eine separate Aktion **Einfügen als Unterknoten**:

- neuer Menüpunkt im Knoten-Menü,
- verfügbar im Baum-Kontextmenü,
- fügt den kopierten Teilbaum als erstes Kind des markierten Knotens ein,
- schützt weiterhin gegen Ausschneiden in sich selbst oder eigene Unterknoten.

Damit sind beide praxisrelevanten Varianten direkt erreichbar: das alte `paste_anything(False)`-Verhalten und ein explizites Unterknoten-Einfügen.

### Wiederholender Wecker nach `wecker.vb`

Der bisher einfache Wecker wurde durch ein portierbares Alarm-Modell erweitert:

- neues Modul `notizen_py_qt.alarms`,
- `AlarmSpec` als Qt-unabhängige Beschreibung,
- einmalige Wecker,
- tägliche Wiederholung,
- wöchentliche Wiederholung mit Wochentagen,
- monatliche Wiederholung,
- jährliche Wiederholung,
- Intervall-Unterstützung,
- robuste Behandlung von Monatsenden und Schaltjahren.

Der Qt-Dialog bietet jetzt die alten Wiederholungsarten aus `wecker.vb` an. Die Berechnung des nächsten Termins ist ohne Qt testbar.

### QTimer-Scheduling robuster gemacht

Die Weckerplanung berücksichtigt die 32-Bit-Millisekunden-Grenze von `QTimer`. Sehr weit entfernte Termine werden in sicheren Timer-Abschnitten weiter geplant, bis der tatsächliche Zielzeitpunkt erreicht ist.

### Druckpfade über QtPrintSupport

Der alte Code enthält einen Druckbutton, dessen eigentliche WinForms-Drucklogik im historischen Stand nicht vollständig aktiv war. In 0.9.5 ist der Python/Qt-Port trotzdem funktional weitergeführt:

- aktuelle Notiz drucken,
- aktuellen Teilbaum drucken,
- ganzen Baum drucken,
- Druckdialog über `QtPrintSupport.QPrintDialog`,
- Druckausgabe über `QTextDocument`.

Teilbaum- und Baumdruck verwenden die bestehende RTF-Zusammenfassung und die RTF→HTML-Brücke.

### Legacy-Tastaturbedienung ergänzt

Aus `Notizen.vb` wurden weitere Tastaturvarianten übernommen:

- `Shift+Insert` → Knoten einfügen,
- `Shift+Delete` → Knoten ausschneiden,
- `Ctrl+Space` bleibt Wecker,
- `Insert`, `Delete`, `Return` bleiben bei Baum-Fokus Knotenbefehle.

### About-Dialog und README aktualisiert

Der About-Dialog und die README nennen jetzt die neuen 0.9.5-Schwerpunkte:

- systemweites Knoten-Clipboard,
- wiederholende Wecker,
- Qt-Druckpfade,
- ergänzte Legacy-Tastaturvarianten.

## Geänderte / neue Dateien

Neue Dateien:

- `src/notizen_py_qt/alarms.py`
- `src/notizen_py_qt/node_clipboard.py`
- `tests/test_node_clipboard_alarms.py`

Geänderte Dateien:

- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/models.py`
- `src/notizen_py_qt/__init__.py`
- `pyproject.toml`
- `README.md`
- `TRANSPILE_NET_TO_PYQT_REPORT.md`
- `VALIDATION_NET_PORT.md`

## Neue Testabdeckung

Neu getestet sind unter anderem:

- Clipboard-XML-Roundtrip eines Knoten-Teilbaums,
- Erhalt von Titel, RTF, Farben, Expand-Zustand und Kindbeziehungen,
- bewusstes Entfernen von Desktop-Notiz-Zustand beim Kopieren,
- optionaler Erhalt von Desktop-Notiz-Zustand beim expliziten XML-Lesen,
- `legacy_paste_clone()` ohne Desktop-Notiz-Duplikate,
- einmalige und tägliche Wecker,
- wöchentliche Wecker mit Wochentagen,
- monatliche Wecker an Monatsenden,
- jährliche Wecker inklusive Schaltjahrfällen.

## Bekannte Grenzen

- Die GUI konnte in dieser Umgebung weiterhin nicht echt gestartet werden, weil weder PySide6 noch PyQt6 installiert ist.
- Der Runtime-Probe erkennt das sauber und gibt Installationshinweise aus.
- Drucken ist syntaktisch und logisch angebunden, konnte aber ohne Qt-Binding und ohne Druckdialog in dieser Umgebung nicht interaktiv getestet werden.
- Exotische RTF-Fälle aus WinForms/RichTextBox wie OLE-Objekte, WMF/EMF oder Tabellen bleiben weiterhin nicht vollständig WinForms-identisch.
- Das systemweite Knoten-Clipboard ist auf Notizen-Python/Qt-Instanzen ausgelegt. Das alte WinForms-Programm kennt dieses neue MIME-Format nicht.
