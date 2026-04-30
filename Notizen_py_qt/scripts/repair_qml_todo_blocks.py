#!/usr/bin/env python3
"""Repair generated QML TODO blocks that still contain live Slint-style braces.

The Slint-to-QML converter intentionally leaves unsupported callback syntax as
TODO comments. Some generated blocks looked like:

    // TODO(qt611-port): pointer-event(event) => {
        root.someAction()
    }

The opening brace is in a comment, but the closing brace is live QML and breaks
parsing. This script comments the raw block body as well.
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

from qt611_project_utils import find_project_root, is_ignored_path, prune_dirnames  # noqa: E402


SUFFIXES = {".qml", ".js", ".mjs"}


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
        rel = path.relative_to(self.root)
        dst = self.backup_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)

    def write(self, path: Path, text: str) -> None:
        old = path.read_text(encoding="utf-8", errors="ignore")
        if old == text:
            return
        self.add(f"repair QML TODO/balance: {path}")
        if self.apply:
            self.backup(path)
            path.write_text(text, encoding="utf-8")


def iter_qml(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        prune_dirnames(dirnames)
        if is_ignored_path(d, root):
            continue
        for filename in filenames:
            p = d / filename
            if p.suffix in SUFFIXES and not is_ignored_path(p, root):
                yield p


def brace_delta(line: str) -> int:
    # Good enough for generated TODO snippets. These lines are not compiled
    # after this script comments them out.
    return line.count("{") - line.count("}")


def comment_line(line: str, prefix: str = "TODO(qt611-port raw)") -> str:
    nl = "\n" if line.endswith("\n") else ""
    body = line[:-1] if nl else line
    if not body.strip():
        return line
    if body.lstrip().startswith("//"):
        return line
    indent = body[: len(body) - len(body.lstrip())]
    return f"{indent}// {prefix}: {body.lstrip()}{nl}"


def comment_todo_blocks(text: str) -> str:
    out: list[str] = []
    depth = 0
    for line in text.splitlines(keepends=True):
        if depth > 0:
            out.append(comment_line(line))
            depth += brace_delta(line)
            if depth <= 0:
                depth = 0
            continue

        out.append(line)
        if "TODO(qt611-port)" in line and "=>" in line and "{" in line:
            d = brace_delta(line)
            if d > 0:
                depth = d
    return "".join(out)


def unmatched_closing_lines(text: str) -> set[int]:
    stack: list[str] = []
    pairs = {"}": "{", "]": "[", ")": "("}
    bad: set[int] = set()
    line = 1
    in_single = in_double = in_block = in_line = escaped = False
    for i, ch in enumerate(text):
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if ch == "\n":
            line += 1
            in_line = False
            escaped = False
            continue
        if in_line:
            continue
        if in_block:
            if ch == "*" and nxt == "/":
                in_block = False
            continue
        if escaped:
            escaped = False
            continue
        if ch == "\\" and (in_single or in_double):
            escaped = True
            continue
        if not in_single and not in_double and ch == "/" and nxt == "/":
            in_line = True
            continue
        if not in_single and not in_double and ch == "/" and nxt == "*":
            in_block = True
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
            stack.append(ch)
        elif ch in "}])":
            if not stack or stack[-1] != pairs[ch]:
                bad.add(line)
            else:
                stack.pop()
    return bad


def comment_unmatched_standalone_closers(text: str) -> str:
    bad = unmatched_closing_lines(text)
    if not bad:
        return text
    out: list[str] = []
    for lineno, line in enumerate(text.splitlines(keepends=True), start=1):
        stripped = line.strip()
        if lineno in bad and re.fullmatch(r"[}\])]+;?,?", stripped):
            out.append(comment_line(line, prefix="TODO(qt611-port unmatched closer)"))
        else:
            out.append(line)
    return "".join(out)


def repair_text(text: str) -> str:
    text = comment_todo_blocks(text)
    text = comment_unmatched_standalone_closers(text)
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repair generated QML TODO blocks after Slint-to-QML conversion")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    root = find_project_root(Path(args.root).resolve())
    log = Log(root=root, apply=args.apply, backup_root=root / ".qt611_qml_todo_repair_backup" / datetime.now().strftime("%Y%m%d-%H%M%S"), actions=[])

    for path in iter_qml(root):
        old = path.read_text(encoding="utf-8", errors="ignore")
        new = repair_text(old)
        log.write(path, new)

    report = root / "QT611_QML_TODO_REPAIR.md"
    lines = [
        "# QML TODO block repair",
        "",
        f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}",
        f"Root: `{root}`",
        "",
        "## Actions",
        "",
        *[f"- {a}" for a in log.actions],
    ]
    if args.apply:
        report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Root: {root}")
    if log.actions:
        for action in log.actions:
            print(f"- {action}")
    else:
        print("OK: no generated QML TODO brace blocks needed repair.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
