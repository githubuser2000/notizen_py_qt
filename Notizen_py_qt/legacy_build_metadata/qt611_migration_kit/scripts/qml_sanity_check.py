#!/usr/bin/env python3
"""Lightweight sanity checks for generated Qt/QML sources."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from qt611_project_utils import find_project_root, is_ignored_path, prune_dirnames  # noqa: E402

SUFFIXES = {".qml", ".js", ".mjs"}


def iter_qml_files(root: Path):
    root = find_project_root(root)
    if root.is_file():
        if root.suffix in SUFFIXES:
            yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        prune_dirnames(dirnames)
        if is_ignored_path(d, root):
            continue
        for filename in filenames:
            path = d / filename
            if path.suffix in SUFFIXES and not is_ignored_path(path, root):
                yield path


def check_balance(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    stack: list[tuple[str, int, int]] = []
    pairs = {"}": "{", "]": "[", ")": "("}
    line = 1
    col = 0
    in_single = False
    in_double = False
    in_block_comment = False
    in_line_comment = False
    escaped = False
    errors: list[str] = []

    for ch_index, ch in enumerate(text):
        nxt = text[ch_index + 1] if ch_index + 1 < len(text) else ""
        if ch == "\n":
            line += 1
            col = 0
            in_line_comment = False
            escaped = False
            continue
        col += 1

        if in_line_comment:
            continue
        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
            continue
        if escaped:
            escaped = False
            continue
        if ch == "\\" and (in_single or in_double):
            escaped = True
            continue
        if not in_single and not in_double and ch == "/" and nxt == "/":
            in_line_comment = True
            continue
        if not in_single and not in_double and ch == "/" and nxt == "*":
            in_block_comment = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if ch in "{[(":
            stack.append((ch, line, col))
        elif ch in "}])":
            if not stack or stack[-1][0] != pairs[ch]:
                errors.append(f"{path}:{line}:{col}: unmatched {ch}")
            else:
                stack.pop()

    if in_single or in_double:
        errors.append(f"{path}:{line}:{col}: unfinished string literal")
    if in_block_comment:
        errors.append(f"{path}:{line}:{col}: unfinished block comment")
    for opener, lno, cno in stack:
        errors.append(f"{path}:{lno}:{cno}: unclosed {opener}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = find_project_root(Path(args.root).resolve())
    errors: list[str] = []
    files = list(iter_qml_files(root))
    for path in files:
        try:
            errors.extend(check_balance(path))
        except UnicodeDecodeError as exc:
            errors.append(f"{path}: cannot decode as UTF-8: {exc}")
    print(f"Root: {root}")
    print(f"Checked {len(files)} active QML/JS file(s).")
    if errors:
        print("Sanity check failed:")
        for error in errors[:200]:
            print("-", error)
        if len(errors) > 200:
            print(f"... {len(errors) - 200} more")
        return 1
    print("OK: active QML/JS has balanced delimiters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
