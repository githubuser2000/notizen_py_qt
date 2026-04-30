from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import struct
import sys

_FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".otc", ".woff", ".woff2"}


@dataclass(slots=True, frozen=True)
class FontEntry:
    family: str
    path: str
    source: str = "file"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def default_font_dirs() -> list[Path]:
    dirs: list[Path] = []
    if sys.platform.startswith("win"):
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        dirs.append(windir / "Fonts")
    elif sys.platform == "darwin":
        dirs.extend([Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home() / "Library" / "Fonts"])
    else:
        dirs.extend([
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
            Path.home() / ".local" / "share" / "fonts",
        ])
    return dirs


def list_system_fonts(*, contains: str | None = None, limit: int | None = None, paths: list[str | Path] | None = None) -> list[FontEntry]:
    """Return installed font families without external packages.

    The original WinForms app filled its font menu from
    ``InstalledFontCollection``.  This portable replacement scans common font
    directories and reads the TrueType/OpenType name table when possible, falling
    back to a cleaned filename stem.
    """

    roots = [Path(p).expanduser() for p in paths] if paths else default_font_dirs()
    wanted = contains.casefold() if contains else None
    found: dict[str, FontEntry] = {}
    for root in roots:
        if not root.exists():
            continue
        files = [root] if root.is_file() else root.rglob("*")
        for file in files:
            try:
                if not file.is_file() or file.suffix.lower() not in _FONT_EXTENSIONS:
                    continue
            except OSError:
                continue
            family = _read_font_family(file) or _family_from_filename(file)
            if not family:
                continue
            if wanted and wanted not in family.casefold() and wanted not in str(file).casefold():
                continue
            key = family.casefold()
            if key not in found:
                found[key] = FontEntry(family=family, path=str(file), source="file")
            if limit is not None and limit > 0 and len(found) >= limit:
                return sorted(found.values(), key=lambda item: item.family.casefold())
    return sorted(found.values(), key=lambda item: item.family.casefold())


def format_font_list(entries: list[FontEntry]) -> str:
    if not entries:
        return "keine Schriften gefunden"
    return "\n".join(f"{entry.family}\t{entry.path}" for entry in entries)


def _family_from_filename(path: Path) -> str:
    stem = path.stem
    for marker in ("-Regular", " Regular", "_Regular", "-Bold", " Bold", "-Italic", " Italic"):
        stem = stem.replace(marker, "")
    stem = stem.replace("_", " ").replace("-", " ").strip()
    return " ".join(stem.split()) or path.stem


def _read_font_family(path: Path) -> str | None:
    try:
        data = path.read_bytes()[:262144]
    except OSError:
        return None
    if len(data) < 12:
        return None
    try:
        if data[:4] in {b"ttcf", b"OTTO", b"\x00\x01\x00\x00", b"true", b"typ1"}:
            offset = 0
            if data[:4] == b"ttcf":
                if len(data) < 16:
                    return None
                offset = struct.unpack(">I", data[12:16])[0]
            return _read_sfnt_name(data, offset)
    except Exception:
        return None
    return None


def _read_sfnt_name(data: bytes, offset: int) -> str | None:
    if offset < 0 or offset + 12 > len(data):
        return None
    num_tables = struct.unpack(">H", data[offset + 4 : offset + 6])[0]
    table_dir = offset + 12
    name_offset = None
    name_length = None
    for index in range(num_tables):
        entry = table_dir + index * 16
        if entry + 16 > len(data):
            break
        tag = data[entry : entry + 4]
        if tag == b"name":
            name_offset = struct.unpack(">I", data[entry + 8 : entry + 12])[0]
            name_length = struct.unpack(">I", data[entry + 12 : entry + 16])[0]
            break
    if name_offset is None or name_length is None:
        return None
    start = name_offset
    if start + 6 > len(data):
        return None
    count, string_offset = struct.unpack(">HH", data[start + 2 : start + 6])
    storage_start = start + string_offset
    best: tuple[int, str] | None = None
    for index in range(count):
        rec = start + 6 + index * 12
        if rec + 12 > len(data):
            break
        platform, encoding, language, name_id, length, off = struct.unpack(">HHHHHH", data[rec : rec + 12])
        if name_id not in {1, 16}:
            continue
        raw_start = storage_start + off
        raw_end = raw_start + length
        if raw_start < 0 or raw_end > len(data):
            continue
        raw = data[raw_start:raw_end]
        text = _decode_name(raw, platform, encoding)
        if not text:
            continue
        score = 0
        if name_id == 16:
            score += 5
        if platform == 3:
            score += 3
        if language in {0x0409, 0x0000}:
            score += 1
        if best is None or score > best[0]:
            best = (score, text)
    return best[1] if best else None


def _decode_name(raw: bytes, platform: int, encoding: int) -> str | None:
    candidates: list[str]
    if platform == 3 or platform == 0:
        candidates = ["utf-16-be", "utf-8", "latin-1"]
    elif platform == 1:
        candidates = ["mac_roman", "latin-1"]
    else:
        candidates = ["utf-8", "latin-1"]
    for enc in candidates:
        try:
            text = raw.decode(enc).strip("\x00 \t\r\n")
        except UnicodeDecodeError:
            continue
        text = " ".join(text.split())
        if text:
            return text
    return None
