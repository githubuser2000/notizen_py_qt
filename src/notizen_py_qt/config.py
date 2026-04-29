from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
from urllib.parse import quote


def config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "notizen-py-qt"


@dataclass(slots=True)
class AppConfig:
    last_file: str | None = None
    recent_files: list[str] = field(default_factory=list)
    backup_count: int = 30
    autosave_seconds: int = 0
    language: str = "de"
    autorun: bool = False
    autorun_minimized: bool = False
    show_in_taskbar: bool = True
    show_desknote_borders: bool = True
    scrollbars_choice: int = 3
    window_x: int | None = None
    window_y: int | None = None
    window_width: int | None = None
    window_height: int | None = None
    window_state: str = "normal"
    ftp_host: str = ""
    ftp_username: str = ""
    ftp_password: str = ""
    ftp_path: str = ""
    ftp_use_tls: bool = False
    toolstrip_positions: dict[str, list[int]] = field(default_factory=lambda: {
        "haupt": [0, 0],
        "elements": [0, 0],
        "font": [0, 0],
        "cutpastecopy": [0, 0],
    })

    @classmethod
    def load(cls) -> "AppConfig":
        path = config_dir() / "config.json"
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            allowed = {field.name for field in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
            return cls(**{k: v for k, v in data.items() if k in allowed})
        except Exception:
            return cls()

    def save(self) -> None:
        path = config_dir() / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")

    def add_recent(self, path: str | Path) -> None:
        text = str(path)
        self.last_file = text
        self.recent_files = [p for p in self.recent_files if p != text]
        self.recent_files.insert(0, text)
        self.recent_files = self.recent_files[:4]

    def set_toolstrip_position(self, name: str, x: int, y: int) -> None:
        key = (name or "").strip().lower()
        if key not in {"haupt", "elements", "font", "cutpastecopy"}:
            raise ValueError("Toolstrip muss haupt, elements, font oder cutpastecopy sein")
        self.toolstrip_positions[key] = [int(x), int(y)]

    def toolstrip_position(self, name: str) -> tuple[int, int]:
        value = self.toolstrip_positions.get((name or "").strip().lower(), [0, 0])
        try:
            return int(value[0]), int(value[1])
        except Exception:
            return 0, 0

    def default_remote_url(self) -> str:
        if not self.ftp_host:
            return ""
        scheme = "ftps" if self.ftp_use_tls else "ftp"
        auth = ""
        if self.ftp_username:
            auth = quote(self.ftp_username, safe="")
            if self.ftp_password:
                auth += ":" + quote(self.ftp_password, safe="")
            auth += "@"
        path = self.ftp_path or "/notizen.alx"
        if not path.startswith("/"):
            path = "/" + path
        return f"{scheme}://{auth}{self.ftp_host}{path}"

    # Backward-compatible name used while porting.
    remember_file = add_recent


def load_config() -> AppConfig:
    return AppConfig.load()


def save_config(config: AppConfig) -> None:
    config.save()
