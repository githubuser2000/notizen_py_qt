import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.notizen.transpiler

ApplicationWindow {
    width: 1100
    height: 720
    visible: true
    title: qsTr("Notizen / Transpiler")

    TranspilerBackend {
        id: backend
    }

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            ToolButton {
                text: qsTr("Transpilieren")
                onClicked: {
                    backend.source = sourceEditor.text
                    backend.transpile()
                    outputEditor.text = backend.output
                }
            }
            Item { Layout.fillWidth: true }
            Label { text: qsTr("Qt 6.11 + CXX-Qt") }
        }
    }

    SplitView {
        anchors.fill: parent
        TextArea {
            id: sourceEditor
            SplitView.preferredWidth: parent.width * 0.5
            placeholderText: qsTr("Quelle hier einfügen …")
            wrapMode: TextArea.NoWrap
        }
        TextArea {
            id: outputEditor
            readOnly: true
            placeholderText: qsTr("Ausgabe …")
            wrapMode: TextArea.NoWrap
        }
    }
}
