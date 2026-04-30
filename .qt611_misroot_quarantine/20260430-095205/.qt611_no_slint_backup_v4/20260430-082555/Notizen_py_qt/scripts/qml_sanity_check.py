#!/usr/bin/env python3
"""Lightweight sanity checks for generated Qt/QML sources.

This is deliberately not a QML compiler. It catches common migration mistakes
before CMake: unbalanced braces/brackets/parentheses and unfinished strings in
.qml/.js files.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

IGNORE_DIRS = {".git", "target", "build", "node_modules", ".qt611_no_slint_backup", "legacy_slint", ".venv"}
SUFFIXES = {".qml", ".js", ".mjs"}


def iter_qml_files(root: Path):
    if root.is_file():
        if root.suffix in SUFFIXES:
            yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix in SUFFIXES:
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
    root = Path(args.root).resolve()
    errors: list[str] = []
    files = list(iter_qml_files(root))
    for path in files:
        try:
            errors.extend(check_balance(path))
        except UnicodeDecodeError as exc:
            errors.append(f"{path}: cannot decode as UTF-8: {exc}")
    print(f"Checked {len(files)} QML/JS file(s).")
    if errors:
        print("Sanity check failed:")
        for error in errors[:200]:
            print("-", error)
        if len(errors) > 200:
            print(f"... {len(errors) - 200} more")
        return 1
    print("OK: generated QML/JS has balanced delimiters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
