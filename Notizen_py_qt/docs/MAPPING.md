# Notizen.NET → Python/Qt Mapping

Aktiver Portierungsstand: **0.10.1**. Diese Datei beschreibt die aktuelle semantische Zuordnung vom alten VB.NET/WinForms-Projekt zu den Python/Qt-Modulen. Die früheren Qt/QML-Zwischenschritte sind archiviert unter `legacy_build_metadata/` und nicht mehr Teil des aktiven Laufzeitpfads.

## Kernstruktur

| Notizen.NET-Quelle | Python/Qt-Ziel | Stand |
|---|---|---|
| `Notizen.vb`, `Notizen.Designer.vb` | `src/notizen_py_qt/app.py` | Hauptfenster, Menüs, Toolbar, Baum, Editor, Dialoge und Legacy-Aktionen sind semantisch portiert. |
| `Baum.vb`, `Baum_Kontext_.vb` | `app.py`, `models.py`, `node_clipboard.py` | Baumoperationen, Einfügen/Ausschneiden/Kopieren, Drag-and-drop-nahe Modellpflege, Knotenfarben, Auf-/Zu-Funktionen und Teilbaum-Zusammenfassung sind portiert. |
| `inhalt.vb`, `kontext_inhalt.vb`, `fontsize.vb` | `app.py`, `rtf_utils.py` | RichText-Bearbeitung, Formatierungen, Datum, Bild-Einfügen, Fokus-abhängige Zwischenablage und RTF/HTML-Brücke sind portiert. |
| `Datei.vb`, `xml_kram.vb` | `alx_io.py`, `settings.py`, `legacy_paths.py`, `app.py` | ALX-Laden/Speichern, UTF-16-XML, GZip, `saftycopies`-Backupordner, Backup-Rotation, Passwortmodus, alte Config-Dateien, Standardordner `Documents/Notizen` und Legacy-Dateipfad-Splitting sind portiert. |
| `suche.vb`, `suchergebnisse.vb` | `search_logic.py`, `SearchDialog`, Schnell-Suchleiste in `app.py` | Suche in aktuellem Knoten oder Gesamtbaum ist portiert; 0.9.8 synchronisiert vorher den Live-Editorinhalt. |
| `desknote.vb`, `desknote_kontext.vb`, `desknote_kontext_opacy.vb` | `DesktopNoteWindow`, `DesktopNoteState`, `legacy_colors.py`, `desktop_note_legacy.py` | Desktop-Notizen, Farben, altes Transparenzmenü, Kontextmenü, Rücksprung ins Hauptfenster und WinForms-nahe Startgeometrie sind portiert. |
| `einstellungen.vb` | `settings.py`, Settings-Dialog in `app.py` | Backups, Autosave, Sprache, Scrollleisten, Desktop-Notiz-Ränder, Autostart-Felder und zuletzt geöffnete Dateien sind portiert. |
| `ftpkram.vb` | `ftp_sync.py`, FTP-Dialog in `app.py` | FTP-Öffnen/Speichern der ALX-Datei ist portiert. |
| `wecker.vb` | `alarms.py`, Alarm-Dialog in `app.py` | Einmalige und wiederholende Wecker sind portiert. |
| `languages.vb`, `.resx`-Sprachdaten | `i18n.py`, dynamische Aktionsbeschriftungen in `app.py` | Wichtige Legacy-Sprachen und Menütexte sind importiert und umschaltbar. |
| `ApplicationEvents.vb` | `startup.py`, `app.py` | Legacy-Startargumente wie minimierter Start und direkte Datei-/FTP-Ziele sind portiert. |
| `passwort_dialog*.vb`, `wanna_save.vb`, `wanna_restart.vb`, `AboutBox1.vb` | Qt-Dialoge in `app.py` | Passwort-, Speicher-, Einstellungs- und Info-Dialoge sind in Qt nachgebildet. |
| `Notizen.ico`, `Notizen.png` | `src/notizen_py_qt/resources/` | Programm-Icon und Ressource sind importiert. |

## In 0.10.1 weitergeführt

- `Datei.vb` ist genauer abgebildet: Der alte Standard-Dateiname `unbenannt.alx` und der Standardordner `MyDocuments\Notizen` entsprechen im Port `Documents/Notizen`.
- `split_legacy_file_location` trennt Windows-Backslash-Pfade, POSIX-Pfade und leere Dateiwerte stabil in Verzeichnis/Dateiname. Damit werden alte Configs mit `C:\...\demo.alx` auf Linux/macOS nicht mehr als ein einziger Dateiname interpretiert.
- Das Desktop-Notiz-Untermenü aus `desknote_kontext_opacy.vb` nutzt wieder die alte Transparenz-Bedeutung: `90 %` Transparenz wird zu 10 % Deckkraft, `0 %` zu 100 % Deckkraft.
- Fensterzustände aus `xml_kram.vb` werden normalisiert. `minimized` und `maximized` werden in der Startlogik berücksichtigt; offensichtlich außerhalb des Arbeitsbereichs liegende Hauptfensterpositionen werden beim Wiederherstellen abgefangen.
- Neue Kernhilfen sind ohne Qt testbar und aus dem Paket exportiert: `LEGACY_DEFAULT_FILENAME`, `legacy_documents_notizen_dir`, `split_legacy_file_location`, `legacy_transparency_menu_options`, `legacy_opacity_percent_for_transparency_percent` und `normalize_window_state`.

## In 0.10.0 weitergeführt

- `xml_kram.vb`/`Notizen.Designer.vb`-Configdetails sind genauer übernommen: `open/once-opened` und `tool-stripes` werden gelesen, gespeichert und bleiben nach einem Import erhalten.
- Die Autosave-Regel aus `einstellungen.vb` ist als `normalize_autosave_seconds` portiert: `0` deaktiviert, aktivierte Werte unter fünf Sekunden werden auf fünf Sekunden gehoben, neue Standard-Config startet mit 60 Sekunden.
- `xml_kram.setshortcut` ist als testbarer Autostart-Adapter in `startup.py` abgebildet. Der Port wählt die jüngste Recent-Datei, setzt optional `-min` davor und schreibt unter Windows einen kleinen Startup-Launcher.
- Die RTF-Brücke behandelt RichTextBox-Tabellensteuerwörter `\cell`, `\nestcell` und `\row` nun als Tabulator-/Zeilen-Grenzen, damit alte Tabelleninhalte in Suche, Statistik und Exporten lesbar bleiben.

## In 0.9.9 weitergeführt

- Die alte `saftycopies`-Sicherungslogik wurde aus `Notizen.vb`/`xml_kram.vb` präzisiert: Backup-Verzeichnis ohne `.alx`-Suffix, Dateinamen nach `Name-YYYY-MM-DD-HH-MM-SS-ms.alx`, Auflistung, Rotation und explizite UI-Aktionen.
- Im Menü und in der Werkzeugleiste gibt es jetzt **Jetzt Sicherung erstellen** und **Sicherung öffnen**. Sicherungen werden aus dem ermittelten Legacy-Ordner geöffnet und durchlaufen vorher denselben Speichern-Abbrechen-Pfad wie normales Öffnen.
- Neue Desktop-Notizen übernehmen die Startwerte des alten Baum-Kontextmenüs: Mausposition, 200×200 Pixel, 85 % Deckkraft und helle Legacy-Farbe.
- Die Backup-Hilfsfunktionen sind als eigenständige API (`backup_directory_for`, `list_backups`, `create_backup`, `prune_backups`) testbar und aus dem Paket exportiert.

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
