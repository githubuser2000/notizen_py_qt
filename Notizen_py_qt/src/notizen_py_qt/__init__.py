"""Python/Qt continuation port of the legacy Notizen.NET application."""

from .models import DesktopNoteState, NoteDocument, NoteNode, legacy_paste_clone
from .alx_io import backup_directory_for, create_backup, dump_alx_bytes, list_backups, load_alx, load_alx_bytes, save_alx
from .settings import normalize_autosave_seconds, normalize_window_state
from .startup import build_autostart_command, legacy_autostart_arguments
from .desktop_note_legacy import legacy_opacity_percent_for_transparency_percent, legacy_transparency_menu_options
from .legacy_paths import LEGACY_DEFAULT_FILENAME, legacy_documents_notizen_dir, split_legacy_file_location

__all__ = [
    "DesktopNoteState",
    "NoteDocument",
    "NoteNode",
    "legacy_paste_clone",
    "backup_directory_for",
    "create_backup",
    "list_backups",
    "load_alx",
    "load_alx_bytes",
    "dump_alx_bytes",
    "save_alx",
    "normalize_autosave_seconds",
    "normalize_window_state",
    "legacy_opacity_percent_for_transparency_percent",
    "legacy_transparency_menu_options",
    "LEGACY_DEFAULT_FILENAME",
    "legacy_documents_notizen_dir",
    "split_legacy_file_location",
    "build_autostart_command",
    "legacy_autostart_arguments",
]

__version__ = "0.10.1"
