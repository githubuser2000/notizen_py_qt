# Qt 6.11 Migration Status

Root: `/home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint`

## Summary

- Reports: 0
- Components generated: 0
- Global singletons generated: 0
- Enums converted to JS helpers: 0
- Structs converted to JS helpers: 0
- Converter warnings: 0
- Generated TODO markers: 19
- Active old-UI references: 38

## Generated TODO samples

- `src/notizen_py_qt/ui/AppWindow.qml:403: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `src/notizen_py_qt/ui/Main.qml:403: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `src/notizen_py_qt/ui/app-window_AppWindow.qml:488: // TODO(qt611-port): pointer-event(event) => {`
- `src/notizen_py_qt/ui/app-window_AppWindow.qml:694: // TODO(qt611-port): pointer-event(event) => {`
- `src/notizen_py_qt/ui/app-window_AppWindow.qml:711: // TODO(qt611-port): edited(text) => { root.editorChanged(text); }`
- `src/notizen_py_qt/ui/app-window_AppWindow.qml:739: // TODO(qt611-port): pointer-event(event) => {`
- `src/notizen_py_qt/ui/app-window.qml:403: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `qml/AppWindow.qml:403: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `qml/Main.qml:403: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `qml/app-window_AppWindow.qml:488: // TODO(qt611-port): pointer-event(event) => {`
- `qml/app-window_AppWindow.qml:694: // TODO(qt611-port): pointer-event(event) => {`
- `qml/app-window_AppWindow.qml:711: // TODO(qt611-port): edited(text) => { root.editorChanged(text); }`
- `qml/app-window_AppWindow.qml:739: // TODO(qt611-port): pointer-event(event) => {`
- `.qt611_no_slint_backup_v4/20260429-212035/qml/AppWindow.qml:403: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `.qt611_no_slint_backup_v4/20260429-212035/qml/Main.qml:403: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:488: // TODO(qt611-port): pointer-event(event) => {`
- `.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:694: // TODO(qt611-port): pointer-event(event) => {`
- `.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:711: // TODO(qt611-port): edited(text) => { root.editorChanged(text); }`
- `.qt611_no_slint_backup_v4/20260429-212035/qml/app-window_AppWindow.qml:739: // TODO(qt611-port): pointer-event(event) => {`

## Active old-UI references still present

- `pyproject.toml:6: name = "notizen-py-qt"`
- `pyproject.toml:8: description = "Python/Qt port of the old VB.NET Notizen.NET application"`
- `pyproject.toml:33: notizen-py-qt = "notizen_py_qt.app:main"`
- `pyproject.toml:35: # Compatibility entry point for old installs. Prefer notizen-py-qt.`
- `pyproject.toml:36: notizen-pypy-qt = "notizen_pypy_qt.app:main"`
- `pyproject.toml:46: notizen_py_qt = ["ui/*.qml", "ui/*.js"]`
- `pyproject.toml:47: "notizen_py_qt.ui" = ["*.qml", "*.js"]`
- `CMakeLists.txt:17: qml/*.qml`
- `src/backend.rs:4: include!("cxx-qt-lib/qstring.h");`
- `src/notizen_py_qt/ui/AppWindow.qml:14: property string windowTitle: "Notizen PyPy Qt"`
- `src/notizen_py_qt/ui/Main.qml:14: property string windowTitle: "Notizen PyPy Qt"`
- `src/notizen_py_qt/ui/app-window_AppWindow.qml:15: property string windowTitle: "Notizen Py Qt"`
- `src/notizen_py_qt/ui/app-window.qml:14: property string windowTitle: "Notizen PyPy Qt"`
- `Notizen_py_qt/template_rust_cxx_qt/Cargo.toml:9: cxx-qt = "0.8.1"`
- `Notizen_py_qt/template_rust_cxx_qt/Cargo.toml:10: cxx-qt-lib = { version = "0.8.1", features = ["qt_full"] }`
- `Notizen_py_qt/template_rust_cxx_qt/Cargo.toml:13: cxx-qt-build = { version = "0.8.1", features = ["link_qt_object_files"] }`
- `Notizen_py_qt/template_rust_cxx_qt/CMakeLists.txt:17: qml/*.qml`
- `Notizen_py_qt/template_rust_cxx_qt/src/backend.rs:4: include!("cxx-qt-lib/qstring.h");`
- `Notizen_py_qt/template_rust_cxx_qt/src/main.rs:12: engine.load(&QUrl::from("qrc:/qt/qml/org/notizen/transpiler/qml/Main.qml"));`
- `Notizen_py_qt/template_rust_cxx_qt/qml/Main.qml:11: title: qsTr("Notizen / Qt 6.11")`
- `Notizen_py_qt/template_rust_cxx_qt/qml/Main.qml:29: Label { text: qsTr("Qt 6.11 + CXX-Qt") }`
- `Notizen_py_qt/template_rust_cxx_qt/qml/Main.qml:35: orientation: Qt.Horizontal`
- `Notizen_py_qt/template_rust_cxx_qt/cpp/main.cpp:10: const QUrl url(QStringLiteral("qrc:/qt/qml/org/notizen/transpiler/qml/Main.qml"));`
- `Notizen_py_qt/template_rust_cxx_qt/cpp/main.cpp:21: Qt::QueuedConnection);`
- `Notizen_py_qt/template_cpp_qml/CMakeLists.txt:17: qml/*.qml`
- `Notizen_py_qt/template_cpp_qml/cpp/main.cpp:13: const QUrl url(QStringLiteral("qrc:/qt/qml/Notizen/Main.qml"));`
- `Notizen_py_qt/template_cpp_qml/cpp/main.cpp:24: Qt::QueuedConnection);`
- `Notizen_py_qt/template_cpp_qml/qml/Main.qml:19: Label { text: qsTr("Qt 6.11") }`
- `Notizen_py_qt/template_cpp_qml/qml/Main.qml:25: orientation: Qt.Horizontal`
- `Notizen_py_qt/cpp/main.cpp:13: const QUrl url(QStringLiteral("qrc:/qt/qml/Notizen/Main.qml"));`
- `Notizen_py_qt/cpp/main.cpp:24: Qt::QueuedConnection);`
- `Notizen_py_qt/qml/Main.qml:19: Label { text: qsTr("Qt 6.11") }`
- `Notizen_py_qt/qml/Main.qml:25: orientation: Qt.Horizontal`
- `qml/AppWindow.qml:14: property string windowTitle: "Notizen PyPy Qt"`
- `qml/Main.qml:14: property string windowTitle: "Notizen PyPy Qt"`
- `qml/app-window_AppWindow.qml:15: property string windowTitle: "Notizen Py Qt"`
- `cpp/main.cpp:13: const QUrl url(QStringLiteral("qrc:/qt/qml/Notizen/Main.qml"));`
- `cpp/main.cpp:24: Qt::QueuedConnection);`

