"""Python/Qt continuation port of the legacy Notizen.NET application."""

from .models import DesktopNoteState, NoteDocument, NoteNode, legacy_paste_clone
from .alx_io import dump_alx_bytes, load_alx, load_alx_bytes, save_alx

__all__ = [
    "DesktopNoteState",
    "NoteDocument",
    "NoteNode",
    "legacy_paste_clone",
    "load_alx",
    "load_alx_bytes",
    "dump_alx_bytes",
    "save_alx",
]

__version__ = "0.9.6"
