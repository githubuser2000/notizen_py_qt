import "."
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1100
    height: 720
    visible: true
    title: qsTr("Notizen / Transpiler")

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            ToolButton { text: qsTr("Öffnen") }
            ToolButton { text: qsTr("Transpilieren") }
            ToolButton { text: qsTr("Export") }
            Item { Layout.fillWidth: true }
            Label { text: qsTr("Qt 6.11") }
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
