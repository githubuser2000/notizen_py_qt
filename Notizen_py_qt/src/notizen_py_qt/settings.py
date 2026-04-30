from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET


def default_config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "Notizen.NET"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "notizen-py-qt"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"yes", "true", "1", "on", "ja"}


@dataclass(slots=True)
class AppSettings:
    config_dir: Path = field(default_factory=default_config_dir)
    language: str = "Auto"
    last_directory: str = ""
    last_file: str = ""
    recent_files: list[str] = field(default_factory=list)
    backup_keep: int = 30
    autosave_seconds: int = 0
    scrollbars_choice: int = 3
    autorun_enabled: bool = False
    autorun_minimized: bool = True
    show_desknote_borders: bool = True
    show_in_taskbar_when_minimized: bool = False
    ftp_host: str = ""
    ftp_path: str = ""
    ftp_username: str = ""
    ftp_password: str = ""
    window_x: int = 60
    window_y: int = 60
    window_width: int = 1000
    window_height: int = 700
    window_state: str = "Normal"

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

    @classmethod
    def load(cls, config_dir: Path | None = None) -> "AppSettings":
        settings = cls(config_dir=config_dir or default_config_dir())
        config_path = next((candidate for candidate in settings._candidate_paths() if candidate.exists()), None)
        if config_path is None:
            settings.save()
            return settings
        try:
            root = ET.parse(config_path).getroot()
        except Exception:
            return settings

        def child(name: str):
            return root.find(name)

        scrolls = child("scrolls")
        if scrolls is not None:
            try:
                settings.scrollbars_choice = int(scrolls.get("choice", settings.scrollbars_choice))
            except (TypeError, ValueError):
                pass

        language = child("language")
        if language is not None:
            settings.language = language.get("choice", settings.language)

        opened = child("open")
        if opened is not None:
            settings.last_directory = opened.get("directory", "")
            settings.last_file = opened.get("file", "")

        files = child("files")
        if files is not None:
            settings.recent_files = [files.get(k, "") for k in ("a", "b", "c", "d") if files.get(k, "")]

        ftp = child("ftp")
        if ftp is not None:
            settings.ftp_host = ftp.get("host", "")
            settings.ftp_path = ftp.get("path", "")
            settings.ftp_username = ftp.get("name", "")
            settings.ftp_password = ftp.get("pass", "")

        backups = child("saftycopies")
        if backups is not None:
            try:
                settings.backup_keep = int(backups.get("amount", settings.backup_keep))
            except (TypeError, ValueError):
                pass

        autosave = child("autosave") or child("x")
        if autosave is not None:
            try:
                settings.autosave_seconds = int(autosave.get("seconds", autosave.get("a", settings.autosave_seconds)))
            except (TypeError, ValueError):
                pass

        autorun = child("autorun")
        if autorun is not None:
            settings.autorun_enabled = _as_bool(autorun.get("if"), settings.autorun_enabled)
            settings.autorun_minimized = _as_bool(autorun.get("minimized"), settings.autorun_minimized)

        desknotes = child("desknotes")
        if desknotes is not None:
            settings.show_desknote_borders = _as_bool(
                desknotes.get("show_desknote_borders"), settings.show_desknote_borders
            )

        minimized = child("minimized-show-in")
        if minimized is not None:
            settings.show_in_taskbar_when_minimized = _as_bool(
                minimized.get("taskbar"), settings.show_in_taskbar_when_minimized
            )

        main_form = child("main-form")
        if main_form is not None:
            for attr, field_name in (
                ("x", "window_x"),
                ("y", "window_y"),
                ("width", "window_width"),
                ("height", "window_height"),
            ):
                try:
                    setattr(settings, field_name, int(main_form.get(attr, getattr(settings, field_name))))
                except (TypeError, ValueError):
                    pass
            settings.window_state = main_form.get("windowstate", settings.window_state)
        return settings

    def remember_file(self, path: str | Path) -> None:
        p = str(Path(path))
        self.last_directory = str(Path(p).parent)
        self.last_file = Path(p).name
        self.recent_files = [x for x in self.recent_files if x != p]
        self.recent_files.append(p)
        self.recent_files = self.recent_files[-4:]

    def save(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        root = ET.Element("notizen-alx")
        ET.SubElement(root, "scrolls", {"choice": str(self.scrollbars_choice)})
        ET.SubElement(root, "saftycopies", {"amount": str(self.backup_keep)})
        ET.SubElement(
            root,
            "autorun",
            {
                "if": "yes" if self.autorun_enabled else "no",
                "minimized": "yes" if self.autorun_minimized else "no",
            },
        )
        ET.SubElement(
            root,
            "ftp",
            {
                "name": self.ftp_username,
                "pass": self.ftp_password,
                "host": self.ftp_host,
                "path": self.ftp_path,
            },
        )
        recent = {key: value for key, value in zip(("a", "b", "c", "d"), self.recent_files[-4:])}
        for key in ("a", "b", "c", "d"):
            recent.setdefault(key, "")
        ET.SubElement(root, "files", recent)
        ET.SubElement(root, "language", {"choice": self.language})
        ET.SubElement(root, "open", {"file": self.last_file, "directory": self.last_directory})
        ET.SubElement(
            root,
            "main-form",
            {
                "x": str(self.window_x),
                "y": str(self.window_y),
                "width": str(self.window_width),
                "height": str(self.window_height),
                "windowstate": self.window_state,
            },
        )
        ET.SubElement(root, "minimized-show-in", {"taskbar": "yes" if self.show_in_taskbar_when_minimized else "no"})
        ET.SubElement(root, "desknotes", {"show_desknote_borders": "yes" if self.show_desknote_borders else "no"})
        tool_stripes = ET.SubElement(root, "tool-stripes")
        for name in ("haupt", "elements", "font", "cutpastecopy"):
            ET.SubElement(tool_stripes, name, {"x": "0", "y": "0"})
        ET.SubElement(root, "x", {"y": "0", "z": "0", "a": str(self.autosave_seconds)})
        tree = ET.ElementTree(root)
        tree.write(self.path, encoding="utf-16", xml_declaration=True)
