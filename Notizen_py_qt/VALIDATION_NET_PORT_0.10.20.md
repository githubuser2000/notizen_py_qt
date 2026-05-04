# Validation 0.10.20

## Ausgeführt

```bash
python3 -m compileall -q src notizen_py_qt scripts
bash -n notizen-starten.sh "Notizen starten.sh" notizen-starten-venv.sh scripts/install_linux_launcher.sh scripts/uninstall_linux_launcher.sh scripts/build_linux_appdir.sh
pytest -vv
```

Ergebnis aus dem vollständigen Testlauf:

```text
203 passed, 3 skipped in 45.30s
```

Zusätzlich wurde der Linux-Installer mit temporärem `HOME`, `XDG_DATA_HOME` und `XDG_STATE_HOME` ausgeführt. Der erzeugte Menüeintrag enthielt:

```desktop
Exec=env NOTIZEN_RESET_WINDOW=1 python3 -m notizen_py_qt --show --no-tray --reset-window %f
Path=/mnt/data/work_notizen/Notizen_py_qt
```

Die stale Datei `Notizen PyQt.desktop` im temporären Applications-Verzeichnis war anschließend nicht vorhanden.

## Neue/erweiterte Regressionstests

- `tests/test_alx_tree_expansion_1020.py`
  - prüft verschachtelten `isexpanded`-Roundtrip,
  - prüft XML-Ausgabe der `isexpanded`-Attribute,
  - prüft per Source-Regression, dass Qt-Expansion erst nach `addTopLevelItem(...)` gesetzt wird.
- `tests/test_rtf_fidelity_1017.py`
  - erweitert um Hoch-/Tiefstellung,
  - CSS/HTML-nach-RTF für `<sup>/<sub>`,
  - Absatz-Ausrichtung und Einzüge,
  - kombinierten RTF-Export dieser neuen Formatfelder.
- Launcher-Tests wurden auf den direkten GNOME-Exec angepasst.

## Einschränkung

Ein echter visueller Klick im GNOME-Menü konnte in der Containerumgebung nicht simuliert werden. Der installierte `.desktop`-Inhalt und der Installerlauf wurden strukturell geprüft.
