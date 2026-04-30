import "."
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    property string titleText: "Notizen"
    signal transpileRequested(string arg0)
    width: 1100
    height: 720
    color: "#20242a"

    ColumnLayout {
        spacing: 8
        TextField {
            id: titleField
            text: root.titleText
            onTextChanged: { root.titleText = text }
            placeholderText: qsTr("Titel")
        }
        Button {
            text: qsTr("Transpilieren")
            onClicked: { root.transpileRequested(root.titleText); }
        }
    }
}
