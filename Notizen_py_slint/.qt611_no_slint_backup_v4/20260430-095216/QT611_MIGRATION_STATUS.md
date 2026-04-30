# Qt 6.11 Migration Status

Root: `/home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint`

## Summary

- Reports: 3
- Components generated: 3
- Global singletons generated: 1
- Enums converted to JS helpers: 1
- Structs converted to JS helpers: 2
- Converter warnings: 15
- Generated TODO markers: 13
- Active old-UI references: 0

## Generated outputs

- `advanced_app_AppState.qml`
- `advanced_app_GeneratedQmlSingletons.cmake`
- `advanced_app_MainWindow.qml`
- `advanced_app_Qt611Types.js`
- `app-window_AppWindow.qml`
- `app-window_Qt611Types.js`
- `main_window_MainWindow.qml`

## Converter warnings

### /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Qt/src/notizen_py_qt/ui/app-window.qml

- line 264: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `text <=> root.search-text`
- line 273: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `checked <=> root.search-case-sensitive`
- line 274: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `checked <=> root.search-whole-words`
- line 275: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `checked <=> root.search-current-subtree`
- line 278: Qt for-loop converted to Repeater; check model roles and delegate sizing — `for row in root.rows: Rectangle`
- line 301: Line copied as TODO comment; manual conversion required — `pointer-event(event) => {`
- line 380: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `text <=> root.note-title`
- line 397: Line copied as TODO comment; manual conversion required — `pointer-event(event) => {`
- line 410: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `text <=> root.editor-text`
- line 412: Line copied as TODO comment; manual conversion required — `edited(text) => { root.editor-changed(text); }`
- line 440: Line copied as TODO comment; manual conversion required — `pointer-event(event) => {`

### /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Qt/Notizen_py_qt/examples/main_window.qml

- line 13: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `text <=> root.title-text`

### /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Qt/Notizen_py_qt/examples/advanced_app.qml

- line 23: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `text <=> root.title-text`
- line 27: Qt for-loop converted to Repeater; check model roles and delegate sizing — `for row in rows: CheckBox`
- line 28: Qt animate block converted to QML Behavior/NumberAnimation; easing may need review — `animate opacity`

## Generated TODO samples

- `src/notizen_py_qt/ui/AppWindow.qml:404: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `src/notizen_py_qt/ui/Main.qml:404: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `src/notizen_py_qt/ui/app-window_AppWindow.qml:489: // TODO(qt611-port): pointer-event(event) => {`
- `src/notizen_py_qt/ui/app-window_AppWindow.qml:695: // TODO(qt611-port): pointer-event(event) => {`
- `src/notizen_py_qt/ui/app-window_AppWindow.qml:712: // TODO(qt611-port): edited(text) => { root.editorChanged(text); }`
- `src/notizen_py_qt/ui/app-window_AppWindow.qml:740: // TODO(qt611-port): pointer-event(event) => {`
- `src/notizen_py_qt/ui/app-window.qml:404: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `qml/AppWindow.qml:404: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `qml/Main.qml:404: // TODO(qt611-port): changed text => { root.editorChanged(root.text); }`
- `qml/app-window_AppWindow.qml:489: // TODO(qt611-port): pointer-event(event) => {`
- `qml/app-window_AppWindow.qml:695: // TODO(qt611-port): pointer-event(event) => {`
- `qml/app-window_AppWindow.qml:712: // TODO(qt611-port): edited(text) => { root.editorChanged(text); }`
- `qml/app-window_AppWindow.qml:740: // TODO(qt611-port): pointer-event(event) => {`

