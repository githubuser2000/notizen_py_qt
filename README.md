# Notizen PyPy Slint

Das ist ein PyPy3-orientierter Port von **Notizen.NET** aus dem gelieferten VB.NET/WinForms-Projekt. Der alte Code wurde nicht nur zeilenweise umgeschrieben: Datei-Format, Notizbaum, RTF-Textinhalt, Sicherheitskopien, Import des alten Intellibit-Formats und die historische DES-Kaskadenverschlüsselung wurden als pure-Python-Kern neu aufgebaut. Die Oberfläche liegt als Slint-Datei plus Python-Controller vor.

## Status

Funktioniert im Port:

- `.alx` laden und speichern
- GZip-komprimiertes UTF-16-XML-Format `<notizen-alx2>` lesen/schreiben
- verschlüsselte `.alx`-Dateien lesen/schreiben, kompatibel zur alten dreifachen DES-CBC-Kaskade mit den alten Passwort-Slicing-Eigenheiten
- Notizbaum anzeigen, Kind-/Nachbarnotizen anlegen, löschen, auf-/zuklappen
- Suche über Titel und Text
- TXT- und RTF-Export
- alte Intellibit-`notes_doc`-Dateien importieren
- Sicherheitskopien beim Speichern
- kleine Kommandozeile ohne GUI als Fallback

Bewusst vereinfacht oder nicht vollständig portiert:

- Slints `TextEdit` ist Plain-Text; vorhandenes RTF wird beim Laden in Text umgewandelt. Unveränderte Notizen werden intern weiter als altes RTF gehalten, aber nach dem Bearbeiten als schlichtes RTF neu gespeichert.
- Sticky/Desktop-Notiz-Metadaten werden im Dateiformat erhalten, aber nicht als separate Desktop-Fenster geöffnet.
- FTP-Speichern, Tray/Autostart, Drag-and-drop, eingebettete Bilder und die alte mehrsprachige WinForms-Menülogik sind nicht in der neuen UI enthalten.
- Die alte Verschlüsselung ist absichtlich nur kompatibel, nicht sicher. Für echte Sicherheit die `.alx` zusätzlich mit einem modernen Werkzeug verschlüsseln.

## Installation

Für den reinen Kern reicht PyPy3 ohne externe Pakete:

```bash
cd notizen_pypy_slint
pypy3 -m pip install -e .
```

Für die Slint-Oberfläche:

```bash
cd notizen_pypy_slint
pypy3 -m pip install -e ".[slint]"
```

Hinweis: Die UI-Abhängigkeit ist absichtlich auf `slint==1.8.0a1` gepinnt, weil neuere Slint-Python-Versionen aktuell Python 3.12+ verlangen, während PyPy aktuell bei Python 3.11 liegt. Je nach Plattform kann Slint unter PyPy trotzdem einen Rust-/Native-Build benötigen oder nicht installierbar sein. Der Kern und das CLI bleiben davon unabhängig.

## Starten

GUI:

```bash
pypy3 -m notizen_pypy_slint
pypy3 -m notizen_pypy_slint pfad/zur/datei.alx
pypy3 -m notizen_pypy_slint pfad/zur/datei.alx --password geheim
```

CLI-Fallback ohne Slint:

```bash
notizen-alx tree tests/fixtures/test.alx
notizen-alx export-txt tests/fixtures/test.alx /tmp/notizen.txt
notizen-alx export-rtf tests/fixtures/test.alx /tmp/notizen.rtf
notizen-alx change-password input.alx output.alx --old-password alt --new-password neu
```

## Tests

```bash
cd notizen_pypy_slint
PYTHONPATH=src pypy3 -m unittest discover -s tests -v
```

Im Erstellungscontainer wurden die Kern-Tests mit CPython ausgeführt, weil dort weder `pypy3` noch `slint` installiert war:

```text
Ran 6 tests in 0.035s
OK
```

Getestet wurden:

- DES-Known-Vector
- Notizen-DES-Kaskaden-Roundtrip
- RTF Plain-Text-Konvertierung
- Laden der originalen `test.alx`-Fixture mit 65 Knoten
- Speichern/Laden unverschlüsselt
- Speichern/Laden verschlüsselt

## Projektstruktur

```text
src/notizen_pypy_slint/
  app.py              Slint-Controller
  ui/app-window.slint Slint-Oberfläche
  model.py            Notizbaum-Datenmodell
  storage.py          .alx/.xml Laden, Speichern, Export
  des_compat.py       pure-Python DES/CBC-Kompatibilität
  rtf.py              einfache RTF<->Text-Konvertierung
  cli.py              CLI-Fallback ohne Slint
  config.py           JSON-Konfiguration
  dialogs.py          Tkinter-/Konsolen-Dialoge
```

## Lizenz

Der Ursprungscode steht unter GPL-3.0. Dieser Port behält die GPL-Lizenz bei; siehe `LICENSE`.
