# Notizen.NET → Python/Qt Weitertranspilierung

Stand: 2026-04-30  
Version: 0.9.2

## Importierter Kontext

- Ausgangspunkt war der vorhandene Port `notizen_py_qt_net_port_0.9.1.tar.bz2` plus das originale VB.NET/WinForms-Archiv `notizen.net.tar.bz2`.
- Der aktive Zielpfad ist weiterhin ein Python-Paket unter `src/notizen_py_qt/`.
- Frühere Projektentscheidung bleibt erhalten: PySide6 ist das bevorzugte Qt-for-Python-Ziel; PyQt6 bleibt als Fallback im Kompatibilitätslayer.

## In dieser Runde weiter transpilierte .NET-Funktionen

### RichTextBox-Verhalten

Der größte offene Block aus 0.9.1 war der RichText-Roundtrip. `rtf_utils.py` wurde deshalb deutlich erweitert:

- RTF → HTML für den Qt-Editor statt nur RTF → Plaintext.
- HTML/Qt-Editorinhalt → RTF für gespeicherte ALX-Inhalte.
- Unterstützung für typische WinForms-`RichTextBox`-Formatierung:
  - fett,
  - kursiv,
  - unterstrichen,
  - durchgestrichen,
  - Schriftgröße,
  - Textfarbe,
  - Texthintergrund/Highlight,
  - Tabs, Absätze, Bullet-Zeichen und Windows-RTF-Sonderzeichen.
- Unicode-Roundtrip inklusive Nicht-BMP-Zeichen wie Emoji über korrekte UTF-16-Surrogates in RTF.
- RTF-Metadaten, Fonttabellen, Farbtabellen, Bilder/Object-Gruppen und andere nicht-textuelle Ziele werden beim Lesen sauber übersprungen.
- HTML-Bilder aus dem Qt-Editor werden bewusst als sichtbarer Marker `[Bild]` gespeichert, statt einen unvollständigen RTF-Bildblock vorzutäuschen.

### Editor- und Tastaturverhalten

`app.py` wurde näher an `Notizen.vb/tastendruck` gebracht:

- Ausschneiden/Kopieren/Einfügen/Löschen ist jetzt fokusabhängig:
  - Editor-Fokus: Textoperation.
  - Baum-Fokus: Knotenoperation.
- `Insert`, `Delete` und `Return` wirken nur noch bei Baum-Fokus als Knotenbefehle.
- `Ctrl+Space` bleibt Wecker.
- `Ctrl+U` bleibt wie im Original für Umbenennen reserviert; Unterstreichen ist weiterhin über Menü/Toolbar erreichbar.
- Drag-and-drop-Verschiebungen im Baum markieren das Dokument jetzt als geändert.

### Format-Menü und Toolbar

Neu ergänzt oder stabilisiert:

- Fett, Kursiv, Unterstrichen, Durchgestrichen.
- Format zurücksetzen.
- Schrift größer/kleiner.
- Textfarbe und Texthintergrund.
- Bullet-Einfügung nach altem `ToolStrip_dot_Click`-Muster.
- RichText-Kontextaktionen im Editor.

### Teilbaum-Export und Zusammenfassung

Das alte `fasse_zusammen`-/Export-Verhalten aus `Notizen.vb` wurde in `exporters.py` nachgebaut:

- RTF-Export des ganzen aktuellen Teilbaums statt nur des aktuellen Knotens.
- TXT-Export des ganzen aktuellen Teilbaums.
- RTF-Export erhält jetzt die unterstützte Body-Formatierung der einzelnen Notizen: Fett, Kursiv, Unterstrichen, Durchgestrichen, Schriftgröße, Textfarbe und Highlight.
- Nummerierung im alten Stil:
  - Root-Titel unnummeriert,
  - Kinder als `1.` / `2.` / …,
  - Enkel als `1.1.` / `1.2.` / ….
- Neue Aktion **Teilbaum zusammenfassen**, die unter dem aktuellen Knoten eine neue zusammengeführte Notiz erzeugt.

Hinweis: Der Export erzeugt bewusst ein robustes, interoperables RTF-Snapshot-Dokument. Er verschmilzt nicht bytegenau mehrere fremde RTF-Dokumente per Raw-RTF-Inline-Merge; das wäre ohne RichTextBox/Qt-Document-Engine fragil. Die vom Port sicher gelesene Formatierungsmenge wird aber in den kombinierten Export übernommen.

### Konfiguration

`settings.py` wurde erweitert, um mehr Felder aus `xml_kram.vb` zu übernehmen:

- `scrolls choice` wird gelesen und geschrieben.
- `autorun if` und `autorun minimized` werden gelesen und geschrieben.
- Spracheinstellung wird im Einstellungsdialog bearbeitbar gespeichert.
- Einstellung „minimiert in Taskleiste zeigen“ ist im Dialog verfügbar.
- Editor-Scrollleisten folgen der gespeicherten `scrolls`-Einstellung.
- Beim Minimieren kann das Fenster wie im alten Programm aus der Taskleiste verschwinden, wenn Tray verfügbar ist und die Einstellung so gesetzt ist.

Autostart wird derzeit nur kompatibel in der Konfigurationsdatei gespeichert; es wird noch kein OS-spezifischer Autostart-Eintrag geschrieben.

### Projektbereinigung

Die aktiven Projektdateien wurden von alten Slint-/QML-Zwischenschritten bereinigt:

- Historische Qt-/QML-/Slint-Migrationsskripte und zugehörige Tests liegen jetzt unter `legacy_build_metadata/qt611_migration_kit/`.
- Der aktive Python/Qt-Port enthält im Hauptpfad nur noch die Notizen-Python/Qt-App, ihre Tests, Ressourcen und schlanke Hilfsskripte.
- `scripts/check_no_slint.sh` meldet für den aktiven Projektpfad jetzt sauber: keine alten UI-Framework-Referenzen.

## Aktive Python/Qt-Struktur

- `src/notizen_py_qt/app.py` – Qt-Hauptfenster, Baum, Editor, Menüs, Tray, Desktop-Notizen, FTP-Dialog, Wecker.
- `src/notizen_py_qt/models.py` – `NoteDocument`, `NoteNode`, `DesktopNoteState`.
- `src/notizen_py_qt/alx_io.py` – ALX-Dateiformat, GZip, UTF-16-XML, Legacy-DES-Passwortmodus, Backups.
- `src/notizen_py_qt/rtf_utils.py` – RTF↔HTML↔Plaintext-Brücke.
- `src/notizen_py_qt/exporters.py` – Teilbaum-Export und Zusammenfassung.
- `src/notizen_py_qt/settings.py` – kompatible `notizen.config.xml`-Konfiguration.
- `src/notizen_py_qt/search_logic.py` – Suchlogik.
- `src/notizen_py_qt/ftp_sync.py` – FTP-Zielnormalisierung, Download und Upload per `ftplib`.
- `src/notizen_py_qt/qt_compat.py` – PySide6 bevorzugt, PyQt6 als Fallback.
- `src/notizen_py_qt/resources/` – Notizen-Icon und `.qrc`.

## Bekannte Grenzen

- RichText ist jetzt deutlich besser, aber nicht vollständig WinForms-byteidentisch. Komplexe RTF-Features wie eingebettete OLE-Objekte, Tabellen oder echte RTF-Bild-Roundtrips sind noch nicht vollständig portiert.
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
