#!/usr/bin/env python3
"""Shared helpers for the Qt 6.11 / no-Slint migration scripts."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence

IGNORE_DIR_NAMES = {
    ".git", ".hg", ".svn",
    "target", "build", "cmake-build-debug", "cmake-build-release",
    "node_modules", ".venv", "venv", "env", ".tox",
    ".mypy_cache", ".pytest_cache", "__pycache__",
    "legacy_slint", "legacy_build_metadata", "dist",
}

IGNORE_PREFIXES = (
    ".qt611",
    "qt611_no_slint_migration_kit",
)

TEXT_SUFFIXES = {
    ".py", ".rs", ".cpp", ".cc", ".cxx", ".h", ".hpp",
    ".qml", ".js", ".mjs", ".toml", ".cmake", ".sh",
    ".json", ".md", ".rst", ".txt", ".desktop", ".plist",
    ".service", ".spec", ".yml", ".yaml",
}

TEXT_NAMES = {"CMakeLists.txt", "build.rs", "Cargo.toml", "pyproject.toml", "MANIFEST.in"}


def should_skip_dir_name(name: str) -> bool:
    return (
        name in IGNORE_DIR_NAMES
        or name.endswith(".egg-info")
        or any(name.startswith(prefix) for prefix in IGNORE_PREFIXES)
    )


def is_ignored_path(path: Path, root: Path | None = None) -> bool:
    try:
        parts = path.relative_to(root).parts if root is not None else path.parts
    except ValueError:
        parts = path.parts
    return any(should_skip_dir_name(part) for part in parts)


def prune_dirnames(dirnames: list[str]) -> None:
    dirnames[:] = [name for name in dirnames if not should_skip_dir_name(name)]


def is_text_file(path: Path) -> bool:
    return path.name in TEXT_NAMES or path.suffix in TEXT_SUFFIXES


def iter_files(root: Path, *, suffixes: set[str] | None = None, names: set[str] | None = None) -> Iterable[Path]:
    root = root.resolve()
    if root.is_file():
        if not is_ignored_path(root.parent) and (suffixes is None or root.suffix in suffixes or root.name in (names or set())):
            yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        prune_dirnames(dirnames)
        if is_ignored_path(d, root):
            continue
        for filename in filenames:
            path = d / filename
            if is_ignored_path(path, root):
                continue
            if suffixes is None and names is None:
                yield path
            elif path.suffix in (suffixes or set()) or path.name in (names or set()):
                yield path


def _pyproject_score(path: Path) -> int:
    root = path.parent
    score = 0
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        text = ""
    if "[project]" in text:
        score += 5
    if "notizen" in text:
        score += 5
    if "notizen_py_qt" in text or "notizen-py-qt" in text:
        score += 20
    if "notizen_py_slint" in text or "notizen-py-slint" in text:
        score += 15
    if (root / "src" / "notizen_py_qt").exists():
        score += 25
    if (root / "src" / "notizen_py_slint").exists():
        score += 20
    if (root / "qml").exists():
        score += 3
    if should_skip_dir_name(root.name):
        score -= 100
    return score


def find_project_root(input_root: str | Path) -> Path:
    """Return the real Python project root.

    The migration kit is often executed from a parent folder. This helper follows
    pyproject.toml instead of blindly trusting the argument, so a call like
    ``scripts/... ..`` can still land on ``../Notizen_py_slint``.
    """
    root = Path(input_root).expanduser().resolve()
    if root.name == "pyproject.toml" and root.is_file():
        return root.parent
    if (root / "pyproject.toml").is_file():
        return root

    candidates: list[Path] = []
    max_depth = 4
    if root.exists() and root.is_dir():
        for dirpath, dirnames, filenames in os.walk(root):
            d = Path(dirpath)
            prune_dirnames(dirnames)
            try:
                depth = len(d.relative_to(root).parts)
            except ValueError:
                depth = 99
            if depth >= max_depth:
                dirnames[:] = []
            if "pyproject.toml" in filenames and not is_ignored_path(d, root):
                candidates.append(d / "pyproject.toml")

    if not candidates:
        return root

    candidates.sort(key=lambda p: (_pyproject_score(p), -len(p.parts)), reverse=True)
    return candidates[0].parent


def describe_root_choice(input_root: str | Path) -> str:
    raw = Path(input_root).expanduser().resolve()
    project = find_project_root(raw)
    if project == raw:
        return f"Project root: {project}"
    return f"Input root: {raw}\nDetected project root: {project}"
