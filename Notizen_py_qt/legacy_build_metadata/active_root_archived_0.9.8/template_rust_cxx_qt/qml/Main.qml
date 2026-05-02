import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.notizen.transpiler 1.0

ApplicationWindow {
    id: root
    width: 1100
    height: 720
    visible: true
    title: qsTr("Notizen / Qt 6.11")

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
        orientation: Qt.Horizontal

        TextArea {
            id: sourceEditor
            SplitView.preferredWidth: root.width * 0.5
            placeholderText: qsTr("Quelle hier einfügen …")
            wrapMode: TextArea.NoWrap
            selectByMouse: true
        }

        TextArea {
            id: outputEditor
            readOnly: true
            placeholderText: qsTr("Transpilierte Ausgabe erscheint hier …")
            wrapMode: TextArea.NoWrap
            selectByMouse: true
        }
    }
}
