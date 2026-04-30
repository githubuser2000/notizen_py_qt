# Qt 6.11 continued transpilation report

Mode: APPLY
Input root: `/home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint`
Detected project root: `/home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint`

## Step results

### recover parent-folder mis-run

Return code: `0`

```text
Mode: APPLY
Outer root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint
Detected project root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint
- quarantine migration backup/report directory: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_controller_restore_backup -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/.qt611_controller_restore_backup
- quarantine migration backup/report directory: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_no_slint_backup_v4 -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/.qt611_no_slint_backup_v4
- quarantine migration backup/report directory: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/.qt611_qml_hardening_backup
- quarantine migration backup/report directory: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_runtime_backup -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/.qt611_runtime_backup
- quarantine stale parent-folder migration report: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_CONTINUE_TRANSPILE_REPORT.md -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/QT611_CONTINUE_TRANSPILE_REPORT.md
- quarantine stale parent-folder migration report: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_CONTROLLER_RESTORE.md -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/QT611_CONTROLLER_RESTORE.md
- quarantine stale parent-folder migration report: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_MIGRATION_STATUS.md -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/QT611_MIGRATION_STATUS.md
- quarantine stale parent-folder migration report: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_PYTHON_QT_MIGRATION_ACTIONS.md -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/QT611_PYTHON_QT_MIGRATION_ACTIONS.md
- quarantine stale parent-folder migration report: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_QML_HARDENING.md -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/QT611_QML_HARDENING.md
- quarantine stale parent-folder migration report: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_RUNTIME_HARDENING.md -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/QT611_RUNTIME_HARDENING.md
- quarantine migration backup/report directory: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/legacy_slint -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_misroot_quarantine/20260430-095205/legacy_slint
Wrote report: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/QT611_MISROOT_RECOVERY.md
```

### repair pyproject

Return code: `0`

```text
TOML validation after repair: valid TOML
No pyproject changes needed: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/pyproject.toml
```

### finish Python package migration

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint
Actions:
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/pyproject.toml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/QT611_MISROOT_RECOVERY.md
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/AppState.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Main.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_AppState.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/main_window_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/__init__.py
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/app.py
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/qt_backend.py
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/__main__.py
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_pypy_qt/app.py
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_pypy_qt/__main__.py
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_pypy_qt/__init__.py
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/scripts/run-gui.sh
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/scripts/check_no_slint.sh
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/scripts/check_no_slint_strict.sh
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/scripts/build_python_qt.sh
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/scripts/repair_pyproject_qt611.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/QT611_PYTHON_QT_MIGRATION_ACTIONS.md

OK: Python package names, QML strings, entry points and active source references are clean.
```

### repair pyproject again

Return code: `0`

```text
TOML validation after repair: valid TOML
No pyproject changes needed: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/pyproject.toml
```

### harden QML

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/AppState.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/Main.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/advanced_app_AppState.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/advanced_app_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/app-window_AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/main_window_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/advanced_app_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/app-window_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/AppState.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Main.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_AppState.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/main_window_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/qmldir
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/AppState.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Main.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_AppState.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/main_window_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/qmldir
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/__init__.py
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/qmldir
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/QT611_QML_HARDENING.md
```

### comment generated TODO code blocks

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint
- repair QML TODO/balance: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml
- repair QML TODO/balance: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/app-window_AppWindow.qml
```

### harden Python/Qt runtime

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/qt_runtime.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/qt_backend.py
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/qt_compat.py
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/__main__.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/app.py
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/QT611_RUNTIME_HARDENING.md
```

### restore Qt controller from backup

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/qml_runner.py
- restore source: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_runtime_backup/20260430-095205/src/notizen_py_qt/app.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/app.py
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/QT611_CONTROLLER_RESTORE.md
```

### final pyproject repair

Return code: `0`

```text
TOML validation after repair: valid TOML
No pyproject changes needed: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/pyproject.toml
```

### QML sanity check

Return code: `0`

```text
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint
Checked 23 active QML/JS file(s).
OK: active QML/JS has balanced delimiters.
```

### analyze migration

Return code: `0`

```text
Wrote /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/QT611_MIGRATION_STATUS.md
```

### old framework scanner

Return code: `0`

```text
OK: no old UI-framework references found in active source/build files under /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint.
```

### Python/Qt runtime probe

Return code: `1`

```text
Python: /usr/bin/python3
Version: 3.14.3
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint

## pyproject.toml
parse OK

## package import
notizen_py_qt import OK

## PySide6 import
PySide6 import failed: No module named 'PySide6'

## QML candidates
/home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/Main.qml
/home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Main.qml
/home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/AppWindow.qml

## Qt/QML smoke test
/usr/bin/python3: No module named notizen_py_qt

RESULT: 2 problem(s) found.
```
