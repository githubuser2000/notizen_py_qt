#!/usr/bin/env python3
"""Repair pyproject.toml after the Python legacy-UI -> Qt migration.

The previous migrator could create duplicate TOML keys when a project already
had a one-line dependencies entry. This script is line based so it can repair a
currently invalid TOML file that tomllib refuses to parse.
"""
from __future__ import annotations

import argparse
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
from typing import Iterable, Sequence

try:
    import tomllib  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

REPLACEMENTS = [
    (".slint", ".qml"),
    ("notizen-py-slint-subtree", "notizen-py-qt-subtree"),
    ("notizen-py-slint-node-clipboard", "notizen-py-qt-node-clipboard"),
    ("notizen_py_slint", "notizen_py_qt"),
    ("notizen_pypy_slint", "notizen_pypy_qt"),
    ("notizen-py-slint", "notizen-py-qt"),
    ("notizen-pypy-slint", "notizen-pypy-qt"),
    ("Python/Slint", "Python/Qt"),
    ("PyPy3/Slint", "PyPy3/Qt"),
    ("Slint", "Qt"),
    ("SLINT", "QT"),
    ("slint", "qt"),
]
PYSIDE_SPEC = "PySide6>=6.11,<6.12"
SECTION_RE = re.compile(r"^\s*\[[^\]]+\]\s*(?:#.*)?$")
KEY_RE = re.compile(r"^(?P<indent>\s*)(?P<key>(?:[A-Za-z0-9_-]+|\"[^\"]+\"|'[^']+'))\s*=")
QUOTED_VALUE_RE = re.compile(r"[\"']([^\"']+)[\"']")


@dataclass
class Section:
    header: str | None
    lines: list[str]

    @property
    def name(self) -> str | None:
        if self.header is None:
            return None
        clean = self.header.strip().split("#", 1)[0].strip()
        return clean[1:-1].strip()


def apply_replacements(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def split_sections(text: str) -> list[Section]:
    sections: list[Section] = []
    current = Section(header=None, lines=[])
    for line in text.splitlines(keepends=True):
        if SECTION_RE.match(line):
            sections.append(current)
            current = Section(header=line, lines=[])
        else:
            current.lines.append(line)
    sections.append(current)
    return sections


def join_sections(sections: Sequence[Section]) -> str:
    out: list[str] = []
    for section in sections:
        if section.header is not None:
            out.append(section.header)
        out.extend(section.lines)
    return "".join(out)


def key_name(line: str) -> str | None:
    match = KEY_RE.match(line)
    if not match:
        return None
    key = match.group("key").strip()
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1]
    return key


def statement_end(lines: Sequence[str], start: int) -> int:
    if "=" not in lines[start]:
        return start + 1
    balance = 0
    seen_bracket = False
    i = start
    while i < len(lines):
        code = lines[i].split("#", 1)[0]
        balance += code.count("[") + code.count("{") + code.count("(")
        balance -= code.count("]") + code.count("}") + code.count(")")
        seen_bracket = seen_bracket or any(ch in code for ch in "[{(")
        i += 1
        if not seen_bracket or balance <= 0:
            break
    return i


def statement_text(lines: Sequence[str], start: int) -> str:
    return "".join(lines[start:statement_end(lines, start)])


def extract_quoted_values(text: str) -> list[str]:
    return [m.group(1).strip() for m in QUOTED_VALUE_RE.finditer(text)]


def is_legacy_dependency(value: str) -> bool:
    lower = value.lower()
    if "pyside6" in lower:
        return False
    return "slint" in lower or lower.startswith("qt>=1.8") or lower.startswith("qt==1.8") or lower.startswith("qt~=1.8")


def unique_dependencies(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    has_pyside = False
    for value in values:
        value = value.strip()
        if not value or is_legacy_dependency(value):
            continue
        if value.lower().startswith("pyside6"):
            has_pyside = True
            value = PYSIDE_SPEC
        key = value.lower()
        if key not in seen:
            seen.add(key)
            out.append(value)
    if not has_pyside:
        out.append(PYSIDE_SPEC)
    return out


def format_array_assignment(key: str, values: Sequence[str]) -> list[str]:
    if not values:
        return [f"{key} = []\n"]
    return [f"{key} = [\n", *[f'    "{value}",\n' for value in values], "]\n"]


def rewrite_project(lines: list[str]) -> list[str]:
    kept: list[str] = []
    deps: list[str] = []
    i = 0
    while i < len(lines):
        if key_name(lines[i]) == "dependencies":
            deps.extend(extract_quoted_values(statement_text(lines, i)))
            i = statement_end(lines, i)
            continue
        kept.append(lines[i])
        i += 1
    dependencies = format_array_assignment("dependencies", unique_dependencies(deps))
    insert_at = len(kept)
    while insert_at > 0 and kept[insert_at - 1].strip() == "":
        insert_at -= 1
    if insert_at > 0 and kept[insert_at - 1].strip() != "":
        dependencies = ["\n", *dependencies]
    kept[insert_at:insert_at] = dependencies
    return kept


def rewrite_optional_dependencies(lines: list[str]) -> list[str]:
    kept: list[str] = []
    i = 0
    while i < len(lines):
        key = key_name(lines[i])
        if key is not None:
            text = statement_text(lines, i)
            lower_text = text.lower()
            lower_key = key.lower()
            if lower_key in {"slint", "qt"} and ("slint" in lower_text or "qt>=1.8" in lower_text or "qt==1.8" in lower_text):
                i = statement_end(lines, i)
                continue
        kept.append(lines[i])
        i += 1
    return kept


def rewrite_scripts(lines: list[str]) -> list[str]:
    kept: list[str] = []
    canonical_keys = {"notizen-py-qt", "notizen-pypy-qt", "notizen-alx"}
    i = 0
    while i < len(lines):
        key = key_name(lines[i])
        if key is not None:
            text = apply_replacements(statement_text(lines, i))
            normalized_key = apply_replacements(key)
            if normalized_key in canonical_keys:
                i = statement_end(lines, i)
                continue
            kept.extend(text.splitlines(keepends=True))
            i = statement_end(lines, i)
            continue
        kept.append(apply_replacements(lines[i]))
        i += 1
    while kept and kept[-1].strip() == "":
        kept.pop()
    if kept:
        kept.append("\n")
    kept.append('notizen-py-qt = "notizen_py_qt.app:main"\n')
    kept.append('notizen-alx = "notizen_py_qt.cli:main"\n')
    kept.append('notizen-pypy-qt = "notizen_pypy_qt.app:main"\n')
    return kept


def rewrite_package_data(lines: list[str]) -> list[str]:
    kept: list[str] = []
    managed = {"notizen_py_qt", "notizen_py_qt.ui", "notizen_py_slint", "notizen_py_slint.ui"}
    i = 0
    while i < len(lines):
        key = key_name(lines[i])
        if key is not None:
            normalized_key = apply_replacements(key)
            text = apply_replacements(statement_text(lines, i))
            lower_text = text.lower()
            if normalized_key in managed or "*.qml" in lower_text or "*.slint" in lower_text:
                i = statement_end(lines, i)
                continue
            kept.extend(text.splitlines(keepends=True))
            i = statement_end(lines, i)
            continue
        kept.append(apply_replacements(lines[i]))
        i += 1
    while kept and kept[-1].strip() == "":
        kept.pop()
    if kept:
        kept.append("\n")
    kept.append('notizen_py_qt = ["ui/*.qml", "ui/*.js"]\n')
    kept.append('"notizen_py_qt.ui" = ["*.qml", "*.js"]\n')
    return kept


def dedupe_section(lines: list[str]) -> list[str]:
    key_positions: dict[str, list[tuple[int, int]]] = {}
    i = 0
    while i < len(lines):
        key = key_name(lines[i])
        if key is None:
            i += 1
            continue
        end = statement_end(lines, i)
        key_positions.setdefault(key, []).append((i, end))
        i = end
    remove_ranges: set[int] = set()
    for ranges in key_positions.values():
        for start, end in ranges[:-1]:
            remove_ranges.update(range(start, end))
    return [apply_replacements(line) for idx, line in enumerate(lines) if idx not in remove_ranges]


def repair_text(text: str) -> str:
    text = apply_replacements(text)
    sections = split_sections(text)
    out_sections: list[Section] = []
    seen_headers: set[str] = set()
    has_project = False
    has_scripts = False
    has_package_data = False
    for section in sections:
        name = section.name
        if name == "project":
            has_project = True
            section.lines = rewrite_project(section.lines)
        elif name == "project.optional-dependencies":
            section.lines = rewrite_optional_dependencies(section.lines)
        elif name == "project.scripts":
            has_scripts = True
            section.lines = rewrite_scripts(section.lines)
        elif name == "tool.setuptools.package-data":
            has_package_data = True
            section.lines = rewrite_package_data(section.lines)
        else:
            section.lines = dedupe_section(section.lines)
        if name is not None and name in seen_headers:
            section.header = f"# duplicate [{name}] collapsed by repair_pyproject_qt611.py\n"
        elif name is not None:
            seen_headers.add(name)
        out_sections.append(section)
    if not has_project:
        out_sections.append(Section("[project]\n", rewrite_project([])))
    if not has_scripts:
        out_sections.append(Section("\n[project.scripts]\n", rewrite_scripts([])))
    if not has_package_data:
        out_sections.append(Section("\n[tool.setuptools.package-data]\n", rewrite_package_data([])))
    repaired = join_sections(out_sections)
    repaired = re.sub(r"\n{4,}", "\n\n\n", repaired)
    if not repaired.endswith("\n"):
        repaired += "\n"
    return repaired


def validate_toml(text: str) -> tuple[bool, str]:
    if tomllib is None:
        return True, "tomllib not available; skipped syntax validation"
    try:
        tomllib.loads(text)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return True, "valid TOML"


def repair_file(path: Path, apply: bool) -> int:
    original = path.read_text(encoding="utf-8", errors="ignore")
    repaired = repair_text(original)
    ok, message = validate_toml(repaired)
    print(f"TOML validation after repair: {message}")
    if not ok:
        print("ERROR: repair output is still invalid; not writing file.", file=sys.stderr)
        return 2
    if repaired == original:
        print(f"No pyproject changes needed: {path}")
        return 0
    print(f"Repair pyproject: {path}")
    if apply:
        backup_dir = path.parent / ".qt611_pyproject_repair_backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_dir / path.name)
        path.write_text(repaired, encoding="utf-8")
        print(f"Backup: {backup_dir / path.name}")
    else:
        print("Dry-run only; pass --apply to write the repaired file.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repair pyproject.toml after Qt 6.11 migration")
    parser.add_argument("root", nargs="?", default=".", help="Repository root or pyproject.toml path")
    parser.add_argument("--apply", action="store_true", help="Write the repaired pyproject.toml")
    args = parser.parse_args(argv)
    raw = Path(args.root).resolve()
    path = raw if raw.name == "pyproject.toml" else find_project_root(raw) / "pyproject.toml"
    if not path.exists():
        print(f"ERROR: pyproject.toml not found after project-root detection: {path}", file=sys.stderr)
        return 1
    return repair_file(path, apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
