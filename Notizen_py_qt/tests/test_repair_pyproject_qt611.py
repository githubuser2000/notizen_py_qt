from __future__ import annotations

import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path


def test_repair_pyproject_removes_duplicate_dependencies_and_old_ui(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        textwrap.dedent(
            """
            [build-system]
            requires = ["setuptools>=68", "wheel"]

            [project]
            name = "notizen-py-qt"
            version = "0.1.0"
            description = "Python/Qt port"
            requires-python = ">=3.10"
            dependencies = ["rich>=13"]
            dependencies = ["PySide6>=6.11,<6.12"]

            [project.optional-dependencies]
            qt = ["qt>=1.8.0a1"]
            dev = ["pytest"]

            [project.scripts]
            notizen-py-qt = "notizen_py_qt.app:main"
            notizen-alx = "notizen_py_qt.cli:main"
            notizen-pypy-qt = "notizen_pypy_qt.app:main"

            [tool.setuptools.package-data]
            notizen_py_qt = ["ui/*.qml"]
            "notizen_py_qt.ui" = ["*.qml"]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    script = Path(__file__).resolve().parents[1] / "scripts" / "repair_pyproject_qt611.py"
    result = subprocess.run(
        [sys.executable, str(script), str(root), "--apply"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    repaired = pyproject.read_text(encoding="utf-8")
    parsed = tomllib.loads(repaired)
    assert "qt" not in repaired.lower()
    assert parsed["project"]["name"] == "notizen-py-qt"
    assert parsed["project"]["dependencies"].count("PySide6>=6.11,<6.12") == 1
    assert "rich>=13" in parsed["project"]["dependencies"]
    assert "qt" not in parsed["project"].get("optional-dependencies", {})
    assert parsed["project"]["scripts"]["notizen-py-qt"] == "notizen_py_qt.app:main"
    assert parsed["tool"]["setuptools"]["package-data"]["notizen_py_qt"] == ["ui/*.qml", "ui/*.js"]
