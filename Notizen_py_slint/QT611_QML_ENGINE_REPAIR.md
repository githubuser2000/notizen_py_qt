# Qt 6.11 QML engine repair

Mode: APPLY
Root: `/home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint`
Final smoke return code: `0`

## Actions

- `src/notizen_py_qt/ui/Main.qml`:77: non-existent property "padding"
  - before: `padding: 8`
  - after: `property real padding: 8`
- `qml/Main.qml`:77: mirrored QML counterpart
  - before: `padding: 8`
  - after: `property real padding: 8`
- `src/notizen_py_qt/ui/Main.qml`:86: non-existent property "padding"
  - before: `padding: 6`
  - after: `property real padding: 6`
- `qml/Main.qml`:86: mirrored QML counterpart
  - before: `padding: 6`
  - after: `property real padding: 6`
- `src/notizen_py_qt/ui/Main.qml`:283: non-existent property "padding"
  - before: `padding: 6`
  - after: `property real padding: 6`
- `qml/Main.qml`:283: mirrored QML counterpart
  - before: `padding: 6`
  - after: `property real padding: 6`
- `src/notizen_py_qt/ui/Main.qml`:307: non-existent property "viewportHeight"
  - before: `viewportHeight: parent.height - 72`
  - after: `property var viewportHeight: parent.height - 72`
- `qml/Main.qml`:307: mirrored QML counterpart
  - before: `viewportHeight: parent.height - 72`
  - after: `property var viewportHeight: parent.height - 72`
- `src/notizen_py_qt/ui/Main.qml`:306: non-existent property "viewportWidth"
  - before: `viewportWidth: parent.width`
  - after: `property var viewportWidth: parent.width`
- `qml/Main.qml`:306: mirrored QML counterpart
  - before: `viewportWidth: parent.width`
  - after: `property var viewportWidth: parent.width`
- `src/notizen_py_qt/ui/Main.qml`:326: non-existent property "overflow"
  - before: `overflow: elide`
  - after: `property var overflow: elide`
- `qml/Main.qml`:326: mirrored QML counterpart
  - before: `overflow: elide`
  - after: `property var overflow: elide`
- `src/notizen_py_qt/ui/Main.qml`:343: non-existent property "padding"
  - before: `padding: 8`
  - after: `property real padding: 8`
- `qml/Main.qml`:343: mirrored QML counterpart
  - before: `padding: 8`
  - after: `property real padding: 8`
- `src/notizen_py_qt/ui/Main.qml`:417: non-existent property "overflow"
  - before: `overflow: elide`
  - after: `property var overflow: elide`
- `qml/Main.qml`:417: mirrored QML counterpart
  - before: `overflow: elide`
  - after: `property var overflow: elide`
- `src/notizen_py_qt/ui/Main.qml`:435: non-existent property "overflow"
  - before: `overflow: elide`
  - after: `property var overflow: elide`
- `qml/Main.qml`:435: mirrored QML counterpart
  - before: `overflow: elide`
  - after: `property var overflow: elide`

## Last smoke/probe output

```text
file:///home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Main.qml:6:1: QML Main: Layout attached property must be attached to an object deriving from Item
file:///home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint/src/notizen_py_qt/ui/Main.qml:6:1: QML Main: Layout attached property must be attached to an object deriving from Item
```
