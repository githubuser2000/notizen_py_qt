from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_finish_python_qt_migration_cleans_project(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "src" / "notizen_py_slint" / "ui").mkdir(parents=True)
    (root / "src" / "notizen_pypy_slint").mkdir(parents=True)
    (root / "qml").mkdir()
    (root / "scripts").mkdir()

    (root / "pyproject.toml").write_text(
        """
[project]
name = "notizen-py-slint"
description = "Python/Slint port"
[project.optional-dependencies]
slint = ["slint>=1.8.0a1"]
[project.scripts]
notizen-py-slint = "notizen_py_slint.app:main"
notizen-pypy-slint = "notizen_pypy_slint.app:main"
[tool.setuptools.package-data]
notizen_py_slint = ["ui/*.slint"]
"notizen_py_slint.ui" = ["*.slint"]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "src" / "notizen_py_slint" / "__init__.py").write_text(
        '"""Python/Slint port."""\n', encoding="utf-8"
    )
    (root / "src" / "notizen_py_slint" / "app.py").write_text(
        """
def _normalize_legacy_argv(argv=None):
    return []


class NotizenSlintApp:
    def __init__(self):
        import slint
        self.slint = slint
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "src" / "notizen_pypy_slint" / "__init__.py").write_text(
        "from notizen_py_slint import *\n", encoding="utf-8"
    )
    (root / "qml" / "Main.qml").write_text(
        'import QtQuick\nItem { property string titleText: "Notizen Py Slint" }\n',
        encoding="utf-8",
    )
    (root / "scripts" / "run-gui.sh").write_text(
        'exec python3 -m notizen_py_slint "$@"\n', encoding="utf-8"
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
    assert not (root / "src" / "notizen_py_slint").exists()

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "legacy" in path.parts or ".qt611_no_slint_backup_v4" in path.parts:
            continue
        if path.name in {"finish_python_qt_migration.py", "check_no_slint.sh", "check_no_slint_strict.sh"}:
            continue
        if path.suffix in {".py", ".toml", ".qml", ".sh"}:
            assert "slint" not in path.read_text(encoding="utf-8", errors="ignore").lower()
