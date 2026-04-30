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
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_PYTHON_QT_MIGRATION_ACTIONS.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_MIGRATION_STATUS.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_QML_HARDENING.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_RUNTIME_HARDENING.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_CONTROLLER_RESTORE.md
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_CONTINUE_TRANSPILE_REPORT.md
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
-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_qt/template_rust_cxx_qt/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_qt/transpiled_examples
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_qt/transpiled_examples/Main.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_qt/transpiled_examples/MainWindow.qml
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_qt/transpiled_examples/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/Main.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/Main.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/MainWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/advanced_app_MainWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/main_window_MainWindow.qml
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/Main.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/MainWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/advanced_app_MainWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/main_window_MainWindow.qml
- create: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/qml/Main.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_cpp_qml/qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_cpp_qml/qml/Main.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_cpp_qml/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_rust_cxx_qt/qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_rust_cxx_qt/qml/Main.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/template_rust_cxx_qt/qml/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/AppState.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/Main.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/MainWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/Qt611Types.js
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/transpiled_examples/qmldir
- scan qml dir: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/Main.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml
- keep unchanged: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/qmldir
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
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_QML_HARDENING.md
```

### harden Python/Qt runtime

Return code: `0`

```text
Mode: APPLY
Root: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint
- package not found, skipped: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/src/notizen_py_qt
- update: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_RUNTIME_HARDENING.md
```

### final pyproject repair

Return code: `1`

```text
ERROR: pyproject.toml not found: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/pyproject.toml
```

### QML sanity check

Return code: `1`

```text
Checked 117 QML/JS file(s).
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
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:897:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:914:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082649/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:896:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082649/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:912:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082649/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082649/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:896:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082649/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:912:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082649/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/qml/app-window_AppWindow.qml:913:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082649/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:896:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082649/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:912:1: unmatched }
- /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/.qt611_qml_hardening_backup/20260430-082649/.qt611_qml_hardening_backup/20260430-082630/.qt611_qml_hardening_backup/20260430-082557/.qt611_qml_hardening_backup/20260430-082555/Notizen_py_slint/src/notizen_py_qt/ui/app-window_AppWindow.qml:913:1: unmatched }
```

### analyze migration

Return code: `1`

```text
Wrote /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/QT611_MIGRATION_STATUS.md
```

### old framework scanner

Return code: `127`

```text
bash: /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_qt/scripts/check_no_qt.sh: Datei oder Verzeichnis nicht gefunden
```
