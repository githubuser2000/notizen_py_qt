from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path, PureWindowsPath
import xml.etree.ElementTree as ET

from .config import AppConfig, config_dir
from .translations import normalize_language


@dataclass(slots=True)
class LegacyConfig:
    """Portable representation of the old ``notizen.config.xml`` file."""

    backup_count: int = 30
    autosave_seconds: int = 0
    language: str = "auto"
    last_file: str | None = None
    recent_files: list[str] | None = None
    autorun: bool = False
    autorun_minimized: bool = False
    show_in_taskbar: bool = False
    show_desknote_borders: bool = True
    scrollbars_choice: int = 3
    window_x: int | None = None
    window_y: int | None = None
    window_width: int | None = None
    window_height: int | None = None
    window_state: str = "normal"
    ftp_name: str = ""
    ftp_password: str = ""
    ftp_host: str = ""
    ftp_path: str = ""
    toolstrip_positions: dict[str, list[int]] | None = None

    def to_app_config(self, base: AppConfig | None = None) -> AppConfig:
        config = base or AppConfig.load()
        config.backup_count = self.backup_count
        config.autosave_seconds = self.autosave_seconds
        config.language = _normalize_language(self.language)
        config.show_in_taskbar = self.show_in_taskbar
        config.show_desknote_borders = self.show_desknote_borders
        config.autorun = self.autorun
        config.autorun_minimized = self.autorun_minimized
        config.scrollbars_choice = self.scrollbars_choice
        config.window_x = self.window_x
        config.window_y = self.window_y
        config.window_width = self.window_width
        config.window_height = self.window_height
        config.window_state = self.window_state
        config.ftp_username = self.ftp_name
        config.ftp_password = self.ftp_password
        config.ftp_host = self.ftp_host
        config.ftp_path = self.ftp_path
        if self.toolstrip_positions:
            config.toolstrip_positions = {name: [int(pos[0]), int(pos[1])] for name, pos in self.toolstrip_positions.items()}
        if self.last_file:
            config.add_recent(self.last_file)
        for item in reversed(self.recent_files or []):
            if item:
                config.add_recent(item)
        return config

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def default_legacy_config_path() -> Path:
    """Best-effort location of the old WinForms config file.

    VB.NET used CurrentUserApplicationData, which includes vendor/app/version
    folders. There is no exact cross-platform equivalent, so this function
    returns the most likely Windows path and callers can still pass an explicit
    path.
    """
    if os.name == "nt":
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return appdata / "Intellibit" / "Notizen" / "notizen.config.xml"
    return config_dir() / "legacy" / "notizen.config.xml"


def find_legacy_config_candidates() -> list[Path]:
    candidates = [default_legacy_config_path()]
    if os.name == "nt":
        roots = [Path(os.environ.get("APPDATA", "")), Path(os.environ.get("LOCALAPPDATA", ""))]
        for root in roots:
            if not root:
                continue
            for pattern in ("**/notizen.config.xml", "**/Notizen*/**/notizen.config.xml"):
                try:
                    for path in root.glob(pattern):
                        if path not in candidates:
                            candidates.append(path)
                except OSError:
                    pass
    return candidates


def load_legacy_config(path: str | Path | None = None) -> LegacyConfig:
    path = Path(path) if path is not None else default_legacy_config_path()
    root = ET.fromstring(path.read_bytes().decode("utf-16", errors="ignore") if _looks_utf16(path) else path.read_text(encoding="utf-8-sig"))
    if root.tag != "notizen-alx":
        raise ValueError(f"Keine alte Notizen-Konfiguration: <{root.tag}>")

    def attrs(name: str) -> dict[str, str]:
        el = root.find(name)
        return dict(el.attrib) if el is not None else {}

    open_attrs = attrs("open")
    open_file = open_attrs.get("file", "")
    open_dir = open_attrs.get("directory", "")
    last_file = _join_old_path(open_dir, open_file)

    recent = []
    files_attrs = attrs("files")
    for key in ("a", "b", "c", "d"):
        value = files_attrs.get(key, "").strip()
        if value:
            recent.append(value)

    ftp = attrs("ftp")
    main = attrs("main-form")
    toolstrips = _parse_toolstrip_positions(root)
    return LegacyConfig(
        backup_count=_int(attrs("saftycopies").get("amount"), 30),
        autosave_seconds=_int(attrs("x").get("a"), 0),
        language=attrs("language").get("choice", "auto"),
        last_file=last_file,
        recent_files=recent,
        autorun=_yes(attrs("autorun").get("if")),
        autorun_minimized=_yes(attrs("autorun").get("minimized")),
        show_in_taskbar=_yes(attrs("minimized-show-in").get("taskbar")),
        show_desknote_borders=_yes(attrs("desknotes").get("show_desknote_borders"), default=True),
        scrollbars_choice=_int(attrs("scrolls").get("choice"), 3),
        window_x=_int_or_none(main.get("x")),
        window_y=_int_or_none(main.get("y")),
        window_width=_int_or_none(main.get("width")),
        window_height=_int_or_none(main.get("height")),
        window_state=(main.get("windowstate") or "normal").lower(),
        ftp_name=ftp.get("name", ""),
        ftp_password=ftp.get("pass", ""),
        ftp_host=ftp.get("host", ""),
        ftp_path=ftp.get("path", ""),
        toolstrip_positions=toolstrips,
    )


def import_legacy_config(path: str | Path | None = None) -> AppConfig:
    legacy = load_legacy_config(path)
    config = legacy.to_app_config(AppConfig.load())
    config.save()
    return config


def write_legacy_like_config(config: AppConfig, path: str | Path) -> Path:
    """Write a minimal old-style XML file for diagnostics or round-trip checks."""
    path = Path(path)
    root = ET.Element("notizen-alx")
    ET.SubElement(root, "scrolls", {"choice": str(config.scrollbars_choice)})
    ET.SubElement(root, "saftycopies", {"amount": str(config.backup_count)})
    ET.SubElement(root, "autorun", {"if": _yesno(config.autorun), "minimized": _yesno(config.autorun_minimized)})
    ET.SubElement(root, "ftp", {"name": config.ftp_username, "pass": config.ftp_password, "host": config.ftp_host, "path": config.ftp_path})
    recent = list(config.recent_files[:4])
    ET.SubElement(root, "files", {"a": _item(recent, 0), "b": _item(recent, 1), "c": _item(recent, 2), "d": _item(recent, 3)})
    ET.SubElement(root, "language", {"choice": config.language})
    if config.last_file and "://" not in config.last_file:
        last = Path(config.last_file)
        open_file = last.name
        open_dir = str(last.parent)
    elif config.last_file:
        open_file = config.last_file
        open_dir = ""
    else:
        open_file = open_dir = ""
    ET.SubElement(root, "open", {"file": open_file, "directory": open_dir})
    ET.SubElement(
        root,
        "main-form",
        {
            "x": str(config.window_x or 0),
            "y": str(config.window_y or 0),
            "width": str(config.window_width or 0),
            "height": str(config.window_height or 0),
            "windowstate": config.window_state,
        },
    )
    ET.SubElement(root, "minimized-show-in", {"taskbar": _yesno(config.show_in_taskbar)})
    ET.SubElement(root, "desknotes", {"show_desknote_borders": _yesno(config.show_desknote_borders)})
    strips = ET.SubElement(root, "tool-stripes")
    for name in ("haupt", "elements", "font", "cutpastecopy"):
        try:
            x, y = config.toolstrip_position(name)
        except Exception:
            x, y = 0, 0
        ET.SubElement(strips, name, {"x": str(x), "y": str(y)})
    ET.SubElement(root, "x", {"y": "0", "z": "0", "a": str(config.autosave_seconds)})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(ET.tostring(root, encoding="utf-16", xml_declaration=True, short_empty_elements=False))
    return path


def _parse_toolstrip_positions(root: ET.Element) -> dict[str, list[int]]:
    positions: dict[str, list[int]] = {}
    strips = root.find("tool-stripes")
    if strips is None:
        return positions
    for name in ("haupt", "elements", "font", "cutpastecopy"):
        el = strips.find(name)
        if el is None:
            continue
        positions[name] = [_int(el.attrib.get("x"), 0), _int(el.attrib.get("y"), 0)]
    return positions


def _looks_utf16(path: Path) -> bool:
    try:
        return path.read_bytes()[:2] in (b"\xff\xfe", b"\xfe\xff")
    except OSError:
        return False


def _join_old_path(directory: str, filename: str) -> str | None:
    directory = (directory or "").strip()
    filename = (filename or "").strip()
    if not filename:
        return None
    if not directory:
        return filename
    if "://" in filename:
        return filename
    if "\\" in directory or (len(directory) >= 2 and directory[1] == ":"):
        return str(PureWindowsPath(directory) / filename)
    return str(Path(directory) / filename)


def _yes(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"yes", "true", "1", "ja"}


def _yesno(value: bool) -> str:
    return "yes" if value else "no"


def _int(value: str | None, default: int) -> int:
    parsed = _int_or_none(value)
    return default if parsed is None else parsed


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _item(values: list[str], index: int) -> str:
    return values[index] if index < len(values) else ""


def _normalize_language(value: str) -> str:
    text = (value or "auto").strip().lower()
    if text == "auto":
        return "auto"
    return normalize_language(text)
