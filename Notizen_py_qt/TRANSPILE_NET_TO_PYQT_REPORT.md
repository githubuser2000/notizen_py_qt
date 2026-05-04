# Weitertranspilierung Notizen.NET → Python/Qt 0.10.18

## Schwerpunkt

Diese Runde arbeitet die nächsten Punkte aus der großen Rest-Transpilierungsuntersuchung ab: Systemintegration, sichere Hilfe-/Feedback-Parität und FTP-Härtung. Der sichtbare GNOME-Startpfad wurde bewusst **nicht** umgebaut. Er bleibt wie in den sichtbaren Zwischenständen:

```text
--show --reset-window --no-tray
QT_QPA_PLATFORM=wayland;xcb
kein pauschales Löschen von DISPLAY
```

## Windows-`.alx`-Dateizuordnung aus `Notizen.Designer.vb`

Das alte Notizen.NET schrieb beim Start Registry-Werte unter `HKEY_CLASSES_ROOT`, um `.alx`-Dateien mit `Notizen.exe "%1"` zu öffnen. Diese Idee ist jetzt portiert, aber sicherer:

- keine automatische Registry-Änderung beim App-Start,
- keine Administratorrechte nötig,
- per Benutzerinstallation unter `HKCU\Software\Classes`,
- testbare reine Python-Abbildung in `system_integration.py`,
- explizites Installationsskript für Windows.

Neu:

```text
src/notizen_py_qt/system_integration.py
scripts/install_windows_file_association.ps1
Notizen starten.cmd
notizen-starten.ps1
```

Die testbare Registry-Struktur entspricht dem alten Code:

```text
.alx → Notizenfile
.alx\OpenWithList\Notizen.exe
.alx\OpenWithProgIds\notizenfile
notizenfile\Shell = Open
notizenfile\Shell\Open\Command = ... "%1"
notizenfile\DefaultIcon = ...
```

## Linux-/GNOME-Systemintegration

Der bestehende GNOME-Starter bleibt sichtbar-first und ohne Tray. Ergänzt wurden zwei praktische Werkzeuge:

```bash
scripts/uninstall_linux_launcher.sh
scripts/build_linux_appdir.sh
```

`uninstall_linux_launcher.sh` entfernt Menüeintrag, MIME-Datei und Icon wieder aus dem Benutzerprofil. `build_linux_appdir.sh` erzeugt eine portable AppDir-Struktur mit `AppRun` als Vorstufe für ein mögliches AppImage. Das ist noch kein voll signiertes/veröffentlichtes AppImage, aber eine belastbare Zwischenstufe für die Paketierungs-Roadmap.

## Sicherer Hilfe-/Feedback-Dialog aus `info_help_and_feedback.vb`

Das alte Formular enthielt:

- Produktname,
- Autor,
- Weblink,
- Mailadresse,
- Hilfe-/Beschreibungstext,
- Feedback-Feld,
- Senden-Button.

Der PyQt-Port bildet diesen Dialog jetzt semantisch nach. Der alte hartkodierte FTP-Upload zu `notiza.de` wird aber **nicht** reaktiviert. Stattdessen wird Feedback lokal als gzip-Datei gespeichert:

```text
~/.local/state/notizen-py-qt/feedback/feedback.YYYY-MM-DD-HH-MM-SS.txt.gz
```

Der Payload bleibt wie im alten Code UTF-16-kodiert. Damit ist das alte Verhalten nachvollziehbar, ohne private Rückmeldungen ungefragt über Legacy-FTP-Zugangsdaten zu versenden.

## Feedback-Zähler `x.y`/`x.z`

Die alte Config nutzte im Element `x` neben `a` für Autosave auch:

```text
x.y = DateTime.Today.Ticks
x.z = Tageszähler
```

Diese Werte werden jetzt gelesen, geschrieben und für die lokale Feedback-Drossel genutzt. Vorher wurden sie beim Speichern faktisch auf `0` zurückgesetzt.

Neu:

```text
src/notizen_py_qt/feedback.py
legacy_feedback_decision(...)
legacy_feedback_next_state(...)
write_local_feedback_archive(...)
```

## FTP-Härtung

`ftp_sync.py` wurde robuster und besser testbar:

- prozentkodierte Benutzernamen, Passwörter und Pfade werden dekodiert,
- Anzeige-URLs zeigen kein Passwort,
- passiver/aktiver FTP-Modus ist im Zielobjekt konfigurierbar,
- Upload/Download können über `ftp_factory` mit einem Fake-FTP-Adapter getestet werden.

Das ersetzt noch keinen echten FTP-Server-Integrationstest, aber die Kernlogik ist jetzt ohne Live-Server prüfbar.

## Neue Tests

Neu hinzugekommen:

```text
tests/test_system_integration_1018.py
tests/test_feedback_help_1018.py
tests/test_ftp_integration_1018.py
```

Sie prüfen:

- Windows-Open-Command mit `"%1"`,
- Registry-Key-Mapping nach altem `.alx`/`notizenfile`-Schema,
- Linux-Desktop-Exec-Zeile mit sichtbarem Start,
- neue Installations-/Deinstallationsskripte,
- lokale Feedback-gzip-Dateien mit UTF-16-Payload,
- Feedback-Drossel nach altem `x.y`/`x.z`-Prinzip,
- Config-Roundtrip dieser Werte,
- FTP-URL-Dekodierung,
- Fake-FTP-Download und Upload.

## Bewusst nicht geändert

Der GNOME-/Wayland-Startpfad wurde nicht erneut verändert. Die Nutzeranforderung war, das sichtbar gewesene Startverhalten beizubehalten. 0.10.18 konzentriert sich deshalb auf Systemintegration, Hilfe/Feedback und FTP-Härtung.

## Validierung

Die Validierung steht in `VALIDATION_NET_PORT.md`.
