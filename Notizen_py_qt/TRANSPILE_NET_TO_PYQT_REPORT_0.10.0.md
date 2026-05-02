# Transpilationsbericht Notizen.NET → Python/Qt 0.10.0

Datum: 2026-05-01

## Ziel dieser Runde

Der vorhandene Python/Qt-Port 0.9.9 wurde erneut gegen das alte VB.NET/WinForms-Projekt geprüft und semantisch weitergeführt. Der Projektkontext aus den bisherigen Notizen-Chats bleibt übernommen: Die frühere Slint-Richtung ist nur noch historisches Material; der aktive Port ist Python/Qt mit PySide6/PyQt6-Kompatibilität.

## Ausgewertete Ausgangslage

- Original: `Notizen.NET/Notizen/*.vb`, in dieser Runde besonders `xml_kram.vb`, `einstellungen.vb`, `Notizen.Designer.vb` und RichTextBox-nahe RTF-Fälle.
- Zielprojekt: `src/notizen_py_qt/` mit getrennten Modulen für Datenmodell, ALX-IO, Einstellungen, Startparameter, RTF-Brücke und Qt-Oberfläche.
- Vorheriger Stand: 0.9.9 mit ALX, Baum/Editor, Suche, Export, Desktop-Notizen, FTP, Wecker, Statistik, Config-Import, Recent-Dateien, Baum-Zusammenfassung und präzisierter Backup-Verwaltung.

## Umgesetzte Änderungen in 0.10.0

### 1. Legacy-Configdetails aus `xml_kram.vb` weiter portiert

Die alte Standard-Config legt nicht nur Datei-, Sprach- und Fensterdaten ab, sondern enthält auch verschachtelte Start-/Öffnen-Informationen und Toolbar-Positionen. 0.10.0 übernimmt diese Details:

- `open/once-opened` mit `file` und `timestamp` wird gelesen.
- `open/once-opened` wird beim Speichern wieder geschrieben.
- `tool-stripes/haupt`, `elements`, `font` und `cutpastecopy` werden mit `x`/`y` gelesen.
- Die Toolbar-Positionen bleiben in `AppSettings.toolstrip_positions` erhalten und werden in die Config zurückgeschrieben.
- Neue Standard-Config startet mit `autosave_seconds = 60`, entsprechend dem alten `<x a="60">`-Default.

### 2. Autosave-Regel aus `einstellungen.vb` vereinheitlicht

Im alten Einstellungsdialog deaktiviert `0` den Autosave; aktivierte Werte unter fünf Sekunden werden auf fünf Sekunden angehoben. 0.10.0 macht daraus eine testbare Kernfunktion:

- `normalize_autosave_seconds(value)`
- Anwendung beim Lesen alter Configs
- Anwendung beim Speichern der aktuellen Config
- Anwendung im Qt-Einstellungsdialog

Damit kann ein versehentlicher extrem kurzer Autosave-Intervall nicht mehr in die Config geschrieben werden.

### 3. Autostart-Verhalten aus `xml_kram.setshortcut` portiert

Das alte Notizen.NET erzeugte unter Windows eine Startup-Verknüpfung und nutzte dafür bevorzugt die jüngste zuletzt geöffnete Datei. Der Port bildet diese Logik jetzt ohne COM-Abhängigkeit ab:

- `legacy_autostart_target_file(...)` wählt die jüngste brauchbare Recent-Datei.
- `legacy_autostart_arguments(...)` setzt optional `-min` vor die Datei.
- `build_autostart_command(...)` baut eine Windows-kompatibel quotierte `python -m notizen_py_qt`-Kommandozeile.
- `apply_windows_autostart_script(...)` schreibt oder entfernt unter Windows eine kleine `Notizen PyQt.cmd` im Startup-Ordner.
- Der Einstellungsdialog ruft diese Umsetzung nach dem Speichern der Autostart-Option auf.

Auf Nicht-Windows-Systemen bleibt die Funktion ohne expliziten Test-Startup-Ordner ein sicherer No-op.

### 4. RichTextBox-Tabellen lesbarer gemacht

Alte RichTextBox-Inhalte können RTF-Tabellensteuerwörter enthalten. Die Python/Qt-Brücke rendert weiterhin keine vollständigen Tabellenlayouts, aber 0.10.0 erhält die Textgrenzen:

- `\cell` und `\nestcell` werden als Tabulator behandelt.
- `\row` wird als Zeilenumbruch behandelt.
- Suche, Statistik und Text-/HTML-/RTF-Exports schieben alte Tabellenzellen dadurch nicht mehr zusammen.

### 5. Paket- und API-Stand aktualisiert

- Paketversion: `0.10.0`
- Neue API-Exports in `notizen_py_qt.__init__`:
  - `normalize_autosave_seconds`
  - `build_autostart_command`
  - `legacy_autostart_arguments`

## Neue Tests

Neu ergänzt:

- `tests/test_settings_startup_rtf_100.py`
  - Legacy-Config-Roundtrip für `open/once-opened`
  - Legacy-Config-Roundtrip für `tool-stripes`
  - Autosave-Minimum und Standardwert
  - Autostart-Argumentlogik und Startup-Skript-Erzeugung
  - RTF-Tabellensteuerwörter `\cell`/`\row`

## Nicht visuell geprüft

In dieser Umgebung ist keine Qt-Bindung installiert. Deshalb konnte das Hauptfenster nicht interaktiv geöffnet werden. Die headless Validierung, Import-/Datenmodelltests, RTF-/Config-/Autostarttests und statischen UI-Quellprüfungen laufen durch. Eine lokale Sichtprüfung mit `PySide6>=6.6,<7` oder `PyQt6>=6.6,<7` bleibt sinnvoll.
