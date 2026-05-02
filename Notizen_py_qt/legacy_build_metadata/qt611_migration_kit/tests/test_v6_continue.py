from __future__ import annotations

import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_fix_qml_hardens_imports_and_qmldir(tmp_path: Path) -> None:
    script = load_script("fix_qml_for_pyside.py")
    qml = tmp_path / "qml"
    qml.mkdir()
    (qml / "Main.qml").write_text('ApplicationWindow { title: "Notizen Py Slint"; property var rows; Button {} }\n')
    (qml / "AppState.qml").write_text("pragma Singleton\nQtObject { signal saveRequested(string title) }\n")
    assert script.main([str(tmp_path), "--apply"]) == 0
    main = (qml / "Main.qml").read_text()
    assert "import QtQuick" in main
    assert "import QtQuick.Controls" in main
    assert "Notizen Py Qt" in main
    assert "property var rows: []" in main
    qmldir = (qml / "qmldir").read_text()
    assert "singleton AppState 1.0 AppState.qml" in qmldir


def test_restore_controller_inserts_compat_after_future() -> None:
    script = load_script("restore_qt_controller_from_backup.py")
    src = textwrap.dedent(
        '''
        from __future__ import annotations
        from importlib import resources
        class NotizenSlintApp:
            def __init__(self):
                import slint
                self.slint = slint
                ui_path = resources.files("notizen_py_slint.ui").joinpath("app-window.slint")
                components = slint.load_file(str(ui_path))
                self.window = components.AppWindow()
            def load(self):
                self.window.rows = self.slint.ListModel([])
        '''
    ).lstrip()
    out = script.transform_controller(src)
    assert out.startswith("from __future__ import annotations\n")
    assert "from .qt_compat import" in out
    assert "create_qt_window()" in out
    assert "NotizenQtApp" in out
    assert "slint" not in out.lower()
    compile(out, "app.py", "exec")


def test_continue_qt611_transpile_cleans_synthetic_project(tmp_path: Path) -> None:
    (tmp_path / "src/notizen_py_slint/ui").mkdir(parents=True)
    (tmp_path / "src/notizen_pypy_slint").mkdir(parents=True)
    (tmp_path / "qml").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            '''
            [build-system]
            requires = ["setuptools>=68"]
            build-backend = "setuptools.build_meta"
            [project]
            name = "notizen-py-slint"
            description = "Python/Slint port"
            dependencies = ["click"]
            dependencies = ["slint>=1.8.0a1"]
            [project.scripts]
            notizen-py-slint = "notizen_py_slint.app:main"
            '''
        ).strip() + "\n"
    )
    (tmp_path / "src/notizen_py_slint/__init__.py").write_text('"""Python/Slint port."""\n')
    (tmp_path / "src/notizen_py_slint/app.py").write_text(
        "class NotizenSlintApp:\n    pass\n"
    )
    (tmp_path / "src/notizen_pypy_slint/__init__.py").write_text("from notizen_py_slint import *\n")
    (tmp_path / "qml/Main.qml").write_text('ApplicationWindow { title: "Notizen Py Slint"; Button {} }\n')
    script = ROOT / "scripts" / "continue_qt611_transpile.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path), "--apply", "--no-restore-controller"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stdout
    check = subprocess.run(["bash", str(ROOT / "scripts" / "check_no_slint.sh"), str(tmp_path)], text=True, stdout=subprocess.PIPE)
    assert check.returncode == 0, check.stdout
    assert (tmp_path / "src/notizen_py_qt/qt_runtime.py").exists()
    assert "Notizen Py Qt" in (tmp_path / "qml/Main.qml").read_text()
