# Transpilationsbericht Notizen.NET → Python/Qt 0.9.4

Stand: 2026-04-30

## Ziel dieser Runde

Diese Runde setzt den Python/Qt-Port aus 0.9.3 fort und gleicht weitere Verhaltensdetails aus dem ursprünglichen VB.NET/WinForms-Projekt an. Schwerpunkte waren diesmal Sprache/Startparameter, alte Baum-Einfügelogik, Desktop-Notiz-Synchronisation und Export-Parität.

## Neu portiert / weiter angenähert

### Sprachsystem aus `languages.vb`

- `languages.vb` wurde in ein Python-Modul `notizen_py_qt.i18n` übertragen.
- Enthalten sind die alten Sprachvarianten:
  - Deutsch,
  - English,
  - Chinese,
  - français,
  - spanish,
  - russian.
- Die alte `Auto`-Logik wird nachgebildet:
  - `de*` → Deutsch,
  - `fr*` → français,
  - `es*` → spanish,
  - `ru*` → russian,
  - `zh*` → Chinese,
  - sonst English.
- Menü- und Aktionsbeschriftungen werden im laufenden Qt-Fenster über `MainWindow.apply_language()` gesetzt.
- Der Einstellungsdialog speichert nun die kanonischen alten Sprachkennungen statt nur sichtbarer Labels.

### Legacy-Startparameter aus `ApplicationEvents.vb`

Neu ist `notizen_py_qt.startup` mit Parser für die alten Startvarianten:

- `/min`, `-min`, `min` starten minimiert.
- `/h`, `-h`, `h`, `/?`, `-?`, `?` zeigen Hilfe an.
- Lokale `.alx`-Dateien werden als Startdatei erkannt.
- Direkte `ftp://.../*.alx`-Ziele werden erkannt und an den FTP-Lader übergeben.
- Moderne Argumente wie `--password` und `--smoke-test` bleiben erhalten.

### FTP-Startziel

Neben dem bestehenden FTP-Dialog kann das Programm jetzt auch direkt mit einer FTP-URL gestartet werden, zum Beispiel:

```bash
notizen-py-qt ftp://user:pass@example.org/pfad/notizen.alx
```

Der Port lädt dann die Datei, übernimmt die FTP-Daten in die Einstellungen und verwendet den bestehenden ALX-Lader inklusive Passwortabfrage.

### WinForms-nahe Knoten-Einfügelogik

Das alte `paste_anything(False)` aus Notizen.NET hat eingefügte Knoten nicht einfach als Kind des markierten Knotens angehängt. Dieses Verhalten ist jetzt in `models.legacy_paste_clone()` umgesetzt:

- Ist die Wurzel markiert, wird der eingefügte Teilbaum als erster Unterknoten der Wurzel eingefügt.
- Ist ein normaler Knoten markiert, wird der eingefügte Teilbaum als Geschwisterknoten direkt vor dem markierten Knoten eingefügt.
- Ausschneiden in sich selbst oder in eigene Unterknoten wird verhindert.

### Desktop-Notizen live synchronisiert

Desktop-Notizen werden nun bei laufenden Editoränderungen im Hauptfenster aktualisiert. Auch Änderungen aus einem Desktop-Notizfenster werden an weitere offene Desktop-Fenster desselben Knotens weitergegeben.

Zusätzlich:

- Fehlende Desktop-Notiz-Farbe wird jetzt mit einer zufälligen hellen Farbe aus der alten WinForms-Palette belegt.
- Die Palette ist in `legacy_colors.py` abgebildet und liefert signierte ARGB-Integer wie `Color.ToArgb()`.

### Baum-Expansion wird live gespeichert

Auf- und Zuklappen eines Knotens aktualisiert nun direkt das Modell und markiert das Dokument als geändert. Vor 0.9.4 wurde der Expand-Zustand vor allem beim Speichern synchronisiert.

### Export-Parität erweitert

Der Export wurde erweitert:

- aktueller Teilbaum als RTF,
- aktueller Teilbaum als UTF-8-TXT,
- aktueller Teilbaum als ANSI-TXT / Windows-1252,
- aktueller Teilbaum als Unicode-TXT / UTF-16 mit BOM,
- ganzer Baum in denselben Formaten,
- Roh-RTF des aktuellen Knotens über den Baum-Kontextbereich.

Text-Exporte verwenden Windows-CRLF-Zeilenenden, damit sie näher an den alten RichTextBox/TXT-Exporten liegen.

### Passwortdialog näher am Original

`change_password()` verwendet nun einen Dialog mit:

- altem Passwort,
- neuem Passwort,
- Wiederholung,
- 24-Zeichen-Grenze,
- leerem neuem Passwort als „kein Passwort“.

Die Validierung nutzt die alte Notizen.NET-Passwortnormalisierung.

## Geänderte / neue Dateien

- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/models.py`
- `src/notizen_py_qt/alx_io.py`
- `src/notizen_py_qt/exporters.py`
- `src/notizen_py_qt/i18n.py`
- `src/notizen_py_qt/legacy_colors.py`
- `src/notizen_py_qt/startup.py`
- `src/notizen_py_qt/__init__.py`
- `tests/test_legacy_behaviour_094.py`
- `pyproject.toml`
- `README.md`

## Bekannte Grenzen

- Die GUI konnte in dieser Umgebung weiterhin nicht echt gestartet werden, weil weder PySide6 noch PyQt6 installiert ist.
- Die Runtime-Probe erkennt das sauber und gibt Installationshinweise aus.
- Die Sprachumschaltung deckt jetzt Menüs und viele sichtbare Aktionen ab, aber nicht jedes einzelne Laufzeitlabel jedes Dialogs ist vollständig wie im alten Designer gebunden.
- Exotische RTF-Fälle aus WinForms/RichTextBox wie OLE-Objekte, WMF/EMF oder Tabellen bleiben weiterhin nicht vollständig WinForms-identisch.
