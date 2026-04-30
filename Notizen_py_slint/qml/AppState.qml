pragma Singleton
import QtQml

QtObject {
    id: root
    property bool busy: false
    signal saveRequested(string arg0)
}
