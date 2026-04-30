from __future__ import annotations

"""Default file locations inherited from the old ``Datei.vb`` helper.

The original WinForms app created a ``Notizen`` directory inside the user's
Documents folder and used ``unbenannt.alx`` as the initial filename.  The Python
port keeps this behavior as a small, testable helper instead of baking it into a
window-only workflow.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import sys

DEFAULT_FILE_NAME = "unbenannt.alx"
DEFAULT_FOLDER_NAME = "Notizen"


@dataclass(slots=True, frozen=True)
class DefaultPaths:
    documents_dir: str
    notes_dir: str
    default_file: str
    created_notes_dir: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def documents_directory() -> Path:
    """Return a best-effort equivalent of ``SpecialDirectories.MyDocuments``."""
    if sys.platform.startswith("win"):
        value = os.environ.get("USERPROFILE")
        if value:
            return Path(value) / "Documents"
    xdg_docs = Path.home() / "Documents"
    return xdg_docs


def notes_directory(*, create: bool = False) -> Path:
    path = documents_directory() / DEFAULT_FOLDER_NAME
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def default_file_path(*, create_dir: bool = False) -> Path:
    return notes_directory(create=create_dir) / DEFAULT_FILE_NAME


def default_paths(*, create: bool = False) -> DefaultPaths:
    docs = documents_directory()
    notes = docs / DEFAULT_FOLDER_NAME
    existed = notes.exists()
    if create:
        notes.mkdir(parents=True, exist_ok=True)
    return DefaultPaths(
        documents_dir=str(docs),
        notes_dir=str(notes),
        default_file=str(notes / DEFAULT_FILE_NAME),
        created_notes_dir=bool(create and not existed and notes.exists()),
    )
