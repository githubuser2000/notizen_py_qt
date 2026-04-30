# Qt 6.11 no-legacy-UI migration kit v6

v6 setzt dort fort, wo v5 nach der `pyproject.toml`-Reparatur aufgehört hat. Es ist für dein Python-Projekt mit generierter QML-Oberfläche gedacht und räumt die nächsten typischen Bruchstellen auf: QML-Ladefähigkeit, PySide6-Laufzeit, alte Paketnamen, kopierte Ressourcen und optional den aus Backups wiederhergestellten Python-Controller.

## Empfohlener Fortsetzungslauf

Aus dem entpackten Kit-Verzeichnis:

```bash
python3 scripts/continue_qt611_transpile.py .. --apply
bash scripts/check_no_slint.sh ..
bash scripts/build_python_qt.sh ..
```

`build_python_qt.sh` ruft den Fortsetzungslauf selbst erneut auf, repariert `pyproject.toml`, installiert das Paket editierbar und startet einen Qt/QML-Smoke-Test mit Offscreen-/Software-Rendering:

```bash
PYTHON=python3 bash scripts/build_python_qt.sh ..
```

Wenn dein System mit Python 3.14 Probleme beim PySide6-Wheel hat, nimm gezielt einen vorhandenen stabileren Interpreter:

```bash
PYTHON=python3.13 bash scripts/build_python_qt.sh ..
# oder
PYTHON=python3.12 bash scripts/build_python_qt.sh ..
```

## Neu in v6

- `scripts/continue_qt611_transpile.py`: One-shot-Fortsetzung, die Reparatur, Paketmigration, QML-Härtung, Runtime-Härtung, Analyse und Restscanner in sinnvoller Reihenfolge ausführt.
- `scripts/fix_qml_for_pyside.py`: ergänzt fehlende `QtQuick`/`QtQuick.Controls`/`QtQuick.Layouts`/`QtQml`-Imports, erzeugt `qmldir`, normalisiert generierte Dateinamen und kopiert QML/JS in `src/notizen_py_qt/ui/`.
- `scripts/harden_python_qt_runtime.py`: erzeugt `qt_runtime.py`, `qt_backend.py`, `qt_compat.py` und einen robusteren `app.py`-Runner.
- `scripts/restore_qt_controller_from_backup.py`: versucht, den alten umfangreichen Python-Controller aus `.qt611_no_slint_backup_v4/` zu holen und mechanisch auf Qt-Kompatibilität zu portieren, statt dauerhaft nur beim Minimal-Runner zu bleiben.
- `scripts/probe_python_qt_runtime.py`: prüft `pyproject.toml`, Paketimport, PySide6/Qt-Version, QML-Dateien und den `--smoke-test`.
- `scripts/build_python_qt.sh`: nutzt jetzt `PYTHON=${PYTHON:-python3}`, Software-Rendering-Fallbacks und den Runtime-Probe.

## Wichtige Einzelschritte

Nur QML nachhärten:

```bash
python3 scripts/fix_qml_for_pyside.py .. --apply
python3 scripts/qml_sanity_check.py ..
```

Nur Python/Qt-Runtime nachschreiben:

```bash
python3 scripts/harden_python_qt_runtime.py .. --apply
```

Nur den alten Controller aus Backups zurückholen:

```bash
python3 scripts/restore_qt_controller_from_backup.py .. --apply
```

Nur den Runtime-Probe ausführen:

```bash
python3 scripts/probe_python_qt_runtime.py ..
```

## Erwartete Projektstruktur nach v6

```text
pyproject.toml
qml/Main.qml
qml/qmldir
src/notizen_py_qt/
  __init__.py
  __main__.py
  app.py
  qt_backend.py
  qt_compat.py
  qt_runtime.py
  ui/
    Main.qml
    qmldir
```

Backups bleiben bewusst erhalten, werden vom Scanner aber ignoriert:

```text
.qt611_pyproject_repair_backup/
.qt611_qml_hardening_backup/
.qt611_runtime_backup/
.qt611_controller_restore_backup/
.qt611_no_slint_backup_v4/
legacy_slint/
legacy_build_metadata/
```

## Kompletter Ablauf bei frischem Projektstand

```bash
python3 scripts/migrate_remove_slint_to_qt611.py .. --apply --rust-cxx-qt --overwrite-qml
python3 scripts/finish_python_qt_migration.py .. --apply
python3 scripts/repair_pyproject_qt611.py .. --apply
python3 scripts/continue_qt611_transpile.py .. --apply
bash scripts/check_no_slint.sh ..
bash scripts/build_python_qt.sh ..
```

## Validierung dieses Kits

```text
python3 -m py_compile scripts/*.py: OK
bash -n scripts/*.sh: OK
pytest tests: 8 passed
synthetische v6-Fortsetzungsmigration: OK
synthetische Controller-Restore-Migration: OK
```

Der echte Build deines Repositories wurde hier nicht ausgeführt, weil dein lokaler Projektbaum und deine lokale PySide6/Qt-Installation nicht in diesem Workspace liegen. Das Kit ist dafür gemacht, genau auf deinem Pfad `Notizen_Py_Slint` weiterzulaufen.
