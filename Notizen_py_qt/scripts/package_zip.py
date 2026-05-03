#!/usr/bin/env python3
from __future__ import annotations

import argparse
import stat
import time
import zipfile
from pathlib import Path

EXECUTABLE_SUFFIXES = {".sh", ".desktop"}
EXECUTABLE_NAMES = {
    "build_python_qt.sh",
    "check_no_slint.sh",
    "check_no_slint_strict.sh",
    "package_zip.py",
}
IGNORED_NAMES = {".git", ".pytest_cache", "__pycache__"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def unix_zip_mode_for_path(path: Path, rel: Path | None = None) -> int:
    """Return a portable Unix mode for a ZIP entry.

    Previous hand-made archives accidentally stored several directories as
    ``0600``/``drw-------``.  Directories must be searchable/executable, and
    actual launcher/helper scripts should be executable after extraction on
    Unix-like systems.  Archived migration metadata is deliberately kept as
    normal data, even when it contains old helper scripts.
    """

    if path.is_dir():
        return stat.S_IFDIR | 0o755
    if rel is not None and rel.parts and rel.parts[0] == "legacy_build_metadata":
        return stat.S_IFREG | 0o644
    if path.suffix in EXECUTABLE_SUFFIXES or path.name in EXECUTABLE_NAMES:
        return stat.S_IFREG | 0o755
    if rel is not None and len(rel.parts) == 2 and rel.parts[0] == "scripts" and path.suffix == ".py":
        return stat.S_IFREG | 0o755
    return stat.S_IFREG | 0o644


def add_entry(zf: zipfile.ZipFile, src: Path, arcname: str, rel: Path | None = None) -> None:
    mode = unix_zip_mode_for_path(src, rel)
    info = zipfile.ZipInfo(arcname + ("/" if src.is_dir() and not arcname.endswith("/") else ""))
    info.create_system = 3
    info.external_attr = mode << 16
    try:
        info.date_time = time.localtime(src.stat().st_mtime)[:6]
    except Exception:
        pass
    if src.is_dir():
        zf.writestr(info, b"")
    else:
        zf.writestr(info, src.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)


def should_include(path: Path) -> bool:
    if any(part in IGNORED_NAMES for part in path.parts):
        return False
    if path.suffix in IGNORED_SUFFIXES:
        return False
    return True


def build_zip(source_dir: Path, output_zip: Path, root_name: str | None = None) -> None:
    source_dir = source_dir.resolve()
    root_name = root_name or source_dir.name
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        add_entry(zf, source_dir, root_name)
        for path in sorted(source_dir.rglob("*")):
            if not should_include(path.relative_to(source_dir)):
                continue
            rel_path = path.relative_to(source_dir)
            rel = rel_path.as_posix()
            add_entry(zf, path, f"{root_name}/{rel}", rel_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Package Notizen PyQt with correct Unix ZIP permissions.")
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_zip", type=Path)
    parser.add_argument("--root-name", default=None)
    args = parser.parse_args()
    build_zip(args.source_dir, args.output_zip, args.root_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
