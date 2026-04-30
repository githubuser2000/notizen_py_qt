import "."
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    // Use preferred/minimum geometry instead of fixed width/height so the
    // desktop window can be resized and maximized by the window manager.
    Layout.preferredWidth: 1280
    Layout.preferredHeight: 860
    Layout.minimumWidth: 760
    Layout.minimumHeight: 520
    title: root.windowTitle

    property string windowTitle: "Notizen Py Qt"
    property var rows: []
    property int selectedIndex: -1
    property string editorText
    property string noteTitle
    property string searchText
    property bool searchCaseSensitive: false
    property bool searchWholeWords: false
    property bool searchCurrentSubtree: false
    property string statusText: "Bereit"
    property string metaText: ""
    property string modeLabel: "Modus: Text"
    property bool dirty: false
    property bool treeContextVisible: false
    property bool editorContextVisible: false
    property int contextRowIndex: -1
    property real editorContextX: 24
    property real editorContextY: 24
    property bool fullscreenEnabled: false

    signal newDocument()
    signal openDocument()
    signal openRecentDocument()
    signal openRemoteDocument()
    signal saveDocument()
    signal saveDocumentAs()
    signal saveRemoteDocument()
    signal setPassword()
    signal exportText()
    signal exportRtf()
    signal exportHtml()
    signal exportMarkdown()
    signal exportJson()
    signal exportAlx()
    signal exportOpml()
    signal exportNotesDoc()
    signal exportSubtreeText()
    signal exportSubtreeRtf()
    signal exportNoteRtf()
    signal exportStickyHtml()
    signal extractImages()
    signal importText()
    signal importRtf()
    signal importJson()
    signal importOpml()
    signal insertImage()
    signal appendDate()
    signal appendBullet()
    signal addChild()
    signal addSibling()
    signal deleteNote()
    signal duplicateNote()
    signal combineSubtree()
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
    signal renameRow(int arg0)
    signal renameCurrent(string arg0)
    signal editorChanged(string arg0)
    signal searchNext(string arg0)
    signal searchAll(string arg0)
    signal replaceText(string arg0)
    signal toggleRawRtf()
    signal toggleSticky()
    signal setStickyGeometry()
    signal autosizeSticky()
    signal setColors()
    signal applyLightColor()
    signal clearColors()
    signal formatNote()
    signal applyBold()
    signal applyItalic()
    signal applyUnderline()
    signal applyStrike()
    signal applyRegular()
    signal increaseFontSize()
    signal decreaseFontSize()
    signal openSettings()
    signal importLegacyConfig()
    signal openAlarm()
    signal showNextAlarm()
    signal showStats()
    signal showBackups()
    signal showAbout()
    signal showShortcuts()
    signal showContextMenus()
    signal showFonts()
    signal showCompatReport()
    signal showDefaultPaths()
    signal showPasswordInfo()
    signal repairDocument()
    signal showToolstrips()
    signal toggleMaximized()
    signal toggleFullscreen()

    ColumnLayout {
        padding: 8
        spacing: 8

        Rectangle {
            // Compact global toolbar. Node/editor actions live in their own
            // context menus, so the tree and text editor stay visible.
            height: 184
            color: "#f6f6f6"
            border.color: "#dadada"
            border.width: 1
            ColumnLayout {
                padding: 6
                spacing: 5
                RowLayout {
                    spacing: 8
                    Rectangle {
                        Layout.fillWidth: true  // from horizontal-stretch: 1
                        ColumnLayout {
                            spacing: 4
                            Text {
                                text: "Datei"
                                font.weight: 700
                                verticalAlignment: Text.AlignHCenter
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "Neu"
                                    onClicked: { root.newDocument(); }
                                }
                                Button {
                                    text: "Öffnen"
                                    onClicked: { root.openDocument(); }
                                }
                                Button {
                                    text: "Zuletzt"
                                    onClicked: { root.openRecentDocument(); }
                                }
                                Button {
                                    text: "FTP auf"
                                    onClicked: { root.openRemoteDocument(); }
                                }
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "Speichern"
                                    onClicked: { root.saveDocument(); }
                                }
                                Button {
                                    text: "Unter"
                                    onClicked: { root.saveDocumentAs(); }
                                }
                                Button {
                                    text: "FTP speich."
                                    onClicked: { root.saveRemoteDocument(); }
                                }
                                Button {
                                    text: "PW"
                                    onClicked: { root.setPassword(); }
                                }
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "Max"
                                    onClicked: { root.toggleMaximized(); }
                                }
                                Button {
                                    text: "Vollbild"
                                    onClicked: { root.toggleFullscreen(); }
                                }
                                Text {
                                    text: root.dirty ? "● geändert" : "gespeichert"
                                    verticalAlignment: Text.AlignHCenter
                                    color: "#666666"
                                }
                            }
                        }
                    }
                    Rectangle {
                        width: 1
                        color: "#dddddd"
                    }
                    Rectangle {
                        Layout.fillWidth: true  // from horizontal-stretch: 1
                        ColumnLayout {
                            spacing: 4
                            Text {
                                text: "Export"
                                font.weight: 700
                                verticalAlignment: Text.AlignHCenter
                            }
                            RowLayout {
                                spacing: 4
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
                                    text: "MD"
                                    onClicked: { root.exportMarkdown(); }
                                }
                                Button {
                                    text: "JSON"
                                    onClicked: { root.exportJson(); }
                                }
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "OPML"
                                    onClicked: { root.exportOpml(); }
                                }
                                Button {
                                    text: "NotesDoc"
                                    onClicked: { root.exportNotesDoc(); }
                                }
                                Button {
                                    text: "Teil ALX"
                                    onClicked: { root.exportAlx(); }
                                }
                                Button {
                                    text: "Teil TXT"
                                    onClicked: { root.exportSubtreeText(); }
                                }
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "Teil RTF"
                                    onClicked: { root.exportSubtreeRtf(); }
                                }
                                Button {
                                    text: "Sticky HTML"
                                    onClicked: { root.exportStickyHtml(); }
                                }
                                Button {
                                    text: "Bilder raus"
                                    onClicked: { root.extractImages(); }
                                }
                            }
                        }
                    }
                    Rectangle {
                        width: 1
                        color: "#dddddd"
                    }
                    Rectangle {
                        Layout.fillWidth: true  // from horizontal-stretch: 1
                        ColumnLayout {
                            spacing: 4
                            Text {
                                text: "Import / Einstellungen"
                                font.weight: 700
                                verticalAlignment: Text.AlignHCenter
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "TXT rein"
                                    onClicked: { root.importText(); }
                                }
                                Button {
                                    text: "RTF rein"
                                    onClicked: { root.importRtf(); }
                                }
                                Button {
                                    text: "JSON rein"
                                    onClicked: { root.importJson(); }
                                }
                                Button {
                                    text: "OPML rein"
                                    onClicked: { root.importOpml(); }
                                }
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "Einst."
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
                                    text: "AltCfg"
                                    onClicked: { root.importLegacyConfig(); }
                                }
                            }
                            RowLayout {
                                spacing: 4
                                Text {
                                    text: "Baum: Rechtsklick"
                                    color: "#666666"
                                    verticalAlignment: Text.AlignHCenter
                                }
                                Text {
                                    text: "Text: Rechtsklick"
                                    color: "#666666"
                                    verticalAlignment: Text.AlignHCenter
                                }
                            }
                        }
                    }
                    Rectangle {
                        width: 1
                        color: "#dddddd"
                    }
                    Rectangle {
                        Layout.fillWidth: true  // from horizontal-stretch: 1
                        ColumnLayout {
                            spacing: 4
                            Text {
                                text: "Info / Werkzeuge"
                                font.weight: 700
                                verticalAlignment: Text.AlignHCenter
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "Stats"
                                    onClicked: { root.showStats(); }
                                }
                                Button {
                                    text: "Backups"
                                    onClicked: { root.showBackups(); }
                                }
                                Button {
                                    text: "Info"
                                    onClicked: { root.showAbout(); }
                                }
                                Button {
                                    text: "Tasten"
                                    onClicked: { root.showShortcuts(); }
                                }
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "Kontext"
                                    onClicked: { root.showContextMenus(); }
                                }
                                Button {
                                    text: "Fonts"
                                    onClicked: { root.showFonts(); }
                                }
                                Button {
                                    text: "Compat"
                                    onClicked: { root.showCompatReport(); }
                                }
                                Button {
                                    text: "Pfade"
                                    onClicked: { root.showDefaultPaths(); }
                                }
                            }
                            RowLayout {
                                spacing: 4
                                Button {
                                    text: "PwInfo"
                                    onClicked: { root.showPasswordInfo(); }
                                }
                                Button {
                                    text: "Repar."
                                    onClicked: { root.repairDocument(); }
                                }
                                Button {
                                    text: "Strips"
                                    onClicked: { root.showToolstrips(); }
                                }
                            }
                        }
                    }
                }
            }
        }
        RowLayout {
            spacing: 8
            Rectangle {
                width: 320
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
                        Button {
                            text: "Ersetzen"
                            onClicked: { root.replaceText(root.searchText); }
                        }
                    }
                    RowLayout {
                        spacing: 4
                        CheckBox {
                            text: "Aa"
                            checked: root.searchCaseSensitive
                            onCheckedChanged: { root.searchCaseSensitive = checked }
                        }
                        CheckBox {
                            text: "Wort"
                            checked: root.searchWholeWords
                            onCheckedChanged: { root.searchWholeWords = checked }
                        }
                        CheckBox {
                            text: "Teilbaum"
                            checked: root.searchCurrentSubtree
                            onCheckedChanged: { root.searchCurrentSubtree = checked }
                        }
                    }
                    ListView {
                        Repeater {
                            model: root.rows
                            delegate: Rectangle {
                                property var row: modelData
                                property int i: index
                                width: parent.width
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
                                    width: parent.width
                                    height: parent.height
                                    onClicked: {
                                        root.selectRow(i)
                                        root.treeContextVisible = false
                                        root.editorContextVisible = false
                                    }
                                    // TODO(qt611-port): pointer-event(event) => {
                                    // TODO(qt611-port raw): if (event.kind == PointerEventKind.down && event.button == PointerEventButton.right) {
                                    // TODO(qt611-port raw): root.selectRow(i)
                                    // TODO(qt611-port raw): root.contextRowIndex = i
                                    // TODO(qt611-port raw): root.treeContextVisible = true
                                    // TODO(qt611-port raw): root.editorContextVisible = false
                                // TODO(qt611-port raw): }
                            // TODO(qt611-port raw): }
                        }
                    }
                }
            }
        }

        Rectangle {
            visible: root.treeContextVisible
            x: 6
            y: 88
            width: 308
            height: 428
            color: "#ffffff"
            border.color: "#8a8a8a"
            border.width: 1
            z: 20
            ColumnLayout {
                padding: 5
                spacing: 4
                Text {
                    text: "Baum-Kontext"
                    font.weight: 700
                    height: 22
                    verticalAlignment: Text.AlignHCenter
                }
                RowLayout {
                    spacing: 5
                    ColumnLayout {
                        spacing: 3
                        Text {
                            text: "Bearbeiten"
                            font.weight: 700
                            height: 20
                            verticalAlignment: Text.AlignHCenter
                        }
                        Button {
                            text: "Neu Kind"
                            onClicked: { root.addChild(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Neu daneben"
                            onClicked: { root.addSibling(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Umbenennen"
                            onClicked: { root.renameRow(root.contextRowIndex); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Kopieren"
                            onClicked: { root.copyNode(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Ausschneiden"
                            onClicked: { root.cutNode(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Einfügen"
                            onClicked: { root.pasteNode(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Duplizieren"
                            onClicked: { root.duplicateNote(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Löschen"
                            onClicked: { root.deleteNote(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Zusammenf."
                            onClicked: { root.combineSubtree(); root.treeContextVisible = false; }
                        }
                    }
                    Rectangle {
                        width: 1
                        color: "#dddddd"
                    }
                    ColumnLayout {
                        spacing: 3
                        Text {
                            text: "Ansicht / Extras"
                            font.weight: 700
                            height: 20
                            verticalAlignment: Text.AlignHCenter
                        }
                        Button {
                            text: "Auf/Zukl."
                            onClicked: { root.toggleExpand(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Alle auf"
                            onClicked: { root.expandAll(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Alle zu"
                            onClicked: { root.collapseAll(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Hoch"
                            onClicked: { root.moveUp(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Runter"
                            onClicked: { root.moveDown(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Einrücken"
                            onClicked: { root.indentNote(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Ausrücken"
                            onClicked: { root.outdentNote(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Notiz-RTF"
                            onClicked: { root.exportNoteRtf(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Sticky"
                            onClicked: { root.toggleSticky(); root.treeContextVisible = false; }
                        }
                        Button {
                            text: "Farben"
                            onClicked: { root.setColors(); root.treeContextVisible = false; }
                        }
                    }
                }
                RowLayout {
                    spacing: 4
                    Button {
                        text: "Auto-Größe"
                        onClicked: { root.autosizeSticky(); root.treeContextVisible = false; }
                    }
                    Button {
                        text: "Hell"
                        onClicked: { root.applyLightColor(); root.treeContextVisible = false; }
                    }
                    Button {
                        text: "Farbe weg"
                        onClicked: { root.clearColors(); root.treeContextVisible = false; }
                    }
                    Button {
                        text: "Schließen"
                        onClicked: { root.treeContextVisible = false; }
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
                Rectangle {
                    Layout.fillWidth: true  // from horizontal-stretch: 1
                }
                Text {
                    text: "RTF/Text-Aktionen per Rechtsklick im Textfeld"
                    verticalAlignment: Text.AlignHCenter
                    color: "#666666"
                }
            }
            Rectangle {
                Layout.fillHeight: true  // from vertical-stretch: 1
                // The TouchArea wraps the TextEdit so right-clicks in the real
                // text area can open the RTF context menu. The TextEdit remains
                // the visible/editable child; the extra right strip is only a fallback.
                MouseArea {
                    id: editor_hitbox
                    x: 0
                    y: 0
                    width: parent.width - 28
                    height: parent.height
                    // TODO(qt611-port): pointer-event(event) => {
                    // TODO(qt611-port raw): if (event.kind == PointerEventKind.down && event.button == PointerEventButton.right) {
                    // TODO(qt611-port raw): root.editorContextX = editor_hitbox.mouseX
                    // TODO(qt611-port raw): root.editorContextY = editor_hitbox.mouseY
                    // TODO(qt611-port raw): root.editorContextVisible = true
                    // TODO(qt611-port raw): root.treeContextVisible = false
                // TODO(qt611-port raw): }
            // TODO(qt611-port raw): }
            TextArea {
                id: editor
                x: 0
                y: 0
                width: parent.width
                height: parent.height
                text: root.editorText
                onTextChanged: { root.editorText = text }
                wrapMode: Text.WordWrap
                // TODO(qt611-port): edited(text) => { root.editorChanged(text); }
            }
        }
        Rectangle {
            x: parent.width - 28
            y: 0
            width: 28
            height: parent.height
            color: "#f5f5f5"
            border.color: "#dddddd"
            border.width: 1
            Text {
                width: parent.width
                height: 36
                text: "☰"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignHCenter
                font.pixelSize: 20
            }
            MouseArea {
                width: parent.width
                height: parent.height
                onClicked: {
                    root.editorContextX = parent.x - 520
                    root.editorContextY = 8
                    root.editorContextVisible = true
                    root.treeContextVisible = false
                }
                // TODO(qt611-port): pointer-event(event) => {
                // TODO(qt611-port raw): if (event.kind == PointerEventKind.down && event.button == PointerEventButton.right) {
                // TODO(qt611-port raw): root.editorContextX = parent.x - 520
                // TODO(qt611-port raw): root.editorContextY = 8
                // TODO(qt611-port raw): root.editorContextVisible = true
                // TODO(qt611-port raw): root.treeContextVisible = false
            // TODO(qt611-port raw): }
        // TODO(qt611-port raw): }
    }
}
Rectangle {
    visible: root.editorContextVisible
    x: root.editorContextX
    y: root.editorContextY
    width: 520
    height: 344
    color: "#ffffff"
    border.color: "#8a8a8a"
    border.width: 1
    z: 20
    ColumnLayout {
        padding: 5
        spacing: 4
        Text {
            text: "RTF-/Text-Kontext"
            font.weight: 700
            height: 22
            verticalAlignment: Text.AlignHCenter
        }
        RowLayout {
            spacing: 5
            ColumnLayout {
                spacing: 3
                Text {
                    text: "Bearbeiten"
                    font.weight: 700
                    height: 20
                    verticalAlignment: Text.AlignHCenter
                }
                Button {
                    text: "Kopieren"
                    onClicked: { editor.copy(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Ausschneiden"
                    onClicked: { editor.cut(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Einfügen"
                    onClicked: { editor.paste(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Alles markieren"
                    onClicked: { editor.selectAll(); }
                }
                Button {
                    text: "Löschen"
                    onClicked: { editor.cut(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Bild einfügen"
                    onClicked: { root.insertImage(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Datum einfügen"
                    onClicked: { root.appendDate(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Aufzählung"
                    onClicked: { root.appendBullet(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Suchen"
                    onClicked: { root.searchNext(root.searchText); root.editorContextVisible = false; }
                }
                Button {
                    text: "Alle Treffer"
                    onClicked: { root.searchAll(root.searchText); root.editorContextVisible = false; }
                }
                Button {
                    text: "Ersetzen"
                    onClicked: { root.replaceText(root.searchText); root.editorContextVisible = false; }
                }
            }
            Rectangle {
                width: 1
                color: "#dddddd"
            }
            ColumnLayout {
                spacing: 3
                Text {
                    text: "Format"
                    font.weight: 700
                    height: 20
                    verticalAlignment: Text.AlignHCenter
                }
                Button {
                    text: "Ganznotiz formatieren"
                    onClicked: { root.formatNote(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Fett"
                    onClicked: { root.applyBold(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Kursiv"
                    onClicked: { root.applyItalic(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Unterstrichen"
                    onClicked: { root.applyUnderline(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Durchgestrichen"
                    onClicked: { root.applyStrike(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Normal"
                    onClicked: { root.applyRegular(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Schrift größer"
                    onClicked: { root.increaseFontSize(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Schrift kleiner"
                    onClicked: { root.decreaseFontSize(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Roh-RTF/Text"
                    onClicked: { root.toggleRawRtf(); root.editorContextVisible = false; }
                }
                Button {
                    text: "Schließen"
                    onClicked: { root.editorContextVisible = false; }
                }
            }
        }
    }
}
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
