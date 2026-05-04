# Validation 0.10.21

## Ausgeführt

```bash
python3 -m compileall -q src notizen_py_qt scripts
bash -n notizen-starten.sh "Notizen starten.sh" notizen-starten-venv.sh scripts/install_linux_launcher.sh scripts/uninstall_linux_launcher.sh scripts/build_linux_appdir.sh
pytest -q --ignore=tests/test_v6_continue.py
pytest -q tests/test_v6_continue.py
```

Ergebnis:

```text
208 passed, 3 skipped in 10.65s
3 passed in 21.91s
```

Das entspricht den 214 gesammelten Tests der Suite, in zwei Läufen ausgeführt. Der komplette Ein-Prozess-Lauf wurde in der Containerumgebung durch das Tool-Timeout abgebrochen, nachdem keine Fehlschläge mehr angezeigt wurden; deshalb ist der reproduzierbare Split-Lauf hier dokumentiert.

## Installer-Probe

Zusätzlich wurde der Linux-Installer mit temporärem `HOME` und `XDG_DATA_HOME` ausgeführt. Der erzeugte Menüeintrag enthielt:

```desktop
Exec=env NOTIZEN_RESET_WINDOW=1 RESOURCE_NAME=notizen-py-qt python3 -m notizen_py_qt --show --no-tray --reset-window %f
Path=/mnt/data/work_notizen2/Notizen_py_qt
Icon=notizen-py-qt
StartupWMClass=notizen-py-qt
```

Die stale Datei `Notizen PyQt.desktop` im temporären Applications-Verzeichnis wurde entfernt beziehungsweise war danach nicht vorhanden.

## Neue/erweiterte Regressionstests

- `tests/test_runtime_icon_launcher_1021.py`: Runtime-App-ID, `setDesktopFileName`, `RESOURCE_NAME`, WindowIcon und direkter GNOME-Exec mit Resource-Name.
- `tests/test_rtf_fidelity_1021.py`: Absatz-HTML auf `<p>`, `\sb`/`\sa`/`\sl`, `\up`/`\dn`, Überschriften und Qt-Blockeinzug.
- `tests/test_alx_roundtrip_1021.py`: Kern-Roundtrip für RTF-Rohinhalt, `isexpanded`, Farben, Desktop-Haftnotiz-Zustand und unbekannte Legacy-Attribute.

## Einschränkung

Ein echter visueller Klick im GNOME-Menü und die tatsächliche Taskleisten-Darstellung konnten im Container nicht simuliert werden. Geprüft wurden der installierte `.desktop`-Inhalt, die Qt-Laufzeitidentität im Source, Shell-Syntax und Regressionstests.
