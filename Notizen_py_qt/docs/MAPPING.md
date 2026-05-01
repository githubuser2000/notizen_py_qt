# Notizen.NET → Python/Qt Mapping

Aktiver Portierungsstand: **0.9.8**. Diese Datei beschreibt die aktuelle semantische Zuordnung vom alten VB.NET/WinForms-Projekt zu den Python/Qt-Modulen. Die früheren Qt/QML-Zwischenschritte sind archiviert unter `legacy_build_metadata/` und nicht mehr Teil des aktiven Laufzeitpfads.

## Kernstruktur

| Notizen.NET-Quelle | Python/Qt-Ziel | Stand |
|---|---|---|
| `Notizen.vb`, `Notizen.Designer.vb` | `src/notizen_py_qt/app.py` | Hauptfenster, Menüs, Toolbar, Baum, Editor, Dialoge und Legacy-Aktionen sind semantisch portiert. |
| `Baum.vb`, `Baum_Kontext_.vb` | `app.py`, `models.py`, `node_clipboard.py` | Baumoperationen, Einfügen/Ausschneiden/Kopieren, Drag-and-drop-nahe Modellpflege, Knotenfarben, Auf-/Zu-Funktionen und Teilbaum-Zusammenfassung sind portiert. |
| `inhalt.vb`, `kontext_inhalt.vb`, `fontsize.vb` | `app.py`, `rtf_utils.py` | RichText-Bearbeitung, Formatierungen, Datum, Bild-Einfügen, Fokus-abhängige Zwischenablage und RTF/HTML-Brücke sind portiert. |
| `Datei.vb`, `xml_kram.vb` | `alx_io.py`, `settings.py`, `app.py` | ALX-Laden/Speichern, UTF-16-XML, GZip, Backups, Passwortmodus und alte Config-Dateien sind portiert. |
| `suche.vb`, `suchergebnisse.vb` | `search_logic.py`, `SearchDialog`, Schnell-Suchleiste in `app.py` | Suche in aktuellem Knoten oder Gesamtbaum ist portiert; 0.9.8 synchronisiert vorher den Live-Editorinhalt. |
| `desknote.vb`, `desknote_kontext.vb`, `desknote_kontext_opacy.vb` | `DesktopNoteWindow`, `DesktopNoteState`, `legacy_colors.py` | Desktop-Notizen, Farben, Transparenz, Kontextmenü und Rücksprung ins Hauptfenster sind portiert. |
| `einstellungen.vb` | `settings.py`, Settings-Dialog in `app.py` | Backups, Autosave, Sprache, Scrollleisten, Desktop-Notiz-Ränder, Autostart-Felder und zuletzt geöffnete Dateien sind portiert. |
| `ftpkram.vb` | `ftp_sync.py`, FTP-Dialog in `app.py` | FTP-Öffnen/Speichern der ALX-Datei ist portiert. |
| `wecker.vb` | `alarms.py`, Alarm-Dialog in `app.py` | Einmalige und wiederholende Wecker sind portiert. |
| `languages.vb`, `.resx`-Sprachdaten | `i18n.py`, dynamische Aktionsbeschriftungen in `app.py` | Wichtige Legacy-Sprachen und Menütexte sind importiert und umschaltbar. |
| `ApplicationEvents.vb` | `startup.py`, `app.py` | Legacy-Startargumente wie minimierter Start und direkte Datei-/FTP-Ziele sind portiert. |
| `passwort_dialog*.vb`, `wanna_save.vb`, `wanna_restart.vb`, `AboutBox1.vb` | Qt-Dialoge in `app.py` | Passwort-, Speicher-, Einstellungs- und Info-Dialoge sind in Qt nachgebildet. |
| `Notizen.ico`, `Notizen.png` | `src/notizen_py_qt/resources/` | Programm-Icon und Ressource sind importiert. |

## In 0.9.8 weitergeführt

- `einheit_node_MenuItem_Click` bleibt als **Teilbaum zusammenfassen** erhalten.
- `einheit_start_MenuItem_Click` ist jetzt zusätzlich als **Ganzen Baum zusammenfassen** portiert. Die neue Notiz wird wie im alten Programm als Kind des ausgewählten Wurzel-/Quellknotens angelegt und anschließend ausgewählt.
- Suche, Schnell-Suche und Exporte schreiben den gerade sichtbaren Editorinhalt vor der Modellauswertung zurück, damit nicht mehr versehentlich ältere Knotendaten exportiert oder durchsucht werden.
- Das Menü **Zuletzt geöffnet** nutzt nun denselben Speichern-Verwerfen-Abbrechen-Pfad wie normales Öffnen und warnt bei fehlenden Dateien.
- Alte Migrationshilfen aus früheren UI-Zwischenschritten wurden aus dem aktiven Pfad entfernt und im Legacy-Bereich aufbewahrt.

## Noch offene beziehungsweise bewusst zurückgestellte Punkte

- Die RTF-Brücke deckt die üblichen alten Notizen-Fälle ab, ist aber kein vollständiger Microsoft-RTF-Renderer.
- FTP bleibt absichtlich eine Legacy-Kompatibilitätsfunktion; für vertrauliche Daten sollte mindestens die ALX-Datei selbst verschlüsselt werden.
- Visuelle Qt-Prüfung benötigt lokal PySide6 oder PyQt6. In dieser Ausführungsumgebung war keine Qt-Bindung installiert.
