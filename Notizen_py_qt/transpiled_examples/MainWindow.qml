import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    property string titleText: "Notizen"
    property string sourceCode: ""
    readonly property string outputCode: ""
    signal transpileRequested(string arg0)

    width: 1100
    height: 720
    color: "#202124"

    ColumnLayout {
        spacing: 8
        Text {
            text: root.titleText
            color: "#ffffff"
            font.pixelSize: 24
        }
        RowLayout {
            Button {
                text: "Transpilieren"
                onClicked: { root.transpileRequested(root.sourceCode); }
            }
            TextField {
                placeholderText: "Datei oder Code"
                text: root.sourceCode
            }
        }
        Repeater {
            model: rows
            delegate: Text {
                property var row: modelData
                property int i: index
                text: row.title
            }
        }
        Text {
            visible: root.outputCode != ""
            text: root.outputCode
        }
    }
}
