#!/usr/bin/env python3
"""Summarize the Qt 6.11 migration output and remaining manual work."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

IGNORE_DIRS = {".git", "target", "build", "node_modules", ".qt611_no_qt_backup", "legacy_qt", ".venv"}
ACTIVE_SUFFIXES = {".rs", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".qml", ".js", ".toml", ".cmake"}
FORBIDDEN_RE = re.compile(r"(^|[^A-Za-z0-9_])(qt|Qt|QT|qt_build|qt-build|qt_interpreter|\.qml)([^A-Za-z0-9_]|$)")
TODO_RE = re.compile(r"TODO\(qt611-port\)")


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for filename in filenames:
            yield Path(dirpath) / filename


def load_reports(root: Path) -> list[dict]:
    reports = []
    for path in iter_files(root):
        if path.name.endswith(".qml_to_qml.report.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                data["_path"] = str(path.relative_to(root))
                reports.append(data)
            except Exception as exc:
                reports.append({"_path": str(path.relative_to(root)), "error": str(exc), "warnings": []})
    return reports


def scan_active_refs(root: Path) -> list[str]:
    hits = []
    for path in iter_files(root):
        if path.suffix not in ACTIVE_SUFFIXES and path.name not in {"CMakeLists.txt", "build.rs"}:
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
    for path in iter_files(root):
        if path.suffix not in {".qml", ".js"}:
            continue
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
    root = Path(args.root).resolve()
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
