# Notizen.NET → Python/Qt Weitertranspilierung

Stand: 2026-04-30

## Importierter Kontext

- Die beiden gelieferten Archive wurden entpackt und verglichen:
  - `notizen.net.tar.bz2`: VB.NET/WinForms-Originalprojekt.
  - `notizen_py_qt.tar.bz2`: vorhandener Qt-/QML-Migrationsstand mit Hilfsskripten.
- Aus dem abrufbaren Projektgedächtnis war nur wenig konkreter Notizen.NET-Kontext verfügbar. Verwertbar war vor allem die frühere Entscheidung, Qt for Python mit PySide6 zu bevorzugen und Ressourcen über Qt-/Paketressourcen zu führen. Deshalb nutzt der neue Port PySide6 als Standard, lässt aber PyQt6 als Fallback zu.

## Analysierte .NET-Quelle

Wichtige VB.NET-Dateien im Original:

- `Notizen.vb` – Hauptfenster, Menülogik, Laden/Speichern, Passwort-/DES-Kette, Export, Tastenkürzel, Desktop-Notizen.
- `Baum.vb` – TreeView-Operationen, Einfügen, Löschen, Kopieren, Rekursion über alle Knoten.
- `inhalt.vb` – RichTextBox ↔ TreeNode.Tag/CText-Synchronisation.
- `CText.vb` – RTF-Inhalt plus Verweis auf Desktop-Notiz.
- `xml_kram.vb` – Konfigurationsdatei `notizen.config.xml`.
- `suche.vb` – Suche im aktuellen oder gesamten Baum.
- `desknote.vb` – schwebende Desktop-Notizen.
- `ftpkram.vb` – FTP-Öffnen/Speichern.
- `wecker.vb` – Wecker-Dialogansatz.

## Neu transpilierte Python/Qt-Struktur

Ein echtes Python-Paket wurde in `src/notizen_py_qt/` angelegt:

- `app.py` – Qt-Hauptfenster, Baum, Editor, Menüs, Tray, Desktop-Notizen, FTP-Dialog, Wecker.
- `models.py` – `NoteDocument`, `NoteNode`, `DesktopNoteState`.
- `alx_io.py` – Notizen-ALX-Dateiformat, GZip, UTF-16-XML, Legacy-DES-Passwortmodus, Backups.
- `rtf_utils.py` – einfache RTF↔Plaintext-Brücke, damit alte RTF-Inhalte lesbar bleiben.
- `settings.py` – kompatible `notizen.config.xml`-Konfiguration mit Fensterdaten, Dateien, FTP-Daten, Backups.
- `search_logic.py` – Suchlogik mit Ganzwort- und Groß-/Kleinschreibung.
- `ftp_sync.py` – FTP-Zielnormalisierung, Download und Upload per stdlib-`ftplib`.
- `qt_compat.py` – PySide6 bevorzugt, PyQt6 als Fallback.
- `resources/` – importiertes Notizen-Icon plus `.qrc`-Datei.

## Portierte Funktionen

- Öffnen und Speichern von `.alx`-Dateien.
- Kompatibles ALX-v2-XML mit `<notizen-alx2>` und verschachtelten `<Notiz>`-Elementen.
- Legacy-Import von `<notes_doc>`-Dokumenten.
- GZip-komprimierte UTF-16-XML-Dateien wie im Original.
- Passwortmodus mit der dreifachen DES-Kette des VB.NET-Codes.
- Sicherungskopien im Dateistamm-Unterordner, begrenzt nach Einstellung.
- Notizbaum mit Hinzufügen, Umbenennen, Löschen, Kopieren, Ausschneiden und Einfügen.
- Synchronisation zwischen Baumknoten und Editor.
- Suche im aktuellen Knoten oder im gesamten Baum.
- Export als RTF oder TXT.
- Desktop-Notizen als schwebende Qt-Fenster mit gespeicherter Position/Größe/Deckkraft.
- System-Tray-Menü mit Anzeigen/Ausblenden und Desktop-Notiz-Einträgen.
- Grundkonfiguration und zuletzt geöffnete Dateien.
- FTP-Dialog zum Öffnen/Speichern, angelehnt an `ftpkram.vb`.
- Wecker-Dialog mit Qt-Timer, aufrufbar per `Ctrl+Space`.
- Importiertes 64x64-Notizen-Icon als Paketressource und `.qrc`.

## Bekannte Grenzen

- Der Editor zeigt alte RTF-Inhalte lesbar als Text an. Formatierung wird beim bloßen Öffnen/Speichern erhalten, aber nach Bearbeitung noch nicht vollständig als RichText-Roundtrip rekonstruiert.
- Die WinForms-Oberfläche ist funktional nachgebaut, nicht pixelgenau kopiert.
- Die vollständigen Spracharrays aus `languages.vb` wurden noch nicht 1:1 portiert; die aktuelle Oberfläche ist überwiegend deutsch.
- FTP ist aus Kompatibilitätsgründen enthalten, bleibt aber wie im Original unverschlüsselt. Für vertrauliche Notizen sollte die ALX-Datei selbst mit Passwort gespeichert werden.
- Die GUI konnte in dieser Umgebung nicht gestartet werden, weil weder PySide6 noch PyQt6 installiert ist. Die nicht-GUI-seitigen Parser-, Format- und Migrationstests laufen durch.

## Installation und Start

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

## Ressourcen

Das Icon liegt als Paketdatei unter `src/notizen_py_qt/resources/notizen.png`. Zusätzlich liegt `notizen.qrc` bereit. Auf einem Rechner mit PySide6 kann daraus bei Bedarf ein Python-Resource-Modul erzeugt werden:

```bash
pyside6-rcc src/notizen_py_qt/resources/notizen.qrc -o src/notizen_py_qt/resources_rc.py
```

Der Code funktioniert auch ohne kompiliertes `.qrc`, weil er auf die Paketressource zurückfällt.
