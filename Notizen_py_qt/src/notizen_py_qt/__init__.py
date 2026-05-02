"""Python/Qt continuation port of the legacy Notizen.NET application."""

from .models import (
    DesktopNoteState,
    NoteDocument,
    NoteNode,
    legacy_delete_fallback_node,
    legacy_new_next_node,
    legacy_new_next_parent,
    legacy_paste_clone,
    legacy_previous_visible_node,
    legacy_visible_walk,
)
from .alx_io import backup_directory_for, create_backup, dump_alx_bytes, list_backups, load_alx, load_alx_bytes, save_alx
from .settings import legacy_autosave_should_save, normalize_autosave_seconds, normalize_window_state
from .tray_support import decide_startup_tray_visibility, is_gnome_session
from .startup import build_autostart_command, legacy_autostart_arguments
from .desktop_note_legacy import legacy_opacity_percent_for_transparency_percent, legacy_transparency_menu_options
from .legacy_paths import LEGACY_DEFAULT_FILENAME, legacy_documents_notizen_dir, split_legacy_file_location
from .search_results import SearchHitView, build_search_hit_views, legacy_search_result_label, legacy_search_snippet, node_path

__all__ = [
    "DesktopNoteState",
    "NoteDocument",
    "NoteNode",
    "legacy_paste_clone",
    "legacy_new_next_parent",
    "legacy_new_next_node",
    "legacy_visible_walk",
    "legacy_previous_visible_node",
    "legacy_delete_fallback_node",
    "backup_directory_for",
    "create_backup",
    "list_backups",
    "load_alx",
    "load_alx_bytes",
    "dump_alx_bytes",
    "save_alx",
    "normalize_autosave_seconds",
    "legacy_autosave_should_save",
    "normalize_window_state",
    "decide_startup_tray_visibility",
    "is_gnome_session",
    "legacy_opacity_percent_for_transparency_percent",
    "legacy_transparency_menu_options",
    "LEGACY_DEFAULT_FILENAME",
    "legacy_documents_notizen_dir",
    "split_legacy_file_location",
    "build_autostart_command",
    "legacy_autostart_arguments",
    "node_path",
    "legacy_search_snippet",
    "legacy_search_result_label",
    "build_search_hit_views",
    "SearchHitView",
]

__version__ = "0.10.7"
