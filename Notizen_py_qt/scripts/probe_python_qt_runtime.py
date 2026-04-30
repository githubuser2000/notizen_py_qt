#!/usr/bin/env python3
"""Probe the migrated Python/Qt package without modifying the repository."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from qt611_project_utils import find_project_root

try:
    import tomllib  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> tuple[int, str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(cmd, cwd=str(cwd), env=merged, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def print_block(title: str, body: str) -> None:
    print(f"\n## {title}")
    if body.strip():
        print(body.rstrip())
    else:
        print("OK")


def py_snippet(root: Path, code: str) -> tuple[int, str]:
    return run([sys.executable, "-c", code], cwd=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe migrated Python/Qt runtime")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--skip-smoke", action="store_true")
    args = parser.parse_args(argv)
    root = find_project_root(Path(args.root).resolve())
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version.split()[0]}")
    print(f"Root: {root}")

    errors = 0
    pyproject = root / "pyproject.toml"
    if pyproject.exists() and tomllib is not None:
        try:
            tomllib.loads(pyproject.read_text(encoding="utf-8"))
            print_block("pyproject.toml", "parse OK")
        except Exception as exc:
            errors += 1
            print_block("pyproject.toml", f"ERROR: {exc}")

    code = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path('src').resolve()))
import notizen_py_qt
print('notizen_py_qt import OK')
"""
    rc, out = py_snippet(root, code)
    print_block("package import", out)
    if rc != 0:
        errors += 1

    code = """
try:
    import PySide6
    print('PySide6', getattr(PySide6, '__version__', 'unknown'))
    from PySide6.QtCore import qVersion
    print('Qt', qVersion())
except Exception as exc:
    raise SystemExit(f'PySide6 import failed: {exc}')
"""
    rc, out = py_snippet(root, code)
    print_block("PySide6 import", out)
    if rc != 0:
        errors += 1

    qml_candidates = [root / "qml" / "Main.qml", root / "src" / "notizen_py_qt" / "ui" / "Main.qml", root / "qml" / "AppWindow.qml"]
    found_qml = [p for p in qml_candidates if p.exists()]
    print_block("QML candidates", "\n".join(str(p) for p in found_qml) if found_qml else "ERROR: no Main/AppWindow QML found")
    if not found_qml:
        errors += 1

    if not args.skip_smoke:
        env = {
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "QSG_RHI_BACKEND": "software",
            "NOTIZEN_QT_SMOKE_TEST": "1",
        }
        rc, out = run([sys.executable, "-m", "notizen_py_qt", "--smoke-test"], cwd=root, env=env)
        print_block("Qt/QML smoke test", out)
        if rc != 0:
            errors += 1

    if errors:
        print(f"\nRESULT: {errors} problem(s) found.")
        return 1
    print("\nRESULT: Python/Qt runtime probe passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
