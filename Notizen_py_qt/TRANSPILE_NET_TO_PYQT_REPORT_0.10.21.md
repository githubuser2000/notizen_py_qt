# Notizen.NET -> Python/Qt Transpilation Report 0.10.21

## Fokus dieser Runde

Diese Runde baut direkt auf 0.10.20 auf:

1. Der GNOME-Menüstart blieb beim bestätigten direkten `python3 -m notizen_py_qt`-Pfad, aber das laufende Qt-Programm bekommt jetzt dieselbe App-Identität wie der Desktop-Starter.
2. Die RTF-Brücke wurde weiter Richtung WinForms-`RichTextBox` erweitert, vor allem für echte Absatzformatierung, Absatzabstände, Zeilenhöhe, Überschriften und Qt-HTML-Rückimport.
3. Das `.alx`-Speichern/Laden wurde gegen den alten `notizen-alx2`-Kern erneut geprüft und zusätzlich getestet.

## Runtime-Icon / Taskleiste / Window-Manager

Nur `Icon=notizen-py-qt` in der `.desktop`-Datei reicht unter GNOME/Wayland/X11 oft nicht aus. Der Window-Manager muss das laufende Fenster der Desktop-Datei zuordnen können.

Änderungen:

- Neue Konstanten `APP_DESKTOP_ID = "notizen-py-qt"` und `APP_DISPLAY_NAME = "Notizen PyQt"`.
- Vor und nach dem Erzeugen von `QApplication` wird die Runtime-Identität gesetzt:
  - `RESOURCE_NAME=notizen-py-qt`,
  - `QCoreApplication.setApplicationName("notizen-py-qt")`,
  - `QApplication.setApplicationDisplayName("Notizen PyQt")`,
  - `QApplication.setDesktopFileName("notizen-py-qt")`,
  - globales `QApplication`-Icon.
- Das Hauptfenster und Desktop-Haftnotizen setzen zusätzlich ihr eigenes `setWindowIcon(app_icon())`.
- `QApplication` wird mit `argv[0] == "notizen-py-qt"` erzeugt, statt dem Window-Manager nur `python3` als Prozessnamen zu geben.
- Der direkte GNOME-Exec bleibt ohne Shell-Wrapper, ergänzt aber `RESOURCE_NAME=notizen-py-qt`:

```desktop
Exec=env NOTIZEN_RESET_WINDOW=1 RESOURCE_NAME=notizen-py-qt python3 -m notizen_py_qt --show --no-tray --reset-window %f
```

## RTF-Weitertranspilierung

Die alte WinForms-Anwendung speicherte den Inhalt als `RichTextBox.Rtf`. Die Python/Qt-Seite muss deshalb RTF nicht nur in Plaintext reduzieren, sondern möglichst viel Format über die HTML/QTextEdit-Brücke retten.

Neu/erweitert:

- RTF -> HTML:
  - Absatzformatierung wird auf `<p style="...">` ausgegeben, nicht mehr nur inline.
  - `\sb`, `\sa` und `\sl` werden als `margin-top`, `margin-bottom` und `line-height` abgebildet.
  - `\upN` und `\dnN` werden als Hoch-/Tiefstellung erkannt.
- HTML -> RTF:
  - `margin-top`, `margin-bottom`, `margin`, `line-height` werden wieder als `\sb`, `\sa`, `\sl` geschrieben.
  - `align="center/right/justify"` wird zusätzlich zu CSS `text-align` gelesen.
  - `<h1>` bis `<h6>` werden mit Bold, Größe und Absatzabständen approximiert.
  - `-qt-block-indent` aus QTextEdit-HTML wird als linker RTF-Einzug abgebildet.
- Die internen `RtfTextStyle`-Segmente tragen jetzt auch Absatzabstand und Zeilenhöhe. Dadurch können Exporte und Tests diese Formatfelder weiterreichen.

## `.alx`-Portierungsstand

Für den bekannten `notizen-alx2`-Kern ist Speichern/Laden ausreichend portiert:

- Baumstruktur und Reihenfolge,
- Knotentitel (`name`/`title`),
- Roh-RTF im Elementtext,
- `isexpanded`,
- `bgcolor`/`fgcolor`,
- Desktop-Haftnotiz-Attribute `visible`, `x`, `y`, `width`, `height`, `opacity`, `argb`,
- unbekannte Legacy-Attribute auf `Notiz`-Elementen,
- gzip und optionale alte DES-Verschlüsselung.

Einschränkungen bleiben:

- Sehr alte `notes_doc`-Dateien werden nur als Basis-Import abgedeckt.
- Unbekannte zukünftige Kind-XML-Strukturen unter `Notiz` werden nicht vollständig modelliert.
- RTF/OLE-Inhalte bleiben nur dann vollständig roh erhalten, solange die Notiz nicht im Qt-Editor verändert wird; nach einer Bearbeitung entscheidet die HTML->RTF-Brücke über die unterstützten Formatfelder.

## Weitere offene Bereiche

Weiter offen beziehungsweise nur approximiert:

- vollständige OLE-/RichTextBox-Semantik jenseits der vorhandenen Bild-, Link-, Objektplatzhalter- und Formatbrücke,
- pixelgenaue WinForms-Paint-Details der Desktop-Haftnotiz-Ränder/Ecken,
- alte FTP-Dialog-UI in allen WinForms-Details,
- historische Windows-/ClickOnce-Installationsdetails.
