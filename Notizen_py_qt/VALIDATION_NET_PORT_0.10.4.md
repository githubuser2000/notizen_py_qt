# Validierungsbericht Notizen.NET → Python/Qt 0.10.4

## Prüfumfang

Der Stand 0.10.4 wurde aus dem entpackten Archiv 0.10.3 weitergeführt. Geprüft wurden die neue RTF-Bild-Parität beim Zusammenfassen, die Linux/GNOME-Dateizuordnung und die bisherigen Regressionstests.

Die GUI konnte in dieser Umgebung weiterhin nicht visuell gestartet werden, weil keine Qt-Bindung installiert ist. Die Qt-unabhängige Kernlogik und die Starter-/Packaging-Logik wurden geprüft.

## Ausgeführte Prüfungen

```text
PYTHONPATH=src pytest -q
python -m compileall -q src tests scripts
bash -n scripts/*.sh *.sh
bash scripts/check_no_slint_strict.sh
PYTHONPATH=src python -c "import notizen_py_qt; print(notizen_py_qt.__version__)"
python scripts/package_zip.py . /mnt/data/notizenPyQt_0.10.4.zip --root-name Notizen_py_qt
```

## Ergebnis

```text
pytest: 65 passed, 2 skipped
compileall: OK
bash -n scripts/*.sh *.sh: OK
check_no_slint_strict.sh: OK
API probe: OK, Version 0.10.4
ZIP permission check: OK
```

## Neue Tests in 0.10.4

`tests/test_rtf_images_mime_104.py` prüft:

- `rtf_to_content_parts(...)` behält die Reihenfolge Text → Bild → Text.
- `tree_to_rtf(...)` erhält eingebettete PNG-Bilder als `\pict\pngblip`.
- `create_unified_note(...)` behält eingebettete Bilder in der zusammengefassten Notiz.
- `scripts/install_linux_launcher.sh` registriert `application/x-notizen-alx` und setzt `xdg-mime default`.
- Der Desktop-Starter führt weiterhin `MimeType=application/x-notizen-alx;`.

## ZIP-Rechte

Das Archiv wird weiter mit `scripts/package_zip.py` erstellt. Geprüfte Regeln:

```text
Verzeichnisse: 755
Shell-Skripte: 755
Python-Skripte in `scripts`-Pfaden: 755
.desktop-Dateien: 755
normale Dateien: 644
```

## Offene visuelle Prüfung

Lokal sollte zusätzlich geprüft werden:

```bash
python3 -m pip install --user "PySide6>=6.6,<7"
unzip notizenPyQt_0.10.4.zip
cd Notizen_py_qt
./Notizen\ starten.sh
./scripts/install_linux_launcher.sh
```

Danach sollte eine `.alx`-Datei im GNOME-Dateimanager dem Notizen-Starter zugeordnet werden beziehungsweise über „Öffnen mit“ Notizen PyQt anbieten.
