# Transpilationsbericht Notizen.NET → Python/Qt 0.10.2

Datum: 2026-05-02

## Ziel dieser Runde

Der vorhandene Python/Qt-Port 0.10.1 wurde aufgrund der aktuellen Rückmeldung weitergeführt: Das ZIP-Archiv musste portable Unix-Rechte bekommen, und der minimierte Start über Tray durfte unter GNOME nicht mehr zu einer unsichtbaren, praktisch unerreichbaren Anwendung führen. Der aktive Port bleibt Python/Qt mit PySide6/PyQt6-Kompatibilität; frühere Slint-/QML-Zwischenschritte bleiben historisches Material.

## Ausgewertete Ausgangslage

- Original: `Notizen.NET/Notizen/*.vb`, erneut besonders `Notizen.Designer.vb`, `xml_kram.vb`, `ApplicationEvents.vb` und die Tray-/Minimize-Logik.
- Zielprojekt: `src/notizen_py_qt/` mit Qt-Oberfläche, Einstellungen, Startparameterlogik und neuen Tray-Hilfen.
- Vorheriger Stand: 0.10.1 mit ALX, Baum/Editor, Suche, Export, Desktop-Notizen, FTP, Wecker, Statistik, Config-/Autostart-Parität, Backup-Verwaltung, Legacy-Pfaden und Fensterzustandsnormalisierung.

## Umgesetzte Änderungen in 0.10.2

### 1. ZIP-Berechtigungen korrigiert

Das alte Archiv enthielt mehrere Verzeichniseinträge mit `drw-------`. Solche ZIP-Metadaten sind für portable Quellarchive falsch, weil Verzeichnisse ohne Ausführungs-/Suchrecht auf Unix-Systemen nicht sauber betreten werden können. 0.10.2 paketiert nun mit klarer Rechte-Policy:

- Verzeichnisse: `755`
- Shell-/Python-Build-Skripte: `755`
- normale Dateien: `644`

Dafür wurde `scripts/package_zip.py` ergänzt. Die neue Verpackungshilfe setzt `ZipInfo.create_system = 3` und schreibt die Unix-Rechte explizit in `external_attr`, statt sich auf zufällige Rechtewerte eines vorherigen Extraktionslaufs zu verlassen.

### 2. GNOME-Tray-Schutz ergänzt

Das alte Notizen.NET konnte unter Windows zuverlässig minimiert mit NotifyIcon starten, weil die Windows-Notification-Area vorhanden war. Unter GNOME ist das nicht gleichwertig: Ohne AppIndicator/KStatusNotifier-/Legacy-Tray-Erweiterung kann ein verstecktes Qt-Trayfenster für Nutzer unsichtbar und unerreichbar werden.

Neu ist `src/notizen_py_qt/tray_support.py` mit testbaren Hilfen:

- `is_gnome_session(...)`
- `parse_gnome_extension_list(...)`
- `detect_enabled_gnome_extensions(...)`
- `has_known_gnome_tray_extension(...)`
- `decide_startup_tray_visibility(...)`
- `gnome_tray_install_hint()`

Beim minimierten Start entscheidet der Port jetzt:

- Wenn kein Qt-Tray existiert: Hauptfenster sichtbar starten.
- Wenn „Minimiert in Taskleiste zeigen“ aktiv ist: nicht ins Tray verstecken.
- Wenn GNOME erkannt wird und keine bekannte Tray-Erweiterung aktiv ist: Hauptfenster sichtbar starten.
- Wenn eine bekannte GNOME-Tray-Erweiterung erkannt wird: altes Tray-Verhalten erlauben.
- Wenn `--force-tray-start` gesetzt ist: altes verstecktes Tray-Verhalten erzwingen.

### 3. Neue Startoptionen

- `--no-tray`: Trayicon deaktivieren und nie unsichtbar starten.
- `--force-tray-start`: auch unter GNOME verborgen ins Tray starten.

Damit kann der Nutzer die sichere Voreinstellung umgehen, wenn die eigene GNOME-Umgebung tatsächlich ein funktionierendes Tray bereitstellt.

### 4. Neue Einstellung für GNOME-Sicherheit

`AppSettings` enthält jetzt `gnome_safe_tray_start`. Die Einstellung wird als `<tray gnome-safe-start="yes|no" />` gespeichert und im Einstellungsdialog als „GNOME ohne Tray nicht verstecken“ angeboten.

### 5. Kleine Bereinigung im Desktop-Notiz-Fenster

In `DesktopNoteWindow` wurde eine doppelt verschachtelte Initialisierungsprüfung für `node.desktop_note is None` bereinigt. Das Verhalten bleibt gleich, der Code ist aber wieder sauberer.

### 6. Paket- und API-Stand aktualisiert

- Paketversion: `0.10.2`
- Neue API-Exports in `notizen_py_qt.__init__`:
  - `decide_startup_tray_visibility`
  - `is_gnome_session`

## Neue Tests

Neu ergänzt:

- `tests/test_tray_permissions_102.py`
  - GNOME-Sitzungserkennung
  - Erkennung bekannter AppIndicator/KStatusNotifier-Erweiterungen
  - sichere Entscheidung gegen versteckten Tray-Start unter GNOME ohne Erweiterung
  - erzwungener Tray-Start
  - Roundtrip von `<tray gnome-safe-start="..." />`
  - ZIP-Rechte-Policy für Verzeichnisse, Skripte und normale Dateien

## Nicht visuell geprüft

In dieser Umgebung ist keine Qt-Bindung installiert. Deshalb konnte das Hauptfenster nicht interaktiv geöffnet werden. Die headless Validierung, Import-/Datenmodelltests, Legacy-Pfadtests, Tray-Entscheidungstests, Paketierungslogik und statischen Prüfungen laufen durch. Eine lokale Sichtprüfung mit `PySide6>=6.6,<7` oder `PyQt6>=6.6,<7` bleibt sinnvoll.
