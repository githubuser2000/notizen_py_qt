# Slint → Qt Quick/QML Mapping

Dieses Dokument beschreibt, was `scripts/slint_to_qml.py` automatisch umsetzt.

## Komponenten

| Slint | QML |
|---|---|
| `export component MainWindow inherits Window { ... }` | `ApplicationWindow { id: root ... }` in `MainWindow.qml` |
| `component Foo inherits Rectangle { ... }` | `Rectangle { id: root ... }` in `Foo.qml` |
| kein Komponentenblock | wird als `Main.qml` gewrappt |

## Typen

| Slint | QML |
|---|---|
| `Window`, `AppWindow` | `ApplicationWindow` |
| `VerticalBox`, `VerticalLayout` | `ColumnLayout` |
| `HorizontalBox`, `HorizontalLayout` | `RowLayout` |
| `GridBox`, `GridLayout` | `GridLayout` |
| `LineEdit` | `TextField` |
| `TextEdit` | `TextArea` |
| `TouchArea` | `MouseArea` |
| `Button`, `CheckBox`, `Slider`, `ComboBox`, `Image`, `ListView` | gleichnamige oder naheliegende Qt-Quick/Controls-Typen |

## Eigenschaften

| Slint | QML |
|---|---|
| `in property <string> title-text: "X";` | `property string titleText: "X"` |
| `out property <string> output-code;` | `readonly property string outputCode` |
| `background: #112233;` | `color: "#112233"` |
| `font-size: 20px;` | `font.pixelSize: 20` |
| `border-color` | `border.color` |
| `border-width` | `border.width` |
| `border-radius` | `radius` |
| `placeholder-text` | `placeholderText` |
| `horizontal-stretch` | `Layout.fillWidth` |
| `vertical-stretch` | `Layout.fillHeight` |

Kebab-case-Namen werden für QML nach camelCase übertragen. Aus `root.source-code` wird `root.sourceCode`.

## Callbacks und Events

| Slint | QML |
|---|---|
| `callback save-requested(string);` | `signal saveRequested(string arg0)` |
| `clicked => { root.save-requested(text); }` | `onClicked: { root.saveRequested(text); }` |
| `pressed`, `released`, `toggled`, `accepted` | entsprechende `on...`-Handler |

Pointer-/Touch-Events werden nur grob gemappt und im Report gewarnt, weil QML-Maus-/Pointerdetails anders modelliert sind.

## Inline-Objekte

```slint
Text { text: root.title-text; font-size: 20px; }
```

wird zu:

```qml
Text {
    text: root.titleText
    font.pixelSize: 20
}
```

## Schleifen und Bedingungen

```slint
for row[i] in rows: Text { text: row.title; }
```

wird zu:

```qml
Repeater {
    model: rows
    delegate: Text {
        property var row: modelData
        property int i: index
        text: row.title
    }
}
```

```slint
if root.output-code != "": Text { text: root.output-code; }
```

wird zu einem immer erzeugten QML-Objekt mit `visible`-Binding:

```qml
Text {
    visible: root.outputCode != ""
    text: root.outputCode
}
```

Das ist absichtlich transparent, aber nicht in allen Fällen semantisch identisch. Prüfe insbesondere Lifecycle, Layoutplatz und Model-Rollen.

## Manuelle Nacharbeit

Diese Konstrukte werden als TODO oder Warnung markiert:

- `states [...]`
- `animate property { ... }`
- `global` Singletons
- `struct` und `enum`
- komplexe Modelle und Rollen
- Custom Render-Pfade
- Touch-/Pointerdetails
- Rückgabewerte von Slint-Callbacks

## Zielarchitektur

Für ein Rust-Projekt ist die Zielstruktur:

```text
Cargo.toml
build.rs
src/main.rs
src/backend.rs
qml/Main.qml
qml/*.qml
```

Die UI lebt in Qt Quick/QML. Rust bleibt Backend über CXX-Qt. Dadurch wird Slint wirklich entfernt und nicht nur aus der Oberfläche herausgeschoben.
