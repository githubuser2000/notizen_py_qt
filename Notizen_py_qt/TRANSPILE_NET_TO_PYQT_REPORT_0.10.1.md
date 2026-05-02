# Transpilationsbericht Notizen.NET → Python/Qt 0.10.1

Datum: 2026-05-02

## Ziel dieser Runde

Der vorhandene Python/Qt-Port 0.10.0 wurde erneut gegen das alte VB.NET/WinForms-Projekt geprüft und semantisch weitergeführt. Der aktive Port bleibt Python/Qt mit PySide6/PyQt6-Kompatibilität; frühere Slint-/QML-Zwischenschritte bleiben historisches Material und sind nicht Teil des aktiven Laufzeitpfads.

## Ausgewertete Ausgangslage

- Original: `Notizen.NET/Notizen/*.vb`, in dieser Runde besonders `Datei.vb`, `desknote_kontext_opacy.vb` und `xml_kram.vb`.
- Zielprojekt: `src/notizen_py_qt/` mit getrennten Modulen für Datenmodell, ALX-IO, Einstellungen, Startparameter, RTF-Brücke, Legacy-Pfade und Qt-Oberfläche.
- Vorheriger Stand: 0.10.0 mit ALX, Baum/Editor, Suche, Export, Desktop-Notizen, FTP, Wecker, Statistik, Config-/Autostart-Parität, Backup-Verwaltung und RTF-Tabellengrenzen.

## Umgesetzte Änderungen in 0.10.1

### 1. Datei-Standardlogik aus `Datei.vb` portiert

Das alte `Datei.vb` nutzt als Startverzeichnis `MyDocuments\\Notizen`, legt diesen Ordner beim Start an und startet mit dem Dateinamen `unbenannt.alx`. 0.10.1 bildet diese Details als reine, testbare Python-Helfer ab:

- `LEGACY_DEFAULT_FILENAME = "unbenannt.alx"`
- `legacy_documents_notizen_dir(...)`
- `ensure_legacy_documents_notizen_dir(...)`
- `split_legacy_file_location(...)`

Der Standardordner ist im Port plattformneutral `Documents/Notizen` unterhalb des Benutzerordners.

### 2. Legacy-Dateipfade robuster gesplittet

Die alte VB.NET-Anwendung lief auf Windows und trennte Dateipfade über Backslashes. Unter Linux/macOS interpretiert `pathlib.Path` solche Werte nicht automatisch als Verzeichnistrenner. 0.10.1 trennt daher Windows- und POSIX-Pfade bewusst selbst:

- `C:\\Users\\me\\Notizen\\demo.alx` wird zu Verzeichnis `C:\\Users\\me\\Notizen` und Datei `demo.alx`.
- `/home/me/Notizen/demo.alx` wird weiter korrekt behandelt.
- Leere Werte aus alten Configs fallen auf `Documents/Notizen` und `unbenannt.alx` zurück.
- `AppSettings.remember_file(...)` verwendet diese Logik und erhält Recent-Einträge unverändert.

Damit werden alte `open`-Configwerte und zuletzt geöffnete Dateien auf Nicht-Windows-Systemen nicht mehr falsch als einzelner Dateiname behandelt.

### 3. Desktop-Notiz-Transparenz aus `desknote_kontext_opacy.vb` korrigiert

Das alte Kontextmenü bezeichnete die Einträge als Transparenz, nicht als Deckkraft:

- `90 %` Transparenz bedeutete `Opacity = 0.1`.
- `80 %` Transparenz bedeutete `Opacity = 0.2`.
- `0 %` Transparenz bedeutete `Opacity = 1.0`.

0.10.1 ergänzt dafür `desktop_note_legacy.py` mit:

- `legacy_opacity_percent_for_transparency_percent(...)`
- `legacy_transparency_menu_options()`

`DesktopNoteWindow` nutzt diese Liste jetzt direkt. Das Menü sieht dadurch wie das alte WinForms-Menü aus, während die Qt-Fensterinternas weiterhin mit Deckkraftwerten arbeiten.

### 4. Fensterzustände aus `xml_kram.vb` normalisiert

Alte Configs können `windowstate="minimized"`, `windowstate="maximized"` oder ähnliche Schreibweisen enthalten. 0.10.1 führt dafür `normalize_window_state(...)` ein:

- `minimized` wird zu `Minimized`.
- `maximized` wird zu `Maximized`.
- unbekannte Werte fallen auf `Normal` zurück.

Die Startlogik berücksichtigt gespeicherte minimierte Zustände jetzt zusätzlich zu den alten `/min`-/`-min`-Argumenten. Beim Wiederherstellen des Hauptfensters werden außerdem offensichtlich außerhalb des Arbeitsbereichs liegende Koordinaten abgefangen.

### 5. Paket- und API-Stand aktualisiert

- Paketversion: `0.10.1`
- Neue API-Exports in `notizen_py_qt.__init__`:
  - `LEGACY_DEFAULT_FILENAME`
  - `legacy_documents_notizen_dir`
  - `split_legacy_file_location`
  - `legacy_opacity_percent_for_transparency_percent`
  - `legacy_transparency_menu_options`
  - `normalize_window_state`

## Neue Tests

Neu ergänzt:

- `tests/test_legacy_paths_desktop_101.py`
  - Standardordner und Standarddateiname aus `Datei.vb`
  - Windows-Pfad-Splitting auf Nicht-Windows-Systemen
  - POSIX-Pfad-Splitting und Fallbacks für leere Configwerte
  - `AppSettings.remember_file(...)` mit Backslash-Pfaden
  - alte Desktop-Notiz-Transparenzsemantik
  - Fensterzustandsnormalisierung

## Nicht visuell geprüft

In dieser Umgebung ist keine Qt-Bindung installiert. Deshalb konnte das Hauptfenster nicht interaktiv geöffnet werden. Die headless Validierung, Import-/Datenmodelltests, Legacy-Pfadtests, Desktop-Notiz-Hilfstests, RTF-/Config-/Autostarttests und statischen UI-Quellprüfungen laufen durch. Eine lokale Sichtprüfung mit `PySide6>=6.6,<7` oder `PyQt6>=6.6,<7` bleibt sinnvoll.
