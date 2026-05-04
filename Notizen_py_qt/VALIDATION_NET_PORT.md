# Validierung Notizen Python/Qt Port 0.10.18

## Ergebnis

Der Stand 0.10.18 wurde im Arbeitsbaum validiert. Danach wurde das ZIP neu gebaut, entpackt und erneut geprüft. Eine echte GNOME-/Qt-Oberfläche konnte in dieser Umgebung weiterhin nicht visuell gestartet werden, weil keine echte GNOME-Sitzung mit installierter Qt-Bindung verfügbar ist. Der sichtbare Startpfad wurde in dieser Runde bewusst nicht verändert.

## Durchgeführte Prüfungen

```text
pytest: 180 passed, 3 skipped
compileall: OK
bash -n scripts/*.sh *.sh: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt-Import: OK
API probe: OK, Version 0.10.18
AppDir script smoke: OK
ZIP permission check: OK
package recheck via unzip: OK
```

## Neue Tests in 0.10.18

`tests/test_system_integration_1018.py` prüft:

- `build_windows_module_open_command(...)` mit sichtbar-first Flags und quoted `"%1"`,
- `build_windows_script_open_command(...)`,
- das alte `.alx`/`notizenfile`-Registry-Mapping unter `Software\Classes`,
- stabile Vorschauzeilen für Registry-Installationslogs,
- Linux-Desktop-Exec-Zeile mit `NOTIZEN_KEEP_DISPLAY=1`, `--show`, `--no-tray`, `--reset-window`,
- Vorhandensein der neuen Windows-/Linux-Installationshilfen.

`tests/test_feedback_help_1018.py` prüft:

- .NET-`DateTime.Today.Ticks`-Berechnung,
- alte Feedback-Mindestlänge,
- alte Tagesdrossel über `x.y`/`x.z`,
- lokale UTF-16-gzip-Feedbackdatei,
- Config-Roundtrip der Feedback-Zähler inklusive unbekanntem Zusatzattribut.

`tests/test_ftp_integration_1018.py` prüft:

- prozentkodierte FTP-URLs,
- passwortfreie Anzeige-URL,
- FTP-Download über Fake-FTP mit `cwd` und `RETR`,
- FTP-Upload über Fake-FTP mit `STOR`,
- passiven/aktiven Modus über `set_pasv`.

## Einschränkung

Die neuen Windows-Registry- und AppDir-Hilfen wurden in dieser Linux-Umgebung nicht auf einem echten Windows-Desktop beziehungsweise als fertiges AppImage visuell ausgeführt. Ihre Kernlogik und Skript-Syntax sind testbar abgesichert. Der alte FTP-Live-Server-Test bleibt weiterhin offen; 0.10.18 macht die FTP-Logik aber erstmals ohne echten Server testbar.
