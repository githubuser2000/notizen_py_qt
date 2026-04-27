from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path


def config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "notizen-pypy-slint"


@dataclass(slots=True)
class AppConfig:
    last_file: str | None = None
    recent_files: list[str] = field(default_factory=list)
    backup_count: int = 30
    autosave_seconds: int = 0
    language: str = "de"

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
        text = str(Path(path))
        self.last_file = text
        self.recent_files = [p for p in self.recent_files if p != text]
        self.recent_files.insert(0, text)
        self.recent_files = self.recent_files[:4]

    # Backward-compatible name used while porting.
    remember_file = add_recent


def load_config() -> AppConfig:
    return AppConfig.load()


def save_config(config: AppConfig) -> None:
    config.save()
