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


if __name__ == "__main__":
    unittest.main()
