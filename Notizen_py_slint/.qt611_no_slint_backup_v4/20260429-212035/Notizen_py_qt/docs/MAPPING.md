# Slint→Qt Quick/QML Mapping v3

Diese Tabelle dokumentiert die automatische Abbildung des Transpilierers. Alles,
was semantisch riskant ist, wird zusätzlich im JSON-Report und in
`QT611_MIGRATION_STATUS.md` sichtbar gemacht.

## Komponenten und Top-Level-Konstrukte

| Slint | Qt/QML-Ausgabe | Hinweis |
|---|---|---|
| `export component MainWindow inherits Window { ... }` | `MainWindow.qml` mit `ApplicationWindow { ... }` | `visible: true` wird ergänzt, wenn keine Root-Visibility gesetzt ist. |
| `component Foo inherits Rectangle { ... }` | `Foo.qml` mit `Rectangle { ... }` | Basistyp wird über `TYPE_MAP` übertragen. |
| `export global AppState { ... }` | `AppState.qml` mit `pragma Singleton` und `QtObject` | `GeneratedQmlSingletons.cmake` setzt `QT_QML_SINGLETON_TYPE`. |
| `enum Theme { Light, Dark }` | `Qt611Types.js` mit `var Theme = Object.freeze(...)` | Als JS-Hilfe, später idealerweise durch typed Backend ersetzen. |
| `struct Todo { title: string }` | `Qt611Types.js` mit `makeTodo(values)` | Als JS-Factory für QML-Modelle. |

## UI-Elemente

| Slint | QML |
|---|---|
| `Window`, `AppWindow` | `ApplicationWindow` |
| `Dialog` | `Dialog` |
| `PopupWindow` | `Popup` |
| `VerticalBox`, `VerticalLayout` | `ColumnLayout` |
| `HorizontalBox`, `HorizontalLayout` | `RowLayout` |
| `GridBox`, `GridLayout` | `GridLayout` |
| `LineEdit` | `TextField` |
| `TextEdit` | `TextArea` |
| `Button` | `Button` |
| `CheckBox` | `CheckBox` |
| `TouchArea` | `MouseArea` |
| `Image` | `Image` |

## Properties

| Slint | QML |
|---|---|
| `font-size` | `font.pixelSize` |
| `font-weight` | `font.weight` |
| `background`, `background-color` | `color` |
| `border-color` | `border.color` |
| `border-width` | `border.width` |
| `border-radius` | `radius` |
| `horizontal-stretch` | `Layout.fillWidth` |
| `vertical-stretch` | `Layout.fillHeight` |
| `preferred-width` | `Layout.preferredWidth` |
| `preferred-height` | `Layout.preferredHeight` |
| `placeholder-text` | `placeholderText` |
| `current-index` | `currentIndex` |

Slint-Längen wie `800px` werden als QML-Zahlen ausgegeben, also `800`.
Zeitwerte wie `250ms` werden als Millisekunden-Zahl ausgegeben, also `250`.
Prozentwerte wie `50%` werden nach `0.5` normalisiert.

## Signale, Callbacks und Events

| Slint | QML |
|---|---|
| `callback save-requested(string);` | `signal saveRequested(string arg0)` |
| `clicked => { ... }` | `onClicked: { ... }` |
| `pressed => { ... }` | `onPressed: { ... }` |
| `edited => { ... }` | `onEditingFinished: { ... }` |
| `text-changed => { ... }` | `onTextChanged: { ... }` |
| `key-pressed => { ... }` | `Keys.onPressed: { ... }` |

Callback-Namen in kebab-case werden nach camelCase konvertiert.

## Bindings

| Slint | QML-Ausgabe |
|---|---|
| `text: root.title-text;` | `text: root.titleText` |
| `text <=> root.title-text;` | `text: root.titleText` plus `onTextChanged: { root.titleText = text }` |
| `in-out property <string> title-text <=> field.text;` | `property alias titleText: field.text` |

Zwei-Wege-Bindings können in QML Binding-Loops erzeugen. Der Transpilierer erzeugt
nur die offensichtliche mechanische Variante und markiert sie im Report.

## Schleifen und Bedingungen

| Slint | QML |
|---|---|
| `for row[i] in rows: Text { ... }` | `Repeater { model: rows; delegate: Text { property var row: modelData; property int i: index; ... } }` |
| `if cond: Text { ... }` | `Text { visible: cond; ... }` |

## Animationen

| Slint | QML |
|---|---|
| `animate opacity { duration: 250ms; }` | `Behavior on opacity { NumberAnimation { duration: 250 } }` |

Komplexe Transitions, States und Easing-Details müssen manuell geprüft werden.

## Nicht automatisch vollständig gelöst

- komplexe `states [...]`-Blöcke
- `@children` / Default-Property-Slots
- Backend-Modelle mit stark typisierten Rust- oder C++-Objekten
- Pointer-/Touch-Eventdetails
- Callback-Rückgabewerte
- semantisch komplexe Rust-UI-Startlogik

Diese Fälle werden nicht verschwiegen, sondern als Warnungen im Report sichtbar.
