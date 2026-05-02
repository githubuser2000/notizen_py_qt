#!/usr/bin/env python3
"""Summarize the Qt 6.11 migration output and remaining manual work."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from qt611_project_utils import find_project_root, iter_files  # noqa: E402

ACTIVE_SUFFIXES = {".rs", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".qml", ".js", ".toml", ".cmake", ".py", ".sh"}
ACTIVE_NAMES = {"CMakeLists.txt", "build.rs", "Cargo.toml", "pyproject.toml"}
FORBIDDEN_RE = re.compile(r"(^|[^A-Za-z0-9_])(slint|Slint|SLINT|slint_build|slint-build|slint_interpreter|\.slint)([^A-Za-z0-9_]|$)")
TODO_RE = re.compile(r"TODO\(qt611-port\)")


def load_reports(root: Path) -> list[dict]:
    reports = []
    for path in iter_files(root, suffixes={".json"}):
        if path.name.endswith(".slint_to_qml.report.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                data["_path"] = str(path.relative_to(root))
                reports.append(data)
            except Exception as exc:
                reports.append({"_path": str(path.relative_to(root)), "error": str(exc), "warnings": []})
    return reports


def scan_active_refs(root: Path) -> list[str]:
    hits = []
    for path in iter_files(root, suffixes=ACTIVE_SUFFIXES, names=ACTIVE_NAMES):
        if path.suffix not in ACTIVE_SUFFIXES and path.name not in ACTIVE_NAMES:
            continue
        if path.name in {
            "migrate_remove_slint_to_qt611.py", "slint_to_qml.py", "finish_python_qt_migration.py",
            "check_no_slint.sh", "check_no_slint_strict.sh", "repair_pyproject_qt611.py",
            "continue_qt611_transpile.py", "probe_python_qt_runtime.py", "restore_qt_controller_from_backup.py",
            "harden_python_qt_runtime.py", "fix_qml_for_pyside.py", "recover_misrooted_qt611_migration.py",
            "repair_qml_todo_blocks.py",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if FORBIDDEN_RE.search(line):
                hits.append(f"{path.relative_to(root)}:{lineno}: {line.strip()[:180]}")
    return hits


def count_todos(root: Path) -> tuple[int, list[str]]:
    total = 0
    samples = []
    for path in iter_files(root, suffixes={".qml", ".js", ".mjs"}):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if TODO_RE.search(line):
                total += 1
                if len(samples) < 50:
                    samples.append(f"{path.relative_to(root)}:{lineno}: {line.strip()[:180]}")
    return total, samples


def build_markdown(root: Path, reports: list[dict], active_hits: list[str], todo_total: int, todo_samples: list[str]) -> str:
    warning_total = sum(len(r.get("warnings", [])) for r in reports)
    units = {"components": 0, "globals": 0, "enums": 0, "structs": 0}
    outputs = []
    for report in reports:
        for key in units:
            units[key] += int(report.get("units", {}).get(key, 0) or 0)
        outputs.extend(report.get("outputs", []))

    lines = [
        "# Qt 6.11 Migration Status",
        "",
        f"Root: `{root}`",
        "",
        "## Summary",
        "",
        f"- Reports: {len(reports)}",
        f"- Components generated: {units['components']}",
        f"- Global singletons generated: {units['globals']}",
        f"- Enums converted to JS helpers: {units['enums']}",
        f"- Structs converted to JS helpers: {units['structs']}",
        f"- Converter warnings: {warning_total}",
        f"- Generated TODO markers: {todo_total}",
        f"- Active old-UI references: {len(active_hits)}",
        "",
    ]
    if outputs:
        lines.extend(["## Generated outputs", ""])
        for name in sorted(set(outputs)):
            lines.append(f"- `{name}`")
        lines.append("")
    if reports:
        lines.extend(["## Converter warnings", ""])
        for report in reports:
            warnings = report.get("warnings", [])
            if not warnings:
                continue
            lines.append(f"### {report.get('source', report.get('_path', '<unknown>'))}")
            lines.append("")
            for warning in warnings[:100]:
                lines.append(f"- line {warning.get('line')}: {warning.get('message')} — `{warning.get('source')}`")
            if len(warnings) > 100:
                lines.append(f"- ... {len(warnings) - 100} more")
            lines.append("")
    if todo_samples:
        lines.extend(["## Generated TODO samples", ""])
        for sample in todo_samples:
            lines.append(f"- `{sample}`")
        lines.append("")
    if active_hits:
        lines.extend(["## Active old-UI references still present", ""])
        for hit in active_hits[:200]:
            lines.append(f"- `{hit}`")
        if len(active_hits) > 200:
            lines.append(f"- ... {len(active_hits) - 200} more")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="write QT611_MIGRATION_STATUS.md")
    args = parser.parse_args()
    root = find_project_root(Path(args.root).resolve())
    reports = load_reports(root)
    active_hits = scan_active_refs(root)
    todo_total, todo_samples = count_todos(root)
    markdown = build_markdown(root, reports, active_hits, todo_total, todo_samples)
    if args.write:
        target = root / "QT611_MIGRATION_STATUS.md"
        target.write_text(markdown, encoding="utf-8")
        print(f"Wrote {target}")
    else:
        print(markdown)
    return 1 if active_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
