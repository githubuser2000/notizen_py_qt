# Transpilationsbericht Notizen.NET → Python/Qt 0.9.9

Datum: 2026-05-01

## Ziel dieser Runde

Der vorhandene Python/Qt-Port 0.9.8 wurde erneut gegen das alte VB.NET/WinForms-Projekt geprüft und semantisch weitergeführt. Der Projektkontext aus den bisherigen Notizen-Chats bleibt übernommen: Ziel ist eine wartbare Python/Qt-Portierung, nicht das mechanische Nachbauen alter WinForms-Designerdateien.

## Ausgewertete Ausgangslage

- Original: `Notizen.NET/Notizen/*.vb`, insbesondere `Notizen.vb`, `xml_kram.vb`, `Baum_Kontext_.vb`, `desknote.vb`, `desknote_kontext.vb`, `Datei.vb` und `ftpkram.vb`.
- Zielprojekt: `src/notizen_py_qt/` mit PySide6/PyQt6-Kompatibilitätslayer.
- Vorheriger Stand: 0.9.8 mit ALX, Baum/Editor, Suche, Export, Desktop-Notizen, FTP, Wecker, Statistik, Config-Import, Recent-Dateien und Baum-Zusammenfassung.

## Umgesetzte Änderungen in 0.9.9

### 1. Notizen.NET-Backupverwaltung präzisiert

Die alte Speicherlogik in `Notizen.vb` erzeugt vor dem Überschreiben einer bestehenden `.alx`-Datei Sicherheitskopien. Der Ordner trägt den Namen der Datei ohne `.alx`-Endung, die Backup-Dateien folgen dem Muster `Name-YYYY-MM-DD-HH-MM-SS-ms.alx`, und die Anzahl wird über `saftycopies amount` gesteuert.

Das wurde im Python/Qt-Port gehärtet:

- neue `BackupEntry`-Struktur
- `backup_directory_for(path)` für den alten Sicherungsordner
- `backup_file_pattern(path)` für Legacy-Dateinamen
- `parse_legacy_backup_timestamp(...)` für alte Zeitstempel
- `list_backups(path)` mit stabiler Sortierung
- `prune_backups(path, keep)` für Rotation
- `create_backup(path, keep)` nutzt nun diese Hilfsfunktionen
- API-Export über `notizen_py_qt.__init__`

### 2. Backupaktionen in der Oberfläche ergänzt

Im alten Programm waren Sicherheitskopien Teil der Speichern-/Config-Logik, aber schwer sichtbar. In 0.9.9 gibt es zusätzlich explizite Qt-Aktionen:

- **Jetzt Sicherung erstellen**
- **Sicherung öffnen**

Beide sind im Datei-Menü und in der Datei-Werkzeugleiste verdrahtet. Beim Öffnen einer Sicherung wird der Legacy-Sicherungsordner aus der aktuellen `.alx`-Datei abgeleitet; ungespeicherte Änderungen werden vorher wie beim normalen Öffnen abgefragt.

Der Einstellungsdialog zeigt neben der Anzahl zu behaltender Sicherungen jetzt auch den konkret ermittelten Sicherungsordner an.

### 3. Desktop-Notiz-Startwerte näher an WinForms gebracht

`Baum_Kontext_.vb` erzeugte neue Desktop-Notizen am aktuellen Mauszeiger mit 200×200 Pixeln, 85 % Deckkraft und heller Legacy-Farbe. Der Port hatte bisher generische Standardwerte. 0.9.9 ergänzt:

- `default_desktop_note_state()` im Hauptfenster
- Startposition über `QtGui.QCursor.pos()` mit Fallback
- Breite/Höhe 200×200
- Deckkraft 0.85
- helle Legacy-Farbe über `legacy_light_color_argb()`

### 4. Kleine Bereinigung

Eine doppelte Zuweisung der Wecker-Aktion im Aktionsaufbau wurde entfernt.

## Neue Tests

Neu ergänzt:

- `tests/test_backup_management_099.py`
  - Backup-Ordner und Dateimuster
  - Legacy-Zeitstempelparser
  - Backup-Erstellung und Rotation
  - `keep=0` entfernt alle alten Sicherungen
- `tests/test_legacy_ui_source_099.py`
  - Backupaktionen sind in `app.py` verdrahtet
  - Backup-Hilfsfunktionen erhalten das alte Namensschema
  - Desktop-Notiz-Startwerte entsprechen dem WinForms-Kontextmenü

## Nicht visuell geprüft

In dieser Umgebung ist keine Qt-Bindung installiert. Deshalb konnte das Hauptfenster nicht interaktiv geöffnet werden. Die headless Validierung, Import-/Datenmodelltests und statischen UI-Quellprüfungen laufen durch. Eine lokale Sichtprüfung mit `PySide6>=6.6,<7` oder `PyQt6>=6.6,<7` bleibt sinnvoll.
