#!/usr/bin/env python3
"""Harden generated QML so it can be loaded by PySide6/QQmlApplicationEngine.

This is intentionally conservative. It does not try to understand every QML
construct. It fixes the common artifacts of the Slint-to-QML generator: missing
imports, old product strings, unsafe generated file names, missing qmldir files,
and uncopied root-level QML resources.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

IGNORE_DIRS = {
    ".git", ".hg", ".svn", "target", "build", "cmake-build-debug", "cmake-build-release",
    "node_modules", ".venv", "venv", "env", ".tox", "__pycache__", ".pytest_cache", ".mypy_cache",
    "legacy_slint", "legacy_build_metadata", "dist", ".qt611_no_slint_backup",
    ".qt611_no_slint_backup_v4", ".qt611_pyproject_repair_backup",
}

REPLACEMENTS = [
    ("Notizen PyPy Slint", "Notizen PyPy Qt"),
    ("Notizen Py Slint", "Notizen Py Qt"),
    ("Python/Slint", "Python/Qt"),
    ("PyPy3/Slint", "PyPy3/Qt"),
    ("SLINT", "QT"),
    ("Slint", "Qt"),
    ("slint", "qt"),
]

CONTROL_TOKENS = {
    "ApplicationWindow", "Button", "TextField", "TextArea", "CheckBox", "ComboBox", "SpinBox",
    "Slider", "ToolBar", "ToolButton", "Menu", "MenuBar", "Action", "Dialog", "Popup", "Label",
    "ScrollView", "SplitView", "TreeView", "TableView",
}
LAYOUT_TOKENS = {"ColumnLayout", "RowLayout", "GridLayout", "StackLayout", "Layout."}
QTQUICK_TOKENS = {"Window", "Rectangle", "Text", "Image", "MouseArea", "Repeater", "ListView", "GridView", "Flickable"}
QTQML_TOKENS = {"QtObject", "ListModel", "ListElement", "Timer", "Connections"}

IDENT_RE = re.compile(r"^[A-Z][A-Za-z0-9_]*$")
IMPORT_RE = re.compile(r"^\s*import\s+([^\s]+)", re.M)


@dataclass
class Log:
    root: Path
    apply: bool
    backup_root: Path
    actions: list[str]

    def add(self, text: str) -> None:
        self.actions.append(text)

    def backup_file(self, path: Path) -> None:
        if not self.apply or not path.exists() or not path.is_file():
            return
        try:
            rel = path.relative_to(self.root)
        except ValueError:
            return
        dst = self.backup_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)

    def write_text(self, path: Path, text: str) -> None:
        old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else None
        if old == text:
            self.add(f"keep unchanged: {path}")
            return
        self.add(("update" if path.exists() else "create") + f": {path}")
        if self.apply:
            self.backup_file(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


def apply_replacements(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def should_skip_dir(path: Path) -> bool:
    return any(part in IGNORE_DIRS or part.startswith("qt611_no_slint_migration_kit") for part in path.parts)


def qml_dirs(root: Path) -> list[Path]:
    dirs: set[Path] = set()
    direct = [root / "qml", root / "src" / "notizen_py_qt" / "ui"]
    for path in direct:
        if path.exists() and any(path.glob("*.qml")):
            dirs.add(path)
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        dirnames[:] = [name for name in dirnames if name not in IGNORE_DIRS and not name.startswith("qt611_no_slint_migration_kit")]
        if should_skip_dir(d):
            continue
        if any(name.endswith(".qml") for name in filenames):
            dirs.add(d)
    return sorted(dirs)


def current_imports(text: str) -> set[str]:
    return {m.group(1) for m in IMPORT_RE.finditer(text)}


def insert_imports(text: str, imports: list[str]) -> str:
    if not imports:
        return text
    lines = text.splitlines()
    insert_at = 0
    # QML pragmas must remain before imports.
    while insert_at < len(lines) and lines[insert_at].strip().startswith(("pragma ", ".pragma ")):
        insert_at += 1
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1
    lines[insert_at:insert_at] = imports
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def needs_any(text: str, tokens: set[str]) -> bool:
    return any(token in text for token in tokens)


def harden_qml_text(text: str, filename: str) -> str:
    original_ending = "\n" if text.endswith("\n") else ""
    text = apply_replacements(text)
    imports = current_imports(text)
    required: list[str] = []

    if needs_any(text, QTQUICK_TOKENS | CONTROL_TOKENS | LAYOUT_TOKENS) and "QtQuick" not in imports:
        required.append("import QtQuick")
    if needs_any(text, CONTROL_TOKENS) and "QtQuick.Controls" not in imports:
        required.append("import QtQuick.Controls")
    if needs_any(text, LAYOUT_TOKENS) and "QtQuick.Layouts" not in imports:
        required.append("import QtQuick.Layouts")
    if needs_any(text, QTQML_TOKENS) and "QtQml" not in imports:
        required.append("import QtQml")
    if re.search(r"\b[A-Z][A-Za-z0-9_]*\.", text) and '"."' not in imports and "." not in imports:
        # This helps local generated singletons such as AppState.saveRequested(...).
        required.append('import "."')

    text = insert_imports(text, required)
    # A bare property var is legal but inconvenient for Repeater/ListView; default to an empty model.
    text = re.sub(r"(\bproperty\s+var\s+rows)(?=\s*[;\n}])", r"\1: []", text)
    text = re.sub(r"(\bproperty\s+var\s+model)(?=\s*[;\n}])", r"\1: []", text)
    return text.rstrip() + original_ending if original_ending else text


def qml_type_name(path: Path) -> str | None:
    stem = path.stem
    if "_" in stem:
        maybe = stem.split("_")[-1]
        if IDENT_RE.match(maybe):
            stem = maybe
    if IDENT_RE.match(stem):
        return stem
    return None


def normalized_qml_name(path: Path) -> str | None:
    stem = path.stem
    if "_" in stem:
        maybe = stem.split("_")[-1]
        if IDENT_RE.match(maybe):
            return f"{maybe}.qml"
    return None


def write_qmldir(directory: Path, log: Log) -> None:
    qml_files = sorted(p for p in directory.glob("*.qml") if p.is_file())
    if not qml_files:
        return
    lines = ["# Generated by Qt 6.11 migration tooling.\n"]
    used: set[str] = set()
    for path in qml_files:
        name = qml_type_name(path)
        if not name or name in used:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        prefix = "singleton " if re.search(r"^\s*pragma\s+Singleton\b", text, flags=re.M) else ""
        lines.append(f"{prefix}{name} 1.0 {path.name}\n")
        used.add(name)
    if len(lines) > 1:
        log.write_text(directory / "qmldir", "".join(lines))


def harden_qml_dir(directory: Path, log: Log) -> None:
    for path in sorted(directory.glob("*.qml")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        new = harden_qml_text(text, path.name)
        log.write_text(path, new)
        normalized = normalized_qml_name(path)
        if normalized and normalized != path.name:
            target = path.with_name(normalized)
            if not target.exists():
                log.write_text(target, new)
    for path in sorted(directory.glob("*.js")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        new = apply_replacements(text)
        log.write_text(path, new)
    write_qmldir(directory, log)


def copy_root_qml_to_package(root: Path, log: Log) -> None:
    root_qml = root / "qml"
    pkg_ui = root / "src" / "notizen_py_qt" / "ui"
    if not root_qml.exists() or not (root / "src" / "notizen_py_qt").exists():
        return
    for src in sorted(root_qml.iterdir()):
        if src.suffix not in {".qml", ".js"} and src.name != "qmldir":
            continue
        if not src.is_file():
            continue
        dst = pkg_ui / src.name
        text = src.read_text(encoding="utf-8", errors="ignore")
        if src.suffix == ".qml":
            text = harden_qml_text(text, src.name)
        else:
            text = apply_replacements(text)
        log.write_text(dst, text)
    if pkg_ui.exists() or log.apply:
        log.write_text(pkg_ui / "__init__.py", '"""Packaged QML resources for the Qt UI."""\n')
        write_qmldir(pkg_ui, log)


def write_report(root: Path, log: Log) -> None:
    report = root / "QT611_QML_HARDENING.md"
    lines = ["# QML hardening report", "", f"Mode: {'APPLY' if log.apply else 'DRY-RUN'}", f"Root: `{root}`", "", "## Actions", ""]
    lines.extend(f"- {a}" for a in log.actions)
    log.write_text(report, "\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Harden generated QML for PySide6/QQmlApplicationEngine")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log = Log(root=root, apply=args.apply, backup_root=root / ".qt611_qml_hardening_backup" / timestamp, actions=[])

    dirs = qml_dirs(root)
    if not dirs:
        log.add("no QML directories found")
    for directory in dirs:
        log.add(f"scan qml dir: {directory}")
        harden_qml_dir(directory, log)
    copy_root_qml_to_package(root, log)
    write_report(root, log)

    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Root: {root}")
    for action in log.actions:
        print(f"- {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
