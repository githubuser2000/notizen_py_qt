from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import platform
import re
import shutil
import subprocess


@dataclass(frozen=True, slots=True)
class FontInfo:
    name: str
    path: str
    source: str = "filesystem"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


_FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".woff", ".woff2"}


def default_font_dirs() -> list[Path]:
    """Return platform-specific directories that usually contain installed fonts."""
    home = Path.home()
    dirs: list[Path] = []
    system = platform.system().lower()
    if system == "windows":
        windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot") or r"C:\Windows"
        dirs.extend([Path(windir) / "Fonts", home / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts"])
    elif system == "darwin":
        dirs.extend([Path("/System/Library/Fonts"), Path("/Library/Fonts"), home / "Library" / "Fonts"])
    else:
        dirs.extend([Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), home / ".fonts", home / ".local" / "share" / "fonts"])
    return dirs


def font_name_from_path(path: str | Path) -> str:
    """Best-effort font family/name from a font filename.

    The old WinForms code received exact family names from System.Drawing.  The
    Python port avoids binary font parsing and instead normalises common file
    names such as ``DejaVuSans-Bold.ttf`` to ``DejaVuSans``.  When ``fc-list`` is
    available, :func:`list_system_fonts` prefers the exact family name returned
    by fontconfig.
    """
    stem = Path(path).stem.strip()
    stem = re.sub(r"(?i)[-_ ](regular|book|medium|normal|roman|bold|italic|oblique|light|thin|black|condensed|semibold|demibold|extrabold|heavy).*", "", stem)
    stem = stem.replace("_", " ").strip(" -_")
    return stem or Path(path).stem or "Unbekannte Schrift"


def list_system_fonts(*, contains: str | None = None, limit: int | None = None, include_paths: list[str | Path] | None = None) -> list[FontInfo]:
    """List installed fonts without external Python packages.

    On Linux/BSD the function first tries ``fc-list`` because it knows real
    family names.  It then falls back to scanning common font directories on all
    platforms. Duplicate family/path pairs are removed, and the result is stable
    and alphabetically sorted.
    """
    if limit == 0:
        return []
    needle = (contains or "").casefold().strip()
    seen: set[tuple[str, str]] = set()
    result: list[FontInfo] = []

    def add(info: FontInfo) -> None:
        if needle and needle not in info.name.casefold() and needle not in info.path.casefold():
            return
        key = (info.name.casefold(), info.path)
        if key in seen:
            return
        seen.add(key)
        result.append(info)

    for info in _fontconfig_fonts():
        add(info)

    dirs = [Path(p) for p in (include_paths or [])] + default_font_dirs()
    for directory in dirs:
        if not directory.exists():
            continue
        for path in _iter_font_files(directory):
            add(FontInfo(name=font_name_from_path(path), path=str(path), source="filesystem"))

    result.sort(key=lambda item: (item.name.casefold(), item.path.casefold()))
    if limit is not None and limit >= 0:
        return result[:limit]
    return result


def format_font_list(fonts: list[FontInfo]) -> str:
    if not fonts:
        return "keine Schriften gefunden"
    return "\n".join(f"{font.name}\t{font.path}" for font in fonts)


def _fontconfig_fonts() -> list[FontInfo]:
    exe = shutil.which("fc-list")
    if not exe:
        return []
    try:
        completed = subprocess.run(
            [exe, "--format", "%{family[0]}\t%{file}\n"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
    except Exception:
        return []
    fonts: list[FontInfo] = []
    for line in completed.stdout.splitlines():
        if "\t" not in line:
            continue
        name, path = line.split("\t", 1)
        name = name.strip() or font_name_from_path(path)
        path = path.strip()
        if path:
            fonts.append(FontInfo(name=name, path=path, source="fontconfig"))
    return fonts


def _iter_font_files(directory: Path):
    try:
        iterator = directory.rglob("*")
        for path in iterator:
            try:
                if path.is_file() and path.suffix.lower() in _FONT_EXTENSIONS:
                    yield path
            except OSError:
                continue
    except OSError:
        return
