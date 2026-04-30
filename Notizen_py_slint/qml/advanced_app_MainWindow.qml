import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    property alias titleText: titleField.text
    property var rows
    width: 900
    height: 600

    ColumnLayout {
        TextField {
            id: titleField
            text: root.titleText
            onTextChanged: { root.titleText = text }
            placeholderText: qsTr("Titel")
        }
        Button {
            text: qsTr("Speichern")
            onClicked: { AppState.saveRequested(root.titleText); }
        }
        Repeater {
            model: rows
            delegate: CheckBox {
                property var row: modelData
                property int i: index
                text: row.title
                checked: row.done
            }
        }
        Behavior on opacity {
            NumberAnimation {
                duration: 250
            }
        }
    }
}
