import "."
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    width: 1240
    height: 820
    Layout.minimumWidth: 940
    Layout.minimumHeight: 620
    title: root.windowTitle

    property string windowTitle: "Notizen PyPy Qt"
    property var rows: []
    property int selectedIndex: -1
    property string editorText
    property string noteTitle
    property string searchText
    property string statusText: "Bereit"
    property string metaText: ""
    property string modeLabel: "Modus: Text"
    property bool dirty: false

    signal newDocument()
    signal openDocument()
    signal openRemoteDocument()
    signal saveDocument()
    signal saveDocumentAs()
    signal saveRemoteDocument()
    signal setPassword()
    signal exportText()
    signal exportRtf()
    signal exportHtml()
    signal exportSubtreeText()
    signal exportSubtreeRtf()
    signal exportNoteRtf()
    signal extractImages()
    signal importText()
    signal importRtf()
    signal insertImage()
    signal appendDate()
    signal appendBullet()
    signal addChild()
    signal addSibling()
    signal deleteNote()
    signal duplicateNote()
    signal copyNode()
    signal cutNode()
    signal pasteNode()
    signal moveUp()
    signal moveDown()
    signal indentNote()
    signal outdentNote()
    signal toggleExpand()
    signal expandAll()
    signal collapseAll()
    signal selectRow(int arg0)
    signal renameCurrent(string arg0)
    signal editorChanged(string arg0)
    signal searchNext(string arg0)
    signal searchAll(string arg0)
    signal toggleRawRtf()
    signal toggleSticky()
    signal setStickyGeometry()
    signal setColors()
    signal clearColors()
    signal formatNote()
    signal openSettings()
    signal importLegacyConfig()
    signal openAlarm()
    signal showNextAlarm()
    signal showStats()

    ColumnLayout {
        padding: 8
        spacing: 8

        Rectangle {
            height: 122
            color: "#f6f6f6"
            border.color: "#dadada"
            border.width: 1
            ColumnLayout {
                padding: 6
                spacing: 5
                RowLayout {
                    spacing: 6
                    Button {
                        text: "Neu"
                        onClicked: { root.newDocument(); }
                    }
                    Button {
                        text: "Öffnen"
                        onClicked: { root.openDocument(); }
                    }
                    Button {
                        text: "FTP öffnen"
                        onClicked: { root.openRemoteDocument(); }
                    }
                    Button {
                        text: "Speichern"
                        onClicked: { root.saveDocument(); }
                    }
                    Button {
                        text: "Speichern unter"
                        onClicked: { root.saveDocumentAs(); }
                    }
                    Button {
                        text: "FTP speichern"
                        onClicked: { root.saveRemoteDocument(); }
                    }
                    Button {
                        text: "Passwort"
                        onClicked: { root.setPassword(); }
                    }
                    Rectangle {
                        width: 1
                        color: "#cccccc"
                    }
                    Button {
                        text: "TXT"
                        onClicked: { root.exportText(); }
                    }
                    Button {
                        text: "RTF"
                        onClicked: { root.exportRtf(); }
                    }
                    Button {
                        text: "HTML"
                        onClicked: { root.exportHtml(); }
                    }
                    Button {
                        text: "Teil TXT"
                        onClicked: { root.exportSubtreeText(); }
                    }
                    Button {
                        text: "Teil RTF"
                        onClicked: { root.exportSubtreeRtf(); }
                    }
                    Rectangle {
                        Layout.fillWidth: true  // from horizontal-stretch: 1
                    }
                    Text {
                        text: root.dirty ? "● geändert" : "gespeichert"
                        verticalAlignment: Text.AlignHCenter
                    }
                }
                RowLayout {
                    spacing: 6
                    Button {
                        text: "+ Kind"
                        onClicked: { root.addChild(); }
                    }
                    Button {
                        text: "+ Daneben"
                        onClicked: { root.addSibling(); }
                    }
                    Button {
                        text: "Dupl."
                        onClicked: { root.duplicateNote(); }
                    }
                    Button {
                        text: "Löschen"
                        onClicked: { root.deleteNote(); }
                    }
                    Button {
                        text: "Kopieren"
                        onClicked: { root.copyNode(); }
                    }
                    Button {
                        text: "Ausschneiden"
                        onClicked: { root.cutNode(); }
                    }
                    Button {
                        text: "Einfügen"
                        onClicked: { root.pasteNode(); }
                    }
                    Rectangle {
                        width: 1
                        color: "#cccccc"
                    }
                    Button {
                        text: "↑"
                        onClicked: { root.moveUp(); }
                    }
                    Button {
                        text: "↓"
                        onClicked: { root.moveDown(); }
                    }
                    Button {
                        text: "Einr."
                        onClicked: { root.indentNote(); }
                    }
                    Button {
                        text: "Ausr."
                        onClicked: { root.outdentNote(); }
                    }
                    Button {
                        text: "Auf/Zu"
                        onClicked: { root.toggleExpand(); }
                    }
                    Button {
                        text: "Alle auf"
                        onClicked: { root.expandAll(); }
                    }
                    Button {
                        text: "Alle zu"
                        onClicked: { root.collapseAll(); }
                    }
                    Rectangle {
                        width: 1
                        color: "#cccccc"
                    }
                    Button {
                        text: "Sticky"
                        onClicked: { root.toggleSticky(); }
                    }
                    Button {
                        text: "Geom."
                        onClicked: { root.setStickyGeometry(); }
                    }
                    Button {
                        text: "Farben"
                        onClicked: { root.setColors(); }
                    }
                    Button {
                        text: "Farbe weg"
                        onClicked: { root.clearColors(); }
                    }
                    Button {
                        text: "Format"
                        onClicked: { root.formatNote(); }
                    }
                    Button {
                        text: "Bilder"
                        onClicked: { root.extractImages(); }
                    }
                }
                RowLayout {
                    spacing: 6
                    Button {
                        text: "Stats"
                        onClicked: { root.showStats(); }
                    }
                    Button {
                        text: "Einstellungen"
                        onClicked: { root.openSettings(); }
                    }
                    Button {
                        text: "Wecker"
                        onClicked: { root.openAlarm(); }
                    }
                    Button {
                        text: "Nächster"
                        onClicked: { root.showNextAlarm(); }
                    }
                    Button {
                        text: "Alt-Config importieren"
                        onClicked: { root.importLegacyConfig(); }
                    }
                    Rectangle {
                        Layout.fillWidth: true  // from horizontal-stretch: 1
                    }
                    Text {
                        text: "HTML/Bilder/FTP/Wecker/Autosave erweitert"
                        verticalAlignment: Text.AlignHCenter
                        color: "#666666"
                    }
                }
            }
        }

        RowLayout {
            spacing: 8
            Rectangle {
                width: 350
                color: "#ffffff"
                border.color: "#d0d0d0"
                border.width: 1
                ColumnLayout {
                    padding: 6
                    spacing: 6
                    Text {
                        text: "Baum"
                        font.weight: 700
                    }
                    RowLayout {
                        spacing: 4
                        TextField {
                            text: root.searchText
                            onTextChanged: { root.searchText = text }
                            placeholderText: "Suchen"
                        }
                        Button {
                            text: "Weiter"
                            onClicked: { root.searchNext(root.searchText); }
                        }
                        Button {
                            text: "Alle"
                            onClicked: { root.searchAll(root.searchText); }
                        }
                    }
                    ScrollView {
                        viewportWidth: parent.width
                        viewportHeight: parent.height - 72
                        ColumnLayout {
                            spacing: 1
                            Repeater {
                                model: root.rows
                                delegate: Rectangle {
                                    property var row: modelData
                                    property int i: index
                                    height: 30
                                    color: row.selected ? "#dbeafe" : "#ffffff"
                                    border.color: row.selected ? "#93c5fd" : "#ffffff"
                                    border.width: 1
                                    Text {
                                        x: 6
                                        y: 0
                                        width: parent.width - 12
                                        height: parent.height
                                        text: row.label
                                        verticalAlignment: Text.AlignHCenter
                                        overflow: elide
                                    }
                                    MouseArea {
                                        onClicked: { root.selectRow(i); }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                color: "#ffffff"
                border.color: "#d0d0d0"
                border.width: 1
                ColumnLayout {
                    padding: 8
                    spacing: 8
                    RowLayout {
                        spacing: 6
                        Text {
                            text: "Titel:"
                            verticalAlignment: Text.AlignHCenter
                        }
                        TextField {
                            text: root.noteTitle
                            onTextChanged: { root.noteTitle = text }
                        }
                        Button {
                            text: "Umbenennen"
                            onClicked: { root.renameCurrent(root.noteTitle); }
                        }
                        Rectangle {
                            width: 1
                            color: "#cccccc"
                        }
                        Text {
                            text: root.modeLabel
                            verticalAlignment: Text.AlignHCenter
                        }
                        Button {
                            text: "RTF/Text"
                            onClicked: { root.toggleRawRtf(); }
                        }
                        Button {
                            text: "Import TXT"
                            onClicked: { root.importText(); }
                        }
                        Button {
                            text: "Import RTF"
                            onClicked: { root.importRtf(); }
                        }
                        Button {
                            text: "Bild+"
                            onClicked: { root.insertImage(); }
                        }
                        Button {
                            text: "Datum+"
                            onClicked: { root.appendDate(); }
                        }
                        Button {
                            text: "•+"
                            onClicked: { root.appendBullet(); }
                        }
                        Button {
                            text: "Notiz-RTF"
                            onClicked: { root.exportNoteRtf(); }
                        }
                        Button {
                            text: "Bilder"
                            onClicked: { root.extractImages(); }
                        }
                    }
                    TextArea {
                        text: root.editorText
                        onTextChanged: { root.editorText = text }
                        wrapMode: Text.WordWrap
                        // TODO(qt611-port): changed text => { root.editorChanged(root.text); }
                    }
                    Rectangle {
                        height: 28
                        color: "#fbfbfb"
                        border.color: "#eeeeee"
                        border.width: 1
                        Text {
                            x: 6
                            width: parent.width - 12
                            height: parent.height
                            text: root.metaText
                            verticalAlignment: Text.AlignHCenter
                            overflow: elide
                        }
                    }
                }
            }
        }

        Rectangle {
            height: 30
            color: "#f6f6f6"
            border.color: "#dadada"
            border.width: 1
            Text {
                x: 8
                width: parent.width - 16
                height: parent.height
                text: root.statusText
                verticalAlignment: Text.AlignHCenter
                overflow: elide
            }
        }
    }
}
