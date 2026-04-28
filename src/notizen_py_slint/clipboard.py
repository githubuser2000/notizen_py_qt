from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any

from .config import config_dir
from .model import Note
from .storage import NotizenFileError, note_from_dict, note_to_dict

CLIPBOARD_FORMAT = "notizen-py-slint-node-clipboard"
CLIPBOARD_VERSION = 1


class NotizenClipboardError(NotizenFileError):
    pass


@dataclass(slots=True)
class ClipboardEntry:
    """Portable replacement for Notizen.NET's in-process TreeNode clipboard."""

    note: Note
    created: float
    source_path: str = ""
    source_path_titles: list[str] | None = None
    cut: bool = False

    @property
    def title(self) -> str:
        return self.note.title

    def as_dict(self) -> dict[str, Any]:
        return {
            "format": CLIPBOARD_FORMAT,
            "version": CLIPBOARD_VERSION,
            "created": self.created,
            "source_path": self.source_path,
            "source_path_titles": self.source_path_titles or [],
            "cut": self.cut,
            "note": note_to_dict(self.note),
        }

    def summary(self) -> str:
        mode = "Ausschneiden" if self.cut else "Kopieren"
        path = " / ".join(self.source_path_titles or [])
        source = f" aus {self.source_path}" if self.source_path else ""
        location = f" [{path}]" if path else ""
        return f"{mode}: {self.title}{location}{source}"


def clipboard_path() -> Path:
    return config_dir() / "node-clipboard.json"


def summarize_note(note: Note) -> dict[str, int | str]:
    notes = 0
    characters = 0
    max_depth = 0

    def rec(current: Note, depth: int) -> None:
        nonlocal notes, characters, max_depth
        notes += 1
        characters += len(current.text)
        max_depth = max(max_depth, depth)
        for child in current.children:
            rec(child, depth + 1)

    rec(note, 0)
    return {"title": note.title, "notes": notes, "nodes": notes, "characters": characters, "max_depth": max_depth}


def plain_text_preview(note: Note, *, max_chars: int = 160) -> str:
    text = "\n".join(line.strip() for line in note.text.splitlines()).strip()
    if len(text) > max_chars:
        return text[: max(0, max_chars - 1)].rstrip() + "…"
    return text


def make_clipboard_entry(note: Note, *, source_path: str | None = None, cut: bool = False) -> ClipboardEntry:
    return ClipboardEntry(
        note=note.clone_deep(),
        created=time.time(),
        source_path=str(source_path or ""),
        source_path_titles=note.path_titles(),
        cut=bool(cut),
    )


def note_to_clipboard_text(note: Note, *, source_path: str | None = None, cut: bool = False) -> str:
    return json.dumps(make_clipboard_entry(note, source_path=source_path, cut=cut).as_dict(), indent=2, ensure_ascii=False)


def entry_from_clipboard_text(text: str) -> ClipboardEntry:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise NotizenClipboardError(f"Zwischenablage ist kein gültiges JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("format") != CLIPBOARD_FORMAT:
        raise NotizenClipboardError("Zwischenablage enthält keinen Notizen-Knoten.")
    note_data = data.get("note")
    if not isinstance(note_data, dict):
        raise NotizenClipboardError("Zwischenablage enthält keine Notizdaten.")
    titles = data.get("source_path_titles")
    if not isinstance(titles, list):
        titles = []
    return ClipboardEntry(
        note=note_from_dict(note_data),
        created=float(data.get("created") or 0),
        source_path=str(data.get("source_path") or ""),
        source_path_titles=[str(item) for item in titles],
        cut=bool(data.get("cut", False)),
    )


def note_from_clipboard_text(text: str) -> Note:
    return entry_from_clipboard_text(text).note


def write_clipboard_file(note: Note, path: str | Path | None = None, *, source_path: str | None = None, cut: bool = False) -> Path:
    target = Path(path) if path is not None else clipboard_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(note_to_clipboard_text(note, source_path=source_path, cut=cut), encoding="utf-8")
    return target


def read_clipboard_file(path: str | Path | None = None) -> ClipboardEntry:
    target = Path(path) if path is not None else clipboard_path()
    if not target.exists():
        raise NotizenClipboardError(f"Keine Notizen-Zwischenablage gefunden: {target}")
    return entry_from_clipboard_text(target.read_text(encoding="utf-8"))


# Compatibility aliases for older internal callers during the port.
def write_clipboard_note(note: Note, *, source_path: str | None = None, cut: bool = False) -> ClipboardEntry:
    write_clipboard_file(note, source_path=source_path, cut=cut)
    return read_clipboard_file()


def read_clipboard_entry(path: str | Path | None = None) -> ClipboardEntry:
    return read_clipboard_file(path)


def clear_clipboard(path: str | Path | None = None) -> bool:
    target = Path(path) if path is not None else clipboard_path()
    try:
        target.unlink()
        return True
    except FileNotFoundError:
        return False


def clipboard_info(path: str | Path | None = None) -> dict[str, Any]:
    entry = read_clipboard_file(path)
    info = entry.as_dict()
    info.pop("note", None)
    info.update(summarize_note(entry.note))
    info["summary"] = entry.summary()
    info["preview"] = plain_text_preview(entry.note)
    info["path"] = str(Path(path) if path is not None else clipboard_path())
    return info


def try_copy_to_system_clipboard(text: str) -> tuple[bool, str]:
    """Best-effort system clipboard write without external dependencies."""
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True, "System-Zwischenablage beschrieben"
    except Exception as exc:  # noqa: BLE001 - desktop/headless/toolkit differences
        return False, f"System-Zwischenablage nicht verfügbar: {exc}"


def try_read_system_clipboard() -> tuple[bool, str]:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return True, str(text)
    except Exception as exc:  # noqa: BLE001
        return False, f"System-Zwischenablage nicht verfügbar: {exc}"
