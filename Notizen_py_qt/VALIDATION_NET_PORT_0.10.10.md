# Validierungsbericht Notizen.NET → Python/Qt 0.10.10

## Umfang

Geprüft wurde der weitertranspilierte Stand 0.10.10 aus 0.10.9. Schwerpunkt war der GNOME-Start ohne sichtbares Fenster: sichtbarer Direktstarter, Reset alter Fensterpositionen, genauere Portierung der alten `xml_kram.on_load()`-Bedingung und Diagnoseprotokolle.

## Befehle

```text
python3 -m compileall -q src tests
pytest -q
bash -n notizen-starten.sh "Notizen starten.sh" notizen-diagnose.sh scripts/*.sh
scripts/check_no_slint_strict.sh
python3 scripts/probe_python_qt_runtime.py --skip-qt
PYTHONPATH=src python3 -c "import notizen_py_qt; print(notizen_py_qt.__version__)"
python3 scripts/package_zip.py . /mnt/data/notizenPyQt_0.10.10.zip --root-name Notizen_py_qt
```

## Ergebnis

```text
pytest: 96 passed, 2 skipped
compileall: OK
bash -n scripts/*.sh *.sh: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt-Import: OK
API probe: OK, Version 0.10.10
ZIP permission check: OK
package recheck via unzip: 96 passed, 2 skipped
```

ZIP-Rechte im frisch gepackten Archiv:

```text
Verzeichnisse: 755
Shell-Starter: 755
.desktop-Starter: 755
aktive Python-Hilfsskripte direkt unter scripts/: 755
archivierte Legacy-Migrationsskripte: 644
normale Dateien: 644
keine __pycache__/.pytest_cache/.pyc im Archiv
```

## Neue Tests in 0.10.10

- `test_legacy_default_minimized_state_is_not_restorable_at_zero_zero`
- `test_force_visible_and_reset_override_minimized_requests`
- `test_window_geometry_is_clamped_back_into_current_work_area`
- `test_start_scripts_force_visible_reset_and_have_diagnostics`
- `test_desktop_installers_pass_reset_window`
- `test_visible_start_shell_scripts_are_syntax_valid`

## Nicht visuell geprüft

Die Umgebung enthält keine installierte Qt-Bindung und keine echte GNOME-Sitzung. Deshalb wurde der GUI-Startpfad nicht visuell getestet. Der Runtime-Probe ohne Qt muss weiterhin nur den Installationshinweis liefern.

## Lokaler GNOME-Test

```bash
python3 -m pip install --user "PySide6>=6.6,<7"
unzip notizenPyQt_0.10.10.zip
cd Notizen_py_qt
./Notizen\ starten.sh
```

Falls kein Fenster erscheint:

```bash
./notizen-diagnose.sh
cat ~/.local/state/notizen-py-qt/startup.log
cat ~/.local/state/notizen-py-qt/diagnose.log
```
