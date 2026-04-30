import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from slint_to_qml import transpile_text, transpile_file  # noqa: E402


SAMPLE = '''
import { Button, VerticalBox, LineEdit } from "std-widgets.slint";

export component MainWindow inherits Window {
    in property <string> title-text: "Notizen";
    callback transpile-requested(string);
    width: 800px;
    background: #112233;
    VerticalBox {
        Text { text: root.title-text; font-size: 20px; }
        Button { text: "Go"; clicked => { root.transpile-requested(root.title-text); } }
        for row[i] in rows: Text { text: row.title; }
        if root.title-text != "": Text { text: root.title-text; }
    }
}
'''


ADVANCED = '''
export enum Theme { Light, Dark = 2 }

export struct TodoItem {
    title: string,
    done: bool,
}

export global AppState {
    in-out property <bool> busy: false;
    callback save-requested(string);
}

export component MainWindow inherits Window {
    in-out property <string> title-text <=> titleField.text;
    in property <[TodoItem]> rows;
    width: 50%;
    titleField := LineEdit {
        text <=> root.title-text;
        placeholder-text: @tr("Titel");
    }
    animate opacity { duration: 250ms; }
}
'''


class SlintToQmlTests(unittest.TestCase):
    def test_transpile_common_constructs(self):
        result = transpile_text(SAMPLE, "sample.slint")
        self.assertIn("MainWindow.qml", result.outputs)
        qml = result.outputs["MainWindow.qml"]
        self.assertIn("ApplicationWindow {", qml)
        self.assertIn("visible: true", qml)
        self.assertIn("property string titleText", qml)
        self.assertIn("signal transpileRequested(string arg0)", qml)
        self.assertIn('color: "#112233"', qml)
        self.assertIn("ColumnLayout {", qml)
        self.assertIn("onClicked: { root.transpileRequested(root.titleText); }", qml)
        self.assertIn("Repeater {", qml)
        self.assertIn("visible: root.titleText != \"\"", qml)

    def test_transpile_file_writes_main_alias_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "main.slint"
            out_dir = tmp_path / "qml"
            source.write_text(SAMPLE, encoding="utf-8")
            result = transpile_file(source, out_dir, overwrite=True)
            self.assertTrue((out_dir / "MainWindow.qml").exists())
            self.assertTrue((out_dir / "Main.qml").exists())
            self.assertTrue((out_dir / "main.slint_to_qml.report.json").exists())
            self.assertIn("Main.qml", result.outputs)

    def test_transpile_v3_global_struct_enum_bindings_and_animation(self):
        result = transpile_text(ADVANCED, "advanced.slint")
        self.assertEqual(result.units["globals"], 1)
        self.assertEqual(result.units["structs"], 1)
        self.assertEqual(result.units["enums"], 1)
        self.assertIn("AppState.qml", result.outputs)
        self.assertIn("pragma Singleton", result.outputs["AppState.qml"])
        self.assertIn("signal saveRequested(string arg0)", result.outputs["AppState.qml"])
        self.assertIn("Qt611Types.js", result.outputs)
        self.assertIn("var Theme = Object.freeze", result.outputs["Qt611Types.js"])
        self.assertIn("function makeTodoItem(values)", result.outputs["Qt611Types.js"])
        qml = result.outputs["MainWindow.qml"]
        self.assertIn("property alias titleText: titleField.text", qml)
        self.assertIn("property var rows", qml)
        self.assertIn("width: 0.5", qml)
        self.assertIn("id: titleField", qml)
        self.assertIn("text: root.titleText", qml)
        self.assertIn("onTextChanged: { root.titleText = text }", qml)
        self.assertIn('placeholderText: qsTr("Titel")', qml)
        self.assertIn("Behavior on opacity", qml)
        self.assertIn("NumberAnimation", qml)
        self.assertIn("duration: 250", qml)


if __name__ == "__main__":
    unittest.main()
