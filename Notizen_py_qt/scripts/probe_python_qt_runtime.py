#!/usr/bin/env python3
"""Probe the active Notizen Python/Qt package without modifying the repository."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


def find_project_root(start: Path) -> Path:
    start = start.expanduser().resolve()
    if start.name == "pyproject.toml" and start.is_file():
        return start.parent
    if start.is_file():
        start = start.parent
    cur = start
    while True:
        if (cur / "pyproject.toml").is_file() and (cur / "src" / "notizen_py_qt").is_dir():
            return cur
        if cur.parent == cur:
            return start
        cur = cur.parent


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> tuple[int, str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(cmd, cwd=str(cwd), env=merged, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def print_block(title: str, body: str) -> None:
    print(f"\n## {title}")
    print(body.rstrip() if body.strip() else "OK")


def _python_cmd(*args: str) -> list[str]:
    cmd = [sys.executable]
    if getattr(sys.flags, "no_site", 0):
        cmd.append("-S")
    cmd.extend(args)
    return cmd


def py_snippet(root: Path, code: str) -> tuple[int, str]:
    return run(_python_cmd("-c", code), cwd=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe Notizen Python/Qt runtime")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--skip-smoke", action="store_true", help="do not start the Qt smoke test")
    parser.add_argument("--skip-qt", action="store_true", help="skip Qt binding import checks for headless validation hosts")
    args = parser.parse_args(argv)

    root = find_project_root(Path(args.root))
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version.split()[0]}")
    print(f"Root: {root}")

    errors = 0
    pyproject = root / "pyproject.toml"
    if pyproject.exists() and tomllib is not None:
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            project = data.get("project", {})
            if project.get("name") != "notizen-py-qt":
                raise ValueError(f"unexpected project name: {project.get('name')!r}")
            print_block("pyproject.toml", "parse OK")
        except Exception as exc:
            errors += 1
            print_block("pyproject.toml", f"ERROR: {exc}")

    code = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path('src').resolve()))
import notizen_py_qt
from notizen_py_qt.models import NoteDocument, NoteNode
from notizen_py_qt.alx_io import dump_alx_bytes, load_alx_bytes
from notizen_py_qt.rtf_utils import plain_text_to_rtf, rtf_to_plain_text
node = NoteNode(title='probe', rtf=plain_text_to_rtf('äöü € 😀'))
doc = NoteDocument(root=node)
loaded = load_alx_bytes(dump_alx_bytes(doc))
assert loaded.root is not None
assert rtf_to_plain_text(loaded.root.rtf) == 'äöü € 😀'
print('notizen_py_qt import, RTF and ALX roundtrip OK')
"""
    rc, out = py_snippet(root, code)
    print_block("package import / data roundtrip", out)
    if rc != 0:
        errors += 1

    if not args.skip_qt:
        code = """
try:
    from notizen_py_qt.qt_compat import load_qt
    binding, QtCore, QtGui, QtWidgets = load_qt()
    print(binding)
    print('Qt', QtCore.qVersion())
except Exception as exc:
    raise SystemExit(f'Qt binding import failed: {exc}')
"""
        rc, out = py_snippet(root, code)
        print_block("Qt binding import", out)
        if rc != 0:
            errors += 1
    else:
        print_block("Qt binding import", "SKIPPED (--skip-qt)")

    if not args.skip_smoke and not args.skip_qt:
        env = {"QT_QPA_PLATFORM": "offscreen", "NOTIZEN_QT_SMOKE_TEST": "1"}
        rc, out = run(_python_cmd("-m", "notizen_py_qt", "--smoke-test"), cwd=root, env=env)
        print_block("Qt smoke test", out)
        if rc != 0:
            errors += 1

    if errors:
        print(f"\nRESULT: {errors} problem(s) found.")
        return 1
    print("\nRESULT: Python/Qt runtime probe passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
