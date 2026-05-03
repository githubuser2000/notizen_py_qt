"""Python/Qt continuation port of the legacy Notizen.NET application."""

from .models import (
    DesktopNoteState,
    NoteDocument,
    NoteNode,
    legacy_delete_fallback_node,
    legacy_new_next_node,
    legacy_new_next_parent,
    legacy_can_move_before_target,
    legacy_move_before_target,
    legacy_paste_clone,
    legacy_previous_visible_node,
    legacy_visible_walk,
)
from .alx_io import backup_directory_for, create_backup, dump_alx_bytes, list_backups, load_alx, load_alx_bytes, save_alx
from .settings import legacy_autosave_should_save, normalize_autosave_seconds, normalize_window_state
from .tray_support import decide_startup_tray_visibility, is_gnome_session
from .startup import StartupTargetValidation, build_autostart_command, legacy_autostart_arguments, validate_legacy_startup_target
from .desktop_note_legacy import legacy_opacity_percent_for_transparency_percent, legacy_transparency_menu_options
from .legacy_paths import LEGACY_DEFAULT_FILENAME, legacy_documents_notizen_dir, split_legacy_file_location
from .search_results import SearchHitView, build_search_hit_views, legacy_search_result_label, legacy_search_snippet, node_path
from .editor_legacy import legacy_clipboard_bullet_text, qt_bullet_insert_text
from .rtf_utils import bmp_to_dib_bytes, dib_to_bmp_bytes
from .window_visibility import VisibleWindowGeometry, env_requests_window_reset, legacy_window_state_is_restorable, sanitize_legacy_window_geometry, should_start_minimized

__all__ = [
    "DesktopNoteState",
    "NoteDocument",
    "NoteNode",
    "legacy_paste_clone",
    "legacy_new_next_parent",
    "legacy_new_next_node",
    "legacy_can_move_before_target",
    "legacy_move_before_target",
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
    "StartupTargetValidation",
    "validate_legacy_startup_target",
    "legacy_clipboard_bullet_text",
    "qt_bullet_insert_text",
    "node_path",
    "legacy_search_snippet",
    "legacy_search_result_label",
    "build_search_hit_views",
    "SearchHitView",
    "bmp_to_dib_bytes",
    "dib_to_bmp_bytes",
    "VisibleWindowGeometry",
    "sanitize_legacy_window_geometry",
    "legacy_window_state_is_restorable",
    "should_start_minimized",
    "env_requests_window_reset",
]

__version__ = "0.10.10"
