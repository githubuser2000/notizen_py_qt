from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

from .legacy_paths import LEGACY_DEFAULT_FILENAME, legacy_documents_notizen_dir, split_legacy_file_location


LEGACY_RECENT_FILE_SLOTS: tuple[str, ...] = ("a", "b", "c", "d")


def default_config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "Notizen.NET"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "notizen-py-qt"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"yes", "true", "1", "on", "ja"}


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_autosave_seconds(value: int | str | None) -> int:
    """Return the WinForms-compatible autosave interval.

    ``einstellungen.vb`` disabled autosave at ``0`` and raised enabled values
    below five seconds to five seconds.  Keeping this logic in a pure helper
    lets tests and the Qt settings dialog share the same behavior.
    """

    try:
        seconds = int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0
    if seconds <= 0:
        return 0
    return max(5, seconds)


def legacy_autosave_should_save(*, root_exists: bool, path: str | Path | None, changed: bool) -> bool:
    """Return whether the old ``Autosavetimer_Tick`` would save.

    Notizen.NET autosaved only when a tree root existed, a real file was already
    associated with the document, that file still existed on disk and the model
    was marked as changed.  In particular, autosave did **not** silently create
    a missing file after it had been moved or deleted.
    """

    if not root_exists or not changed or path is None:
        return False
    try:
        return Path(path).exists()
    except (OSError, TypeError):
        return False




def normalize_window_state(value: str | None) -> str:
    """Normalize legacy/main-form window state names from ``xml_kram.vb``."""

    state = (value or "").strip().lower()
    if state in {"maximized", "maximise", "maximize", "maximiert"}:
        return "Maximized"
    if state in {"minimized", "minimised", "minimize", "minimieren", "minimiert"}:
        return "Minimized"
    return "Normal"



def legacy_recent_files_from_slots(slots: dict[str, str] | object) -> list[str]:
    """Return the old four-file ``<files a=... b=... c=... d=...>`` list.

    ``xml_kram.vb`` stored exactly four recent-file attributes. Empty slots are
    ignored on read, but their order is preserved. The helper accepts either a
    mapping-like object or an ``Element`` with ``.get`` so the XML parser and
    tests use the same tiny piece of legacy logic.
    """

    getter = getattr(slots, "get")
    result: list[str] = []
    for key in LEGACY_RECENT_FILE_SLOTS:
        value = getter(key, "")
        if value:
            result.append(str(value))
    return result


def legacy_recent_slots_from_files(recent_files: list[str] | tuple[str, ...]) -> dict[str, str]:
    """Serialize recent files back to the four legacy XML attributes."""

    values = [str(path) for path in recent_files if str(path)]
    values = values[-len(LEGACY_RECENT_FILE_SLOTS) :]
    return {
        key: values[index] if index < len(values) else ""
        for index, key in enumerate(LEGACY_RECENT_FILE_SLOTS)
    }


def legacy_remember_recent_file(recent_files: list[str] | tuple[str, ...], path: str | Path) -> list[str]:
    """Move ``path`` to the newest slot using the Notizen.NET four-entry cap."""

    value = os.fspath(path)
    result = [entry for entry in recent_files if entry and entry != value]
    result.append(value)
    return result[-len(LEGACY_RECENT_FILE_SLOTS) :]


def legacy_activate_recent_file(
    recent_files: list[str] | tuple[str, ...], path_or_index: str | Path | int
) -> tuple[str | None, list[str]]:
    """Return the selected recent file and the rotated legacy menu order.

    The original menu handlers made the clicked recent file the latest entry.
    The selected path is returned separately so callers can open it before
    saving the updated order.
    """

    files = [entry for entry in recent_files if entry]
    if isinstance(path_or_index, int):
        if not (0 <= path_or_index < len(files)):
            return None, files[-len(LEGACY_RECENT_FILE_SLOTS) :]
        selected = files[path_or_index]
    else:
        selected = os.fspath(path_or_index)
        if selected not in files:
            return None, files[-len(LEGACY_RECENT_FILE_SLOTS) :]
    return selected, legacy_remember_recent_file(files, selected)

def default_toolstrip_positions() -> dict[str, tuple[int, int]]:
    """Legacy toolbar position map from ``xml_kram.vb``/``Notizen.Designer.vb``."""

    return {
        "haupt": (0, 0),
        "elements": (0, 0),
        "font": (0, 0),
        "cutpastecopy": (0, 0),
    }


@dataclass(slots=True)
class AppSettings:
    config_dir: Path = field(default_factory=default_config_dir)
    language: str = "Auto"
    last_directory: str = field(default_factory=lambda: str(legacy_documents_notizen_dir()))
    last_file: str = LEGACY_DEFAULT_FILENAME
    recent_files: list[str] = field(default_factory=list)
    backup_keep: int = 30
    autosave_seconds: int = 60
    scrollbars_choice: int = 3
    open_once_file: str = ""
    open_once_timestamp: str = ""
    toolstrip_positions: dict[str, tuple[int, int]] = field(default_factory=default_toolstrip_positions)
    autorun_enabled: bool = False
    autorun_minimized: bool = True
    show_desknote_borders: bool = True
    show_in_taskbar_when_minimized: bool = False
    gnome_safe_tray_start: bool = True
    ftp_host: str = ""
    ftp_path: str = ""
    ftp_username: str = ""
    ftp_password: str = ""
    window_x: int = 60
    window_y: int = 60
    window_width: int = 1000
    window_height: int = 700
    window_state: str = "Normal"
    legacy_root_attributes: dict[str, str] = field(default_factory=dict)
    legacy_known_element_attrs: dict[str, dict[str, str]] = field(default_factory=dict)
    legacy_known_nested_element_attrs: dict[str, dict[str, str]] = field(default_factory=dict)
    legacy_passthrough_elements: list[str] = field(default_factory=list)

    @property
    def path(self) -> Path:
        return self.config_dir / "notizen.config.xml"

    def _candidate_paths(self) -> list[Path]:
        """Return legacy and current configuration file names in lookup order."""
        names = [
            "notizen.config.xml",
            "Notizen.config.xml",
            "notizen.xml",
            "Notizen.xml",
        ]
        candidates = [self.config_dir / name for name in names]
        candidates.extend(Path.cwd() / name for name in names)
        unique: list[Path] = []
        seen: set[Path] = set()
        for candidate in candidates:
            resolved = candidate.resolve() if candidate.exists() else candidate.absolute()
            if resolved not in seen:
                seen.add(resolved)
                unique.append(candidate)
        return unique

    def apply_xml_root(self, root: ET.Element) -> None:
        """Apply a Notizen.NET ``notizen.config.xml`` XML tree to this instance.

        The old WinForms application stores most settings as XML element
        attributes.  Keeping this parser as an instance method lets the Qt port
        import an arbitrary legacy config file without replacing the live
        ``config_dir`` used by the current platform.
        """

        def child(name: str) -> ET.Element | None:
            return root.find(name)

        known_top_level = {
            "scrolls",
            "language",
            "open",
            "files",
            "ftp",
            "saftycopies",
            "autosave",
            "x",
            "tool-stripes",
            "autorun",
            "desknotes",
            "minimized-show-in",
            "tray",
            "main-form",
        }
        known_attrs = {
            "scrolls": {"choice"},
            "language": {"choice"},
            "open": {"file", "directory"},
            "files": set(LEGACY_RECENT_FILE_SLOTS),
            "ftp": {"name", "pass", "host", "path"},
            "saftycopies": {"amount"},
            "autosave": {"seconds"},
            "x": {"y", "z", "a"},
            "tool-stripes": set(),
            "autorun": {"if", "minimized"},
            "desknotes": {"show_desknote_borders"},
            "minimized-show-in": {"taskbar"},
            "tray": {"gnome-safe-start", "gnome_safe_start"},
            "main-form": {"x", "y", "width", "height", "windowstate"},
        }
        known_nested_attrs = {
            "open/once-opened": {"file", "timestamp"},
            "tool-stripes/haupt": {"x", "y"},
            "tool-stripes/elements": {"x", "y"},
            "tool-stripes/font": {"x", "y"},
            "tool-stripes/cutpastecopy": {"x", "y"},
        }
        self.legacy_root_attributes = dict(root.attrib)
        self.legacy_known_element_attrs = {}
        self.legacy_known_nested_element_attrs = {}
        for element in list(root):
            if element.tag not in known_top_level:
                continue
            extras = {key: value for key, value in element.attrib.items() if key not in known_attrs.get(element.tag, set())}
            if extras:
                self.legacy_known_element_attrs[element.tag] = extras
            for child_element in list(element):
                path = f"{element.tag}/{child_element.tag}"
                if path not in known_nested_attrs:
                    continue
                child_extras = {
                    key: value
                    for key, value in child_element.attrib.items()
                    if key not in known_nested_attrs[path]
                }
                if child_extras:
                    self.legacy_known_nested_element_attrs[path] = child_extras
        self.legacy_passthrough_elements = [
            ET.tostring(element, encoding="unicode")
            for element in list(root)
            if element.tag not in known_top_level
        ]

        scrolls = child("scrolls")
        if scrolls is not None:
            self.scrollbars_choice = _as_int(scrolls.get("choice"), self.scrollbars_choice)

        language = child("language")
        if language is not None:
            self.language = language.get("choice", self.language)

        opened = child("open")
        if opened is not None:
            directory = opened.get("directory", self.last_directory)
            file_name = opened.get("file", self.last_file)
            if directory is not None and len(directory.strip()) >= 2:
                self.last_directory = directory
            else:
                self.last_directory = str(legacy_documents_notizen_dir())
            self.last_file = file_name or LEGACY_DEFAULT_FILENAME
            once_opened = opened.find("once-opened")
            if once_opened is not None:
                self.open_once_file = once_opened.get("file", self.open_once_file)
                self.open_once_timestamp = once_opened.get("timestamp", self.open_once_timestamp)

        files = child("files")
        if files is not None:
            self.recent_files = legacy_recent_files_from_slots(files)

        ftp = child("ftp")
        if ftp is not None:
            self.ftp_host = ftp.get("host", self.ftp_host)
            self.ftp_path = ftp.get("path", self.ftp_path)
            self.ftp_username = ftp.get("name", self.ftp_username)
            self.ftp_password = ftp.get("pass", self.ftp_password)

        backups = child("saftycopies")
        if backups is not None:
            self.backup_keep = _as_int(backups.get("amount"), self.backup_keep)

        autosave = child("autosave")
        if autosave is None:
            autosave = child("x")
        if autosave is not None:
            self.autosave_seconds = normalize_autosave_seconds(
                _as_int(autosave.get("seconds", autosave.get("a")), self.autosave_seconds)
            )

        tool_stripes = child("tool-stripes")
        if tool_stripes is not None:
            positions = default_toolstrip_positions()
            positions.update(self.toolstrip_positions)
            for name in positions:
                element = tool_stripes.find(name)
                if element is None:
                    continue
                positions[name] = (
                    _as_int(element.get("x"), positions[name][0]),
                    _as_int(element.get("y"), positions[name][1]),
                )
            self.toolstrip_positions = positions

        autorun = child("autorun")
        if autorun is not None:
            self.autorun_enabled = _as_bool(autorun.get("if"), self.autorun_enabled)
            self.autorun_minimized = _as_bool(autorun.get("minimized"), self.autorun_minimized)

        desknotes = child("desknotes")
        if desknotes is not None:
            self.show_desknote_borders = _as_bool(
                desknotes.get("show_desknote_borders"), self.show_desknote_borders
            )

        minimized = child("minimized-show-in")
        if minimized is not None:
            self.show_in_taskbar_when_minimized = _as_bool(
                minimized.get("taskbar"), self.show_in_taskbar_when_minimized
            )

        tray = child("tray")
        if tray is not None:
            self.gnome_safe_tray_start = _as_bool(
                tray.get("gnome-safe-start", tray.get("gnome_safe_start")), self.gnome_safe_tray_start
            )

        main_form = child("main-form")
        if main_form is not None:
            for attr, field_name in (
                ("x", "window_x"),
                ("y", "window_y"),
                ("width", "window_width"),
                ("height", "window_height"),
            ):
                setattr(self, field_name, _as_int(main_form.get(attr), getattr(self, field_name)))
            self.window_state = normalize_window_state(main_form.get("windowstate", self.window_state))

    def apply_from_file(self, path: str | Path) -> None:
        """Import settings from a selected legacy/current config XML file."""
        root = ET.parse(Path(path)).getroot()
        self.apply_xml_root(root)

    @classmethod
    def load(cls, config_dir: Path | None = None) -> "AppSettings":
        settings = cls(config_dir=config_dir or default_config_dir())
        config_path = next((candidate for candidate in settings._candidate_paths() if candidate.exists()), None)
        if config_path is None:
            settings.save()
            return settings
        try:
            settings.apply_from_file(config_path)
        except Exception:
            return settings
        return settings

    def remember_file(self, path: str | Path) -> None:
        p = os.fspath(path)
        self.last_directory, self.last_file = split_legacy_file_location(p, self.last_directory)
        self.recent_files = legacy_remember_recent_file(self.recent_files, p)

    def activate_recent_file(self, path_or_index: str | Path | int) -> str | None:
        """Mark a legacy recent-file menu entry as the latest one."""

        selected, recent = legacy_activate_recent_file(self.recent_files, path_or_index)
        self.recent_files = recent
        return selected

    def save(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)

        def attrs_for(path: str, attrs: dict[str, str]) -> dict[str, str]:
            extras = (
                self.legacy_known_nested_element_attrs.get(path, {})
                if "/" in path
                else self.legacy_known_element_attrs.get(path, {})
            )
            merged = dict(extras)
            merged.update(attrs)
            return merged

        root = ET.Element("notizen-alx", dict(self.legacy_root_attributes))
        ET.SubElement(root, "scrolls", attrs_for("scrolls", {"choice": str(self.scrollbars_choice)}))
        ET.SubElement(root, "saftycopies", attrs_for("saftycopies", {"amount": str(self.backup_keep)}))
        ET.SubElement(
            root,
            "autorun",
            attrs_for(
                "autorun",
                {
                    "if": "yes" if self.autorun_enabled else "no",
                    "minimized": "yes" if self.autorun_minimized else "no",
                },
            ),
        )
        ET.SubElement(
            root,
            "ftp",
            attrs_for(
                "ftp",
                {
                    "name": self.ftp_username,
                    "pass": self.ftp_password,
                    "host": self.ftp_host,
                    "path": self.ftp_path,
                },
            ),
        )
        recent = legacy_recent_slots_from_files(self.recent_files)
        ET.SubElement(root, "files", attrs_for("files", recent))
        ET.SubElement(root, "language", attrs_for("language", {"choice": self.language}))
        opened = ET.SubElement(root, "open", attrs_for("open", {"file": self.last_file, "directory": self.last_directory}))
        ET.SubElement(
            opened,
            "once-opened",
            attrs_for("open/once-opened", {"file": self.open_once_file, "timestamp": self.open_once_timestamp}),
        )
        ET.SubElement(
            root,
            "main-form",
            attrs_for(
                "main-form",
                {
                    "x": str(self.window_x),
                    "y": str(self.window_y),
                    "width": str(self.window_width),
                    "height": str(self.window_height),
                    "windowstate": normalize_window_state(self.window_state),
                },
            ),
        )
        ET.SubElement(root, "minimized-show-in", attrs_for("minimized-show-in", {"taskbar": "yes" if self.show_in_taskbar_when_minimized else "no"}))
        ET.SubElement(root, "tray", attrs_for("tray", {"gnome-safe-start": "yes" if self.gnome_safe_tray_start else "no"}))
        ET.SubElement(root, "desknotes", attrs_for("desknotes", {"show_desknote_borders": "yes" if self.show_desknote_borders else "no"}))
        tool_stripes = ET.SubElement(root, "tool-stripes", attrs_for("tool-stripes", {}))
        positions = default_toolstrip_positions()
        positions.update(self.toolstrip_positions)
        for name in ("haupt", "elements", "font", "cutpastecopy"):
            x, y = positions[name]
            ET.SubElement(tool_stripes, name, attrs_for(f"tool-stripes/{name}", {"x": str(x), "y": str(y)}))
        ET.SubElement(root, "x", attrs_for("x", {"y": "0", "z": "0", "a": str(normalize_autosave_seconds(self.autosave_seconds))}))
        existing_tags = {element.tag for element in list(root)}
        for xml_text in self.legacy_passthrough_elements:
            try:
                element = ET.fromstring(xml_text)
            except ET.ParseError:
                continue
            if element.tag in existing_tags:
                continue
            root.append(element)
            existing_tags.add(element.tag)
        tree = ET.ElementTree(root)
        tree.write(self.path, encoding="utf-16", xml_declaration=True)
