# Qt 6.11 continued transpilation report

Mode: APPLY
Root: `/home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint`

## Step results

### repair pyproject

Return code: `1`

```text
ERROR: pyproject.toml not found: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/pyproject.toml
```

### finish Python package migration

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint
Actions:
- archive remaining old UI file: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/examples/advanced_app.slint -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/legacy_slint/Notizen_py_qt/examples/advanced_app.slint
- archive remaining old UI file: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/examples/main_window.slint -> /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/legacy_slint/Notizen_py_qt/examples/main_window.slint
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_PYTHON_QT_MIGRATION_ACTIONS.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_MIGRATION_STATUS.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/README.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/QT611_MIGRATION_STATUS.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/VALIDATION_V6.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/scripts/build_qt611.sh
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/scripts/qml_sanity_check.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/scripts/analyze_transpilation.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/scripts/fix_qml_for_pyside.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/scripts/restore_qt_controller_from_backup.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/scripts/continue_qt611_transpile.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/tests/test_slint_to_qml.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/tests/test_finish_python_qt_migration.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/tests/test_repair_pyproject_qt611.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/tests/test_v6_continue.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/docs/MAPPING.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/main_window.slint_to_qml.report.json
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/advanced_app.slint_to_qml.report.json
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/pyproject.toml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/scripts/check_no_slint.sh
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/scripts/check_no_slint_strict.sh
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/scripts/build_python_qt.sh
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/scripts/repair_pyproject_qt611.py
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_PYTHON_QT_MIGRATION_ACTIONS.md

OK: Python package names, QML strings, entry points and active source references are clean.
```

### repair pyproject again

Return code: `1`

```text
ERROR: pyproject.toml not found: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/pyproject.toml
```

### harden QML

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/qml/Main.qml
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_cpp_qml/qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_cpp_qml/qml/Main.qml
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_cpp_qml/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_rust_cxx_qt/qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_rust_cxx_qt/qml/Main.qml
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_rust_cxx_qt/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/AppState.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/Main.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/Qt611Types.js
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/Main.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/AppState.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/Main.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/advanced_app_AppState.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/advanced_app_MainWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/app-window_AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/main_window_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/advanced_app_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/app-window_Qt611Types.js
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/AppState.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Main.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_AppState.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_MainWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/main_window_MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_Qt611Types.js
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/qmldir
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_QML_HARDENING.md
```

### harden Python/Qt runtime

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint
- package not found, skipped: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/src/notizen_py_qt
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_RUNTIME_HARDENING.md
```

### restore Qt controller from backup

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint
- no backed-up legacy controller found; keeping current Qt runner
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_CONTROLLER_RESTORE.md
```

### final pyproject repair

Return code: `1`

```text
ERROR: pyproject.toml not found: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/pyproject.toml
```

### QML sanity check

Return code: `1`

```text
Checked 54 QML/JS file(s).
Sanity check failed:
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/qml/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:896:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:912:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:896:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:912:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:896:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:912:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:913:1: unmatched }
```

### analyze migration

Return code: `1`

```text
Wrote /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_MIGRATION_STATUS.md
```

### old framework scanner

Return code: `0`

```text
OK: no old UI-framework references found in active source/build files.
```
