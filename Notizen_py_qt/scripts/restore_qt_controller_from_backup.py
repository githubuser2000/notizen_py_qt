#!/usr/bin/env python3
"""Recover the old Python controller from migration backups and port it to Qt.

v4/v5 intentionally installed a minimal Qt runner so the package would import.
For a real application, the old controller methods are valuable. This script
finds the backed-up app.py, removes the legacy UI loader, replaces it with a
Qt-compatible dynamic window proxy, and writes the result back as the active
``notizen_py_qt.app`` controller.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from qt611_project_utils import find_project_root

BACKUP_DIRS = [
    ".qt611_no_slint_backup_v4",
    ".qt611_no_slint_backup",
    ".qt611_runtime_backup",
]

REPLACEMENTS = [
    ("notizen_py_slint", "notizen_py_qt"),
    ("notizen_pypy_slint", "notizen_pypy_qt"),
    ("notizen-py-slint", "notizen-py-qt"),
    ("notizen-pypy-slint", "notizen-pypy-qt"),
    ("NotizenSlintApp", "NotizenQtApp"),
    ("_format_slint_compile_error", "_format_qt_load_error"),
    ("SLINT_FULLSCREEN", "QT_FULLSCREEN"),
    ("app-window.slint", "Main.qml"),
    (".slint", ".qml"),
    ("Python/Slint", "Python/Qt"),
    ("PyPy3/Slint", "PyPy3/Qt"),
    ("Slint", "Qt"),
    ("SLINT", "QT"),
    ("slint", "qt"),
]

SKIP_TOKENS = [
    "import slint",
    "self.slint = slint",
    "components = slint.load_file",
    "components = qt.load_file",
    "slint.load_file",
    "qt.load_file",
]

BOOTSTRAP = [
    "from .qt_compat import QtCompatNamespace, create_qt_window\n",
    "self.qt = QtCompatNamespace()\n",
    "self.window = create_qt_window()\n",
]


@dataclass
class Log:
    root: Path
    apply: bool
    backup_root: Path
    actions: list[str]

    def add(self, text: str) -> None:
        self.actions.append(text)

    def backup(self, path: Path) -> None:
        if not self.apply or not path.exists():
            return
        try:
            rel = path.relative_to(self.root)
        except ValueError:
            return
        dst = self.backup_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)

    def write(self, path: Path, text: str) -> None:
        old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else None
        if old == text:
            self.add(f"keep unchanged: {path}")
            return
        self.add(("update" if path.exists() else "create") + f": {path}")
        if self.apply:
            self.backup(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


def apply_replacements(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def latest_backup_app(root: Path) -> Path | None:
    candidates: list[Path] = []
    for dirname in BACKUP_DIRS:
        base = root / dirname
        if not base.exists():
            continue
        for path in base.rglob("app.py"):
            if "notizen_py_slint" in str(path) or "notizen_py_qt" in str(path):
                text = path.read_text(encoding="utf-8", errors="ignore")
                if "class NotizenSlintApp" in text or "class NotizenQtApp" in text or "slint.load_file" in text or "qt.load_file" in text:
                    candidates.append(path)
    if not candidates:
        # If the user runs this before v4/v5, use the active old package as source.
        direct = root / "src" / "notizen_py_slint" / "app.py"
        if direct.exists():
            return direct
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def transform_controller(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    skipping_loader = False
    bootstrap_written = False
    skip_indent = ""

    for line in lines:
        stripped = line.strip()
        # Skip the old diagnostic helper body if it explicitly formats old UI compiler errors.
        if any(token in line for token in SKIP_TOKENS):
            if not bootstrap_written and "import slint" in line:
                base = indent_of(line)
                out.extend(base + part for part in BOOTSTRAP)
                bootstrap_written = True
            skipping_loader = True
            skip_indent = indent_of(line)
            continue
        if skipping_loader:
            # Consume the old try/except loader until the instantiated window line or
            # until the indentation returns to the surrounding method body.
            if "self.window" in line and ("components." in line or "AppWindow" in line):
                skipping_loader = False
                continue
            if stripped.startswith("except ") or stripped.startswith("try:") or stripped.startswith("raise RuntimeError"):
                continue
            if stripped.startswith("ui_path") or stripped.startswith("components") or "resources.files" in line or "joinpath" in line:
                continue
            # Stop skipping once regular controller initialization resumes.
            if skip_indent and indent_of(line) == skip_indent and stripped and not stripped.startswith(("except", "try", "raise", "ui_path", "components")):
                skipping_loader = False
            else:
                continue
        out.append(line)

    transformed = "".join(out)
    transformed = apply_replacements(transformed)

    # Make ListModel calls use the compatibility namespace.
    transformed = transformed.replace("self.qt.ListModel", "self.qt.ListModel")
    transformed = re.sub(r"\bqt\.ListModel\b", "QtCompatNamespace.ListModel", transformed)

    def insert_after_future(source: str, import_line: str) -> str:
        future = "from __future__ import annotations\n"
        if future in source:
            return source.replace(future, future + import_line, 1)
        return import_line + source

    imports_to_add = ""
    if "from .qt_runtime import run_qml_app" not in transformed:
        # This does not have to be used directly, but ensures runtime import errors
        # surface early during byte-compilation.
        imports_to_add += "\nfrom .qt_runtime import run_qml_app\n"
    if "from .qt_compat import" not in transformed:
        imports_to_add += "from .qt_compat import QtCompatNamespace, create_qt_window\n"
    if imports_to_add:
        transformed = insert_after_future(transformed, imports_to_add)

    # If the legacy main still calls an old environment variable, make smoke tests work.
    transformed = transformed.replace("QT_FULLSCREEN", "QT_FULLSCREEN")
    if "--smoke-test" not in transformed and "parser.add_argument" in transformed:
        transformed = transformed.replace(
            "args = parser.parse_args(_normalize_legacy_argv(argv))",
            "parser.add_argument(\"--smoke-test\", action=\"store_true\", help=\"QML laden und ohne Eventloop beenden\")\n    args = parser.parse_args(_normalize_legacy_argv(argv))",
        )
    # Convert the final event-loop call when the old code had a main() function.
    transformed = transformed.replace("return app.run()", "return app.run(smoke_test=getattr(args, 'smoke_test', False))")
    transformed = transformed.replace("app.window.run()", "app.window.run()")
    return transformed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restore and port the old Python controller from migration backups")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--force", action="store_true", help="overwrite app.py even if the source backup is small")
    args = parser.parse_args(argv)
    root = find_project_root(Path(args.root).resolve())
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log = Log(root=root, apply=args.apply, backup_root=root / ".qt611_controller_restore_backup" / timestamp, actions=[])
    source = latest_backup_app(root)
    target = root / "src" / "notizen_py_qt" / "app.py"

    if source is None:
        log.add("no backed-up legacy controller found; keeping current Qt runner")
    elif not target.parent.exists():
        log.add(f"target package missing; skipped controller restore: {target.parent}")
    else:
        source_text = source.read_text(encoding="utf-8", errors="ignore")
        if not args.force and len(source_text.splitlines()) < 120:
            log.add(f"backup controller too small, skipped: {source}")
        else:
            new = transform_controller(source_text)
            # Keep an importable fallback runner if the old controller still needs hand work.
            current = target.read_text(encoding="utf-8", errors="ignore") if target.exists() else ""
            if "Qt/QML runner for the migrated Notizen UI" in current or "Qt/QML application runner" in current:
                log.write(target.with_name("qml_runner.py"), current)
            log.add(f"restore source: {source}")
            log.write(target, new)

    report = root / "QT611_CONTROLLER_RESTORE.md"
    lines = ["# Qt controller restore", "", f"Mode: {'APPLY' if log.apply else 'DRY-RUN'}", f"Root: `{root}`", "", "## Actions", ""]
    lines.extend(f"- {a}" for a in log.actions)
    log.write(report, "\n".join(lines) + "\n")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Root: {root}")
    for action in log.actions:
        print(f"- {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
