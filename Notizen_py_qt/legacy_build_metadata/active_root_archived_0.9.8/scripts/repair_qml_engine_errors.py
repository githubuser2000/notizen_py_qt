#!/usr/bin/env python3
"""Repair first-order QML engine errors after the Slint -> Qt/QML migration.

This is intentionally conservative: it only edits active QML files in the
resolved project root and keeps a backup before every changed file.  The main
case it fixes is produced by Slint-to-QML conversion when a generic Qt Quick
object (Item/Rectangle/etc.) receives a property that exists only on Qt Quick
Controls, for example ``padding: 8``.  PySide/Qt reports this as:

    Cannot assign to non-existent property "padding"

For simple property assignments the script preserves the value by converting it
into a custom QML property, for example:

    padding: 8

becomes:

    property real padding: 8

This lets the QML component load while keeping the value available for later
manual layout refinement.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from qt611_project_utils import find_project_root, is_ignored_path, iter_files  # noqa: E402

ERROR_RE = re.compile(
    r"(?P<uri>file://[^:\n]+(?:/[^:\n]*)?):(?P<line>\d+):(?P<col>\d+):\s*"
    r"Cannot assign to non-existent property [\"'](?P<prop>[^\"']+)[\"']"
)
# Handles paths that contain ':' poorly represented by Qt on unusual systems.
ERROR_RE_FALLBACK = re.compile(
    r"(?P<path>/[^\n:]+(?:/[^\n:]+)*\.qml):(?P<line>\d+):(?P<col>\d+):\s*"
    r"Cannot assign to non-existent property [\"'](?P<prop>[^\"']+)[\"']"
)
ASSIGN_RE = re.compile(r"^(?P<indent>\s*)(?P<name>[A-Za-z_][A-Za-z0-9_]*):(?P<rest>.*)$")
COMMENT_RE = re.compile(r"^(?P<body>.*?)(?P<comment>\s*//.*)?$")

REAL_PROPS = {
    "padding", "leftPadding", "rightPadding", "topPadding", "bottomPadding",
    "horizontalPadding", "verticalPadding", "spacing", "margin", "leftMargin",
    "rightMargin", "topMargin", "bottomMargin", "radius", "opacity",
}
INT_PROPS = {"currentIndex", "selectedIndex", "row", "column", "count"}
BOOL_PROPS = {"checked", "expanded", "collapsed", "selected", "active", "hovered"}
STRING_HINT_PROPS = {"text", "title", "windowTitle", "placeholderText", "toolTip"}


@dataclass(frozen=True)
class EngineError:
    path: Path
    line: int
    column: int
    prop: str
    raw: str


@dataclass
class PatchAction:
    path: Path
    line: int
    before: str
    after: str
    reason: str


def uri_to_path(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        # urlparse('file:///tmp/a.qml').path -> '/tmp/a.qml'
        return Path(unquote(parsed.path))
    return Path(unquote(uri.removeprefix("file://")))


def parse_engine_errors(text: str) -> list[EngineError]:
    errors: list[EngineError] = []
    for line in text.splitlines():
        m = ERROR_RE.search(line)
        if m:
            errors.append(
                EngineError(
                    path=uri_to_path(m.group("uri")),
                    line=int(m.group("line")),
                    column=int(m.group("col")),
                    prop=m.group("prop"),
                    raw=line,
                )
            )
            continue
        m = ERROR_RE_FALLBACK.search(line)
        if m:
            errors.append(
                EngineError(
                    path=Path(m.group("path")),
                    line=int(m.group("line")),
                    column=int(m.group("col")),
                    prop=m.group("prop"),
                    raw=line,
                )
            )
    return errors


def qml_type_for_value(prop: str, value: str) -> str:
    stripped = value.strip()
    if prop in REAL_PROPS:
        return "real"
    if prop in INT_PROPS:
        return "int"
    if prop in BOOL_PROPS or stripped in {"true", "false"}:
        return "bool"
    if prop in STRING_HINT_PROPS or (len(stripped) >= 2 and stripped[0] in {'"', "'"}):
        return "string"
    # var is the safest preservation type for expressions, arrays and objects.
    return "var"


def split_comment(rest: str) -> tuple[str, str]:
    # Do not attempt a full JS lexer; this keeps normal trailing comments while
    # avoiding breakage for the common generated one-line assignments.
    m = COMMENT_RE.match(rest.rstrip("\n"))
    if not m:
        return rest.rstrip("\n"), ""
    return m.group("body").rstrip(), m.group("comment") or ""


def patch_line_for_error(line_text: str, prop: str) -> str | None:
    if prop.startswith("on") and len(prop) > 2 and prop[2:3].isupper():
        # Missing signal handlers need semantic work, not a dummy custom property.
        return None
    if "." in prop:
        # Attached/grouped properties cannot be declared as custom properties.
        return None
    m = ASSIGN_RE.match(line_text)
    if not m or m.group("name") != prop:
        return None
    rest_body, comment = split_comment(m.group("rest"))
    value = rest_body.strip()
    if not value:
        return None
    qml_type = qml_type_for_value(prop, value)
    suffix = f" {comment.strip()}" if comment.strip() else ""
    return f"{m.group('indent')}property {qml_type} {prop}: {value}{suffix}"


def backup_file(path: Path, root: Path, backup_root: Path) -> Path:
    rel = path.resolve().relative_to(root.resolve())
    target = backup_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)
    return target


def patch_file_line(path: Path, line_number: int, prop: str, root: Path, backup_root: Path, apply: bool) -> PatchAction | None:
    if not path.exists() or path.suffix != ".qml":
        return None
    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    if is_ignored_path(resolved, root):
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    if line_number < 1 or line_number > len(lines):
        return None
    before = lines[line_number - 1]
    after = patch_line_for_error(before, prop)
    if after is None or after == before:
        return None
    action = PatchAction(path=path, line=line_number, before=before, after=after, reason=f'non-existent property "{prop}"')
    if apply:
        backup_file(path, root, backup_root)
        lines[line_number - 1] = after
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return action


def find_counterpart_files(path: Path, root: Path) -> list[Path]:
    """Find mirrored QML files, e.g. qml/Main.qml and src/notizen_py_qt/ui/Main.qml."""
    candidates: list[Path] = []
    basename = path.name
    for candidate in [root / "qml" / basename, root / "src" / "notizen_py_qt" / "ui" / basename]:
        if candidate.exists() and candidate.resolve() != path.resolve():
            candidates.append(candidate)
    return candidates


def patch_counterparts(action: PatchAction, root: Path, backup_root: Path, apply: bool) -> list[PatchAction]:
    results: list[PatchAction] = []
    for counterpart in find_counterpart_files(action.path, root):
        try:
            lines = counterpart.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        # First try same line number and exact same original text.
        idx = action.line - 1
        if 0 <= idx < len(lines) and lines[idx] == action.before:
            if apply:
                backup_file(counterpart, root, backup_root)
                lines[idx] = action.after
                counterpart.write_text("\n".join(lines) + "\n", encoding="utf-8")
            results.append(PatchAction(counterpart, action.line, action.before, action.after, "mirrored QML counterpart"))
            continue
        # Fall back to the first identical assignment line.
        for i, line in enumerate(lines):
            if line == action.before:
                if apply:
                    backup_file(counterpart, root, backup_root)
                    lines[i] = action.after
                    counterpart.write_text("\n".join(lines) + "\n", encoding="utf-8")
                results.append(PatchAction(counterpart, i + 1, action.before, action.after, "mirrored QML counterpart"))
                break
    return results


def static_known_property_scan(root: Path, backup_root: Path, apply: bool) -> list[PatchAction]:
    """Conservative static pass for common generated invalid padding lines.

    This catches the exact family of errors shown by Qt without needing the smoke
    test to trip on every copy one by one.
    """
    actions: list[PatchAction] = []
    # Object types that do not provide Control-style padding.  If a future Qt
    # release adds one, the runtime-driven repair still remains safe because it
    # only fires on actual engine errors.  The static pass is opt-in.
    no_padding_types = {"Item", "Rectangle", "MouseArea", "Flickable", "ListView", "GridView", "PathView"}
    object_stack: list[tuple[int, str]] = []
    header_re = re.compile(r"^(?P<indent>\s*)(?P<type>[A-Z][A-Za-z0-9_]*)(?:\s+\w+)?\s*\{")
    for qml in iter_files(root, suffixes={".qml"}):
        lines = qml.read_text(encoding="utf-8", errors="ignore").splitlines()
        changed = False
        new_lines = lines[:]
        object_stack = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Pop approximately by indentation when blocks close.  This is not a
            # full parser but is enough for generated declarative QML.
            if stripped.startswith("}"):
                indent = len(line) - len(line.lstrip())
                while object_stack and object_stack[-1][0] >= indent:
                    object_stack.pop()
            hm = header_re.match(line)
            if hm:
                object_stack.append((len(hm.group("indent")), hm.group("type")))
            am = ASSIGN_RE.match(line)
            if not am:
                continue
            prop = am.group("name")
            if prop not in {"padding", "leftPadding", "rightPadding", "topPadding", "bottomPadding", "horizontalPadding", "verticalPadding"}:
                continue
            current_type = object_stack[-1][1] if object_stack else ""
            if current_type not in no_padding_types:
                continue
            patched = patch_line_for_error(line, prop)
            if patched and patched != line:
                if apply and not changed:
                    backup_file(qml, root, backup_root)
                new_lines[i] = patched
                changed = True
                actions.append(PatchAction(qml, i + 1, line, patched, f"static padding repair in {current_type}"))
        if apply and changed:
            qml.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return actions


def run_smoke(root: Path, python: str) -> tuple[int, str]:
    env = os.environ.copy()
    env.update({
        "QT_QPA_PLATFORM": env.get("QT_QPA_PLATFORM", "offscreen"),
        "QT_QUICK_BACKEND": env.get("QT_QUICK_BACKEND", "software"),
        "QSG_RHI_BACKEND": env.get("QSG_RHI_BACKEND", "software"),
        "NOTIZEN_QT_SMOKE_TEST": "1",
    })
    proc = subprocess.run(
        [python, "-m", "notizen_py_qt", "--smoke-test"],
        cwd=str(root),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.returncode, proc.stdout


def load_log_sources(paths: Iterable[str]) -> str:
    chunks: list[str] = []
    for p in paths:
        chunks.append(Path(p).read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def write_report(root: Path, mode: str, actions: list[PatchAction], smoke_output: str, final_rc: int) -> Path:
    report = root / "QT611_QML_ENGINE_REPAIR.md"
    lines = [
        "# Qt 6.11 QML engine repair",
        "",
        f"Mode: {mode}",
        f"Root: `{root}`",
        f"Final smoke return code: `{final_rc}`",
        "",
        "## Actions",
        "",
    ]
    if actions:
        for a in actions:
            lines.append(f"- `{a.path.relative_to(root)}`:{a.line}: {a.reason}")
            lines.append("  - before: `" + a.before.strip().replace("`", "\\`") + "`")
            lines.append("  - after: `" + a.after.strip().replace("`", "\\`") + "`")
    else:
        lines.append("- no changes")
    if smoke_output.strip():
        lines.extend(["", "## Last smoke/probe output", "", "```text", smoke_output.rstrip()[-12000:], "```"])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repair QML engine errors after Qt 6.11/PySide migration")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--run-smoke", action="store_true", help="run python -m notizen_py_qt --smoke-test and patch errors iteratively")
    parser.add_argument("--max-rounds", type=int, default=10)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--log", action="append", default=[], help="parse an existing log file for QML engine errors")
    parser.add_argument("--static-padding-pass", action="store_true", help="also patch generated padding assignments on obvious non-Control QML types")
    args = parser.parse_args(argv)

    root = find_project_root(Path(args.root).resolve())
    mode = "APPLY" if args.apply else "DRY-RUN"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = root / ".qt611_qml_engine_repair_backup" / stamp
    actions: list[PatchAction] = []
    last_output = ""
    final_rc = 0

    print(f"Mode: {mode}")
    print(f"Root: {root}")

    if args.static_padding_pass:
        static_actions = static_known_property_scan(root, backup_root, args.apply)
        actions.extend(static_actions)
        for a in static_actions:
            print(f"- static repair: {a.path}:{a.line}: {a.before.strip()} -> {a.after.strip()}")

    if args.log:
        log_text = load_log_sources(args.log)
        for err in parse_engine_errors(log_text):
            action = patch_file_line(err.path, err.line, err.prop, root, backup_root, args.apply)
            if action:
                actions.append(action)
                actions.extend(patch_counterparts(action, root, backup_root, args.apply))
                print(f"- repair from log: {action.path}:{action.line}: {action.before.strip()} -> {action.after.strip()}")
            else:
                print(f"- cannot auto-repair from log: {err.raw}")

    if args.run_smoke:
        for round_index in range(1, max(1, args.max_rounds) + 1):
            rc, out = run_smoke(root, args.python)
            last_output = out
            final_rc = rc
            print(f"\nSmoke round {round_index}: rc={rc}")
            if out.strip():
                print(out.rstrip()[-4000:])
            if rc == 0:
                break
            errors = parse_engine_errors(out)
            if not errors:
                print("- no auto-repairable 'Cannot assign to non-existent property' error found in smoke output")
                break
            repaired_this_round = 0
            for err in errors:
                action = patch_file_line(err.path, err.line, err.prop, root, backup_root, args.apply)
                if action:
                    actions.append(action)
                    counterparts = patch_counterparts(action, root, backup_root, args.apply)
                    actions.extend(counterparts)
                    repaired_this_round += 1
                    print(f"- repair: {action.path}:{action.line}: {action.before.strip()} -> {action.after.strip()}")
                else:
                    print(f"- cannot auto-repair: {err.raw}")
            if repaired_this_round == 0:
                break

    report = write_report(root, mode, actions, last_output, final_rc)
    print(f"\nWrote report: {report}")
    if args.apply and actions:
        print(f"Backups: {backup_root}")
    if args.run_smoke and final_rc != 0:
        print("\nFinished with remaining QML engine issues.")
        return final_rc
    print("\nOK: QML engine repair step finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
