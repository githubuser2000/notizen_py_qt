from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_finish_python_qt_migration_cleans_project(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "src" / "notizen_py_qt" / "ui").mkdir(parents=True)
    (root / "src" / "notizen_pypy_qt").mkdir(parents=True)
    (root / "qml").mkdir()
    (root / "scripts").mkdir()

    (root / "pyproject.toml").write_text(
        """
[project]
name = "notizen-py-qt"
description = "Python/Qt port"
[project.optional-dependencies]
qt = ["qt>=1.8.0a1"]
[project.scripts]
notizen-py-qt = "notizen_py_qt.app:main"
notizen-pypy-qt = "notizen_pypy_qt.app:main"
[tool.setuptools.package-data]
notizen_py_qt = ["ui/*.qml"]
"notizen_py_qt.ui" = ["*.qml"]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "src" / "notizen_py_qt" / "__init__.py").write_text(
        '"""Python/Qt port."""\n', encoding="utf-8"
    )
    (root / "src" / "notizen_py_qt" / "app.py").write_text(
        """
def _normalize_legacy_argv(argv=None):
    return []


class NotizenQtApp:
    def __init__(self):
        import qt
        self.qml = qt
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "src" / "notizen_pypy_qt" / "__init__.py").write_text(
        "from notizen_py_qt import *\n", encoding="utf-8"
    )
    (root / "qml" / "Main.qml").write_text(
        'import QtQuick\nItem { property string titleText: "Notizen Py Qt" }\n',
        encoding="utf-8",
    )
    (root / "scripts" / "run-gui.sh").write_text(
        'exec python3 -m notizen_py_qt "$@"\n', encoding="utf-8"
    )

    script = Path(__file__).resolve().parents[1] / "scripts" / "finish_python_qt_migration.py"
    result = subprocess.run(
        [sys.executable, str(script), str(root), "--apply"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    assert (root / "src" / "notizen_py_qt" / "app.py").exists()
    assert (root / "src" / "notizen_py_qt" / "qt_backend.py").exists()
    assert (root / "src" / "notizen_py_qt" / "ui" / "Main.qml").exists()
    assert not (root / "src" / "notizen_py_qt").exists()

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "legacy" in path.parts or ".qt611_no_qt_backup_v4" in path.parts:
            continue
        if path.name in {"finish_python_qt_migration.py", "check_no_qt.sh", "check_no_qt_strict.sh"}:
            continue
        if path.suffix in {".py", ".toml", ".qml", ".sh"}:
            assert "qt" not in path.read_text(encoding="utf-8", errors="ignore").lower()
