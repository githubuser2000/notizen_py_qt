# Notizen.NET → Python/Qt Transpilationsbericht 0.10.19

## Fokus dieser Runde

Diese Runde prüfte gezielt zwei vom Nutzer gemeldete Lücken:

1. Desktop-Haftnotizen fehlte die Auto-Resize-Logik aus `desknote.vb`.
2. Der GNOME-Menüeintrag startete nicht sichtbar, obwohl `gio launch` auf der `.desktop`-Datei funktionierte.

## Aus dem VB.NET-Original nachgezogen

### `desknote.vb`: `set_clientsizes()` / Scrollbar-Autosize

Im Original besteht die Größenkorrektur aus drei Schritten:

- `set_clientsizes_a(10)`: Form diagonal verkleinern, bis der RichTextBox-Clientbereich knapp nicht mehr reicht oder die 111px-Höhengrenze erreicht wird.
- `set_clientsizes_b(10)`: Form diagonal vergrößern, solange Scrollbar-/Clientbereichsdifferenzen bestehen und die Arbeitsfläche noch Platz bietet.
- `set_clientsizes_c(10)`: Danach Breite separat vergrößern, um RichTextBox-Wrapping/Vertikal-Overflow abzufangen.

Diese Logik ist jetzt in `DesktopNoteWindow` und `desktop_note_legacy.py` portiert:

- Konstanten: 10px Schrittweite, 6px Scrollbar-Toleranz, 11px Arbeitsbereichsrand, 111px Mindesthöhe.
- Trigger: RichText-/Dokumentänderungen, vertikale und horizontale Scrollbereichsänderungen, `show2()` nach dem Erzeugen/Anzeigen.
- Schutz: Benutzer-Resize setzt wieder `scroll_manual`, damit manuelle Größen nicht sofort überschrieben werden.
- Speicherung: Kompakte Desktop-Haftnotiz-Geometrie wird beim Speichern wieder in das logische WinForms-Rechteck zurückgerechnet.

## GNOME-Menüstart

Die Startreparatur adressiert zwei Fehlerquellen:

- eine alte Kopie `Notizen PyQt.desktop` in `~/.local/share/applications`, die GNOME weiterhin anzeigen kann,
- relative beziehungsweise aus `%k` abgeleitete Starterpfade, die im GNOME-Menü fragiler sind als beim direkten `gio launch`.

Geändert wurde:

- `scripts/install_linux_launcher.sh` schreibt nur noch den kanonischen `notizen-py-qt.desktop`-Starter,
- der Starter verwendet einen absoluten `notizen-starten.sh`-Pfad,
- `NOTIZEN_KEEP_DISPLAY=1`, `NOTIZEN_MENU_LAUNCH=1`, `NOTIZEN_FORCE_VISIBLE=1` und `NOTIZEN_RESET_WINDOW=1` werden gesetzt,
- stale `~/.local/share/applications/Notizen PyQt.desktop` wird entfernt,
- Desktop-/MIME-/Icon-Caches werden aktualisiert,
- `NoDisplay=false`, `DBusActivatable=false` und `StartupWMClass=notizen-py-qt` sind gesetzt,
- AppDir-Desktop-Dateien starten jetzt über `Exec=AppRun %f`.

## Was nach dem Audit noch offen bleibt

Nicht mehr offen ist die vom Nutzer genannte Auto-Resize-Lücke der Desktop-Haftnotizen. Weiterhin nicht vollständig historisch identisch sind:

- pixelgenaue WinForms-Paint-Details der Haftnotiz-Ränder, Ecken und dekorativen Linien,
- vollständige Microsoft-RichTextBox-/OLE-Semantik jenseits der bereits portierten RTF-Brücke, Bild-/Hyperlink-/Listenbehandlung und sichtbaren Objekt-Platzhalter,
- die alte FTP-Dialog-Oberfläche in allen UI-Details; die sichere/testbare FTP-Kompatibilitätslogik ist vorhanden,
- historische Windows-/ClickOnce-Installationsdetails; die aktuelle Version bietet explizite Linux- und Windows-Installationsskripte.

## Geänderte Dateien

- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/desktop_note_legacy.py`
- `src/notizen_py_qt/system_integration.py`
- `src/notizen_py_qt/__init__.py`
- `Notizen PyQt.desktop`
- `scripts/install_linux_launcher.sh`
- `scripts/uninstall_linux_launcher.sh`
- `scripts/build_linux_appdir.sh`
- `README.md`
- `docs/MAPPING.md`
- `tests/test_desktop_note_autoresize_1019.py`
- `tests/test_system_integration_1018.py`
- `pyproject.toml`

