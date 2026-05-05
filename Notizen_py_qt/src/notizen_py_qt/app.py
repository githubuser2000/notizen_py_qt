from __future__ import annotations

import argparse
import base64
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .alarms import AlarmSpec, describe_recurrence, legacy_wecker_weekday_labels, next_occurrence
from .alx_io import AlxError, InvalidPassword, PasswordRequired, backup_directory_for, create_backup, dump_alx_bytes, list_backups, load_alx, load_alx_bytes, save_alx, normalize_password
from .exporters import create_unified_note, tree_to_plain_text, tree_to_rtf, tree_to_text_bytes
from .editor_legacy import qt_bullet_insert_text
from .html_export import HtmlExportOptions, tree_to_html_bytes
from .ftp_sync import FtpSyncError, FtpTarget
from .feedback import (
    LEGACY_FEEDBACK_EMAIL,
    LEGACY_FEEDBACK_WEB_URL,
    legacy_feedback_decision,
    legacy_feedback_next_state,
    write_local_feedback_archive,
)
from .i18n import available_languages, tr
from .keyboard_legacy import legacy_shortcut_action
from .legacy_colors import legacy_light_color_argb
from .legacy_paths import LEGACY_DEFAULT_FILENAME, ensure_legacy_documents_notizen_dir
from .models import DesktopNoteState, NoteDocument, NoteNode, legacy_can_move_before_target, legacy_delete_fallback_node, legacy_move_before_target, legacy_new_next_node, legacy_paste_clone
from .desktop_note_legacy import (
    LEGACY_DESKNOTE_AUTORESIZE_IDLE_MS,
    LEGACY_DESKNOTE_AUTORESIZE_SCROLL_PAD,
    LEGACY_DESKNOTE_AUTORESIZE_STEP,
    LEGACY_DESKNOTE_AUTORESIZE_WORK_AREA_PAD,
    LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT,
    LegacyDeskNoteCursor,
    LegacyDeskNoteMouseAction,
    LegacyDeskNoteRect,
    legacy_desknote_clamp_to_work_area,
    legacy_desknote_cursor_for_move_action,
    legacy_desknote_editor_rect,
    legacy_desknote_hidden_border_geometry,
    legacy_desknote_hover_geometry,
    legacy_desknote_label_geometry,
    legacy_desknote_mouse_down_action,
    legacy_desknote_mouse_move_action,
    legacy_desknote_move_geometry,
    legacy_desknote_opacity_for_active,
    legacy_desknote_opacity_for_inactive,
    legacy_desknote_resize_geometry,
    legacy_desknote_show2_geometry,
    legacy_transparency_menu_options,
)
from .node_clipboard import NODE_MIME_TYPE, looks_like_node_clipboard_xml, node_from_clipboard_xml, node_to_clipboard_xml
from .startup import apply_windows_autostart_script, parse_legacy_startup_args, validate_legacy_startup_target
from .tray_support import decide_startup_tray_visibility, gnome_tray_install_hint
from .display_env import append_startup_log, normalize_qt_display_environment
from .window_visibility import env_requests_window_reset, legacy_window_state_is_restorable, sanitize_legacy_window_geometry, should_start_minimized
from .rtf_utils import html_to_rtf, plain_text_to_rtf, rtf_to_desktop_html, rtf_to_html, rtf_to_plain_text
from .search_logic import SearchResult, search_nodes
from .search_results import SearchHitView, build_search_hit_views
from .settings import AppSettings, legacy_autosave_should_save, normalize_autosave_seconds, normalize_window_state
from .stats import collect_tree_stats

APP_DESKTOP_ID = "notizen-py-qt"
APP_DISPLAY_NAME = "Notizen PyQt"
APP_ORGANIZATION_NAME = "Notizen.NET Migration"


_DISPLAY_ENV_DECISION = normalize_qt_display_environment(sys.argv[1:])
append_startup_log(
    "PRE_QT_ENV %s"
    % _DISPLAY_ENV_DECISION.summary()
)

try:  # Importing is optional so tests and CLI helpers work without Qt installed.
    from .qt_compat import load_qt

    BINDING, QtCore, QtGui, QtWidgets = load_qt()
    QT_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - exercised on systems without Qt
    BINDING = ""
    QtCore = QtGui = QtWidgets = None  # type: ignore[assignment]
    QT_IMPORT_ERROR = exc


def _load_qt_print_support() -> Any:
    """Load QtPrintSupport lazily from the active Qt binding.

    Printing is optional in tests and command-line helpers, so the main module is
    allowed to import without Qt.  At print time, however, retry both supported
    bindings instead of relying only on the module-level ``BINDING`` value.
    """
    tried: list[str] = []
    candidates = [BINDING, "PySide6", "PyQt6"]
    for binding in candidates:
        if not binding or binding in tried:
            continue
        tried.append(binding)
        try:
            if binding == "PySide6":
                from PySide6 import QtPrintSupport  # type: ignore

                return QtPrintSupport
            if binding == "PyQt6":
                from PyQt6 import QtPrintSupport  # type: ignore

                return QtPrintSupport
        except Exception:
            continue
    raise RuntimeError("QtPrintSupport ist nicht verfügbar; bitte PySide6/PyQt6 mit Druckunterstützung installieren.")


def _enum(parent: Any, enum_name: str, value_name: str) -> Any:
    enum_obj = getattr(parent, enum_name, None)
    if enum_obj is not None:
        return getattr(enum_obj, value_name)
    return getattr(parent, value_name)


if QtWidgets is not None:
    USER_ROLE = _enum(QtCore.Qt, "ItemDataRole", "UserRole")
    YES = _enum(QtWidgets.QMessageBox, "StandardButton", "Yes")
    NO = _enum(QtWidgets.QMessageBox, "StandardButton", "No")
    CANCEL = _enum(QtWidgets.QMessageBox, "StandardButton", "Cancel")
    OK = _enum(QtWidgets.QMessageBox, "StandardButton", "Ok")
    ACCEPTED = _enum(QtWidgets.QDialog, "DialogCode", "Accepted")
    SELECT_ROWS = _enum(QtWidgets.QAbstractItemView, "SelectionBehavior", "SelectRows")
    INTERNAL_MOVE = _enum(QtWidgets.QAbstractItemView, "DragDropMode", "InternalMove")
    EXTENDED_SELECTION = _enum(QtWidgets.QAbstractItemView, "SelectionMode", "ExtendedSelection")
    MOVE_ACTION = _enum(QtCore.Qt, "DropAction", "MoveAction")
    ITEM_EDITABLE = _enum(QtCore.Qt, "ItemFlag", "ItemIsEditable")
    ITEM_SELECTABLE = _enum(QtCore.Qt, "ItemFlag", "ItemIsSelectable")
    ITEM_ENABLED = _enum(QtCore.Qt, "ItemFlag", "ItemIsEnabled")
    ITEM_DRAG = _enum(QtCore.Qt, "ItemFlag", "ItemIsDragEnabled")
    ITEM_DROP = _enum(QtCore.Qt, "ItemFlag", "ItemIsDropEnabled")
    LEFT_BUTTON = _enum(QtCore.Qt, "MouseButton", "LeftButton")
    WINDOW = _enum(QtCore.Qt, "WindowType", "Window")
    TOOL = _enum(QtCore.Qt, "WindowType", "Tool")
    FRAMELESS = _enum(QtCore.Qt, "WindowType", "FramelessWindowHint")
    try:
        WINDOW_STAYS_ON_BOTTOM_HINT = _enum(QtCore.Qt, "WindowType", "WindowStaysOnBottomHint")
    except Exception:
        WINDOW_STAYS_ON_BOTTOM_HINT = 0
    CTRL = _enum(QtCore.Qt, "KeyboardModifier", "ControlModifier")
    SHIFT = _enum(QtCore.Qt, "KeyboardModifier", "ShiftModifier")
    ALT = _enum(QtCore.Qt, "KeyboardModifier", "AltModifier")
    CUSTOM_CONTEXT_MENU = _enum(QtCore.Qt, "ContextMenuPolicy", "CustomContextMenu")
    NO_CONTEXT_MENU = _enum(QtCore.Qt, "ContextMenuPolicy", "NoContextMenu")
    NO_TEXT_INTERACTION = _enum(QtCore.Qt, "TextInteractionFlag", "NoTextInteraction")
    ARROW_CURSOR = _enum(QtCore.Qt, "CursorShape", "ArrowCursor")
    SIZE_ALL_CURSOR = _enum(QtCore.Qt, "CursorShape", "SizeAllCursor")
    SIZE_FDIAG_CURSOR = _enum(QtCore.Qt, "CursorShape", "SizeFDiagCursor")
    POINTING_HAND_CURSOR = _enum(QtCore.Qt, "CursorShape", "PointingHandCursor")
    MOUSE_PRESS_EVENT = _enum(QtCore.QEvent, "Type", "MouseButtonPress")
    MOUSE_MOVE_EVENT = _enum(QtCore.QEvent, "Type", "MouseMove")
    MOUSE_RELEASE_EVENT = _enum(QtCore.QEvent, "Type", "MouseButtonRelease")
    MOUSE_DOUBLE_EVENT = _enum(QtCore.QEvent, "Type", "MouseButtonDblClick")
    KEY_PRESS_EVENT = _enum(QtCore.QEvent, "Type", "KeyPress")
    ENTER_EVENT = _enum(QtCore.QEvent, "Type", "Enter")
    LEAVE_EVENT = _enum(QtCore.QEvent, "Type", "Leave")
    ALIGN_CENTER = _enum(QtCore.Qt, "AlignmentFlag", "AlignCenter")

    def color_from_argb(argb: int) -> Any:
        value = argb & 0xFFFFFFFF
        a = (value >> 24) & 0xFF
        r = (value >> 16) & 0xFF
        g = (value >> 8) & 0xFF
        b = value & 0xFF
        return QtGui.QColor(r, g, b, a or 255)

    def argb_from_color(color: Any) -> int:
        value = (
            ((color.alpha() & 0xFF) << 24)
            | ((color.red() & 0xFF) << 16)
            | ((color.green() & 0xFF) << 8)
            | (color.blue() & 0xFF)
        )
        if value >= 2**31:
            value -= 2**32
        return int(value)

    def app_icon() -> Any:
        """Return the legacy Notizen icon from Qt resources or package data."""
        try:
            from . import resources_rc as _resources_rc  # noqa: F401
        except Exception:
            pass
        icon = QtGui.QIcon(":/notizen/notizen.png")
        if not icon.isNull():
            return icon
        try:
            from importlib import resources as importlib_resources

            data = importlib_resources.files("notizen_py_qt.resources").joinpath("notizen.png").read_bytes()
            pixmap = QtGui.QPixmap()
            if pixmap.loadFromData(data, "PNG"):
                icon = QtGui.QIcon()
                icon.addPixmap(pixmap)
                return icon
        except Exception:
            pass
        return QtGui.QIcon()

    def configure_qt_application_identity(app: Any | None = None) -> None:
        """Set GNOME/Wayland/X11 runtime identity to match notizen-py-qt.desktop."""

        os.environ.setdefault("RESOURCE_NAME", APP_DESKTOP_ID)
        try:
            QtCore.QCoreApplication.setApplicationName(APP_DESKTOP_ID)
        except Exception:
            pass
        try:
            QtCore.QCoreApplication.setOrganizationName(APP_ORGANIZATION_NAME)
        except Exception:
            pass
        try:
            from . import __version__ as _runtime_version

            QtCore.QCoreApplication.setApplicationVersion(str(_runtime_version))
        except Exception:
            pass
        if app is None:
            return
        try:
            if hasattr(app, "setApplicationDisplayName"):
                app.setApplicationDisplayName(APP_DISPLAY_NAME)
        except Exception:
            pass
        try:
            if hasattr(app, "setDesktopFileName"):
                # Qt/GNOME expects the basename without the .desktop suffix.
                app.setDesktopFileName(APP_DESKTOP_ID)
        except Exception:
            pass
        try:
            icon = app_icon()
            if not icon.isNull():
                app.setWindowIcon(icon)
        except Exception:
            pass

    def _event_pos(event: Any) -> Any:
        try:
            return event.position().toPoint()
        except Exception:
            return event.pos()

    class LegacyTreeWidget(QtWidgets.QTreeWidget):
        """QTreeWidget with the old Notizen.NET sibling-before-target drop rule."""

        def __init__(self, main_window: "MainWindow") -> None:
            super().__init__(main_window)
            self.main_window = main_window
            self._legacy_drag_source_item: Any | None = None

        def mousePressEvent(self, event: Any) -> None:
            if event.button() == LEFT_BUTTON:
                self._legacy_drag_source_item = self.itemAt(_event_pos(event))
            super().mousePressEvent(event)

        def dropEvent(self, event: Any) -> None:
            source_item = self._legacy_drag_source_item or self.currentItem()
            target_item = self.itemAt(_event_pos(event))
            source = source_item.data(0, USER_ROLE) if source_item is not None else None
            target = target_item.data(0, USER_ROLE) if target_item is not None else None
            if not isinstance(source, NoteNode) or not isinstance(target, NoteNode):
                event.ignore()
                return
            if not legacy_can_move_before_target(source, target):
                event.ignore()
                return
            self.main_window.save_current_editor_to_node()
            moved = legacy_move_before_target(source, target)
            if moved is None:
                event.ignore()
                return
            self.main_window.build_tree()
            self.main_window.select_node(moved)
            self.main_window.document.mark_changed()
            self.main_window.update_title()
            self.main_window.update_tray_menu()
            self._legacy_drag_source_item = None
            event.acceptProposedAction()

    class DesktopNoteWindow(QtWidgets.QWidget):
        """Legacy-style frameless desktop note from ``desknote.vb``.

        The old WinForms form was not an editable floating QTextEdit.  It was a
        read-only sticky note: a compact text-only rectangle when idle, a
        custom title/border strip on hover, left/right title hot zones for
        hide/remove, drag-to-move almost everywhere and a lower-right resize
        handle while expanded.
        """

        def __init__(self, main_window: "MainWindow", node: NoteNode) -> None:
            # Sticky notes must be independent top-level windows.  Using the
            # main window as parent plus Qt.Tool makes some GNOME/window-manager
            # combinations ignore taskbar minimization and window opacity.
            flags = WINDOW | FRAMELESS
            if WINDOW_STAYS_ON_BOTTOM_HINT:
                flags |= WINDOW_STAYS_ON_BOTTOM_HINT
            super().__init__(None, flags)
            self.main_window = main_window
            self.node = node
            self.setObjectName(f"{APP_DESKTOP_ID}-desktop-note")
            icon = app_icon()
            if not icon.isNull():
                self.setWindowIcon(icon)
            if self.node.desktop_note is None:
                self.node.desktop_note = main_window.default_desktop_note_state()
            self.setWindowTitle(node.title)
            self.setAttribute(_enum(QtCore.Qt, "WidgetAttribute", "WA_DeleteOnClose"), False)
            try:
                self.setAttribute(_enum(QtCore.Qt, "WidgetAttribute", "WA_TranslucentBackground"), True)
            except Exception:
                pass
            self.setMouseTracking(True)
            self._loading = False
            self._desired_opacity = 0.85
            self._expanded = False
            self._geometry_transition = False
            self._drag_move = False
            self._drag_resize = False
            self._system_drag_move = False
            self._system_drag_resize = False
            self._drag_offset_x = 0
            self._drag_offset_y = 0
            self._title_dark = False
            self._scroll_manual = True
            self._auto_resize_in_progress = False

            self._geometry_store_timer = QtCore.QTimer(self)
            self._geometry_store_timer.setSingleShot(True)
            self._geometry_store_timer.setInterval(500)
            self._geometry_store_timer.timeout.connect(self._store_after_system_geometry_change)

            self._auto_resize_timer = QtCore.QTimer(self)
            self._auto_resize_timer.setSingleShot(True)
            self._auto_resize_timer.setInterval(LEGACY_DESKNOTE_AUTORESIZE_IDLE_MS)
            self._auto_resize_timer.timeout.connect(self._set_clientsizes)

            self.editor = QtWidgets.QTextEdit(self)
            self._editor_opacity_effect: Any | None = None
            try:
                self._editor_opacity_effect = QtWidgets.QGraphicsOpacityEffect(self.editor)
                self.editor.setGraphicsEffect(self._editor_opacity_effect)
            except Exception:
                self._editor_opacity_effect = None
            self.editor.setAcceptRichText(True)
            self.editor.setReadOnly(True)
            self.editor.setFrameShape(_enum(QtWidgets.QFrame, "Shape", "NoFrame"))
            self.editor.setContentsMargins(0, 0, 0, 0)
            try:
                self.editor.viewport().setContentsMargins(0, 0, 0, 0)
            except Exception:
                pass
            self._apply_desktop_note_text_layout()
            self.editor.setHtml(rtf_to_desktop_html(node.rtf))
            self._apply_desktop_note_text_layout()
            self._compact_desktop_note_blocks()
            self.editor.setMouseTracking(True)
            self.editor.setCursor(QtGui.QCursor(SIZE_ALL_CURSOR))
            self.editor.setContextMenuPolicy(CUSTOM_CONTEXT_MENU)
            try:
                self.editor.setTextInteractionFlags(NO_TEXT_INTERACTION)
            except Exception:
                pass
            self.editor.customContextMenuRequested.connect(
                lambda pos: self._show_context_menu(self.editor.mapToGlobal(pos))
            )
            self.editor.installEventFilter(self)
            self.editor.viewport().installEventFilter(self)
            try:
                self.editor.document().contentsChanged.connect(self._schedule_auto_resize_from_content)
                self.editor.verticalScrollBar().rangeChanged.connect(lambda _minimum, _maximum: self._schedule_auto_resize_from_scroll())
                self.editor.horizontalScrollBar().rangeChanged.connect(lambda _minimum, _maximum: self._schedule_auto_resize_from_scroll())
            except Exception:
                pass

            self.title_label = QtWidgets.QLabel(node.title, self)
            self._title_opacity_effect: Any | None = None
            try:
                self._title_opacity_effect = QtWidgets.QGraphicsOpacityEffect(self.title_label)
                self.title_label.setGraphicsEffect(self._title_opacity_effect)
            except Exception:
                self._title_opacity_effect = None
            self.title_label.setAlignment(ALIGN_CENTER)
            self.title_label.setMouseTracking(True)
            self.title_label.installEventFilter(self)
            self.title_label.hide()

            self.setContextMenuPolicy(CUSTOM_CONTEXT_MENU)
            self.customContextMenuRequested.connect(lambda pos: self._show_context_menu(self.mapToGlobal(pos)))

            self._collapse_timer = QtCore.QTimer(self)
            self._collapse_timer.setInterval(4000)
            self._collapse_timer.timeout.connect(self._timer_collapse_check)
            self._collapse_timer.start()

            self._restore_geometry()

        def _qt_rect(self, rect: LegacyDeskNoteRect) -> Any:
            return QtCore.QRect(int(rect.x), int(rect.y), int(rect.width), int(rect.height))

        def _current_rect(self) -> LegacyDeskNoteRect:
            geo = self.geometry()
            return LegacyDeskNoteRect(int(geo.x()), int(geo.y()), int(geo.width()), int(geo.height()))

        def _event_global_pos(self, event: Any) -> Any:
            try:
                return event.globalPosition().toPoint()
            except Exception:
                return event.globalPos()

        def _event_local_point(self, event: Any) -> Any:
            try:
                global_pos = self._event_global_pos(event)
                return self.mapFromGlobal(global_pos)
            except Exception:
                return _event_pos(event)

        def _set_geometry_rect(self, rect: LegacyDeskNoteRect, *, transition: bool = True) -> None:
            previous = self._geometry_transition
            self._geometry_transition = transition or previous
            try:
                self.setGeometry(int(rect.x), int(rect.y), max(80, int(rect.width)), max(60, int(rect.height)))
            finally:
                self._geometry_transition = previous
            self._layout_desknote()

        def _state_rect(self) -> LegacyDeskNoteRect:
            state = self.node.desktop_note or DesktopNoteState()
            return LegacyDeskNoteRect(state.x, state.y, max(80, state.width), max(60, state.height))

        def _clamp_initial_rect(self, rect: LegacyDeskNoteRect) -> LegacyDeskNoteRect:
            try:
                screen = self.screen() or QtWidgets.QApplication.primaryScreen()
                if screen is not None:
                    available = screen.availableGeometry()
                    return legacy_desknote_clamp_to_work_area(rect, int(available.width()), int(available.height()))
            except Exception:
                pass
            return rect

        def _restore_geometry(self) -> None:
            state = self.node.desktop_note or DesktopNoteState()
            logical = self._clamp_initial_rect(self._state_rect())
            shown = legacy_desknote_show2_geometry(logical)
            self._expanded = False
            self._set_geometry_rect(shown, transition=True)
            self._desired_opacity = legacy_desknote_opacity_for_inactive(state.opacity)
            self._apply_background()
            self._apply_widget_opacity()
            self._layout_desknote()

        def show2(self) -> None:
            """Show using the old ``desknote.show2`` compact geometry."""

            self._restore_geometry()
            try:
                self.showNormal()
            except Exception:
                self.show()
            self._send_to_back()
            self._scroll_manual = False
            self._schedule_auto_resize(150)
            QtCore.QTimer.singleShot(1000, self._schedule_auto_resize)

        def _layout_desknote(self) -> None:
            editor_rect = legacy_desknote_editor_rect(self.width(), self.height(), expanded=self._expanded)
            self.editor.setGeometry(self._qt_rect(editor_rect))
            self.title_label.setVisible(self._expanded and self.main_window.settings.show_desknote_borders)
            if self.title_label.isVisible():
                self.title_label.adjustSize()
                label_rect = legacy_desknote_label_geometry(self.width(), self.title_label.width(), self.title_label.height())
                self.title_label.setGeometry(self._qt_rect(label_rect))
                fg = "black" if self._title_dark else "whitesmoke"
                self.title_label.setStyleSheet(f"background: transparent; color: {fg};")
            self.update()

        def _schedule_auto_resize(self, delay_ms: int | None = None) -> None:
            if self._loading or self._auto_resize_in_progress:
                return
            if self._drag_move or self._drag_resize or self._system_drag_move or self._system_drag_resize:
                return
            try:
                if delay_ms is None:
                    self._auto_resize_timer.start()
                else:
                    self._auto_resize_timer.start(max(0, int(delay_ms)))
            except Exception:
                pass

        def _schedule_auto_resize_from_content(self) -> None:
            if self._loading or self._auto_resize_in_progress:
                return
            self._scroll_manual = False
            self._schedule_auto_resize()

        def _schedule_auto_resize_from_scroll(self) -> None:
            if self._loading or self._auto_resize_in_progress or self._scroll_manual:
                return
            self._schedule_auto_resize()

        def _candidate_editor_viewport_size(self, window_width: int, window_height: int) -> tuple[int, int]:
            editor_rect = legacy_desknote_editor_rect(window_width, window_height, expanded=self._expanded)
            try:
                chrome_width = max(0, int(self.editor.width()) - int(self.editor.viewport().width()))
                chrome_height = max(0, int(self.editor.height()) - int(self.editor.viewport().height()))
            except Exception:
                chrome_width = 0
                chrome_height = 0
            return (
                max(1, int(editor_rect.width) - chrome_width),
                max(1, int(editor_rect.height) - chrome_height),
            )

        def _document_overflow_for_window_size(self, window_width: int, window_height: int) -> tuple[bool, bool, bool]:
            viewport_width, viewport_height = self._candidate_editor_viewport_size(window_width, window_height)
            document = self.editor.document()
            old_text_width = document.textWidth()
            try:
                document.setTextWidth(max(1, viewport_width))
                doc_size = document.size()
                ideal_width = document.idealWidth()
            finally:
                document.setTextWidth(old_text_width)
            vertical_overflow = float(doc_size.height()) > float(viewport_height + LEGACY_DESKNOTE_AUTORESIZE_SCROLL_PAD)
            horizontal_overflow = False
            try:
                no_wrap = self.editor.lineWrapMode() == QtWidgets.QTextEdit.LineWrapMode.NoWrap
            except Exception:
                try:
                    no_wrap = self.editor.lineWrapMode() == QtWidgets.QTextEdit.NoWrap
                except Exception:
                    no_wrap = False
            if no_wrap:
                horizontal_overflow = float(ideal_width) > float(viewport_width + LEGACY_DESKNOTE_AUTORESIZE_SCROLL_PAD)
            return (not vertical_overflow and not horizontal_overflow, vertical_overflow, horizontal_overflow)

        def _work_area_max_window_size(self, rect: LegacyDeskNoteRect) -> tuple[int, int]:
            try:
                screen = self.screen() or QtWidgets.QApplication.primaryScreen()
                if screen is not None:
                    available = screen.availableGeometry()
                    right = int(available.x()) + int(available.width())
                    bottom = int(available.y()) + int(available.height())
                    return (
                        max(80, right - int(rect.x) - LEGACY_DESKNOTE_AUTORESIZE_WORK_AREA_PAD),
                        max(LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT, bottom - int(rect.y) - LEGACY_DESKNOTE_AUTORESIZE_WORK_AREA_PAD),
                    )
            except Exception:
                pass
            return max(80, int(rect.width)), max(LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT, int(rect.height))

        def _auto_resize_target_rect(self) -> LegacyDeskNoteRect:
            current = self._current_rect()
            max_width, max_height = self._work_area_max_window_size(current)
            width = max(80, min(int(current.width), max_width))
            height = max(LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT, min(int(current.height), max_height))
            step = LEGACY_DESKNOTE_AUTORESIZE_STEP

            # VB ``set_clientsizes_a``: first shrink diagonally until the next
            # step would make a scrollbar necessary or hit the 111px guard.
            for _ in range(500):
                next_width = width - step
                next_height = height - step
                if next_width < 80 or next_height < LEGACY_DESKNOTE_MIN_AUTOSIZE_HEIGHT:
                    break
                fits, _vertical, _horizontal = self._document_overflow_for_window_size(next_width, next_height)
                if not fits:
                    break
                width = next_width
                height = next_height

            # VB ``set_clientsizes_b``: grow width and height while scrollbars
            # are still required and the working area allows more room.
            for _ in range(500):
                fits, vertical, horizontal = self._document_overflow_for_window_size(width, height)
                if fits:
                    break
                old = (width, height)
                if vertical:
                    if width < max_width:
                        width = min(max_width, width + step)
                    if height < max_height:
                        height = min(max_height, height + step)
                # VB ``set_clientsizes_c``: if height still overflows, continue
                # widening only; with word-wrap this often removes the vertical
                # scrollbar without making the form taller.
                if (vertical or horizontal) and width < max_width:
                    width = min(max_width, width + step)
                if old == (width, height):
                    break

            return LegacyDeskNoteRect(int(current.x), int(current.y), width, height)

        def _set_clientsizes(self) -> None:
            """Port of ``desknote.vb`` ``set_clientsizes`` for sticky notes.

            The old form reacted to RichTextBox scroll range changes by shrinking
            first and then growing in ten-pixel steps until the text viewport fit
            again.  Manual user resize/move disables this automatic correction
            until note text changes or a new scroll range appears.
            """

            if self._loading or self._auto_resize_in_progress:
                return
            if self._scroll_manual:
                return
            if self._drag_move or self._drag_resize or self._system_drag_move or self._system_drag_resize:
                return
            current = self._current_rect()
            target = self._auto_resize_target_rect()
            self._scroll_manual = True
            if target == current:
                return
            self._set_active_opacity()
            self._auto_resize_in_progress = True
            try:
                self._set_geometry_rect(target, transition=False)
            finally:
                self._auto_resize_in_progress = False
            self._store_after_user_geometry_change()
            self._restore_inactive_opacity()

        def _apply_desktop_note_text_layout(self) -> None:
            """Remove QTextEdit/HTML padding that RichTextBox did not have."""

            try:
                self.editor.document().setDocumentMargin(0)
            except Exception:
                pass
            try:
                self.editor.setViewportMargins(0, 0, 0, 0)
            except Exception:
                pass
            try:
                self.editor.document().setDefaultStyleSheet(
                    "html, body { margin:0; padding:0; line-height:100%; } "
                    "p, div { margin-top:0; margin-bottom:0; padding-top:0; padding-bottom:0; line-height:100%; }"
                )
            except Exception:
                pass
            try:
                option = self.editor.document().defaultTextOption()
                option.setWrapMode(_enum(QtGui.QTextOption, "WrapMode", "WordWrap"))
                self.editor.document().setDefaultTextOption(option)
            except Exception:
                pass

        def _compact_desktop_note_blocks(self) -> None:
            """Force WinForms RichTextBox-like compact block spacing in desk notes."""

            try:
                document = self.editor.document()
                block = document.begin()
                cursor = QtGui.QTextCursor(document)
                while block.isValid():
                    cursor.setPosition(block.position())
                    block_format = block.blockFormat()
                    block_format.setTopMargin(0)
                    block_format.setBottomMargin(0)
                    block_format.setLeftMargin(0 if block_format.leftMargin() < 0 else block_format.leftMargin())
                    block_format.setRightMargin(0 if block_format.rightMargin() < 0 else block_format.rightMargin())
                    try:
                        block_format.setLineHeight(100, QtGui.QTextBlockFormat.LineHeightTypes.ProportionalHeight)
                    except Exception:
                        try:
                            block_format.setLineHeight(100, 1)
                        except Exception:
                            pass
                    cursor.setBlockFormat(block_format)
                    block = block.next()
            except Exception:
                pass

        def _effective_desktop_opacity(self) -> float:
            return legacy_desknote_opacity_for_inactive(self._desired_opacity)

        def _apply_widget_opacity(self) -> None:
            opacity = self._effective_desktop_opacity()
            try:
                # GNOME/Wayland frequently ignores or quantizes top-level
                # QWidget.windowOpacity().  Paint the editor itself through Qt's
                # graphics effect so background and text fade together.
                if self._editor_opacity_effect is not None:
                    self._editor_opacity_effect.setOpacity(opacity)
            except Exception:
                pass
            try:
                # Keep the native top-level fully composited; otherwise the WM
                # opacity path and Qt's own opacity effect multiply each other.
                self.setWindowOpacity(1.0)
            except Exception:
                pass
            try:
                if self._title_opacity_effect is not None:
                    self._title_opacity_effect.setOpacity(opacity)
            except Exception:
                pass
            self.update()

        def _send_to_back(self) -> None:
            """Keep sticky notes behind normal application windows where Qt/WM allow it."""

            try:
                self.lower()
            except Exception:
                pass
            try:
                QtCore.QTimer.singleShot(0, self.lower)
                QtCore.QTimer.singleShot(150, self.lower)
            except Exception:
                pass

        def _qcolor_to_css_rgba(self, color: Any, alpha_multiplier: float = 1.0) -> str:
            try:
                base_alpha = max(0.0, min(1.0, float(color.alpha()) / 255.0))
                alpha = max(0.0, min(1.0, base_alpha * float(alpha_multiplier)))
                return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha:.3f})"
            except Exception:
                return str(color.name())

        def _apply_background(self) -> None:
            state = self.node.desktop_note or DesktopNoteState()
            if state.argb:
                color = color_from_argb(state.argb)
            else:
                color = color_from_argb(legacy_light_color_argb(0))
            css_color = self._qcolor_to_css_rgba(color)
            # Keep the CSS background opaque; the QGraphicsOpacityEffect below
            # fades background and text together on GNOME/Wayland.  The viewport
            # receives the same color so the old bug where only the custom frame
            # faded cannot return.
            self.editor.setStyleSheet(
                "QTextEdit { "
                f"background-color: {css_color}; "
                "border: none; padding: 0px; margin: 0px; } "
                "QTextEdit::viewport { "
                f"background-color: {css_color}; "
                "padding: 0px; margin: 0px; }"
            )
            self._apply_desktop_note_text_layout()
            self._apply_widget_opacity()
            try:
                pal = self.palette()
                pal.setColor(self.backgroundRole(), color)
                self.setPalette(pal)
                # The QTextEdit/viewport carries the note color.  Do not auto-fill
                # the top-level translucent window with an opaque palette brush.
                self.setAutoFillBackground(False)
            except Exception:
                pass
            try:
                self.editor.setAttribute(_enum(QtCore.Qt, "WidgetAttribute", "WA_StyledBackground"), True)
            except Exception:
                pass
            try:
                self.editor.viewport().setAutoFillBackground(False)
            except Exception:
                pass

        def _store_geometry(self, *, visible: bool | None = None) -> None:
            if self._geometry_transition:
                return
            geo = self._current_rect()
            # ``desktop_note`` stores the logical expanded WinForms rectangle;
            # ``show2`` derives the compact text-only geometry from it.  Persist
            # the inverse transform when the visible note is currently collapsed.
            logical = geo if self._expanded else legacy_desknote_hover_geometry(geo)
            if self.node.desktop_note is None:
                self.node.desktop_note = DesktopNoteState()
            self.node.desktop_note.x = logical.x
            self.node.desktop_note.y = logical.y
            self.node.desktop_note.width = logical.width
            self.node.desktop_note.height = logical.height
            self.node.desktop_note.visible = self.isVisible() if visible is None else visible
            self.node.desktop_note.opacity = self._effective_desktop_opacity()

        def _store_after_user_geometry_change(self) -> None:
            self._store_geometry(visible=True)
            self.main_window.document.mark_changed()
            self.main_window.update_title()
            self.main_window.update_tray_menu()

        def reload_from_node(self) -> None:
            self._loading = True
            try:
                self.setWindowTitle(self.node.title)
                self.title_label.setText(self.node.title)
                self.editor.setHtml(rtf_to_desktop_html(self.node.rtf))
                self._apply_desktop_note_text_layout()
                self._compact_desktop_note_blocks()
                self._apply_background()
                self._layout_desknote()
            finally:
                self._loading = False
            self._scroll_manual = False
            self._schedule_auto_resize(150)

        def _show_context_menu(self, global_pos: Any) -> None:
            menu = QtWidgets.QMenu(self)
            menu.addAction("Hintergrundfarbe", self._choose_background_color)
            opacity_menu = menu.addMenu("Transparenz")
            for label, opacity_percent in legacy_transparency_menu_options():
                action = opacity_menu.addAction(label)
                action.triggered.connect(lambda checked=False, v=opacity_percent: self._set_opacity_percent(v))
            menu.addSeparator()
            menu.addAction("Im Hauptfenster öffnen", self._activate_main_window_node)
            menu.addAction("Ausblenden / minimieren", self._hide_desktop_note)
            menu.addAction("Desktop-Notiz schließen", self._remove_desktop_note)
            menu.exec(global_pos)

        def _choose_background_color(self) -> None:
            color = QtWidgets.QColorDialog.getColor(parent=self)
            if not color.isValid():
                return
            if self.node.desktop_note is None:
                self.node.desktop_note = DesktopNoteState()
            self.node.desktop_note.argb = argb_from_color(color)
            self.node.desktop_note.legacy_sparse = False
            self._apply_background()
            self.main_window.document.mark_changed()
            self.main_window.update_title()

        def _set_opacity_percent(self, value: int) -> None:
            if self.node.desktop_note is None:
                self.node.desktop_note = DesktopNoteState()
            opacity = legacy_desknote_opacity_for_inactive(value / 100.0)
            self._desired_opacity = opacity
            self.node.desktop_note.opacity = opacity
            self.node.desktop_note.legacy_sparse = False
            self._apply_background()
            self._apply_widget_opacity()
            self.main_window.document.mark_changed()
            self.main_window.update_title()

        def _apply_user_opacity(self) -> None:
            # Keep the selected transparency visible even while hovering or using
            # the context menu.  Do it inside Qt painting, not through the native
            # top-level opacity, because GNOME/Wayland may expose only binary
            # transparency for frameless windows.
            self._apply_widget_opacity()

        def _set_active_opacity(self) -> None:
            self._apply_user_opacity()

        def _restore_inactive_opacity(self) -> None:
            self._apply_user_opacity()

        def _expand_for_hover(self) -> None:
            if self._expanded or not self.main_window.settings.show_desknote_borders:
                return
            expanded = legacy_desknote_hover_geometry(self._current_rect())
            self._expanded = True
            self._set_geometry_rect(expanded, transition=True)
            self._set_active_opacity()
            self._send_to_back()

        def _collapse_from_hover(self) -> None:
            if not self._expanded:
                return
            collapsed = legacy_desknote_hidden_border_geometry(self._current_rect())
            self._expanded = False
            self._set_geometry_rect(collapsed, transition=True)
            self._restore_inactive_opacity()
            self._send_to_back()

        def _timer_collapse_check(self) -> None:
            if not self._expanded:
                return
            try:
                pos = QtGui.QCursor.pos()
                top_left = self.mapToGlobal(QtCore.QPoint(0, 0))
                rect = LegacyDeskNoteRect(int(top_left.x()), int(top_left.y()), int(self.width()), int(self.height()))
                from .desktop_note_legacy import legacy_desknote_point_outside
                if legacy_desknote_point_outside(rect, int(pos.x()), int(pos.y())):
                    self._collapse_from_hover()
            except Exception:
                pass

        def _activate_main_window_node(self) -> None:
            self._set_active_opacity()
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            self.main_window.select_node(self.node)
            if self.main_window.current_node_ref is self.node:
                self.main_window.load_editor_from_node(self.node, preserve_focus=False)

        def _hide_desktop_note(self) -> None:
            # Notizen.NET's left title hot-zone minimized the sticky note; it did
            # not delete the ALX desktop-note state.  Keep it visible in the model
            # and ask the window manager to minimize it so it remains reachable
            # from the taskbar/window list.
            self._store_geometry(visible=True)
            if self.node.desktop_note is not None:
                self.node.desktop_note.visible = True
                self.node.desktop_note.legacy_sparse = False
            try:
                self.showMinimized()
            except Exception:
                self.hide()
            self.main_window.document.mark_changed()
            self.main_window.update_title()
            self.main_window.update_tray_menu()

        def _remove_desktop_note(self) -> None:
            self.main_window.close_desktop_note(self.node)
            self.main_window.document.mark_changed()
            self.main_window.update_title()

        def _toggle_title_color(self) -> None:
            self._title_dark = not self._title_dark
            self._layout_desknote()

        def _cursor_for_action(self, action: LegacyDeskNoteMouseAction | str) -> Any:
            cursor = legacy_desknote_cursor_for_move_action(action)
            if cursor is LegacyDeskNoteCursor.RESIZE:
                return QtGui.QCursor(SIZE_FDIAG_CURSOR)
            if cursor is LegacyDeskNoteCursor.ARROW:
                return QtGui.QCursor(ARROW_CURSOR)
            if cursor is LegacyDeskNoteCursor.HIDE:
                return QtGui.QCursor(POINTING_HAND_CURSOR)
            return QtGui.QCursor(SIZE_ALL_CURSOR)

        def _bottom_right_resize_edges(self) -> Any:
            try:
                edge = QtCore.Qt.Edge
                return edge.RightEdge | edge.BottomEdge
            except Exception:
                return QtCore.Qt.RightEdge | QtCore.Qt.BottomEdge

        def _window_handle_for_system_drag(self) -> Any:
            try:
                handle = self.windowHandle()
                if handle is None:
                    self.createWinId()
                    handle = self.windowHandle()
                return handle
            except Exception:
                return None

        def _try_start_system_move(self) -> bool:
            """Ask Qt/the compositor to move this frameless window.

            On GNOME/Wayland a client-side ``setGeometry`` drag can show the
            right cursor yet still be ignored by the compositor.  Qt exposes
            ``QWindow.startSystemMove`` for exactly this case.  X11 or older Qt
            builds fall back to the manual WinForms-style geometry math below.
            """

            handle = self._window_handle_for_system_drag()
            starter = getattr(handle, "startSystemMove", None)
            if starter is None:
                return False
            try:
                started = bool(starter())
            except Exception:
                return False
            if started:
                self._drag_move = False
                self._drag_resize = False
                self._system_drag_move = True
                self._system_drag_resize = False
                self._geometry_store_timer.start()
            return started

        def _try_start_system_resize(self) -> bool:
            self._scroll_manual = True
            handle = self._window_handle_for_system_drag()
            starter = getattr(handle, "startSystemResize", None)
            if starter is None:
                return False
            try:
                started = bool(starter(self._bottom_right_resize_edges()))
            except Exception:
                return False
            if started:
                self._drag_move = False
                self._drag_resize = False
                self._system_drag_move = False
                self._system_drag_resize = True
                self._geometry_store_timer.start()
            return started

        def _grab_for_manual_drag(self) -> None:
            try:
                self.grabMouse()
            except Exception:
                pass

        def _release_manual_drag_grab(self) -> None:
            try:
                self.releaseMouse()
            except Exception:
                pass

        def _start_move(self, global_pos: Any) -> None:
            if self._try_start_system_move():
                return
            geo = self.geometry()
            self._drag_move = True
            self._drag_resize = False
            self._system_drag_move = False
            self._system_drag_resize = False
            self._drag_offset_x = int(global_pos.x()) - int(geo.x())
            self._drag_offset_y = int(global_pos.y()) - int(geo.y())
            self._grab_for_manual_drag()

        def _start_resize(self) -> None:
            self._scroll_manual = True
            if self._try_start_system_resize():
                return
            self._drag_resize = True
            self._drag_move = False
            self._system_drag_move = False
            self._system_drag_resize = False
            self._grab_for_manual_drag()

        def _store_after_system_geometry_change(self) -> None:
            resized = self._system_drag_resize
            if not (self._system_drag_move or self._system_drag_resize):
                return
            self._system_drag_move = False
            self._system_drag_resize = False
            if resized:
                self._scroll_manual = True
            self._store_after_user_geometry_change()

        def _handle_mouse_press(self, event: Any) -> bool:
            self._set_active_opacity()
            self._expand_for_hover()
            local = self._event_local_point(event)
            global_pos = self._event_global_pos(event)
            left = event.button() == LEFT_BUTTON
            if not left:
                return False
            if self._expanded:
                hover_action = legacy_desknote_mouse_move_action(int(local.x()), int(local.y()), int(self.width()), int(self.height()))
                if hover_action is LegacyDeskNoteMouseAction.RESIZE:
                    self._start_resize()
                    return True
            action = legacy_desknote_mouse_down_action(int(local.x()), int(local.y()), int(self.width()), left_button=left)
            if action is LegacyDeskNoteMouseAction.CLOSE:
                self._remove_desktop_note()
                return True
            if action is LegacyDeskNoteMouseAction.HIDE:
                self._hide_desktop_note()
                return True
            self._start_move(global_pos)
            return True

        def _handle_mouse_move(self, event: Any) -> bool:
            local = self._event_local_point(event)
            global_pos = self._event_global_pos(event)
            if self._drag_resize:
                rect = legacy_desknote_resize_geometry(int(self.x()), int(self.y()), int(global_pos.x()), int(global_pos.y()))
                self._set_geometry_rect(rect, transition=False)
                return True
            if self._drag_move:
                rect = legacy_desknote_move_geometry(
                    int(global_pos.x()),
                    int(global_pos.y()),
                    self._drag_offset_x,
                    self._drag_offset_y,
                    int(self.width()),
                    int(self.height()),
                )
                self._set_geometry_rect(rect, transition=False)
                return True
            if self._expanded:
                action = legacy_desknote_mouse_move_action(int(local.x()), int(local.y()), int(self.width()), int(self.height()))
                self.setCursor(self._cursor_for_action(action))
            else:
                self.setCursor(QtGui.QCursor(SIZE_ALL_CURSOR))
            return False

        def _handle_mouse_release(self, event: Any) -> bool:
            if self._drag_move or self._drag_resize:
                self._drag_move = False
                self._drag_resize = False
                self._release_manual_drag_grab()
                self._store_after_user_geometry_change()
                self.update()
                return True
            if self._system_drag_move or self._system_drag_resize:
                self._geometry_store_timer.start()
                return True
            return False

        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802 - Qt override
            etype = event.type()
            if etype == ENTER_EVENT:
                self._set_active_opacity()
                self._expand_for_hover()
                return False
            if etype == LEAVE_EVENT:
                self._restore_inactive_opacity()
                return False
            if etype == KEY_PRESS_EVENT:
                self._activate_main_window_node()
                return True
            if etype == MOUSE_DOUBLE_EVENT:
                self._activate_main_window_node()
                return True
            if etype == MOUSE_PRESS_EVENT:
                if watched is self.editor or watched is self.editor.viewport():
                    self._set_active_opacity()
                    self._expand_for_hover()
                    if event.button() == LEFT_BUTTON:
                        self._start_move(self._event_global_pos(event))
                        return True
                    return False
                if watched is self.title_label and event.button() == LEFT_BUTTON:
                    self._toggle_title_color()
                return self._handle_mouse_press(event)
            if etype == MOUSE_MOVE_EVENT:
                return self._handle_mouse_move(event)
            if etype == MOUSE_RELEASE_EVENT:
                return self._handle_mouse_release(event)
            return super().eventFilter(watched, event)

        def enterEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._set_active_opacity()
            self._expand_for_hover()
            super().enterEvent(event)

        def leaveEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._restore_inactive_opacity()
            self._collapse_from_hover()
            super().leaveEvent(event)

        def focusInEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._set_active_opacity()
            self._expand_for_hover()
            super().focusInEvent(event)

        def focusOutEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._restore_inactive_opacity()
            self._collapse_from_hover()
            super().focusOutEvent(event)

        def mousePressEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            if not self._handle_mouse_press(event):
                super().mousePressEvent(event)

        def mouseMoveEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            if not self._handle_mouse_move(event):
                super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            if not self._handle_mouse_release(event):
                super().mouseReleaseEvent(event)

        def mouseDoubleClickEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._activate_main_window_node()
            event.accept()

        def paintEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            super().paintEvent(event)
            if not (self._expanded and self.main_window.settings.show_desknote_borders):
                return
            painter = QtGui.QPainter(self)
            try:
                try:
                    painter.setOpacity(self._effective_desktop_opacity())
                except Exception:
                    pass
                pen = QtGui.QPen(QtGui.QColor("black"))
                painter.setPen(pen)
                painter.drawLine(36, 26, max(36, self.width() - 36), 26)
                painter.drawLine(36, 0, 36, 40)
                painter.drawLine(max(0, self.width() - 36), 0, max(0, self.width() - 36), 40)
                painter.drawLine(0, 40, 36, 40)
                painter.drawLine(max(0, self.width() - 36), 40, self.width(), 40)
                font = QtGui.QFont("Arial", 20)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(QtCore.QRect(max(0, self.width() - 36), 0, 36, 36), ALIGN_CENTER, "x")
                painter.drawText(QtCore.QRect(0, 0, 36, 36), ALIGN_CENTER, "_")
            finally:
                painter.end()

        def showEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            super().showEvent(event)
            self._send_to_back()

        def moveEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            if self._system_drag_move or self._system_drag_resize:
                self._geometry_store_timer.start()
            super().moveEvent(event)

        def resizeEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._layout_desknote()
            if self._system_drag_move or self._system_drag_resize:
                self._geometry_store_timer.start()
            super().resizeEvent(event)

        def closeEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._hide_desktop_note()
            event.ignore()

    class SearchDialog(QtWidgets.QDialog):
        def __init__(self, main_window: "MainWindow") -> None:
            super().__init__(main_window)
            self.main_window = main_window
            self.results: list[SearchResult] = []
            self.result_views: list[SearchHitView] = []
            self.result_index = 0
            self.setWindowTitle("Suche")
            layout = QtWidgets.QGridLayout(self)
            self.term = QtWidgets.QLineEdit(main_window.last_search)
            self.all_nodes = QtWidgets.QCheckBox("Alle Knoten durchsuchen")
            self.whole_words = QtWidgets.QCheckBox("ganze Wörter")
            self.case_sensitive = QtWidgets.QCheckBox("Groß-/Klein-Schreibung beachten")
            self.count_label = QtWidgets.QLabel("")
            self.result_list = QtWidgets.QListWidget()
            self.result_list.setObjectName("Suchliste")
            self.result_list.setMinimumHeight(180)
            search_button = QtWidgets.QPushButton("Suchen / Weiter")
            previous_button = QtWidgets.QPushButton("Zurück")
            close_button = QtWidgets.QPushButton("Fertig")
            search_button.clicked.connect(self.search_next)
            previous_button.clicked.connect(self.search_previous)
            close_button.clicked.connect(self.accept)
            self.term.returnPressed.connect(self.search_next)
            self.result_list.itemActivated.connect(self._activate_list_item)
            layout.addWidget(QtWidgets.QLabel("Suchbegriff:"), 0, 0)
            layout.addWidget(self.term, 0, 1, 1, 3)
            layout.addWidget(self.all_nodes, 1, 0, 1, 4)
            layout.addWidget(self.whole_words, 2, 0, 1, 4)
            layout.addWidget(self.case_sensitive, 3, 0, 1, 4)
            layout.addWidget(QtWidgets.QLabel("Ergebnisse:"), 4, 0)
            layout.addWidget(self.count_label, 4, 1)
            layout.addWidget(self.result_list, 5, 0, 1, 4)
            layout.addWidget(previous_button, 6, 1)
            layout.addWidget(search_button, 6, 2)
            layout.addWidget(close_button, 6, 3)

        def _collect_results(self) -> None:
            self.main_window.save_current_editor_to_node()
            term = self.term.text()
            self.main_window.last_search = term
            self.result_list.clear()
            if not term:
                self.results = []
                self.result_views = []
                self.count_label.setText("0")
                return
            if self.all_nodes.isChecked():
                nodes = list(self.main_window.document.walk())
            else:
                current = self.main_window.current_node()
                nodes = [current] if current is not None else []
            self.results = search_nodes(
                nodes,
                term,
                whole_words=self.whole_words.isChecked(),
                case_sensitive=self.case_sensitive.isChecked(),
            )
            self.result_views = build_search_hit_views(self.results)
            self.result_index = 0
            self.count_label.setText(str(len(self.results)))
            for index, view in enumerate(self.result_views):
                item = QtWidgets.QListWidgetItem(view.label)
                item.setToolTip(f"{view.node_path}\n{view.snippet}")
                item.setData(USER_ROLE, index)
                self.result_list.addItem(item)

        def _ensure_current_results(self) -> bool:
            previous_signature = (
                self.term.text(),
                self.all_nodes.isChecked(),
                self.whole_words.isChecked(),
                self.case_sensitive.isChecked(),
            )
            if getattr(self, "_signature", None) != previous_signature:
                self._signature = previous_signature
                self._collect_results()
            return bool(self.results)

        def _activate_list_item(self, item: Any) -> None:
            index = item.data(USER_ROLE)
            try:
                numeric_index = int(index)
            except Exception:
                return
            self.activate_result(numeric_index)

        def activate_result(self, index: int) -> None:
            if not self.results:
                return
            if index < 0 or index >= len(self.results):
                index = index % len(self.results)
            result = self.results[index]
            self.result_index = (index + 1) % len(self.results)
            self.result_list.setCurrentRow(index)
            self.main_window.select_node(result.node)
            cursor = self.main_window.editor.textCursor()
            cursor.setPosition(result.start)
            cursor.setPosition(result.start + result.length, QtGui.QTextCursor.MoveMode.KeepAnchor)
            self.main_window.editor.setTextCursor(cursor)
            self.main_window.editor.setFocus()

        def search_next(self) -> None:
            if not self._ensure_current_results():
                return
            row = self.result_list.currentRow()
            index = row + 1 if row >= 0 else self.result_index
            self.activate_result(index)

        def search_previous(self) -> None:
            if not self._ensure_current_results():
                return
            row = self.result_list.currentRow()
            index = row - 1 if row >= 0 else len(self.results) - 1
            self.activate_result(index)

    class AlarmDialog(QtWidgets.QDialog):
        def __init__(self, main_window: "MainWindow") -> None:
            super().__init__(main_window)
            self.main_window = main_window
            self.setWindowTitle("Wecker")
            layout = QtWidgets.QFormLayout(self)
            self.enabled_check = QtWidgets.QCheckBox("Wecker aktiviert")
            self.enabled_check.setChecked(True)
            self.when = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime().addSecs(5 * 60))
            self.when.setCalendarPopup(True)
            self.message = QtWidgets.QLineEdit("Notizen-Wecker")
            self.repeat = QtWidgets.QComboBox()
            self.repeat.addItem("Einmalig", "none")
            self.repeat.addItem("Täglich", "daily")
            self.repeat.addItem("Wöchentlich", "weekly")
            self.repeat.addItem("Monatlich", "monthly")
            self.repeat.addItem("Jährlich", "yearly")
            self.interval = QtWidgets.QSpinBox()
            self.interval.setRange(1, 999)
            self.interval.setValue(1)
            self.weekday_container = QtWidgets.QWidget()
            weekday_layout = QtWidgets.QHBoxLayout(self.weekday_container)
            weekday_layout.setContentsMargins(0, 0, 0, 0)
            self.weekday_checks: list[Any] = []
            current_day = QtCore.QDate.currentDate().dayOfWeek() - 1
            for index, label in enumerate(legacy_wecker_weekday_labels()):
                box = QtWidgets.QCheckBox(label[:2])
                box.setChecked(index == current_day)
                self.weekday_checks.append(box)
                weekday_layout.addWidget(box)
            weekday_layout.addStretch(1)

            layout.addRow(self.enabled_check)
            layout.addRow("Zeitpunkt", self.when)
            layout.addRow("Meldung", self.message)
            layout.addRow("Wiederholung", self.repeat)
            layout.addRow("Intervall", self.interval)
            layout.addRow("Wochentage", self.weekday_container)
            hint = QtWidgets.QLabel("Portiert nach wecker.vb: einmalig, täglich, wöchentlich, monatlich oder jährlich.")
            hint.setWordWrap(True)
            layout.addRow(hint)
            buttons = QtWidgets.QDialogButtonBox(
                _enum(QtWidgets.QDialogButtonBox, "StandardButton", "Ok")
                | _enum(QtWidgets.QDialogButtonBox, "StandardButton", "Cancel")
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addRow(buttons)
            self.repeat.currentIndexChanged.connect(self._update_repeat_controls)
            self.enabled_check.toggled.connect(self._update_repeat_controls)
            self._update_repeat_controls()

        def _update_repeat_controls(self) -> None:
            active = self.enabled_check.isChecked()
            kind = self.repeat.currentData()
            self.when.setEnabled(active)
            self.message.setEnabled(active)
            self.repeat.setEnabled(active)
            self.interval.setEnabled(active and kind != "none")
            self.weekday_container.setEnabled(active)
            self.weekday_container.setVisible(kind == "weekly")

        def accept(self) -> None:  # noqa: N802 - Qt override
            if not self.enabled_check.isChecked():
                self.main_window.statusBar().showMessage("Wecker deaktiviert.")
                super().accept()
                return
            when = self.when.dateTime()
            try:
                start = datetime.fromtimestamp(int(when.toSecsSinceEpoch()))
            except Exception:
                start = datetime.now()
            kind = str(self.repeat.currentData() or "none")
            weekdays = tuple(index for index, box in enumerate(self.weekday_checks) if box.isChecked())
            spec = AlarmSpec(
                start=start,
                message=self.message.text(),
                recurrence=kind,  # type: ignore[arg-type]
                interval=self.interval.value(),
                weekdays=weekdays,
                enabled=True,
            ).normalized()
            self.main_window.schedule_alarm_spec(spec)
            super().accept()


    class PasswordChangeDialog(QtWidgets.QDialog):
        """Legacy-style password dialog with old/new/repeat validation."""

        def __init__(self, main_window: "MainWindow") -> None:
            super().__init__(main_window)
            self.main_window = main_window
            self.new_password = ""
            self.setWindowTitle(main_window.tr("strip1_21", "Passwort ändern"))
            layout = QtWidgets.QFormLayout(self)

            self.old_password = QtWidgets.QLineEdit()
            self.old_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.new_password_edit = QtWidgets.QLineEdit()
            self.new_password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.repeat_password = QtWidgets.QLineEdit()
            self.repeat_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

            layout.addRow(main_window.tr("pass1", "Altes Passwort"), self.old_password)
            layout.addRow(main_window.tr("pass2", "Neues Passwort"), self.new_password_edit)
            layout.addRow(main_window.tr("pass3", "Neues Passwort wiederholen"), self.repeat_password)
            info = QtWidgets.QLabel(main_window.tr("pw_unten_info", "Maximal 24 Zeichen. Leer lassen entfernt das Passwort."))
            info.setWordWrap(True)
            layout.addRow(info)

            buttons = QtWidgets.QDialogButtonBox(
                _enum(QtWidgets.QDialogButtonBox, "StandardButton", "Ok")
                | _enum(QtWidgets.QDialogButtonBox, "StandardButton", "Cancel")
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addRow(buttons)

        def accept(self) -> None:  # noqa: N802 - Qt override
            current = self.main_window.document.password or ""
            if current and normalize_password(self.old_password.text()) != normalize_password(current):
                QtWidgets.QMessageBox.warning(
                    self,
                    self.main_window.tr("strip1_21", "Passwort ändern"),
                    self.main_window.tr("passerror2", "Das alte Passwort ist falsch."),
                )
                return
            first = self.new_password_edit.text()
            second = self.repeat_password.text()
            if first != second:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.main_window.tr("strip1_21", "Passwort ändern"),
                    self.main_window.tr("passerror3", "Die neuen Passwörter stimmen nicht überein."),
                )
                return
            if len(first) > 24:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.main_window.tr("strip1_21", "Passwort ändern"),
                    self.main_window.tr("passerror1", "Das Passwort darf höchstens 24 Zeichen haben."),
                )
                return
            self.new_password = first
            super().accept()


    class MainWindow(QtWidgets.QMainWindow):
        def __init__(
            self,
            initial_path: str | None = None,
            password: str | None = None,
            *,
            disable_tray: bool = False,
            force_tray_start: bool = False,
            reset_window_geometry: bool = False,
        ) -> None:
            super().__init__()
            self.setObjectName(APP_DESKTOP_ID)
            self.disable_tray = bool(disable_tray)
            self.force_tray_start = bool(force_tray_start)
            self.reset_window_geometry = bool(reset_window_geometry)
            self.tray_icon = None
            self.tray_menu = None
            self.settings = AppSettings.load()
            self.document = NoteDocument.new()
            self.document.password = password or ""
            self.current_node_ref: NoteNode | None = None
            self._loading_editor = False
            self._loading_tree = False
            self.node_items: dict[int, Any] = {}
            self.clipboard_node: NoteNode | None = None
            self.cut_source_node: NoteNode | None = None
            self.cut_clipboard_xml: str | None = None
            self.desktop_windows: dict[int, DesktopNoteWindow] = {}
            self.last_search = ""
            self._quick_search_results: list[SearchResult] = []
            self._quick_search_index = 0
            self._quick_search_signature: tuple[str, bool] | None = None
            self.alarms: list[Any] = []
            self._updating_format_controls = False
            self._updating_title_boxes = False
            self.autosave_timer = QtCore.QTimer(self)
            self.autosave_timer.timeout.connect(self.autosave)
            self._build_ui()
            self._restore_window_settings()
            self.build_tree()
            if initial_path:
                if str(initial_path).casefold().startswith("ftp://"):
                    self.load_ftp_url(str(initial_path), password=password or None, ask_save=False)
                else:
                    self.load_path(Path(initial_path), password=password or None)
            elif self.settings.last_directory and self.settings.last_file:
                candidate = Path(self.settings.last_directory) / self.settings.last_file
                if candidate.exists():
                    self.statusBar().showMessage(f"Letzte Datei: {candidate}")
            self.update_title()
            self.update_actions()
            self._configure_autosave()

        def tr(self, key: str, default: str | None = None) -> str:
            return tr(getattr(self.settings, "language", "Auto"), key, default)

        def _build_ui(self) -> None:
            icon = app_icon()
            if not icon.isNull():
                self.setWindowIcon(icon)

            self.tree = LegacyTreeWidget(self)
            self.tree.setObjectName("Baum")
            self.tree.setHeaderLabel("Notizen")
            self.tree.setHeaderHidden(True)
            self.tree.setSelectionBehavior(SELECT_ROWS)
            self.tree.setSelectionMode(EXTENDED_SELECTION)
            self.tree.setDragDropMode(INTERNAL_MOVE)
            self.tree.setDefaultDropAction(MOVE_ACTION)
            self.tree.setAlternatingRowColors(True)
            self.tree.setMinimumSize(240, 260)
            self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
            self.tree.itemChanged.connect(self.on_item_changed)
            # Legacy BaumTyp_NodeMouseDoubleClick: double-click starts label editing.
            self.tree.itemDoubleClicked.connect(self.edit_tree_item)
            self.tree.itemExpanded.connect(lambda item: self.on_tree_expansion_changed(item, True))
            self.tree.itemCollapsed.connect(lambda item: self.on_tree_expansion_changed(item, False))
            try:
                self.tree.model().rowsMoved.connect(lambda *_: self.on_tree_rows_moved())
            except Exception:
                pass

            self.editor = QtWidgets.QTextEdit()
            self.editor.setObjectName("Inhalt")
            self.editor.setAcceptRichText(True)
            self.editor.setMinimumSize(420, 300)
            self.editor.setPlaceholderText("Notiztext")
            self._apply_scrollbar_settings()
            self.editor.textChanged.connect(self.on_editor_changed)
            self.editor.setContextMenuPolicy(_enum(QtCore.Qt, "ContextMenuPolicy", "ActionsContextMenu"))

            self.tree_top_edit = QtWidgets.QLineEdit()
            self.tree_top_edit.setObjectName("txt1")
            self.tree_top_edit.setReadOnly(True)
            self.tree_top_edit.setMinimumHeight(24)
            self.tree_top_edit.setToolTip("Oberster Baumknoten wie im alten Notizen.NET-Feld txt1")
            self.tree_top_edit.setStyleSheet("QLineEdit { background: rgb(255, 255, 192); border: 1px solid palette(mid); }")

            self.node_title_edit = QtWidgets.QLineEdit()
            self.node_title_edit.setObjectName("txt2")
            self.node_title_edit.setMinimumHeight(24)
            self.node_title_edit.setToolTip("Titel des aktuell markierten Knotens wie im alten Notizen.NET-Feld txt2")
            self.node_title_edit.setStyleSheet("QLineEdit { background: rgb(255, 255, 192); border: 1px solid palette(mid); }")
            self.node_title_edit.editingFinished.connect(self.commit_title_box)
            self.node_title_edit.returnPressed.connect(self.commit_title_box)

            self.title_apply_button = QtWidgets.QPushButton("Umbenennen")
            self.title_apply_button.setObjectName("applyTxt2")
            self.title_apply_button.clicked.connect(self.commit_title_box)

            self.quick_search_edit = QtWidgets.QLineEdit()
            self.quick_search_edit.setObjectName("treeQuickSearch")
            self.quick_search_edit.setPlaceholderText("Suchen")
            self.quick_search_edit.returnPressed.connect(self.quick_search_next)
            self.quick_search_next_button = QtWidgets.QPushButton("Weiter")
            self.quick_search_all_button = QtWidgets.QPushButton("Alle")
            self.quick_search_next_button.clicked.connect(self.quick_search_next)
            self.quick_search_all_button.clicked.connect(self.quick_search_all)

            central = QtWidgets.QWidget()
            central.setObjectName("legacySplitContent")
            outer_layout = QtWidgets.QVBoxLayout(central)
            outer_layout.setContentsMargins(6, 6, 6, 6)
            outer_layout.setSpacing(6)

            splitter = QtWidgets.QSplitter()
            splitter.setObjectName("SplitContainer1")
            splitter.setChildrenCollapsible(False)

            left_panel = QtWidgets.QWidget()
            left_panel.setObjectName("SplitContainer3")
            left_layout = QtWidgets.QVBoxLayout(left_panel)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(4)
            left_layout.addWidget(self.tree_top_edit)
            left_layout.addWidget(self.tree, 1)

            search_row = QtWidgets.QHBoxLayout()
            search_row.setContentsMargins(0, 0, 0, 0)
            search_row.setSpacing(4)
            search_row.addWidget(self.quick_search_edit, 1)
            search_row.addWidget(self.quick_search_next_button)
            search_row.addWidget(self.quick_search_all_button)
            left_layout.addLayout(search_row)

            right_panel = QtWidgets.QWidget()
            right_panel.setObjectName("SplitContainer2")
            right_layout = QtWidgets.QVBoxLayout(right_panel)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(4)

            title_row = QtWidgets.QHBoxLayout()
            title_row.setContentsMargins(0, 0, 0, 0)
            title_row.setSpacing(0)
            self.editor_mode_label = QtWidgets.QLabel("Modus: RTF/Text")
            self.editor_mode_label.setObjectName("modeCaption")
            self.editor_mode_label.hide()
            self.title_apply_button.hide()
            title_row.addWidget(self.node_title_edit, 1)

            right_layout.addLayout(title_row)
            right_layout.addWidget(self.editor, 1)

            splitter.addWidget(left_panel)
            splitter.addWidget(right_panel)
            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 3)
            splitter.setSizes([320, 960])

            outer_layout.addWidget(splitter, 1)
            self.setCentralWidget(central)

            self._create_actions()
            self._create_menus()
            self._create_toolbars()
            self.editor.cursorPositionChanged.connect(self.update_format_controls)
            self.statusBar().showMessage(self.tr("ready", "Bereit"))
            self._create_tray_icon()
            self.apply_language()
            self.update_node_text_boxes()


        def _act(self, text: str, slot: Any, shortcut: str | None = None, checkable: bool = False) -> Any:
            action = QtGui.QAction(text, self)
            if shortcut:
                action.setShortcut(QtGui.QKeySequence(shortcut))
            action.setCheckable(checkable)
            action.triggered.connect(slot)
            return action

        def _style_rtf_toolstrip_actions(self) -> None:
            """Keep RTF actions prominent while the toolbar itself stays icon-only."""

            try:
                priority = QtGui.QAction.Priority.HighPriority
            except Exception:
                priority = None
            if priority is not None:
                for action in (
                    self.regular_action,
                    self.bold_action,
                    self.italic_action,
                    self.underline_action,
                    self.strike_action,
                ):
                    try:
                        action.setPriority(priority)
                    except Exception:
                        pass

        def _standard_toolbar_icon(self, standard_name: str) -> Any:
            # Kept for compatibility with older code paths, but toolbar icons are
            # now drawn explicitly so no desktop theme can replace them with
            # generic square placeholders.
            try:
                style = self.style()
                if style is None:
                    return QtGui.QIcon()
                return style.standardIcon(_enum(QtWidgets.QStyle, "StandardPixmap", standard_name))
            except Exception:
                return QtGui.QIcon()

        def _draw_toolbar_icon(self, kind: str, size: int = 44) -> Any:
            """Draw one distinctive, theme-independent toolbar icon.

            The old migration used text-only buttons.  The current toolbar must be
            icon-only, so every visible command receives a semantic pictogram here
            instead of falling back to standard desktop theme icons.  That avoids
            the GNOME/Qt cases where unknown standard icons become identical
            empty squares.
            """

            pixmap = QtGui.QPixmap(size, size)
            pixmap.fill(QtCore.Qt.GlobalColor.transparent)
            painter = QtGui.QPainter(pixmap)
            try:
                painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
            except Exception:
                painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

            u = size / 44.0
            stroke = QtGui.QColor(45, 52, 64)
            blue = QtGui.QColor(36, 120, 190)
            green = QtGui.QColor(46, 154, 88)
            yellow = QtGui.QColor(238, 185, 49)
            orange = QtGui.QColor(218, 118, 39)
            red = QtGui.QColor(201, 66, 66)
            purple = QtGui.QColor(126, 87, 194)
            cyan = QtGui.QColor(24, 151, 164)
            grey = QtGui.QColor(116, 124, 137)
            white = QtGui.QColor(255, 255, 255)
            pale = {
                "file": QtGui.QColor(231, 243, 255),
                "tree": QtGui.QColor(231, 248, 235),
                "edit": QtGui.QColor(246, 246, 248),
                "rtf": QtGui.QColor(246, 246, 248),
                "color": QtGui.QColor(255, 247, 218),
                "danger": QtGui.QColor(255, 238, 238),
                "note": QtGui.QColor(255, 250, 214),
                "misc": QtGui.QColor(238, 244, 255),
            }

            def group_for(k: str) -> str:
                if k.startswith(("file_", "open_", "save_", "backup_", "print_", "export_", "import_", "ftp", "close_doc")):
                    return "file"
                if k.startswith(("tree_", "move_", "expand", "collapse", "toggle", "unify")):
                    return "tree"
                if k in {"delete_node", "delete_text", "exit_app"}:
                    return "danger"
                if k in {"desktop_note", "sticky_note"}:
                    return "note"
                if k in {"text_color", "highlight", "bg_color", "fg_color"}:
                    return "color"
                if k in {"bold", "italic", "underline", "strike", "regular", "bigger", "smaller", "align_left", "align_center", "align_right", "align_justify", "bullet", "scrollbars"}:
                    return "rtf"
                if k in {"cut", "copy", "paste", "paste_child", "undo", "redo", "rename", "insert_image", "insert_date", "search"}:
                    return "edit"
                return "misc"

            def set_pen(color=stroke, width: float | None = None) -> None:
                pen = QtGui.QPen(color)
                pen.setWidthF(width if width is not None else max(2.0, size / 18.0))
                try:
                    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
                    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
                except Exception:
                    pass
                painter.setPen(pen)

            def no_pen() -> None:
                painter.setPen(QtCore.Qt.PenStyle.NoPen)

            def no_brush() -> None:
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

            def brush(color: Any) -> None:
                painter.setBrush(color)

            def line(x1: float, y1: float, x2: float, y2: float, color=stroke, width: float | None = None) -> None:
                set_pen(color, width)
                painter.drawLine(QtCore.QPointF(x1 * u, y1 * u), QtCore.QPointF(x2 * u, y2 * u))

            def rect(x: float, y: float, w: float, h: float, fill: Any | None = None, outline=stroke, radius: float = 3.0, width: float | None = None) -> None:
                set_pen(outline, width)
                if fill is None:
                    no_brush()
                else:
                    brush(fill)
                painter.drawRoundedRect(QtCore.QRectF(x * u, y * u, w * u, h * u), radius * u, radius * u)
                no_brush()

            def circle(cx: float, cy: float, r: float, fill: Any | None = None, outline=stroke, width: float | None = None) -> None:
                set_pen(outline, width)
                if fill is None:
                    no_brush()
                else:
                    brush(fill)
                painter.drawEllipse(QtCore.QPointF(cx * u, cy * u), r * u, r * u)
                no_brush()

            def dot(cx: float, cy: float, r: float, color=stroke) -> None:
                no_pen()
                brush(color)
                painter.drawEllipse(QtCore.QPointF(cx * u, cy * u), r * u, r * u)
                no_brush()
                set_pen()

            def plus(cx: float, cy: float, color=green) -> None:
                line(cx, cy - 5, cx, cy + 5, color, max(2.5, size / 14.5))
                line(cx - 5, cy, cx + 5, cy, color, max(2.5, size / 14.5))

            def minus(cx: float, cy: float, color=red) -> None:
                line(cx - 5, cy, cx + 5, cy, color, max(2.5, size / 14.5))

            def cross(cx: float, cy: float, color=red) -> None:
                line(cx - 4.5, cy - 4.5, cx + 4.5, cy + 4.5, color, max(2.5, size / 15.0))
                line(cx + 4.5, cy - 4.5, cx - 4.5, cy + 4.5, color, max(2.5, size / 15.0))

            def arrow_right(x: float, y: float, color=blue) -> None:
                line(x - 6, y, x + 5, y, color, max(2.4, size / 16.0))
                line(x + 5, y, x + 1, y - 4, color, max(2.4, size / 16.0))
                line(x + 5, y, x + 1, y + 4, color, max(2.4, size / 16.0))

            def arrow_left(x: float, y: float, color=blue) -> None:
                line(x + 6, y, x - 5, y, color, max(2.4, size / 16.0))
                line(x - 5, y, x - 1, y - 4, color, max(2.4, size / 16.0))
                line(x - 5, y, x - 1, y + 4, color, max(2.4, size / 16.0))

            def arrow_down(x: float, y: float, color=blue) -> None:
                line(x, y - 6, x, y + 5, color, max(2.4, size / 16.0))
                line(x, y + 5, x - 4, y + 1, color, max(2.4, size / 16.0))
                line(x, y + 5, x + 4, y + 1, color, max(2.4, size / 16.0))

            def arrow_up(x: float, y: float, color=blue) -> None:
                line(x, y + 6, x, y - 5, color, max(2.4, size / 16.0))
                line(x, y - 5, x - 4, y - 1, color, max(2.4, size / 16.0))
                line(x, y - 5, x + 4, y - 1, color, max(2.4, size / 16.0))

            def text_lines(x: float = 11, y0: float = 14, widths=(18, 14, 20), gap: float = 7, color=stroke, width: float | None = None, slant: float = 0) -> None:
                for idx, w in enumerate(widths):
                    y = y0 + idx * gap
                    line(x + slant * idx, y, x + w + slant * idx, y, color, width)

            def draw_page(x=10, y=6, w=19, h=27, fill=white) -> None:
                rect(x, y, w, h, fill, stroke, 2.6)
                line(x + w - 5, y, x + w, y + 5, grey, max(1.5, size / 24.0))
                line(x + w, y + 5, x + w - 5, y + 5, grey, max(1.5, size / 24.0))

            def draw_folder(x=7, y=13, w=28, h=20) -> None:
                rect(x, y, w, h, QtGui.QColor(255, 218, 93), stroke, 2.8)
                line(x + 2, y, x + 9, y - 5, stroke, max(2.0, size / 18.0))
                line(x + 9, y - 5, x + 17, y - 5, stroke, max(2.0, size / 18.0))

            def draw_disk(x=9, y=7) -> None:
                rect(x, y, 25, 28, QtGui.QColor(95, 158, 217), stroke, 3)
                rect(x + 5, y + 3, 13, 7, white, grey, 1.5)
                rect(x + 6, y + 18, 13, 8, white, stroke, 1.5)
                line(x + 21, y + 4, x + 21, y + 11, stroke, max(1.6, size / 24.0))

            def draw_printer() -> None:
                rect(8, 16, 28, 13, QtGui.QColor(230, 233, 238), stroke, 3)
                rect(13, 7, 18, 11, white, stroke, 2)
                rect(13, 27, 18, 8, white, stroke, 2)
                dot(31, 22, 1.6, green)

            def draw_tree(x=8, y=8) -> None:
                line(x, y, x, y + 26, green, max(2.0, size / 17.0))
                line(x, y + 7, x + 9, y + 7, green)
                line(x, y + 19, x + 9, y + 19, green)
                rect(x + 10, y + 3, 10, 8, white, stroke, 2)
                rect(x + 10, y + 15, 10, 8, white, stroke, 2)

            def draw_pencil() -> None:
                line(12, 30, 29, 13, orange, max(4.0, size / 10.5))
                line(27, 11, 32, 16, stroke, max(2.4, size / 16.0))
                line(10, 32, 14, 28, stroke, max(2.0, size / 18.0))

            def draw_magnifier() -> None:
                circle(18, 18, 8, None, stroke)
                line(24, 24, 34, 34, blue, max(3.0, size / 13.0))

            def draw_clock(cx=22, cy=22, r=9) -> None:
                circle(cx, cy, r, None, stroke)
                line(cx, cy, cx, cy - 5, stroke, max(1.8, size / 22.0))
                line(cx, cy, cx + 5, cy + 2, stroke, max(1.8, size / 22.0))

            def draw_palette() -> None:
                circle(20, 20, 12, QtGui.QColor(255, 248, 225), stroke)
                dot(15, 16, 2, red); dot(21, 14, 2, blue); dot(25, 20, 2, green); dot(18, 25, 2, yellow)
                circle(27, 27, 3, pale["color"], pale["color"], width=1)

            def draw_brush(color=blue) -> None:
                line(26, 11, 13, 24, stroke, max(3.4, size / 12.0))
                rect(9, 23, 8, 7, color, stroke, 2)

            def draw_globe() -> None:
                circle(22, 22, 12, None, cyan)
                line(10, 22, 34, 22, cyan, max(1.7, size / 25.0))
                line(22, 10, 22, 34, cyan, max(1.7, size / 25.0))
                line(14, 15, 30, 15, cyan, max(1.4, size / 28.0))
                line(14, 29, 30, 29, cyan, max(1.4, size / 28.0))

            # subtle colored card behind every glyph, but never as the only pictogram
            bg = pale[group_for(kind)]
            rect(3, 3, 38, 38, bg, QtGui.QColor(212, 217, 224), 7, max(1.0, size / 44.0))
            set_pen()

            if kind == "new_file":
                draw_page(); text_lines(13, 16, (12, 10), 6); plus(33, 31)
            elif kind == "open_file":
                draw_folder(); arrow_up(31, 14, blue)
            elif kind == "save_file":
                draw_disk()
            elif kind == "save_as":
                draw_disk(); draw_pencil()
            elif kind == "backup_create":
                draw_disk(7, 7); draw_clock(31, 30, 7)
            elif kind == "backup_open":
                draw_folder(); draw_clock(31, 30, 7)
            elif kind == "close_doc":
                draw_page(); cross(31, 31)
            elif kind == "exit_app":
                rect(10, 8, 16, 28, white, stroke, 2); arrow_right(30, 22, red)
            elif kind == "password":
                circle(16, 23, 5, None, stroke); line(20, 23, 34, 23, yellow, max(3.0, size / 13.5)); line(29, 23, 29, 28, yellow); line(33, 23, 33, 27, yellow)
            elif kind == "ftp":
                draw_globe(); arrow_right(31, 13, blue); arrow_left(13, 31, green)
            elif kind == "print_note":
                draw_printer(); draw_page(17, 8, 11, 14)
            elif kind == "print_subtree":
                draw_printer(); draw_tree(10, 5)
            elif kind == "print_all":
                draw_printer(); rect(14, 6, 12, 8, white, stroke, 1.8); rect(18, 9, 12, 8, white, stroke, 1.8)
            elif kind.startswith("import_"):
                draw_page(); arrow_down(31, 16, green)
                if kind == "import_rtf":
                    draw_brush(purple)
                elif kind == "import_config":
                    draw_clock(18, 24, 6)
                else:
                    text_lines(14, 17, (11, 13, 9), 5)
            elif kind.startswith("export_"):
                draw_page(); arrow_right(31, 22, blue)
                if "html" in kind:
                    line(13, 18, 17, 14, purple); line(13, 18, 17, 22, purple); line(23, 14, 27, 18, purple); line(23, 22, 27, 18, purple)
                elif "rtf" in kind:
                    draw_brush(purple)
                elif "unicode" in kind:
                    draw_globe()
                elif "ansi" in kind:
                    dot(15, 16, 1.4, grey); dot(20, 16, 1.4, grey); dot(25, 16, 1.4, grey); text_lines(14, 22, (13,), 5)
                else:
                    text_lines(13, 16, (12, 15, 9), 5)
                if "all" in kind:
                    plus(13, 31, green)
                if "node" in kind:
                    draw_tree(7, 25)
            elif kind == "tree_child":
                draw_tree(); plus(34, 30)
            elif kind == "tree_sibling":
                draw_tree(); plus(34, 12)
            elif kind == "rename":
                draw_page(8, 9, 20, 25); draw_pencil()
            elif kind in {"delete_node", "delete_text"}:
                if kind == "delete_text":
                    text_lines(11, 14, (18, 14, 17), 6)
                else:
                    draw_tree(7, 9)
                cross(31, 29)
            elif kind == "unify_subtree":
                rect(8, 10, 9, 8, white, stroke, 2); rect(8, 26, 9, 8, white, stroke, 2); rect(27, 18, 9, 8, QtGui.QColor(209, 242, 221), stroke, 2); line(17, 14, 27, 21, green); line(17, 30, 27, 23, green)
            elif kind == "unify_all":
                draw_tree(6, 7); rect(28, 18, 8, 8, QtGui.QColor(209, 242, 221), stroke, 2); arrow_right(27, 22, green)
            elif kind == "desktop_note":
                rect(8, 7, 27, 30, QtGui.QColor(255, 238, 111), stroke, 3); text_lines(13, 15, (15, 15, 10), 6); line(27, 37, 35, 29, yellow)
            elif kind == "bg_color":
                rect(8, 8, 26, 25, QtGui.QColor(255, 238, 111), stroke, 3); draw_brush(yellow)
            elif kind == "fg_color":
                text_lines(10, 14, (22, 18, 20), 7); draw_palette()
            elif kind == "move_up":
                draw_tree(8, 10); arrow_up(33, 15, blue)
            elif kind == "move_down":
                draw_tree(8, 8); arrow_down(33, 27, blue)
            elif kind == "toggle_node":
                draw_tree(8, 9); arrow_right(33, 22, blue)
            elif kind == "expand_all":
                draw_tree(6, 7); arrow_down(34, 16, green); arrow_down(34, 29, green)
            elif kind == "collapse_all":
                draw_tree(6, 7); arrow_up(34, 16, red); arrow_up(34, 29, red)
            elif kind == "cut":
                circle(14, 14, 3, white, stroke); circle(14, 30, 3, white, stroke); line(17, 16, 31, 8, grey); line(17, 28, 31, 36, grey); line(21, 22, 34, 10, grey)
            elif kind == "copy":
                rect(11, 13, 17, 21, white, stroke, 2); rect(17, 8, 17, 21, QtGui.QColor(239, 247, 255), stroke, 2)
            elif kind == "paste":
                rect(10, 11, 24, 28, white, stroke, 3); rect(15, 6, 14, 8, QtGui.QColor(255, 248, 225), stroke, 2); arrow_down(30, 27, green)
            elif kind == "paste_child":
                rect(9, 11, 21, 27, white, stroke, 3); draw_tree(25, 19); plus(34, 33)
            elif kind == "undo":
                arrow_left(18, 22, blue); line(14, 22, 31, 22, blue); line(31, 22, 31, 30, blue)
            elif kind == "redo":
                arrow_right(26, 22, green); line(13, 22, 30, 22, green); line(13, 22, 13, 30, green)
            elif kind == "insert_image":
                rect(7, 9, 30, 25, white, stroke, 3); dot(16, 17, 2.5, yellow); line(10, 31, 19, 22, green); line(19, 22, 25, 28, green); line(25, 28, 35, 17, green)
            elif kind == "insert_date":
                rect(8, 10, 28, 28, white, stroke, 3); line(13, 6, 13, 15); line(31, 6, 31, 15); line(8, 18, 36, 18); draw_clock(25, 29, 6)
            elif kind == "search":
                draw_magnifier()
            elif kind == "alarm":
                circle(22, 24, 11, QtGui.QColor(255, 250, 250), stroke); line(22, 24, 22, 16); line(22, 24, 28, 27); line(13, 11, 8, 7, red); line(31, 11, 36, 7, red)
            elif kind == "stats":
                rect(10, 25, 5, 10, blue, stroke, 1.5); rect(19, 18, 5, 17, green, stroke, 1.5); rect(28, 11, 5, 24, yellow, stroke, 1.5)
            elif kind == "about":
                circle(22, 22, 13, QtGui.QColor(232, 243, 255), blue); line(22, 20, 22, 30, blue); dot(22, 14, 1.8, blue)
            elif kind == "settings":
                circle(22, 22, 5, white, stroke); 
                for x1, y1, x2, y2 in ((22,7,22,12),(22,32,22,37),(7,22,12,22),(32,22,37,22),(11,11,15,15),(29,29,33,33),(29,15,33,11),(11,33,15,29)):
                    line(x1, y1, x2, y2, grey, max(2.2, size / 17.0))
            elif kind == "regular":
                text_lines(10, 14, (22, 17, 22), 7); line(31, 10, 11, 33, red, max(2.5, size / 16.0))
            elif kind == "bold":
                text_lines(9, 13, (25, 20, 25), 8, stroke, max(4.2, size / 9.0))
            elif kind == "italic":
                text_lines(9, 12, (23, 18, 23), 8, stroke, max(2.4, size / 16.0), slant=3.5); line(30, 10, 19, 34, purple)
            elif kind == "underline":
                text_lines(10, 13, (22, 17), 8); line(9, 33, 32, 33, blue, max(3.0, size / 13.5))
            elif kind == "strike":
                text_lines(10, 13, (22, 17, 22), 8); line(8, 22, 34, 22, red, max(3.0, size / 13.5))
            elif kind == "bigger":
                text_lines(8, 15, (15, 13, 15), 7); arrow_up(32, 18, green)
            elif kind == "smaller":
                text_lines(8, 13, (15, 13, 15), 7); arrow_down(32, 27, red)
            elif kind == "align_left":
                text_lines(10, 13, (24, 18, 24, 14), 6)
            elif kind == "align_center":
                line(10, 13, 34, 13); line(14, 19, 30, 19); line(9, 25, 35, 25); line(15, 31, 29, 31)
            elif kind == "align_right":
                line(10, 13, 34, 13); line(16, 19, 34, 19); line(10, 25, 34, 25); line(20, 31, 34, 31)
            elif kind == "align_justify":
                for y in (13, 19, 25, 31):
                    line(10, y, 34, y)
            elif kind == "text_color":
                text_lines(11, 14, (20, 16), 7); no_pen(); brush(blue); painter.drawRoundedRect(QtCore.QRectF(9*u, 33*u, 26*u, 5*u), 2*u, 2*u); no_brush(); set_pen()
            elif kind == "highlight":
                no_pen(); brush(QtGui.QColor(255, 226, 84)); painter.drawRoundedRect(QtCore.QRectF(9*u, 23*u, 26*u, 9*u), 2*u, 2*u); no_brush(); set_pen(); text_lines(11, 14, (20, 16), 7)
            elif kind == "bullet":
                dot(12, 14, 2, stroke); dot(12, 22, 2, stroke); dot(12, 30, 2, stroke); line(18, 14, 33, 14); line(18, 22, 33, 22); line(18, 30, 33, 30)
            elif kind == "scrollbars":
                rect(8, 8, 28, 28, white, stroke, 3); line(8, 29, 36, 29, grey); line(29, 8, 29, 36, grey); arrow_down(33, 22, blue); arrow_right(22, 33, blue)
            else:
                # Deliberately distinctive fallback: diamond with question slash,
                # never just an empty square.  Tests use icon kind coverage to keep
                # normal toolbar actions away from this branch.
                rect(9, 9, 26, 26, QtGui.QColor(255, 245, 245), red, 5)
                line(13, 31, 31, 13, red)
                circle(22, 22, 5, None, red)

            painter.end()
            return QtGui.QIcon(pixmap)

        def _assign_toolbar_icons(self) -> None:
            icon_specs = [
                ("new_action", "new_file"),
                ("open_action", "open_file"),
                ("save_action", "save_file"),
                ("save_as_action", "save_as"),
                ("backup_now_action", "backup_create"),
                ("open_backup_action", "backup_open"),
                ("close_doc_action", "close_doc"),
                ("print_note_action", "print_note"),
                ("print_subtree_action", "print_subtree"),
                ("print_all_action", "print_all"),
                ("exit_action", "exit_app"),
                ("password_action", "password"),
                ("ftp_action", "ftp"),
                ("import_txt_action", "import_txt"),
                ("import_rtf_action", "import_rtf"),
                ("export_html_action", "export_html"),
                ("export_rtf_action", "export_rtf"),
                ("export_txt_action", "export_txt"),
                ("export_ansi_txt_action", "export_ansi"),
                ("export_unicode_txt_action", "export_unicode"),
                ("export_all_html_action", "export_all_html"),
                ("export_all_rtf_action", "export_all_rtf"),
                ("export_all_txt_action", "export_all_txt"),
                ("export_all_ansi_txt_action", "export_all_ansi"),
                ("export_all_unicode_txt_action", "export_all_unicode"),
                ("export_node_rtf_action", "export_node_rtf"),
                ("add_child_action", "tree_child"),
                ("add_sibling_action", "tree_sibling"),
                ("rename_action", "rename"),
                ("delete_action", "delete_node"),
                ("unify_action", "unify_subtree"),
                ("unify_root_action", "unify_all"),
                ("desk_note_action", "desktop_note"),
                ("bg_color_action", "bg_color"),
                ("fg_color_action", "fg_color"),
                ("move_up_action", "move_up"),
                ("move_down_action", "move_down"),
                ("expand_current_action", "toggle_node"),
                ("expand_all_action", "expand_all"),
                ("collapse_all_action", "collapse_all"),
                ("undo_action", "undo"),
                ("redo_action", "redo"),
                ("cut_action", "cut"),
                ("copy_action", "copy"),
                ("paste_action", "paste"),
                ("paste_child_action", "paste_child"),
                ("delete_text_action", "delete_text"),
                ("insert_image_action", "insert_image"),
                ("insert_date_action", "insert_date"),
                ("search_action", "search"),
                ("alarm_action", "alarm"),
                ("regular_action", "regular"),
                ("bold_action", "bold"),
                ("italic_action", "italic"),
                ("underline_action", "underline"),
                ("strike_action", "strike"),
                ("bigger_action", "bigger"),
                ("smaller_action", "smaller"),
                ("align_left_action", "align_left"),
                ("align_center_action", "align_center"),
                ("align_right_action", "align_right"),
                ("align_justify_action", "align_justify"),
                ("text_color_action", "text_color"),
                ("highlight_color_action", "highlight"),
                ("bullet_action", "bullet"),
                ("cycle_scrollbars_action", "scrollbars"),
                ("import_config_action", "import_config"),
                ("stats_action", "stats"),
                ("about_action", "about"),
                ("settings_action", "settings"),
            ]
            for attr, kind in icon_specs:
                action = getattr(self, attr, None)
                if action is None:
                    continue
                try:
                    action.setIcon(self._draw_toolbar_icon(kind))
                except Exception:
                    pass
                try:
                    if not action.toolTip():
                        action.setToolTip(action.text())
                except Exception:
                    pass

        def _create_actions(self) -> None:
            self.new_action = self._act("Neue Datei", self.new_document, "Ctrl+N")
            self.open_action = self._act("Öffnen", self.open_dialog, "Ctrl+O")
            self.save_action = self._act("Speichern", self.save_file, "Ctrl+S")
            self.save_as_action = self._act("Speichern unter", self.save_file_as)
            self.backup_now_action = self._act("Jetzt Sicherung erstellen", self.create_manual_backup)
            self.open_backup_action = self._act("Sicherung öffnen", self.open_backup_dialog)
            self.close_doc_action = self._act("Schließen", self.close_document)
            self.print_note_action = self._act("Aktuelle Notiz drucken", self.print_current_note, "Ctrl+P")
            self.print_subtree_action = self._act("Aktuellen Teilbaum drucken", self.print_current_subtree)
            self.print_all_action = self._act("Ganzen Baum drucken", self.print_root)
            self.exit_action = self._act("Beenden", self.close, "Ctrl+Q")
            self.password_action = self._act("Passwort setzen/ändern", self.change_password)
            self.ftp_action = self._act("FTP öffnen/speichern", self.show_ftp_dialog)
            self.import_txt_action = self._act("TXT importieren", self.import_txt_into_current)
            self.import_rtf_action = self._act("RTF importieren", self.import_rtf_into_current)
            self.export_html_action = self._act("Aktuellen Teilbaum als HTML exportieren", lambda: self.export_current("html"))
            self.export_rtf_action = self._act("Export als RTF", lambda: self.export_current("rtf"))
            self.export_txt_action = self._act("Export als TXT", lambda: self.export_current("txt"))
            self.export_ansi_txt_action = self._act("Export als ANSI TXT", lambda: self.export_current("txt_ansi"))
            self.export_unicode_txt_action = self._act("Export als Unicode TXT", lambda: self.export_current("txt_unicode"))
            self.export_all_html_action = self._act("Ganzen Baum als HTML exportieren", lambda: self.export_root("html"))
            self.export_all_rtf_action = self._act("Ganzen Baum als RTF exportieren", lambda: self.export_root("rtf"))
            self.export_all_txt_action = self._act("Ganzen Baum als TXT exportieren", lambda: self.export_root("txt"))
            self.export_all_ansi_txt_action = self._act("Ganzen Baum als ANSI TXT exportieren", lambda: self.export_root("txt_ansi"))
            self.export_all_unicode_txt_action = self._act("Ganzen Baum als Unicode TXT exportieren", lambda: self.export_root("txt_unicode"))
            self.export_node_rtf_action = self._act("Knoten-RTF speichern", self.export_node_rtf)

            self.add_child_action = self._act("Neu darunter", self.add_child_node)
            self.add_sibling_action = self._act("Neu daneben", self.add_sibling_node)
            self.rename_action = self._act("Umbenennen", self.rename_node, "Ctrl+U")
            self.delete_action = self._act("Löschen", self.delete_anything)
            self.unify_action = self._act("Teilbaum zusammenfassen", self.unify_current_subtree)
            self.unify_root_action = self._act("Ganzen Baum zusammenfassen", self.unify_root_tree)
            self.desk_note_action = self._act("Desktop-Notiz", self.show_desktop_note)
            self.bg_color_action = self._act("Knoten-Hintergrundfarbe", lambda: self.choose_node_color("bg"))
            self.fg_color_action = self._act("Knoten-Schriftfarbe", lambda: self.choose_node_color("fg"))
            self.move_up_action = self._act("Nach oben", self.move_node_up)
            self.move_down_action = self._act("Nach unten", self.move_node_down)
            self.expand_current_action = self._act("Auf-/Zu", self.toggle_current_expanded)
            self.expand_all_action = self._act("Alle auf", self.expand_all_nodes)
            self.collapse_all_action = self._act("Alle zu", self.collapse_all_nodes)

            self.undo_action = self._act("Rückgängig", self.undo_edit, "Ctrl+Z")
            self.redo_action = self._act("Wiederholen", self.redo_edit, "Ctrl+Y")
            self.cut_action = self._act("Ausschneiden", self.cut_anything, "Ctrl+X")
            self.copy_action = self._act("Kopieren", self.copy_anything, "Ctrl+C")
            self.paste_action = self._act("Einfügen", self.paste_anything, "Ctrl+V")
            self.paste_child_action = self._act("Einfügen als Unterknoten", self.paste_node_as_child)
            self.delete_text_action = self._act("Text löschen", self.delete_selection_text)
            self.insert_image_action = self._act("Bild einfügen", self.insert_image)
            self.insert_date_action = self._act("Datum einfügen", self.insert_current_date_time)
            self.search_action = self._act("Suchen", self.show_search, "Ctrl+F")
            self.alarm_action = self._act("Wecker", self.show_alarm_dialog, "Ctrl+Space")

            self.bold_action = self._act("Fett", self.toggle_bold, "Ctrl+B", checkable=True)
            self.bold_action.setToolTip("Fett")
            self.bold_action.setObjectName("ToolStrip_bold")
            self.italic_action = self._act("Kursiv", self.toggle_italic, "Ctrl+I", checkable=True)
            self.italic_action.setToolTip("Kursiv")
            self.italic_action.setObjectName("ToolStrip_italic")
            self.underline_action = self._act("Unterstrichen", self.toggle_underline, checkable=True)
            self.underline_action.setToolTip("Unterstrichen")
            self.underline_action.setObjectName("ToolStrip_underline")
            self.strike_action = self._act("Durchgestrichen", self.toggle_strike, checkable=True)
            self.strike_action.setToolTip("Durchgestrichen")
            self.strike_action.setObjectName("ToolStrip_strikeout")
            self.regular_action = self._act("Normal", self.reset_char_format)
            self.regular_action.setToolTip("Normal")
            self.regular_action.setObjectName("ToolStrip_regular")
            self.bigger_action = self._act("Schrift größer", lambda: self.change_font_size(+1), "Ctrl++")
            self.bigger_action.setToolTip("Schrift größer")
            self.bigger_action.setObjectName("ToolStrip_bigger")
            self.smaller_action = self._act("Schrift kleiner", lambda: self.change_font_size(-1), "Ctrl+-")
            self.smaller_action.setToolTip("Schrift kleiner")
            self.smaller_action.setObjectName("ToolStrip_smaller")
            self._style_rtf_toolstrip_actions()
            self.text_color_action = self._act("Textfarbe", self.choose_text_color)
            self.text_color_action.setObjectName("fgcolorToolStripMenuItem")
            self.highlight_color_action = self._act("Texthintergrund", self.choose_text_background)
            self.highlight_color_action.setObjectName("bgcolorToolStripMenuItem")
            self.align_left_action = self._act("Linksbündig", self.align_left, checkable=True)
            self.align_center_action = self._act("Zentriert", self.align_center, checkable=True)
            self.align_right_action = self._act("Rechtsbündig", self.align_right, checkable=True)
            self.align_justify_action = self._act("Blocksatz", self.align_justify, checkable=True)
            self.bullet_action = self._act("Aufzählungspunkt", self.insert_bullet)
            self.bullet_action.setObjectName("ToolStrip_dot")

            self.cycle_scrollbars_action = self._act("Scrollleisten wechseln", self.cycle_scrollbars)
            self.cycle_scrollbars_action.setObjectName("ToolStrip_whatscroll")
            self.import_config_action = self._act("Alt-Config importieren", self.import_legacy_config_dialog)
            self.stats_action = self._act("Statistik", self.show_stats_dialog)
            self.about_action = self._act("Info", self.show_about)
            self.settings_action = self._act("Einstellungen", self.show_settings_dialog)

            self._assign_toolbar_icons()

        def _create_menus(self) -> None:
            self.file_menu = self.menuBar().addMenu("&Menü")
            self.file_menu.addAction(self.new_action)
            self.file_menu.addAction(self.open_action)
            self.file_menu.addAction(self.save_action)
            self.file_menu.addAction(self.save_as_action)
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.backup_now_action)
            self.file_menu.addAction(self.open_backup_action)
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.close_doc_action)
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.import_txt_action)
            self.file_menu.addAction(self.import_rtf_action)
            self.file_menu.addSeparator()
            self.print_menu = self.file_menu.addMenu("Drucken")
            self.print_menu.addAction(self.print_note_action)
            self.print_menu.addAction(self.print_subtree_action)
            self.print_menu.addAction(self.print_all_action)
            self.file_menu.addSeparator()
            self.recent_menu = self.file_menu.addMenu("Zuletzt geöffnet")
            self.update_recent_menu()
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.password_action)
            self.file_menu.addAction(self.ftp_action)
            self.file_menu.addAction(self.settings_action)
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.exit_action)

            self.edit_menu = self.menuBar().addMenu("Bearbeiten")
            self.edit_menu.addAction(self.undo_action)
            self.edit_menu.addAction(self.redo_action)
            self.edit_menu.addSeparator()
            self.edit_menu.addAction(self.cut_action)
            self.edit_menu.addAction(self.copy_action)
            self.edit_menu.addAction(self.paste_action)
            self.edit_menu.addSeparator()
            self.edit_menu.addAction(self.search_action)

            self.node_menu = self.menuBar().addMenu("Knoten")
            self.node_menu.addAction(self.add_sibling_action)
            self.node_menu.addAction(self.add_child_action)
            self.node_menu.addAction(self.rename_action)
            self.node_menu.addAction(self.delete_action)
            self.node_menu.addSeparator()
            self.node_menu.addAction(self.paste_child_action)
            self.node_menu.addSeparator()
            self.node_menu.addAction(self.unify_action)
            self.node_menu.addAction(self.unify_root_action)
            self.node_menu.addAction(self.desk_note_action)
            self.node_menu.addAction(self.bg_color_action)
            self.node_menu.addAction(self.fg_color_action)
            self.node_menu.addSeparator()
            self.node_menu.addAction(self.move_up_action)
            self.node_menu.addAction(self.move_down_action)
            self.node_menu.addAction(self.expand_current_action)
            self.node_menu.addAction(self.expand_all_action)
            self.node_menu.addAction(self.collapse_all_action)

            self.export_menu = self.menuBar().addMenu("Export")
            self.export_menu.addAction(self.export_html_action)
            self.export_menu.addAction(self.export_rtf_action)
            self.export_menu.addAction(self.export_txt_action)
            self.export_menu.addAction(self.export_ansi_txt_action)
            self.export_menu.addAction(self.export_unicode_txt_action)
            self.export_menu.addSeparator()
            self.export_menu.addAction(self.export_all_html_action)
            self.export_menu.addAction(self.export_all_rtf_action)
            self.export_menu.addAction(self.export_all_txt_action)
            self.export_menu.addAction(self.export_all_ansi_txt_action)
            self.export_menu.addAction(self.export_all_unicode_txt_action)
            self.export_menu.addSeparator()
            self.export_menu.addAction(self.export_node_rtf_action)

            self.extras_menu = self.menuBar().addMenu("Extras")
            self.extras_menu.addAction(self.alarm_action)
            self.extras_menu.addAction(self.stats_action)
            self.extras_menu.addSeparator()
            self.extras_menu.addAction(self.cycle_scrollbars_action)
            self.extras_menu.addAction(self.import_config_action)

            self.help_menu = self.menuBar().addMenu("Hilfe")
            self.help_menu.addAction(self.about_action)

            self.tree.setContextMenuPolicy(_enum(QtCore.Qt, "ContextMenuPolicy", "ActionsContextMenu"))
            for action in (
                self.add_sibling_action,
                self.add_child_action,
                self.rename_action,
                self.delete_action,
                self.unify_action,
                self.unify_root_action,
                self.desk_note_action,
                self.bg_color_action,
                self.fg_color_action,
                self.paste_child_action,
                self.move_up_action,
                self.move_down_action,
                self.expand_current_action,
                self.expand_all_action,
                self.collapse_all_action,
                self.export_node_rtf_action,
            ):
                self.tree.addAction(action)

            for action in (
                self.undo_action,
                self.redo_action,
                self.cut_action,
                self.copy_action,
                self.paste_action,
                self.delete_text_action,
                self.insert_image_action,
                self.insert_date_action,
                self.search_action,
                self.import_txt_action,
                self.import_rtf_action,
            ):
                self.editor.addAction(action)
            separator = QtGui.QAction(self.editor)
            separator.setSeparator(True)
            self.editor.addAction(separator)
            for action in (
                self.bold_action,
                self.italic_action,
                self.underline_action,
                self.strike_action,
                self.regular_action,
                self.bigger_action,
                self.smaller_action,
                self.align_left_action,
                self.align_center_action,
                self.align_right_action,
                self.align_justify_action,
                self.text_color_action,
                self.highlight_color_action,
                self.bullet_action,
            ):
                self.editor.addAction(action)

        def _configure_toolbar(self, toolbar: Any) -> None:
            """Configure compact icon-only toolbars arranged as three usable rows."""
            try:
                toolbar.setToolButtonStyle(_enum(QtCore.Qt, "ToolButtonStyle", "ToolButtonIconOnly"))
            except Exception:
                pass
            try:
                toolbar.setMovable(False)
            except Exception:
                pass
            try:
                toolbar.setFloatable(False)
            except Exception:
                pass
            try:
                toolbar.setIconSize(QtCore.QSize(24, 24))
            except Exception:
                pass
            try:
                toolbar.setMinimumHeight(36)
            except Exception:
                pass
            try:
                toolbar.setStyleSheet(
                    "QToolBar { spacing: 3px; padding: 2px 4px; }"
                    "QToolButton { min-width: 28px; min-height: 28px; max-width: 32px; max-height: 32px; padding: 2px; margin: 1px; }"
                )
            except Exception:
                pass

        def _style_toolbar_field_widget(self, widget: Any) -> None:
            try:
                widget.setMinimumHeight(28)
            except Exception:
                pass
            try:
                widget.setStyleSheet("padding: 1px 4px; margin: 1px;")
            except Exception:
                pass

        def _create_toolbars(self) -> None:
            """Build a compact three-row command strip closer to Notizen.NET."""
            file_bar = self.addToolBar("Datei")
            self._configure_toolbar(file_bar)
            for action in (
                self.new_action,
                self.open_action,
                self.save_action,
                self.save_as_action,
                self.backup_now_action,
                self.open_backup_action,
                self.close_doc_action,
                self.print_note_action,
                self.export_txt_action,
                self.export_rtf_action,
                self.export_html_action,
                self.ftp_action,
                self.settings_action,
                self.about_action,
            ):
                file_bar.addAction(action)

            try:
                self.addToolBarBreak()
            except Exception:
                pass
            node_bar = self.addToolBar("Knoten/Bearbeiten")
            self._configure_toolbar(node_bar)
            for action in (
                self.add_child_action,
                self.add_sibling_action,
                self.rename_action,
                self.delete_action,
                self.move_up_action,
                self.move_down_action,
                self.expand_current_action,
                self.expand_all_action,
                self.collapse_all_action,
                self.unify_action,
                self.unify_root_action,
                self.desk_note_action,
                self.undo_action,
                self.redo_action,
                self.cut_action,
                self.copy_action,
                self.paste_action,
                self.search_action,
                self.insert_image_action,
                self.insert_date_action,
                self.import_txt_action,
                self.import_rtf_action,
                self.alarm_action,
                self.stats_action,
                self.import_config_action,
            ):
                node_bar.addAction(action)

            try:
                self.addToolBarBreak()
            except Exception:
                pass
            font_bar = self.addToolBar("RTF-Formatierung")
            font_bar.setObjectName("ToolStrip_fontstyle")
            self._configure_toolbar(font_bar)
            self.font_size_spin = QtWidgets.QSpinBox()
            self.font_size_spin.setObjectName("ToolStrip_fontsizenumber")
            self.font_size_spin.setRange(6, 99)
            self.font_size_spin.setValue(10)
            self.font_size_spin.setMaximumWidth(52)
            self.font_size_spin.setToolTip("Schriftgröße")
            self.font_size_spin.valueChanged.connect(self.apply_font_size)
            self._style_toolbar_field_widget(self.font_size_spin)
            self.font_family_combo = QtWidgets.QFontComboBox()
            self.font_family_combo.setObjectName("ToolStrip_fonts")
            self.font_family_combo.setToolTip("Schriftart")
            self.font_family_combo.currentFontChanged.connect(self.apply_font_family)
            self.font_family_combo.setMaximumWidth(170)
            self._style_toolbar_field_widget(self.font_family_combo)
            font_bar.addWidget(self.font_size_spin)
            font_bar.addWidget(self.font_family_combo)
            for action in (
                self.regular_action,
                self.bold_action,
                self.italic_action,
                self.underline_action,
                self.strike_action,
                self.bigger_action,
                self.smaller_action,
                self.align_left_action,
                self.align_center_action,
                self.align_right_action,
                self.align_justify_action,
                self.text_color_action,
                self.highlight_color_action,
                self.bullet_action,
                self.cycle_scrollbars_action,
            ):
                font_bar.addAction(action)

        def _create_tray_icon(self) -> None:
            self.tray_icon = None
            self.tray_menu = None
            if self.disable_tray:
                return
            if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
                return
            self.tray_menu = QtWidgets.QMenu(self)
            self.tray_icon = QtWidgets.QSystemTrayIcon(self.windowIcon(), self)
            self.tray_icon.setToolTip("Notizen")
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.setContextMenu(self.tray_menu)
            self.update_tray_menu()
            self.tray_icon.show()

        def tray_hide_decision(self):
            return decide_startup_tray_visibility(
                tray_icon_created=bool(getattr(self, "tray_icon", None)),
                show_in_taskbar_when_minimized=self.settings.show_in_taskbar_when_minimized,
                gnome_safe_start=self.settings.gnome_safe_tray_start,
                force_hide_to_tray=self.force_tray_start,
            )

        def tray_safety_message(self) -> str:
            decision = self.tray_hide_decision()
            if decision.gnome_session and not decision.hide_to_tray:
                return f"{decision.reason} {gnome_tray_install_hint()}"
            return decision.reason

        def update_tray_menu(self) -> None:
            if not getattr(self, "tray_icon", None) or not getattr(self, "tray_menu", None):
                return
            self.tray_menu.clear()
            self.tray_menu.addAction(self.tr("Strip1_8", "Beenden"), self.close)
            self.tray_menu.addAction(self.tr("info3", "Zeigen/Ausblenden"), self.toggle_visible)
            self.tray_menu.addSeparator()
            for node in self.document.walk():
                if node.desktop_note is not None:
                    self.tray_menu.addAction(node.title, lambda checked=False, n=node: self.show_desktop_note(n))

        def apply_language(self) -> None:
            """Apply the legacy language table to visible Qt menus and actions."""
            self.tree.setHeaderLabel(self.tr("info1", "Notizen"))
            if hasattr(self, "quick_search_edit"):
                self.quick_search_edit.setPlaceholderText(self.tr("kontext5", "Suchen"))
                self.quick_search_next_button.setText("Weiter")
                self.quick_search_all_button.setText("Alle")
                self.title_apply_button.setText(self.tr("kontext2_2", "Umbenennen"))
                self.editor_mode_label.setText("Modus: RTF/Text")
            self.file_menu.setTitle(self.tr("Strip1_1", "&Menü"))
            self.print_menu.setTitle(self.tr("Strip1_15", "Drucken"))
            self.edit_menu.setTitle(self.tr("Strip1_17", "Bearbeiten"))
            self.node_menu.setTitle("Knoten")
            self.export_menu.setTitle(self.tr("export", "Export"))
            self.extras_menu.setTitle("Extras")
            self.help_menu.setTitle(self.tr("Strip1_9", "&Hilfe"))

            self.new_action.setText(self.tr("Strip1_2", "Neue Datei"))
            self.open_action.setText(self.tr("Strip1_3", "Öffnen"))
            self.undo_action.setText("Rückgängig")
            self.redo_action.setText("Wiederholen")
            self.align_left_action.setText("Linksbündig")
            self.align_center_action.setText("Zentriert")
            self.align_right_action.setText("Rechtsbündig")
            self.align_justify_action.setText("Blocksatz")
            self.save_action.setText(self.tr("Strip1_4", "Speichern"))
            self.save_as_action.setText(self.tr("Strip1_5", "Speichern unter"))
            self.backup_now_action.setText("Jetzt Sicherung erstellen")
            self.open_backup_action.setText("Sicherung öffnen")
            self.close_doc_action.setText(self.tr("Strip1_6", "Schließen"))
            self.print_note_action.setText(self.tr("Strip1_15", "Aktuelle Notiz drucken"))
            self.print_subtree_action.setText("Aktuellen Teilbaum drucken")
            self.print_all_action.setText("Ganzen Baum drucken")
            self.exit_action.setText(self.tr("Strip1_8", "Beenden"))
            self.password_action.setText(self.tr("strip1_21", "Passwort setzen/ändern"))
            self.settings_action.setText(self.tr("Strip1_7", "Einstellungen"))
            self.ftp_action.setText("FTP öffnen/speichern")
            self.import_txt_action.setText("TXT importieren")
            self.import_rtf_action.setText("RTF importieren")

            self.add_child_action.setText(self.tr("kontext2_1", "Neu darunter"))
            self.add_sibling_action.setText(self.tr("kontext11", "Neu daneben"))
            self.rename_action.setText(self.tr("kontext2_2", "Umbenennen"))
            self.delete_action.setText(self.tr("kontext2_3", "Löschen"))
            self.unify_action.setText("Teilbaum zusammenfassen")
            self.unify_root_action.setText("Ganzen Baum zusammenfassen")
            self.desk_note_action.setText(self.tr("kontext2_5", "Desktop-Notiz"))
            self.bg_color_action.setText(self.tr("kontext2_9", "Hintergrundfarbe"))
            self.fg_color_action.setText(self.tr("kontext2_10", "Schriftfarbe"))
            self.move_up_action.setText("Nach oben")
            self.move_down_action.setText("Nach unten")
            self.expand_current_action.setText("Auf-/Zu")
            self.expand_all_action.setText("Alle auf")
            self.collapse_all_action.setText("Alle zu")
            self.export_node_rtf_action.setText(self.tr("kontext2_4", "Knoten-RTF speichern"))

            self.cut_action.setText(self.tr("Strip4_1", "Ausschneiden"))
            self.copy_action.setText(self.tr("Strip4_2", "Kopieren"))
            self.paste_action.setText(self.tr("Strip4_3", "Einfügen"))
            self.paste_child_action.setText("Einfügen als Unterknoten")
            self.delete_text_action.setText(self.tr("kontext4", "Text löschen"))
            self.insert_image_action.setText(self.tr("kontext6", "Bild einfügen"))
            self.insert_date_action.setText(self.tr("kontext7", "Datum einfügen"))
            self.search_action.setText(self.tr("kontext5", "Suchen"))

            self.export_html_action.setText("Aktuellen Teilbaum als HTML exportieren")
            self.export_rtf_action.setText(f"{self.tr('export', 'Export')} {self.tr('exportrtf', 'in rtf')}")
            self.export_txt_action.setText("Export als UTF-8 TXT")
            self.export_ansi_txt_action.setText(f"{self.tr('export', 'Export')} {self.tr('exporttxt', 'in ansi txt')}")
            self.export_unicode_txt_action.setText(f"{self.tr('export', 'Export')} {self.tr('exporttxt2', 'in unicode txt')}")
            self.export_all_html_action.setText("Ganzen Baum als HTML exportieren")
            self.export_all_rtf_action.setText("Ganzen Baum als RTF exportieren")
            self.export_all_txt_action.setText("Ganzen Baum als UTF-8 TXT exportieren")
            self.export_all_ansi_txt_action.setText("Ganzen Baum als ANSI TXT exportieren")
            self.export_all_unicode_txt_action.setText("Ganzen Baum als Unicode TXT exportieren")

            self.alarm_action.setText("Wecker")
            self.stats_action.setText("Statistik")
            self.cycle_scrollbars_action.setText("Scrollleisten wechseln")
            self.import_config_action.setText("Alt-Config importieren")
            self.about_action.setText(self.tr("Strip1_20", "Info + Hilfe + Feedback"))
            self.update_recent_menu()
            self.update_tray_menu()

        def on_tray_activated(self, reason: Any) -> None:
            trigger = getattr(QtWidgets.QSystemTrayIcon.ActivationReason, "Trigger", None)
            double = getattr(QtWidgets.QSystemTrayIcon.ActivationReason, "DoubleClick", None)
            if reason in {trigger, double}:
                self.toggle_visible()

        def toggle_visible(self) -> None:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()

        def _restore_window_settings(self) -> None:
            x = self.settings.window_x
            y = self.settings.window_y
            width = self.settings.window_width
            height = self.settings.window_height
            screen_left = 0
            screen_top = 0
            screen_width = 1280
            screen_height = 800
            try:
                screen = QtGui.QGuiApplication.primaryScreen()
                available = screen.availableGeometry() if screen is not None else None
                if available is not None:
                    screen_left = int(available.left())
                    screen_top = int(available.top())
                    screen_width = int(available.width())
                    screen_height = int(available.height())
            except Exception:
                pass
            geometry = sanitize_legacy_window_geometry(
                x=x,
                y=y,
                width=width,
                height=height,
                screen_left=screen_left,
                screen_top=screen_top,
                screen_width=screen_width,
                screen_height=screen_height,
                force_reset=self.reset_window_geometry,
            )
            self.resize(geometry.width, geometry.height)
            self.move(geometry.x, geometry.y)
            if geometry.reset:
                self.settings.window_state = "Normal"
            if (
                legacy_window_state_is_restorable(self.settings.window_x, self.settings.window_y)
                and normalize_window_state(self.settings.window_state) == "Maximized"
                and not self.reset_window_geometry
            ):
                self.showMaximized()

        def ensure_main_window_visible(self, *, reset_window: bool = False) -> None:
            """Show the main window as a reachable normal window.

            GNOME/Wayland may ignore focus stealing, but repeated show/raise calls
            after the event loop starts reliably avoid a hidden/minimized/offscreen
            startup state.  This is intentionally stronger than the old Windows
            tray startup path.
            """

            if reset_window:
                self.reset_window_geometry = True
                self._restore_window_settings()
            try:
                no_state = _enum(QtCore.Qt, "WindowState", "WindowNoState")
                self.setWindowState(no_state)
            except Exception:
                pass
            try:
                self.showNormal()
            except Exception:
                self.show()
            self.show()
            try:
                self.raise_()
            except Exception:
                pass
            try:
                self.activateWindow()
            except Exception:
                pass

        def _store_window_settings(self) -> None:
            geo = self.geometry()
            if not self.isMaximized():
                self.settings.window_x = geo.x()
                self.settings.window_y = geo.y()
                self.settings.window_width = geo.width()
                self.settings.window_height = geo.height()
            self.settings.window_state = "Maximized" if self.isMaximized() else "Minimized" if self.isMinimized() else "Normal"
            if self.document.path:
                self.settings.remember_file(self.document.path)
            self.settings.save()

        def _configure_autosave(self) -> None:
            if self.settings.autosave_seconds and self.settings.autosave_seconds > 0:
                self.autosave_timer.start(self.settings.autosave_seconds * 1000)
            else:
                self.autosave_timer.stop()

        def _apply_scrollbar_settings(self) -> None:
            choice = int(getattr(self.settings, "scrollbars_choice", 3))
            as_needed = _enum(QtCore.Qt, "ScrollBarPolicy", "ScrollBarAsNeeded")
            off = _enum(QtCore.Qt, "ScrollBarPolicy", "ScrollBarAlwaysOff")
            self.editor.setHorizontalScrollBarPolicy(as_needed if (choice & 1) else off)
            self.editor.setVerticalScrollBarPolicy(as_needed if (choice & 2) else off)

        def update_recent_menu(self) -> None:
            if not hasattr(self, "recent_menu"):
                return
            self.recent_menu.clear()
            if not self.settings.recent_files:
                action = self.recent_menu.addAction("Keine")
                action.setEnabled(False)
                return
            for path_text in reversed(self.settings.recent_files):
                action = self.recent_menu.addAction(path_text)
                action.triggered.connect(lambda checked=False, p=path_text: self.open_recent_file(p))

        def open_recent_file(self, path_text: str) -> bool:
            """Open and rotate a legacy recent-file entry like the old menu."""
            requested_path = Path(path_text)
            selected = self.settings.activate_recent_file(path_text) or path_text
            self.update_recent_menu()
            path = Path(selected) if selected else requested_path
            if not path.exists():
                QtWidgets.QMessageBox.warning(self, "Zuletzt geöffnet", f"Datei nicht gefunden:\n{path}")
                self.settings.save()
                return False
            if not self.maybe_save_changes():
                self.settings.save()
                return False
            return self.load_path(path)

        def update_title(self) -> None:
            name = self.document.path.name if self.document.path else "unbenannt.alx"
            marker = " *" if self.document.changed else ""
            self.setWindowTitle(f"{name}{marker} - Notizen Python/Qt")

        def _clipboard_has_node(self) -> bool:
            try:
                mime = QtWidgets.QApplication.clipboard().mimeData()
                if mime.hasFormat(NODE_MIME_TYPE):
                    return True
                return mime.hasText() and looks_like_node_clipboard_xml(mime.text())
            except Exception:
                return False

        def update_actions(self) -> None:
            has_root = self.document.root is not None
            has_current = self.current_node() is not None
            for action in (
                self.save_action,
                self.save_as_action,
                self.backup_now_action,
                self.open_backup_action,
                self.close_doc_action,
                self.print_note_action,
                self.print_subtree_action,
                self.print_all_action,
                self.export_html_action,
                self.export_rtf_action,
                self.export_txt_action,
                self.export_ansi_txt_action,
                self.export_unicode_txt_action,
                self.export_all_html_action,
                self.export_all_rtf_action,
                self.export_all_txt_action,
                self.export_all_ansi_txt_action,
                self.export_all_unicode_txt_action,
                self.export_node_rtf_action,
                self.print_note_action,
                self.print_subtree_action,
                self.print_all_action,
                self.password_action,
                self.stats_action,
                self.unify_root_action,
            ):
                action.setEnabled(has_root)
            for action in (
                self.add_child_action,
                self.add_sibling_action,
                self.rename_action,
                self.delete_action,
                self.unify_action,
                self.desk_note_action,
                self.bg_color_action,
                self.fg_color_action,
                self.copy_action,
                self.cut_action,
                self.paste_child_action,
                self.import_txt_action,
                self.import_rtf_action,
                self.move_up_action,
                self.move_down_action,
                self.expand_current_action,
                self.expand_all_action,
                self.collapse_all_action,
            ):
                action.setEnabled(has_current)
            node = self.current_node()
            can_move_up = node is not None and node.parent is not None and node.index_in_parent() > 0
            can_move_down = node is not None and node.parent is not None and node.index_in_parent() < len(node.parent.children) - 1
            self.move_up_action.setEnabled(can_move_up)
            self.move_down_action.setEnabled(can_move_down)
            has_node_clipboard = self.clipboard_node is not None or self._clipboard_has_node()
            text_widget_active = self._editor_active() or self._active_line_edit() is not None
            self.paste_action.setEnabled(has_current and (has_node_clipboard or text_widget_active))
            self.paste_child_action.setEnabled(has_current and has_node_clipboard)

        def update_node_text_boxes(self) -> None:
            """Synchronize the WinForms txt1/txt2 header boxes with the selected node."""
            if not hasattr(self, "tree_top_edit") or not hasattr(self, "node_title_edit"):
                return
            self._updating_title_boxes = True
            try:
                root = self.document.root
                node = self.current_node()
                self.tree_top_edit.setText(root.title if root is not None else "")
                self.node_title_edit.setEnabled(node is not None)
                self.title_apply_button.setEnabled(node is not None)
                self.editor_mode_label.setEnabled(node is not None)
                self.node_title_edit.setText(node.title if node is not None else "")
            finally:
                self._updating_title_boxes = False

        def commit_title_box(self) -> None:
            """Apply the txt2 title field to the selected tree node."""
            if self._updating_title_boxes or not hasattr(self, "node_title_edit"):
                return
            node = self.current_node()
            item = self.tree.currentItem()
            if node is None or item is None:
                return
            title = self.node_title_edit.text().strip() or "..."
            if title == node.title and item.text(0) == title:
                return
            node.title = title
            if item.text(0) != title:
                item.setText(0, title)
            self.document.mark_changed()
            self.update_title()
            self.update_node_text_boxes()
            self.update_tray_menu()
            for win in self.desktop_windows.values():
                if win.node is node:
                    win.reload_from_node()

        def _quick_search_collect(self, *, all_nodes: bool) -> None:
            self.save_current_editor_to_node()
            term = self.quick_search_edit.text() if hasattr(self, "quick_search_edit") else ""
            signature = (term, all_nodes)
            if signature == self._quick_search_signature:
                return
            self._quick_search_signature = signature
            self.last_search = term
            if not term:
                self._quick_search_results = []
                self._quick_search_index = 0
                self.statusBar().showMessage("Keine Suche eingegeben")
                return
            if all_nodes:
                nodes = list(self.document.walk())
            else:
                current = self.current_node()
                nodes = [current] if current is not None else []
            self._quick_search_results = search_nodes(nodes, term)
            self._quick_search_index = 0
            self.statusBar().showMessage(f"{len(self._quick_search_results)} Treffer")

        def quick_search_next(self) -> None:
            if not hasattr(self, "quick_search_edit"):
                return
            # The small button searches the current note by default; if there is
            # no hit, fall back to the whole tree so the field remains useful.
            self._quick_search_collect(all_nodes=False)
            if not self._quick_search_results:
                self._quick_search_collect(all_nodes=True)
            self._activate_quick_search_result()

        def quick_search_all(self) -> None:
            if not hasattr(self, "quick_search_edit"):
                return
            self._quick_search_collect(all_nodes=True)
            self._activate_quick_search_result()

        def _activate_quick_search_result(self) -> None:
            if not self._quick_search_results:
                self.statusBar().showMessage("Keine Treffer")
                return
            result = self._quick_search_results[self._quick_search_index % len(self._quick_search_results)]
            self._quick_search_index += 1
            self.select_node(result.node)
            cursor = self.editor.textCursor()
            cursor.setPosition(result.start)
            cursor.setPosition(result.start + result.length, QtGui.QTextCursor.MoveMode.KeepAnchor)
            self.editor.setTextCursor(cursor)
            self.editor.setFocus()
            self.statusBar().showMessage(
                f"Treffer {((self._quick_search_index - 1) % len(self._quick_search_results)) + 1}"
                f"/{len(self._quick_search_results)}"
            )


        def current_node(self) -> NoteNode | None:
            item = self.tree.currentItem()
            if item is None:
                return None
            data = item.data(0, USER_ROLE)
            return data if isinstance(data, NoteNode) else None

        def item_for_node(self, node: NoteNode) -> Any | None:
            return self.node_items.get(id(node))

        def _make_item(self, node: NoteNode) -> Any:
            item = QtWidgets.QTreeWidgetItem([node.title])
            item.setData(0, USER_ROLE, node)
            item.setFlags(ITEM_SELECTABLE | ITEM_ENABLED | ITEM_EDITABLE | ITEM_DRAG | ITEM_DROP)
            if node.bg_argb:
                item.setBackground(0, QtGui.QBrush(color_from_argb(node.bg_argb)))
            if node.fg_argb:
                item.setForeground(0, QtGui.QBrush(color_from_argb(node.fg_argb)))
            self.node_items[id(node)] = item
            for child in node.children:
                item.addChild(self._make_item(child))
            return item

        def _apply_tree_expansion_state(self, item: Any) -> None:
            node = item.data(0, USER_ROLE)
            if isinstance(node, NoteNode):
                item.setExpanded(bool(node.expanded))
            for index in range(item.childCount()):
                self._apply_tree_expansion_state(item.child(index))

        def build_tree(self) -> None:
            self._loading_tree = True
            self.node_items.clear()
            self.tree.clear()
            if self.document.root is not None:
                root_item = self._make_item(self.document.root)
                self.tree.addTopLevelItem(root_item)
                # QTreeWidgetItem.setExpanded() is only reliable after the item
                # belongs to a QTreeWidget.  Notizen.NET restored ``isexpanded``
                # after creating each TreeNode; applying the state here prevents
                # loaded .alx files from immediately overwriting collapsed nodes
                # during the next save.
                self._apply_tree_expansion_state(root_item)
                self.tree.setCurrentItem(root_item)
            self._loading_tree = False
            self.on_tree_selection_changed()
            self.update_node_text_boxes()
            self.update_actions()
            self.update_tray_menu()

        def sync_model_from_tree(self) -> None:
            if self._loading_tree:
                return

            def sync_item(item: Any, parent_node: NoteNode | None) -> NoteNode | None:
                node = item.data(0, USER_ROLE)
                if not isinstance(node, NoteNode):
                    return None
                node.title = item.text(0)
                node.expanded = item.isExpanded()
                node.parent = parent_node
                node.children = []
                for i in range(item.childCount()):
                    child_node = sync_item(item.child(i), node)
                    if child_node is not None:
                        node.children.append(child_node)
                return node

            if self.tree.topLevelItemCount() > 0:
                self.document.root = sync_item(self.tree.topLevelItem(0), None)

        def on_tree_rows_moved(self) -> None:
            if self._loading_tree:
                return
            self.sync_model_from_tree()
            self.document.mark_changed()
            self.update_title()

        def on_tree_expansion_changed(self, item: Any, expanded: bool) -> None:
            if self._loading_tree:
                return
            node = item.data(0, USER_ROLE)
            if isinstance(node, NoteNode):
                node.expanded = expanded
                self.document.mark_changed()
                self.update_title()

        def sync_expansion_from_tree(self) -> None:
            def update(item: Any) -> None:
                node = item.data(0, USER_ROLE)
                if isinstance(node, NoteNode):
                    node.expanded = item.isExpanded()
                    node.title = item.text(0)
                for i in range(item.childCount()):
                    update(item.child(i))

            for i in range(self.tree.topLevelItemCount()):
                update(self.tree.topLevelItem(i))

        def on_tree_selection_changed(self) -> None:
            if self._loading_tree:
                return
            self.save_current_editor_to_node()
            node = self.current_node()
            self.current_node_ref = node
            self.load_editor_from_node(node)
            self.update_node_text_boxes()
            self.update_actions()

        def on_item_changed(self, item: Any, column: int) -> None:
            if self._loading_tree or column != 0:
                return
            node = item.data(0, USER_ROLE)
            if isinstance(node, NoteNode):
                node.title = item.text(0) or "..."
                for win in self.desktop_windows.values():
                    if win.node is node:
                        win.reload_from_node()
                self.document.mark_changed()
                self.update_title()
                self.update_node_text_boxes()
                self.update_tray_menu()

        def load_editor_from_node(self, node: NoteNode | None, preserve_focus: bool = False) -> None:
            self._loading_editor = True
            if node is None:
                self.editor.clear()
                self.editor.setEnabled(False)
            else:
                self.editor.setEnabled(True)
                cursor_pos = self.editor.textCursor().position() if preserve_focus else 0
                self.editor.setHtml(rtf_to_html(node.rtf))
                self.editor.document().setModified(False)
                if preserve_focus:
                    cursor = self.editor.textCursor()
                    cursor.setPosition(min(cursor_pos, max(0, self.editor.document().characterCount() - 1)))
                    self.editor.setTextCursor(cursor)
            self._loading_editor = False

        def save_current_editor_to_node(self) -> None:
            if self._loading_editor or self.current_node_ref is None:
                return
            if self.editor.document().isModified():
                self.current_node_ref.rtf = html_to_rtf(self.editor.toHtml())
                self.editor.document().setModified(False)
                self.document.mark_changed()
                self.update_title()
                self._reload_desktop_note_windows(self.current_node_ref)

        def _reload_desktop_note_windows(self, node: NoteNode, source_window: "DesktopNoteWindow | None" = None) -> None:
            for win in list(self.desktop_windows.values()):
                if win.node is node and win is not source_window:
                    win.reload_from_node()

        def on_editor_changed(self) -> None:
            if self._loading_editor or self.current_node_ref is None:
                return
            self.current_node_ref.rtf = html_to_rtf(self.editor.toHtml())
            self.document.mark_changed()
            self.update_title()
            self._reload_desktop_note_windows(self.current_node_ref)

        def maybe_save_changes(self) -> bool:
            self.save_current_editor_to_node()
            if not self.document.changed:
                return True
            answer = QtWidgets.QMessageBox.question(
                self,
                "Speichern?",
                "Möchten Sie vorher speichern?",
                YES | NO | CANCEL,
                YES,
            )
            if answer == CANCEL:
                return False
            if answer == YES:
                return self.save_file()
            return True

        def new_document(self) -> None:
            if not self.maybe_save_changes():
                return
            self.document = NoteDocument.new()
            self.current_node_ref = None
            self.close_all_desktop_notes()
            self.build_tree()
            self.update_title()

        def close_document(self) -> None:
            if not self.maybe_save_changes():
                return
            self.document = NoteDocument.new()
            self.current_node_ref = None
            self.close_all_desktop_notes()
            self.build_tree()
            self.update_title()

        def open_dialog(self) -> None:
            if not self.maybe_save_changes():
                return
            start_dir = self.settings.last_directory or str(ensure_legacy_documents_notizen_dir())
            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Notizen öffnen",
                start_dir,
                "Notizen Dateien (*.alx *.xml);;Alle Dateien (*)",
            )
            if file_name:
                self.load_path(Path(file_name))

        def prompt_password(self, title: str = "Passwort") -> str | None:
            text, ok = QtWidgets.QInputDialog.getText(
                self,
                title,
                "Passwort:",
                QtWidgets.QLineEdit.EchoMode.Password,
            )
            return text if ok else None

        def load_path(self, path: Path, password: str | None = None) -> bool:
            try:
                document = load_alx(path, password=password)
            except PasswordRequired:
                pw = self.prompt_password("Passwort erforderlich")
                if pw is None:
                    return False
                return self.load_path(path, password=pw)
            except InvalidPassword:
                pw = self.prompt_password("Falsches Passwort oder falsche Datei")
                if pw is None:
                    return False
                return self.load_path(path, password=pw)
            except (OSError, AlxError, Exception) as exc:
                QtWidgets.QMessageBox.critical(self, "Öffnen fehlgeschlagen", str(exc))
                return False
            self.close_all_desktop_notes()
            self.document = document
            self.current_node_ref = None
            self.settings.remember_file(path)
            self.settings.save()
            self.update_recent_menu()
            self.build_tree()
            self.update_title()
            self.statusBar().showMessage(f"Geöffnet: {path}")
            for node in self.document.walk():
                if node.desktop_note is not None and node.desktop_note.visible:
                    self.show_desktop_note(node)
            return True

        def _load_document_bytes_interactive(self, payload: bytes, label: str, password: str | None = None) -> NoteDocument | None:
            try:
                return load_alx_bytes(payload, password=password)
            except PasswordRequired:
                pw = self.prompt_password("Passwort erforderlich")
                if pw is None:
                    return None
                return self._load_document_bytes_interactive(payload, label, password=pw)
            except InvalidPassword:
                pw = self.prompt_password("Falsches Passwort oder falsche Datei")
                if pw is None:
                    return None
                return self._load_document_bytes_interactive(payload, label, password=pw)
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "Öffnen fehlgeschlagen", f"{label}\n\n{exc}")
                return None

        def _replace_document_after_open(self, document: NoteDocument, status_message: str, *, path: Path | None = None) -> None:
            self.close_all_desktop_notes()
            self.document = document
            if path is not None:
                self.document.path = path
                self.settings.remember_file(path)
                self.update_recent_menu()
            self.current_node_ref = None
            self.settings.save()
            self.build_tree()
            self.update_title()
            self.statusBar().showMessage(status_message)
            for node in self.document.walk():
                if node.desktop_note is not None and node.desktop_note.visible:
                    self.show_desktop_note(node)

        def load_ftp_url(self, url: str, password: str | None = None, *, ask_save: bool = True) -> bool:
            if ask_save and not self.maybe_save_changes():
                return False
            try:
                target = FtpTarget.from_fields(url, "")
                payload = target.download()
            except FtpSyncError as exc:
                QtWidgets.QMessageBox.critical(self, "FTP öffnen fehlgeschlagen", str(exc))
                return False
            document = self._load_document_bytes_interactive(payload, target.display_url, password=password)
            if document is None:
                return False
            self.settings.ftp_host = target.host
            self.settings.ftp_path = target.remote_path
            self.settings.ftp_username = target.username
            self.settings.ftp_password = target.password
            self._replace_document_after_open(document, f"Geöffnet per FTP: {target.display_url}")
            return True

        def _ftp_target_from_settings(self) -> FtpTarget:
            return FtpTarget.from_fields(
                self.settings.ftp_host,
                self.settings.ftp_path,
                self.settings.ftp_username,
                self.settings.ftp_password,
            )

        def show_ftp_dialog(self) -> None:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("FTP")
            layout = QtWidgets.QFormLayout(dialog)
            host = QtWidgets.QLineEdit(self.settings.ftp_host)
            remote_path = QtWidgets.QLineEdit(self.settings.ftp_path)
            username = QtWidgets.QLineEdit(self.settings.ftp_username)
            password = QtWidgets.QLineEdit(self.settings.ftp_password)
            password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            layout.addRow("Host", host)
            layout.addRow("Pfad zur .alx-Datei", remote_path)
            layout.addRow("Benutzer", username)
            layout.addRow("Passwort", password)
            note = QtWidgets.QLabel("Kompatibel zum alten Notizen.NET-FTP-Dialog. FTP überträgt unverschlüsselt; für vertrauliche Daten besser die ALX-Datei selbst mit Passwort speichern.")
            note.setWordWrap(True)
            layout.addRow(note)
            buttons = QtWidgets.QHBoxLayout()
            open_button = QtWidgets.QPushButton("Öffnen")
            save_button = QtWidgets.QPushButton("Speichern")
            apply_button = QtWidgets.QPushButton("Nur übernehmen")
            cancel_button = QtWidgets.QPushButton("Abbrechen")
            for button in (open_button, save_button, apply_button, cancel_button):
                buttons.addWidget(button)
            layout.addRow(buttons)

            def store() -> None:
                self.settings.ftp_host = host.text().strip()
                self.settings.ftp_path = remote_path.text().strip()
                self.settings.ftp_username = username.text().strip()
                self.settings.ftp_password = password.text()
                self.settings.save()

            open_button.clicked.connect(lambda checked=False: (store(), dialog.done(100)))
            save_button.clicked.connect(lambda checked=False: (store(), dialog.done(101)))
            apply_button.clicked.connect(lambda checked=False: (store(), dialog.done(102)))
            cancel_button.clicked.connect(dialog.reject)
            result = dialog.exec()
            if result == 100:
                self.load_from_ftp()
            elif result == 101:
                self.save_to_ftp()

        def load_from_ftp(self) -> bool:
            if not self.maybe_save_changes():
                return False
            try:
                target = self._ftp_target_from_settings()
                payload = target.download()
            except FtpSyncError as exc:
                QtWidgets.QMessageBox.critical(self, "FTP öffnen fehlgeschlagen", str(exc))
                return False
            document = self._load_document_bytes_interactive(payload, target.display_url)
            if document is None:
                return False
            self.close_all_desktop_notes()
            self.document = document
            self.current_node_ref = None
            self.settings.save()
            self.build_tree()
            self.update_title()
            self.statusBar().showMessage(f"Geöffnet per FTP: {target.display_url}")
            for node in self.document.walk():
                if node.desktop_note is not None and node.desktop_note.visible:
                    self.show_desktop_note(node)
            return True

        def save_to_ftp(self) -> bool:
            try:
                target = self._ftp_target_from_settings()
            except FtpSyncError as exc:
                QtWidgets.QMessageBox.critical(self, "FTP speichern fehlgeschlagen", str(exc))
                return False
            try:
                self.save_current_editor_to_node()
                self.sync_expansion_from_tree()
                self.sync_model_from_tree()
                payload = dump_alx_bytes(self.document, password=self.document.password)
                target.upload(payload)
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "FTP speichern fehlgeschlagen", str(exc))
                return False
            self.document.changed = False
            self.update_title()
            self.statusBar().showMessage(f"Gespeichert per FTP: {target.display_url}")
            return True

        def save_file(self) -> bool:
            if self.document.path is None:
                return self.save_file_as()
            return self._save_to(self.document.path)

        def save_file_as(self) -> bool:
            self.save_current_editor_to_node()
            start = str(self.document.path or Path(self.settings.last_directory or str(ensure_legacy_documents_notizen_dir())) / LEGACY_DEFAULT_FILENAME)
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Speichern unter", start, "ALX Dateien (*.alx)")
            if not file_name:
                return False
            return self._save_to(Path(file_name))

        def _save_to(self, path: Path) -> bool:
            try:
                self.save_current_editor_to_node()
                self.sync_expansion_from_tree()
                self.sync_model_from_tree()
                save_alx(
                    self.document,
                    path,
                    password=self.document.password,
                    backup=True,
                    backup_keep=self.settings.backup_keep,
                )
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "Speichern fehlgeschlagen", str(exc))
                return False
            self.settings.remember_file(path)
            self.settings.save()
            self.update_recent_menu()
            self.update_title()
            self.statusBar().showMessage(f"Gespeichert: {path}")
            return True

        def create_manual_backup(self) -> bool:
            """Create an explicit Notizen.NET-style safety copy of the saved ALX file."""
            self.save_current_editor_to_node()
            self.sync_expansion_from_tree()
            self.sync_model_from_tree()
            if self.document.path is None:
                QtWidgets.QMessageBox.information(
                    self,
                    "Sicherung",
                    "Diese Notizdatei wurde noch nicht gespeichert. Bitte zuerst speichern.",
                )
                return False
            path = self.document.path
            if not path.exists():
                QtWidgets.QMessageBox.warning(self, "Sicherung", f"Datei nicht gefunden:\n{path}")
                return False
            try:
                backup = create_backup(path, keep=self.settings.backup_keep)
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "Sicherung fehlgeschlagen", str(exc))
                return False
            if backup is None:
                QtWidgets.QMessageBox.information(
                    self,
                    "Sicherung",
                    "Sicherungen sind deaktiviert oder es gibt noch keine gespeicherte Datei.",
                )
                return False
            self.statusBar().showMessage(f"Sicherung erstellt: {backup}")
            return True

        def open_backup_dialog(self) -> bool:
            """Open one of the legacy safety copies from the configured backup directory."""
            if self.document.path is None:
                QtWidgets.QMessageBox.information(
                    self,
                    "Sicherung öffnen",
                    "Erst eine ALX-Datei öffnen oder speichern, dann kann der Sicherungsordner ermittelt werden.",
                )
                return False
            backup_dir = backup_directory_for(self.document.path)
            if not backup_dir.exists():
                QtWidgets.QMessageBox.information(
                    self,
                    "Sicherung öffnen",
                    f"Noch keine Sicherungen vorhanden:\n{backup_dir}",
                )
                return False
            backups = list_backups(self.document.path)
            start = str(backups[-1].path if backups else backup_dir)
            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Sicherung öffnen",
                start,
                "ALX Sicherungen (*.alx);;Alle Dateien (*)",
            )
            if not file_name:
                return False
            if not self.maybe_save_changes():
                return False
            return self.load_path(Path(file_name))

        def autosave(self) -> None:
            if legacy_autosave_should_save(
                root_exists=self.document.root is not None,
                path=self.document.path,
                changed=self.document.changed,
            ):
                self._save_to(self.document.path)

        def add_child_node(self) -> None:
            parent = self.current_node() or self.document.ensure_root()
            child = parent.add_child(NoteNode(title="...", rtf=""))
            parent_item = self.item_for_node(parent)
            if parent_item is None:
                self.build_tree()
                return
            self._loading_tree = True
            item = self._make_item(child)
            parent_item.addChild(item)
            parent_item.setExpanded(True)
            self._loading_tree = False
            self.tree.setCurrentItem(item)
            self.tree.editItem(item, 0)
            self.document.mark_changed()
            self.update_title()

        def add_sibling_node(self) -> None:
            current = self.current_node()
            if current is None:
                self.add_child_node()
                return
            parent = current if current.parent is None else current.parent
            sibling = legacy_new_next_node(current)
            index = parent.children.index(sibling)
            parent_item = self.item_for_node(parent)
            if parent_item is None:
                self.build_tree()
                return
            self._loading_tree = True
            item = self._make_item(sibling)
            parent_item.insertChild(index, item)
            self._loading_tree = False
            self.tree.setCurrentItem(item)
            self.tree.editItem(item, 0)
            self.document.mark_changed()
            self.update_title()

        def edit_tree_item(self, item: Any | None = None, column: int = 0) -> None:
            target = item or self.tree.currentItem()
            if target is not None:
                self.tree.setCurrentItem(target)
                self.tree.editItem(target, 0)

        def rename_node(self) -> None:
            self.edit_tree_item()

        def delete_node(self) -> None:
            node = self.current_node()
            item = self.tree.currentItem()
            if node is None or item is None:
                return
            if node is self.document.root:
                if QtWidgets.QMessageBox.question(self, "Löschen", "Wirklich die gesamte Notiz schließen?") == YES:
                    self.close_document()
                return
            if QtWidgets.QMessageBox.question(self, "Löschen", "Möchten Sie den Knoten wirklich löschen?") != YES:
                return
            fallback = legacy_delete_fallback_node(node)
            self.close_desktop_notes_in_subtree(node)
            node.remove_from_parent()
            self.build_tree()
            if fallback is not None:
                self.select_node(fallback)
            self.document.mark_changed()
            self.update_title()

        def _set_node_clipboard_payload(self, node: NoteNode) -> str | None:
            try:
                xml_text = node_to_clipboard_xml(node, include_desktop_note=False)
                mime = QtCore.QMimeData()
                mime.setData(NODE_MIME_TYPE, xml_text.encode("utf-8"))
                mime.setText(xml_text)
                QtWidgets.QApplication.clipboard().setMimeData(mime)
                return xml_text
            except Exception:
                return None

        def _node_from_system_clipboard(self) -> tuple[NoteNode | None, str | None]:
            try:
                mime = QtWidgets.QApplication.clipboard().mimeData()
                xml_text = ""
                if mime.hasFormat(NODE_MIME_TYPE):
                    xml_text = bytes(mime.data(NODE_MIME_TYPE)).decode("utf-8", errors="replace")
                elif mime.hasText() and looks_like_node_clipboard_xml(mime.text()):
                    xml_text = mime.text()
                if xml_text:
                    return node_from_clipboard_xml(xml_text, include_desktop_note=False), xml_text
            except Exception:
                pass
            return None, None

        def _clipboard_node_for_paste(self) -> tuple[NoteNode | None, bool]:
            system_node, xml_text = self._node_from_system_clipboard()
            if system_node is not None:
                if self.cut_source_node is not None and xml_text == self.cut_clipboard_xml:
                    return self.clipboard_node or system_node, True
                self.cut_source_node = None
                self.cut_clipboard_xml = None
                self.clipboard_node = system_node
                return system_node, False
            return self.clipboard_node, self.cut_source_node is not None

        def copy_node(self) -> None:
            node = self.current_node()
            if node is None:
                return
            self.clipboard_node = node.clone_deep(include_desktop_note=False)
            self.cut_source_node = None
            self.cut_clipboard_xml = None
            self._set_node_clipboard_payload(self.clipboard_node)
            self.update_actions()

        def cut_node(self) -> None:
            node = self.current_node()
            if node is None or node is self.document.root:
                return
            self.clipboard_node = node.clone_deep(include_desktop_note=False)
            self.cut_source_node = node
            self.cut_clipboard_xml = self._set_node_clipboard_payload(self.clipboard_node)
            self.update_actions()

        def _paste_node_model(self, source: NoteNode, target: NoteNode, *, as_child: bool = False) -> NoteNode:
            if as_child:
                pasted = source.clone_deep(include_desktop_note=False)
                target.insert_child(0, pasted)
                return pasted
            return legacy_paste_clone(source, target)

        def paste_node(self) -> None:
            target = self.current_node()
            source, is_cut = self._clipboard_node_for_paste()
            if target is None or source is None:
                return
            if is_cut and self.cut_source_node is not None and (
                self.cut_source_node is target or self.cut_source_node.is_ancestor_of(target)
            ):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Einfügen",
                    "Ein ausgeschnittener Knoten kann nicht in sich selbst oder darunter eingefügt werden.",
                )
                return
            pasted = self._paste_node_model(source, target, as_child=False)
            if is_cut and self.cut_source_node is not None:
                self.close_desktop_notes_in_subtree(self.cut_source_node)
                self.cut_source_node.remove_from_parent()
                self.cut_source_node = None
                self.cut_clipboard_xml = None
            self.build_tree()
            self.select_node(pasted)
            self.document.mark_changed()
            self.update_title()

        def paste_node_as_child(self) -> None:
            target = self.current_node()
            source, is_cut = self._clipboard_node_for_paste()
            if target is None or source is None:
                return
            if is_cut and self.cut_source_node is not None and (
                self.cut_source_node is target or self.cut_source_node.is_ancestor_of(target)
            ):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Einfügen",
                    "Ein ausgeschnittener Knoten kann nicht in sich selbst oder darunter eingefügt werden.",
                )
                return
            pasted = self._paste_node_model(source, target, as_child=True)
            if is_cut and self.cut_source_node is not None:
                self.close_desktop_notes_in_subtree(self.cut_source_node)
                self.cut_source_node.remove_from_parent()
                self.cut_source_node = None
                self.cut_clipboard_xml = None
            self.build_tree()
            self.select_node(pasted)
            self.document.mark_changed()
            self.update_title()

        def _editor_active(self) -> bool:
            return self.editor.hasFocus() or self.editor.viewport().hasFocus()

        def _active_line_edit(self) -> Any | None:
            widget = QtWidgets.QApplication.focusWidget()
            if not isinstance(widget, QtWidgets.QLineEdit):
                return None
            if widget is getattr(self, "node_title_edit", None) or widget is getattr(self, "quick_search_edit", None):
                return widget
            return None

        def cut_anything(self) -> None:
            line_edit = self._active_line_edit()
            if line_edit is not None:
                line_edit.cut()
            elif self._editor_active():
                self.editor.cut()
                self.save_current_editor_to_node()
            else:
                self.cut_node()

        def copy_anything(self) -> None:
            line_edit = self._active_line_edit()
            if line_edit is not None:
                line_edit.copy()
            elif self._editor_active():
                self.editor.copy()
            else:
                self.copy_node()

        def paste_anything(self) -> None:
            line_edit = self._active_line_edit()
            if line_edit is not None:
                line_edit.paste()
            elif self._editor_active():
                self.editor.paste()
                self.save_current_editor_to_node()
            else:
                self.paste_node()

        def delete_anything(self) -> None:
            line_edit = self._active_line_edit()
            if line_edit is not None:
                if line_edit.hasSelectedText():
                    line_edit.insert("")
                else:
                    line_edit.del_()
            elif self._editor_active():
                self.delete_selection_text()
            else:
                self.delete_node()

        def delete_selection_text(self) -> None:
            cursor = self.editor.textCursor()
            if cursor.hasSelection():
                cursor.removeSelectedText()
            else:
                cursor.deleteChar()
            self.editor.setTextCursor(cursor)
            self.save_current_editor_to_node()

        def insert_current_date_time(self) -> None:
            now = QtCore.QDateTime.currentDateTime()
            date = now.date()
            time = now.time()
            text = f" {date.day()}.{date.month()}.{date.year()} {time.hour()}:{time.minute()} "
            self.editor.textCursor().insertText(text)
            self.save_current_editor_to_node()

        def _image_file_to_data_uri(self, file_name: str) -> str | None:
            image = QtGui.QImage(file_name)
            if image.isNull():
                return None
            byte_array = QtCore.QByteArray()
            buffer = QtCore.QBuffer(byte_array)
            write_only = _enum(QtCore.QIODevice, "OpenModeFlag", "WriteOnly")
            if not buffer.open(write_only):
                return None
            try:
                if not image.save(buffer, "PNG"):
                    return None
            finally:
                buffer.close()
            payload = bytes(byte_array)
            return "data:image/png;base64," + base64.b64encode(payload).decode("ascii")

        def insert_image(self) -> None:
            start_dir = str(Path.home())
            try:
                pictures = _enum(QtCore.QStandardPaths, "StandardLocation", "PicturesLocation")
                paths = QtCore.QStandardPaths.standardLocations(pictures)
                if paths:
                    start_dir = paths[0]
            except Exception:
                pass
            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Bild einfügen",
                start_dir,
                "Bild-Dateien (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff);;Alle Dateien (*)",
            )
            if not file_name:
                return
            data_uri = self._image_file_to_data_uri(file_name)
            if data_uri is None:
                QtWidgets.QMessageBox.warning(self, "Bild einfügen", "Dieses Bild konnte nicht geladen werden.")
                return
            cursor = self.editor.textCursor()
            cursor.insertHtml(f'<img src="{data_uri}"/>')
            self.editor.setTextCursor(cursor)
            self.save_current_editor_to_node()

        def unify_current_subtree(self) -> None:
            source = self.current_node()
            if source is None:
                return
            self._append_unified_note(source, f"Zusammenfassung - {source.title}")

        def unify_root_tree(self) -> None:
            root = self.document.root
            if root is None:
                return
            self._append_unified_note(root, f"Zusammenfassung - {root.title}")

        def _append_unified_note(self, source: NoteNode, title: str) -> None:
            self.save_current_editor_to_node()
            unified = create_unified_note(source, title=title)
            source.add_child(unified)
            source.expanded = True
            self.build_tree()
            self.select_node(unified)
            self.document.mark_changed()
            self.update_title()
            self.update_actions()

        def select_node(self, node: NoteNode) -> None:
            item = self.item_for_node(node)
            if item is not None:
                self.tree.setCurrentItem(item)
                self.tree.scrollToItem(item)

        def default_desktop_note_state(self) -> DesktopNoteState:
            """Return the Notizen.NET defaults for a newly created desktop note."""
            try:
                pos = QtGui.QCursor.pos()
                x = int(pos.x())
                y = int(pos.y())
            except Exception:
                x = 80
                y = 80
            return DesktopNoteState(
                x=x,
                y=y,
                width=200,
                height=200,
                visible=True,
                opacity=0.85,
                argb=legacy_light_color_argb(),
            )

        def show_desktop_note(self, node: NoteNode | None = None) -> None:
            node = node or self.current_node()
            if node is None:
                return
            win = self.desktop_windows.get(id(node))
            if win is None:
                win = DesktopNoteWindow(self, node)
                self.desktop_windows[id(node)] = win
            if node.desktop_note is None:
                node.desktop_note = self.default_desktop_note_state()
            node.desktop_note.visible = True
            win.reload_from_node()
            win.show2()
            win.activateWindow()
            self.document.mark_changed()
            self.update_title()
            self.update_tray_menu()

        def close_desktop_note(self, node: NoteNode) -> None:
            win = self.desktop_windows.pop(id(node), None)
            if win is not None:
                win.hide()
                win.deleteLater()
            node.desktop_note = None
            self.update_tray_menu()

        def close_desktop_notes_in_subtree(self, node: NoteNode) -> None:
            """Close floating notes below ``node`` like ``Baum.mach_haft_weg``."""

            for victim in list(node.walk()):
                self.close_desktop_note(victim)

        def close_all_desktop_notes(self) -> None:
            for win in list(self.desktop_windows.values()):
                win.hide()
                win.deleteLater()
            self.desktop_windows.clear()

        def choose_node_color(self, which: str) -> None:
            node = self.current_node()
            item = self.tree.currentItem()
            if node is None or item is None:
                return
            color = QtWidgets.QColorDialog.getColor(parent=self)
            if not color.isValid():
                return
            if which == "bg":
                node.bg_argb = argb_from_color(color)
                item.setBackground(0, QtGui.QBrush(color))
            else:
                node.fg_argb = argb_from_color(color)
                item.setForeground(0, QtGui.QBrush(color))
            self.document.mark_changed()
            self.update_title()

        def show_search(self) -> None:
            dialog = SearchDialog(self)
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()

        def show_alarm_dialog(self) -> None:
            dialog = AlarmDialog(self)
            dialog.exec()

        def schedule_alarm(self, when: Any, message: str) -> None:
            """Compatibility entry point for the older simple Ctrl+Space alarm."""
            try:
                start = datetime.fromtimestamp(int(when.toSecsSinceEpoch()))
            except Exception:
                start = datetime.now()
            self.schedule_alarm_spec(AlarmSpec(start=start, message=message or "Notizen-Wecker"))

        def schedule_alarm_spec(self, spec: AlarmSpec) -> None:
            spec = spec.normalized()
            due = next_occurrence(spec, datetime.now())
            if due is None:
                QtWidgets.QMessageBox.warning(self, "Wecker", "Der Zeitpunkt liegt in der Vergangenheit.")
                return
            timer = QtCore.QTimer(self)
            timer.setSingleShot(True)
            msecs = max(0, int((due - datetime.now()).total_seconds() * 1000))
            # QTimer accepts a signed 32-bit millisecond interval. Re-arm in
            # chunks for dates that are further away.
            timer.timeout.connect(lambda t=timer, alarm=spec, target_due=due: self._trigger_alarm_spec(t, alarm, target_due))
            self.alarms.append(timer)
            timer.start(int(min(msecs, 2**31 - 1)))
            self.statusBar().showMessage(
                f"Wecker gestellt: {due.strftime('%d.%m.%Y %H:%M')} ({describe_recurrence(spec)})"
            )

        def _trigger_alarm_spec(self, timer: Any, spec: AlarmSpec, due: datetime) -> None:
            try:
                self.alarms.remove(timer)
            except ValueError:
                pass
            # For very distant reminders the timer wakes up early because of the
            # 32-bit QTimer limit. Continue silently until the actual time is due.
            if due > datetime.now():
                self.schedule_alarm_spec(spec)
                return
            self.show()
            self.raise_()
            self.activateWindow()
            QtWidgets.QMessageBox.information(self, "Wecker", spec.message or "Notizen-Wecker")
            if spec.recurrence != "none":
                next_due = next_occurrence(spec, datetime.now())
                if next_due is not None:
                    self.schedule_alarm_spec(spec)

        def _trigger_alarm(self, timer: Any, message: str) -> None:
            self._trigger_alarm_spec(
                timer,
                AlarmSpec(start=datetime.now(), message=message or "Notizen-Wecker"),
                datetime.now(),
            )

        def _print_html(self, html: str, title: str) -> None:
            try:
                QtPrintSupport = _load_qt_print_support()
                printer = QtPrintSupport.QPrinter(_enum(QtPrintSupport.QPrinter, "PrinterMode", "HighResolution"))
                printer.setDocName(title or "Notizen")
                dialog = QtPrintSupport.QPrintDialog(printer, self)
                if dialog.exec() != ACCEPTED:
                    return
                document = QtGui.QTextDocument()
                document.setDefaultFont(self.editor.font())
                document.setHtml(html)
                print_method = getattr(document, "print_", None) or getattr(document, "print", None)
                if print_method is None:
                    raise RuntimeError("QTextDocument-Druckmethode ist in dieser Qt-Bindung nicht verfügbar.")
                print_method(printer)
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "Drucken fehlgeschlagen", str(exc))

        def print_current_note(self) -> None:
            node = self.current_node()
            if node is None:
                return
            self.save_current_editor_to_node()
            html = self.editor.toHtml() if node is self.current_node_ref else rtf_to_html(node.rtf)
            self._print_html(html, node.title)

        def print_current_subtree(self) -> None:
            node = self.current_node()
            if node is None:
                return
            self.save_current_editor_to_node()
            self._print_html(rtf_to_html(tree_to_rtf(node)), node.title)

        def print_root(self) -> None:
            if self.document.root is None:
                return
            self.save_current_editor_to_node()
            self._print_html(rtf_to_html(tree_to_rtf(self.document.root)), self.document.root.title)

        def _safe_export_name(self, title: str, suffix: str) -> str:
            bad = '<>:"/\\|?*'
            clean = "".join("_" if ch in bad else ch for ch in (title or "export")).strip()
            return f"{clean or 'export'}{suffix}"

        def _export_tree_to_file(self, node: NoteNode, kind: str, title: str | None = None) -> None:
            if kind == "rtf":
                suffix = ".rtf"
                file_filter = "RTF-Dateien (*.rtf)"
            elif kind == "html":
                suffix = ".html"
                file_filter = "HTML-Dateien (*.html *.htm)"
            else:
                suffix = ".txt"
                file_filter = "Text-Dateien (*.txt)"
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Export",
                self._safe_export_name(title or node.title, suffix),
                file_filter,
            )
            if not file_name:
                return
            path = Path(file_name)
            if kind == "rtf":
                path.write_text(tree_to_rtf(node), encoding="utf-8", errors="replace")
            elif kind == "html":
                path.write_bytes(tree_to_html_bytes(node, HtmlExportOptions(title=title or node.title)))
            elif kind == "txt_ansi":
                path.write_bytes(tree_to_text_bytes(node, encoding="ansi"))
            elif kind == "txt_unicode":
                path.write_bytes(tree_to_text_bytes(node, encoding="unicode"))
            else:
                path.write_bytes(tree_to_text_bytes(node, encoding="utf-8"))
            self.statusBar().showMessage(f"Exportiert: {path}")

        def export_current(self, kind: str) -> None:
            node = self.current_node()
            if node is None:
                return
            self.save_current_editor_to_node()
            self._export_tree_to_file(node, kind)

        def export_root(self, kind: str) -> None:
            root = self.document.root
            if root is None:
                return
            self.save_current_editor_to_node()
            self._export_tree_to_file(root, kind, title=f"{root.title}_gesamt")

        def export_node_rtf(self) -> None:
            node = self.current_node()
            if node is None:
                return
            self.save_current_editor_to_node()
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Knoten-RTF speichern",
                self._safe_export_name(node.title, ".rtf"),
                "*.rtf",
            )
            if not file_name:
                return
            path = Path(file_name)
            path.write_text(node.rtf or "", encoding="utf-8", errors="replace")
            self.statusBar().showMessage(f"Gespeichert: {path}")

        def _decode_import_bytes(self, data: bytes, *, prefer_ansi: bool = False) -> str:
            """Decode text like the legacy Windows dialogs did, with Unicode fallbacks."""
            if data.startswith((b"\xff\xfe", b"\xfe\xff")):
                return data.decode("utf-16", errors="replace")
            if data.startswith(b"\xef\xbb\xbf"):
                return data.decode("utf-8-sig", errors="replace")
            encodings = ("cp1252", "utf-8") if prefer_ansi else ("utf-8", "cp1252")
            for encoding in encodings:
                try:
                    return data.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return data.decode("utf-8", errors="replace")

        def _replace_current_note_rtf(self, rtf: str, status: str = "") -> None:
            node = self.current_node()
            if node is None:
                return
            node.rtf = rtf or ""
            self.current_node_ref = node
            self.load_editor_from_node(node)
            self.editor.document().setModified(False)
            self._reload_desktop_note_windows(node)
            self.document.mark_changed()
            self.update_title()
            if status:
                self.statusBar().showMessage(status)

        def import_txt_into_current(self, checked: bool = False) -> None:
            node = self.current_node()
            if node is None:
                return
            start = self.settings.last_directory or str(ensure_legacy_documents_notizen_dir())
            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "TXT importieren",
                start,
                "Text-Dateien (*.txt);;Alle Dateien (*)",
            )
            if not file_name:
                return
            try:
                path = Path(file_name)
                text = self._decode_import_bytes(path.read_bytes())
                self._replace_current_note_rtf(plain_text_to_rtf(text), f"TXT importiert: {path}")
                self.settings.last_directory = str(path.parent)
                self.settings.save()
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "TXT importieren fehlgeschlagen", str(exc))

        def import_rtf_into_current(self, checked: bool = False) -> None:
            node = self.current_node()
            if node is None:
                return
            start = self.settings.last_directory or str(ensure_legacy_documents_notizen_dir())
            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "RTF importieren",
                start,
                "RTF-Dateien (*.rtf);;Text-Dateien (*.txt);;Alle Dateien (*)",
            )
            if not file_name:
                return
            try:
                path = Path(file_name)
                text = self._decode_import_bytes(path.read_bytes(), prefer_ansi=True)
                rtf = text if text.lstrip().startswith(r"{\rtf") else plain_text_to_rtf(text)
                self._replace_current_note_rtf(rtf, f"RTF importiert: {path}")
                self.settings.last_directory = str(path.parent)
                self.settings.save()
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "RTF importieren fehlgeschlagen", str(exc))

        def show_stats_dialog(self, checked: bool = False) -> None:
            root = self.document.root
            current = self.current_node()
            if root is None:
                return
            self.save_current_editor_to_node()

            def format_block(title: str, stats: Any) -> str:
                rows = "\n".join(f"{label}: {value}" for label, value in stats.as_legacy_lines())
                return f"{title}\n{rows}"

            blocks = []
            if current is not None:
                blocks.append(format_block(f"Aktueller Teilbaum: {current.title}", collect_tree_stats(current)))
            if root is not current:
                blocks.append(format_block(f"Ganzer Baum: {root.title}", collect_tree_stats(root)))
            QtWidgets.QMessageBox.information(self, "Statistik", "\n\n".join(blocks))

        def move_node_up(self, checked: bool = False) -> None:
            self._move_current_node(-1)

        def move_node_down(self, checked: bool = False) -> None:
            self._move_current_node(1)

        def _move_current_node(self, delta: int) -> None:
            node = self.current_node()
            if node is None or node.parent is None:
                return
            siblings = node.parent.children
            index = siblings.index(node)
            new_index = index + delta
            if new_index < 0 or new_index >= len(siblings):
                return
            self.save_current_editor_to_node()
            siblings[index], siblings[new_index] = siblings[new_index], siblings[index]
            self.build_tree()
            self.select_node(node)
            self.document.mark_changed()
            self.update_title()
            self.update_actions()

        def toggle_current_expanded(self, checked: bool = False) -> None:
            item = self.tree.currentItem()
            if item is None:
                return
            item.setExpanded(not item.isExpanded())
            node = item.data(0, USER_ROLE)
            if isinstance(node, NoteNode):
                node.expanded = item.isExpanded()
                self.document.mark_changed()
                self.update_title()

        def _set_tree_expanded_recursive(self, item: Any, expanded: bool) -> None:
            item.setExpanded(expanded)
            node = item.data(0, USER_ROLE)
            if isinstance(node, NoteNode):
                node.expanded = expanded
            for index in range(item.childCount()):
                self._set_tree_expanded_recursive(item.child(index), expanded)

        def expand_all_nodes(self, checked: bool = False) -> None:
            self._set_all_expanded(True)

        def collapse_all_nodes(self, checked: bool = False) -> None:
            self._set_all_expanded(False)

        def _set_all_expanded(self, expanded: bool) -> None:
            if self.tree.topLevelItemCount() == 0:
                return
            self._loading_tree = True
            try:
                for index in range(self.tree.topLevelItemCount()):
                    self._set_tree_expanded_recursive(self.tree.topLevelItem(index), expanded)
            finally:
                self._loading_tree = False
            self.document.mark_changed()
            self.update_title()
            self.update_actions()

        def cycle_scrollbars(self, checked: bool = False) -> None:
            self.settings.scrollbars_choice = (int(self.settings.scrollbars_choice) + 1) % 4
            self.settings.save()
            self._apply_scrollbar_settings()
            labels = {
                0: "keine Scrollleisten",
                1: "horizontal",
                2: "vertikal",
                3: "horizontal + vertikal",
            }
            self.statusBar().showMessage(f"Editor-Scrollleisten: {labels.get(self.settings.scrollbars_choice, 'unbekannt')}")

        def import_legacy_config_dialog(self, checked: bool = False) -> None:
            start = str(self.settings.config_dir if self.settings.config_dir.exists() else Path.home())
            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Alt-Config importieren",
                start,
                "Notizen-Konfiguration (*.xml);;Alle Dateien (*)",
            )
            if not file_name:
                return
            try:
                self.settings.apply_from_file(file_name)
                self.settings.save()
                self._configure_autosave()
                self._apply_scrollbar_settings()
                self.apply_language()
                autostart = apply_windows_autostart_script(
                    enabled=self.settings.autorun_enabled,
                    minimized=self.settings.autorun_minimized,
                    recent_files=self.settings.recent_files,
                )
                if autostart.message:
                    self.statusBar().showMessage(autostart.message)
                self.update_recent_menu()
                self.statusBar().showMessage(f"Alt-Config importiert: {file_name}")
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "Alt-Config importieren fehlgeschlagen", str(exc))

        def change_password(self) -> None:
            dialog = PasswordChangeDialog(self)
            if dialog.exec() != ACCEPTED:
                return
            self.document.password = dialog.new_password
            self.document.mark_changed()
            self.update_title()
            msg = "Passwort gesetzt." if dialog.new_password else "Passwort entfernt; die nächste Speicherung ist unverschlüsselt."
            self.statusBar().showMessage(msg)

        def merge_editor_format(self, fmt: Any) -> None:
            cursor = self.editor.textCursor()
            had_selection = cursor.hasSelection()
            original_position = cursor.position()
            if not had_selection and not self.editor.document().isEmpty():
                # Notizen.NET's RichTextBox formatter selected the whole note
                # when no text was selected. Keep that legacy behavior for font
                # family, size and style actions instead of only changing the
                # future typing format.
                cursor.select(_enum(QtGui.QTextCursor, "SelectionType", "Document"))
            cursor.mergeCharFormat(fmt)
            if not had_selection:
                self.editor.mergeCurrentCharFormat(fmt)
                try:
                    cursor.setPosition(max(0, min(original_position, self.editor.document().characterCount() - 1)))
                except Exception:
                    pass
            self.editor.setTextCursor(cursor)
            self.save_current_editor_to_node()
            self.update_format_controls()

        def apply_font_family(self, font: Any) -> None:
            if self._updating_format_controls:
                return
            family = font.family() if hasattr(font, "family") else str(font)
            if not family:
                return
            fmt = QtGui.QTextCharFormat()
            try:
                fmt.setFontFamilies([family])
            except Exception:
                fmt.setFontFamily(family)
            self.merge_editor_format(fmt)

        def apply_font_size(self, size: int) -> None:
            if self._updating_format_controls:
                return
            fmt = QtGui.QTextCharFormat()
            fmt.setFontPointSize(float(max(6, min(99, size))))
            self.merge_editor_format(fmt)

        def update_format_controls(self) -> None:
            if not hasattr(self, "font_family_combo") or not hasattr(self, "font_size_spin"):
                return
            fmt = self.editor.currentCharFormat()
            self._updating_format_controls = True
            try:
                family = ""
                try:
                    families = fmt.fontFamilies()
                    if families:
                        family = families[0]
                except Exception:
                    family = fmt.fontFamily()
                if family:
                    self.font_family_combo.setCurrentFont(QtGui.QFont(family))
                size = fmt.fontPointSize() or self.editor.font().pointSizeF() or 10
                self.font_size_spin.setValue(max(6, min(99, int(round(size)))))
                try:
                    current_weight = int(getattr(fmt.fontWeight(), "value", fmt.fontWeight()))
                    bold_weight = int(getattr(QtGui.QFont.Weight.Bold, "value", QtGui.QFont.Weight.Bold))
                    self.bold_action.setChecked(current_weight >= bold_weight)
                    self.italic_action.setChecked(fmt.fontItalic())
                    self.underline_action.setChecked(fmt.fontUnderline())
                    self.strike_action.setChecked(fmt.fontStrikeOut())
                except Exception:
                    pass
                try:
                    alignment = self.editor.alignment()
                    align_left = _enum(QtCore.Qt, "AlignmentFlag", "AlignLeft")
                    align_hcenter = _enum(QtCore.Qt, "AlignmentFlag", "AlignHCenter")
                    align_right = _enum(QtCore.Qt, "AlignmentFlag", "AlignRight")
                    align_justify = _enum(QtCore.Qt, "AlignmentFlag", "AlignJustify")
                    self.align_left_action.setChecked(bool(alignment & align_left) and not bool(alignment & (align_hcenter | align_right | align_justify)))
                    self.align_center_action.setChecked(bool(alignment & align_hcenter))
                    self.align_right_action.setChecked(bool(alignment & align_right))
                    self.align_justify_action.setChecked(bool(alignment & align_justify))
                except Exception:
                    pass
            finally:
                self._updating_format_controls = False

        def undo_edit(self) -> None:
            try:
                self.editor.undo()
            except Exception:
                return
            self.save_current_editor_to_node()
            self.update_format_controls()

        def redo_edit(self) -> None:
            try:
                self.editor.redo()
            except Exception:
                return
            self.save_current_editor_to_node()
            self.update_format_controls()

        def _set_alignment(self, alignment: Any) -> None:
            cursor = self.editor.textCursor()
            if cursor.hasSelection():
                block_fmt = cursor.blockFormat()
                block_fmt.setAlignment(alignment)
                cursor.mergeBlockFormat(block_fmt)
                self.editor.setTextCursor(cursor)
            else:
                self.editor.setAlignment(alignment)
            self.save_current_editor_to_node()
            self.update_format_controls()

        def align_left(self, checked: bool = False) -> None:
            self._set_alignment(_enum(QtCore.Qt, "AlignmentFlag", "AlignLeft"))

        def align_center(self, checked: bool = False) -> None:
            self._set_alignment(_enum(QtCore.Qt, "AlignmentFlag", "AlignHCenter"))

        def align_right(self, checked: bool = False) -> None:
            self._set_alignment(_enum(QtCore.Qt, "AlignmentFlag", "AlignRight"))

        def align_justify(self, checked: bool = False) -> None:
            self._set_alignment(_enum(QtCore.Qt, "AlignmentFlag", "AlignJustify"))

        def toggle_bold(self, checked: bool | None = None) -> None:
            fmt = self.editor.currentCharFormat()
            current = fmt.fontWeight()

            def _weight_value(value: Any) -> int:
                return int(getattr(value, "value", value))

            try:
                bold_weight = QtGui.QFont.Weight.Bold
                normal_weight = QtGui.QFont.Weight.Normal
            except Exception:
                bold_weight = 75
                normal_weight = 50
            if checked is None:
                make_bold = _weight_value(current) < _weight_value(bold_weight)
            else:
                make_bold = bool(checked)
            fmt.setFontWeight(bold_weight if make_bold else normal_weight)
            self.merge_editor_format(fmt)

        def toggle_italic(self, checked: bool | None = None) -> None:
            fmt = self.editor.currentCharFormat()
            fmt.setFontItalic((not fmt.fontItalic()) if checked is None else bool(checked))
            self.merge_editor_format(fmt)

        def toggle_underline(self, checked: bool | None = None) -> None:
            fmt = self.editor.currentCharFormat()
            fmt.setFontUnderline((not fmt.fontUnderline()) if checked is None else bool(checked))
            self.merge_editor_format(fmt)

        def toggle_strike(self, checked: bool | None = None) -> None:
            fmt = self.editor.currentCharFormat()
            fmt.setFontStrikeOut((not fmt.fontStrikeOut()) if checked is None else bool(checked))
            self.merge_editor_format(fmt)

        def reset_char_format(self) -> None:
            fmt = QtGui.QTextCharFormat()
            fmt.setFontWeight(QtGui.QFont.Weight.Normal)
            fmt.setFontItalic(False)
            fmt.setFontUnderline(False)
            fmt.setFontStrikeOut(False)
            self.merge_editor_format(fmt)

        def choose_text_color(self) -> None:
            color = QtWidgets.QColorDialog.getColor(parent=self)
            if color.isValid():
                fmt = QtGui.QTextCharFormat()
                fmt.setForeground(QtGui.QBrush(color))
                self.merge_editor_format(fmt)

        def choose_text_background(self) -> None:
            color = QtWidgets.QColorDialog.getColor(parent=self)
            if color.isValid():
                fmt = QtGui.QTextCharFormat()
                fmt.setBackground(QtGui.QBrush(color))
                self.merge_editor_format(fmt)

        def insert_bullet(self) -> None:
            cursor = self.editor.textCursor()
            cursor.insertText(qt_bullet_insert_text())
            self.editor.setTextCursor(cursor)
            self.save_current_editor_to_node()

        def change_font_size(self, delta: int) -> None:
            fmt = self.editor.currentCharFormat()
            size = fmt.fontPointSize() or self.editor.font().pointSizeF() or 10
            fmt.setFontPointSize(max(6, min(99, size + delta)))
            self.merge_editor_format(fmt)

        def show_settings_dialog(self) -> None:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Einstellungen")
            layout = QtWidgets.QFormLayout(dialog)

            backup_spin = QtWidgets.QSpinBox()
            backup_spin.setRange(0, 999)
            backup_spin.setValue(self.settings.backup_keep)

            autosave_spin = QtWidgets.QSpinBox()
            autosave_spin.setRange(0, 24 * 60 * 60)
            autosave_spin.setValue(self.settings.autosave_seconds)

            language_combo = QtWidgets.QComboBox()
            for display, key in available_languages():
                language_combo.addItem(display, key)
            for index in range(language_combo.count()):
                if language_combo.itemData(index) == self.settings.language:
                    language_combo.setCurrentIndex(index)
                    break

            scroll_combo = QtWidgets.QComboBox()
            for label, value in (
                ("Keine", 0),
                ("Horizontal", 1),
                ("Vertikal", 2),
                ("Horizontal + Vertikal", 3),
            ):
                scroll_combo.addItem(label, value)
            for index in range(scroll_combo.count()):
                if int(scroll_combo.itemData(index)) == int(self.settings.scrollbars_choice):
                    scroll_combo.setCurrentIndex(index)
                    break

            border_check = QtWidgets.QCheckBox()
            border_check.setChecked(self.settings.show_desknote_borders)
            taskbar_check = QtWidgets.QCheckBox()
            taskbar_check.setChecked(self.settings.show_in_taskbar_when_minimized)
            gnome_safe_tray_check = QtWidgets.QCheckBox()
            gnome_safe_tray_check.setChecked(self.settings.gnome_safe_tray_start)
            gnome_safe_tray_check.setToolTip("Unter GNOME nicht unsichtbar ins Tray starten, wenn keine AppIndicator/KStatusNotifier-Erweiterung erkannt wird.")
            autorun_check = QtWidgets.QCheckBox()
            autorun_check.setChecked(self.settings.autorun_enabled)
            autorun_minimized_check = QtWidgets.QCheckBox()
            autorun_minimized_check.setChecked(self.settings.autorun_minimized)

            backup_folder = backup_directory_for(self.document.path) if self.document.path else "nach dem ersten Speichern"
            backup_folder_label = QtWidgets.QLabel(str(backup_folder))
            backup_folder_label.setTextInteractionFlags(_enum(QtCore.Qt, "TextInteractionFlag", "TextSelectableByMouse"))

            layout.addRow("Sicherungen behalten", backup_spin)
            layout.addRow("Sicherungsordner", backup_folder_label)
            layout.addRow("Autosave alle Sekunden (0 = aus)", autosave_spin)
            layout.addRow("Sprache", language_combo)
            layout.addRow("Scrollleisten im Editor", scroll_combo)
            layout.addRow("Desktop-Notiz-Ränder zeigen", border_check)
            layout.addRow("Minimiert in Taskleiste zeigen", taskbar_check)
            layout.addRow("GNOME ohne Tray nicht verstecken", gnome_safe_tray_check)
            layout.addRow("Autostart vormerken", autorun_check)
            layout.addRow("Autostart minimiert", autorun_minimized_check)

            buttons = QtWidgets.QDialogButtonBox(
                _enum(QtWidgets.QDialogButtonBox, "StandardButton", "Ok")
                | _enum(QtWidgets.QDialogButtonBox, "StandardButton", "Cancel")
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)
            if dialog.exec() == ACCEPTED:
                self.settings.backup_keep = backup_spin.value()
                self.settings.autosave_seconds = normalize_autosave_seconds(autosave_spin.value())
                self.settings.language = language_combo.currentData()
                self.settings.scrollbars_choice = int(scroll_combo.currentData())
                self.settings.show_desknote_borders = border_check.isChecked()
                self.settings.show_in_taskbar_when_minimized = taskbar_check.isChecked()
                self.settings.gnome_safe_tray_start = gnome_safe_tray_check.isChecked()
                self.settings.autorun_enabled = autorun_check.isChecked()
                self.settings.autorun_minimized = autorun_minimized_check.isChecked()
                self.settings.save()
                self._configure_autosave()
                self._apply_scrollbar_settings()
                self.apply_language()
                autostart = apply_windows_autostart_script(
                    enabled=self.settings.autorun_enabled,
                    minimized=self.settings.autorun_minimized,
                    recent_files=self.settings.recent_files,
                )
                if autostart.message:
                    self.statusBar().showMessage(autostart.message)

        def show_about(self) -> None:
            """Show the old Info/Hilfe/Feedback dialog without unsafe FTP upload."""

            try:
                from . import __version__
            except Exception:
                __version__ = "0.10.18"

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Info Notizen PyQt")
            dialog.resize(640, 660)
            layout = QtWidgets.QVBoxLayout(dialog)

            product = QtWidgets.QLabel(f"Notizen .NET / PyQt {__version__}")
            author = QtWidgets.QLabel("Alexander Kern / Notizen.NET migration")
            web = QtWidgets.QLabel(f'<a href="{LEGACY_FEEDBACK_WEB_URL}">{LEGACY_FEEDBACK_WEB_URL}</a>')
            web.setOpenExternalLinks(True)
            mail = QtWidgets.QLabel(f"Email: {LEGACY_FEEDBACK_EMAIL}")
            layout.addWidget(product)
            layout.addWidget(author)
            layout.addWidget(web)
            layout.addWidget(mail)

            description = QtWidgets.QTextEdit()
            description.setReadOnly(True)
            description.setPlainText(
                f"{self.tr('aboutinfotext', '')}\n\n"
                "Portiert: ALX-Dateiformat, Notizbaum, lokale/FTP-Speicherung, Suche, "
                "Knotenoperationen, Desktop-Notizen, RichText-Brücke, Teilbaum-Export, "
                "Sprachdateien, legacy Startparameter, alte Tastaturbedienung, "
                "systemweites Knoten-Clipboard, wiederholende Wecker, Qt-Druckpfade, "
                "TXT/RTF-Import, HTML-Export, Statistik, Knoten-Verschieben, "
                "Auf-/Zu-Funktionen, sichere Recent-Dateien, Baum-Zusammenfassung, "
                "Sicherungsverwaltung, Windows-/Linux-Dateizuordnung und sichere lokale "
                "Feedback-Ablage.\n\n"
                f"Qt-Binding: {BINDING}"
            )
            layout.addWidget(description, 1)

            layout.addWidget(QtWidgets.QLabel(self.tr("feedback", "Feedback")))
            feedback_edit = QtWidgets.QTextEdit()
            feedback_edit.setPlaceholderText("Feedback wird lokal als gzip-Datei gespeichert; der alte FTP-Upload wird nicht reaktiviert.")
            feedback_edit.setMinimumHeight(120)
            layout.addWidget(feedback_edit)

            buttons = QtWidgets.QDialogButtonBox()
            save_button = buttons.addButton(self.tr("send", "Senden"), QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
            close_button = buttons.addButton(self.tr("close", "Schließen"), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
            layout.addWidget(buttons)
            close_button.clicked.connect(dialog.reject)

            def save_local_feedback() -> None:
                text = feedback_edit.toPlainText()
                decision = legacy_feedback_decision(
                    text=text,
                    previous_day_ticks=self.settings.feedback_day_ticks,
                    previous_count=self.settings.feedback_count,
                )
                if not decision.allowed:
                    if decision.reason == "char10minimum":
                        message = self.tr("char10minimum", "Mindestens 10 Zeichen eingeben.")
                    else:
                        message = self.tr("no_send", "Heute kann kein weiteres Feedback gespeichert werden.")
                    QtWidgets.QMessageBox.warning(dialog, "Notizen PyQt", message)
                    return
                feedback_dir = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))) / "notizen-py-qt" / "feedback"
                target = write_local_feedback_archive(text, feedback_dir)
                next_state = legacy_feedback_next_state(
                    previous_day_ticks=self.settings.feedback_day_ticks,
                    previous_count=self.settings.feedback_count,
                )
                self.settings.feedback_day_ticks = next_state.day_ticks
                self.settings.feedback_count = next_state.count
                self.settings.save()
                QtWidgets.QMessageBox.information(
                    dialog,
                    "Notizen PyQt",
                    f"Feedback wurde lokal gespeichert:\n{target}\n\nDer alte hartkodierte FTP-Upload aus Notizen.NET bleibt aus Sicherheitsgründen deaktiviert.",
                )
                feedback_edit.clear()

            save_button.clicked.connect(save_local_feedback)
            dialog.exec()

        def _legacy_shortcut_key_name(self, key: Any) -> str:
            key_values = {
                "Space": _enum(QtCore.Qt, "Key", "Key_Space"),
                "S": _enum(QtCore.Qt, "Key", "Key_S"),
                "O": _enum(QtCore.Qt, "Key", "Key_O"),
                "N": _enum(QtCore.Qt, "Key", "Key_N"),
                "Q": _enum(QtCore.Qt, "Key", "Key_Q"),
                "C": _enum(QtCore.Qt, "Key", "Key_C"),
                "V": _enum(QtCore.Qt, "Key", "Key_V"),
                "X": _enum(QtCore.Qt, "Key", "Key_X"),
                "U": _enum(QtCore.Qt, "Key", "Key_U"),
                "F": _enum(QtCore.Qt, "Key", "Key_F"),
                "Insert": _enum(QtCore.Qt, "Key", "Key_Insert"),
                "Delete": _enum(QtCore.Qt, "Key", "Key_Delete"),
                "Return": _enum(QtCore.Qt, "Key", "Key_Return"),
                "Enter": _enum(QtCore.Qt, "Key", "Key_Enter"),
                "Plus": _enum(QtCore.Qt, "Key", "Key_Plus"),
                "=": _enum(QtCore.Qt, "Key", "Key_Equal"),
                "Minus": _enum(QtCore.Qt, "Key", "Key_Minus"),
            }
            for name, qt_key in key_values.items():
                if key == qt_key:
                    return name
            return ""

        def _perform_legacy_shortcut_action(self, action: str) -> None:
            if action == "alarm":
                self.show_alarm_dialog()
            elif action == "save":
                self.save_file()
            elif action == "open":
                self.open_dialog()
            elif action == "new_document":
                self.new_document()
            elif action == "quit":
                self.close()
            elif action == "copy":
                self.copy_anything()
            elif action == "paste":
                self.paste_anything()
            elif action == "cut":
                self.cut_anything()
            elif action == "rename":
                self.rename_node()
            elif action == "search":
                self.show_search()
            elif action == "font_bigger":
                self.change_font_size(+1)
            elif action == "font_smaller":
                self.change_font_size(-1)
            elif action == "paste_node":
                self.paste_node()
            elif action == "cut_node":
                self.cut_node()
            elif action == "add_child":
                self.add_child_node()
            elif action == "delete_node":
                self.delete_node()
            elif action == "add_sibling":
                self.add_sibling_node()

        def keyPressEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            # Keep legacy shortcuts from Notizen.vb/tastendruck focus-aware.
            key_name = self._legacy_shortcut_key_name(event.key())
            modifiers = event.modifiers()
            shortcut = legacy_shortcut_action(
                key_name,
                control=bool(modifiers & CTRL),
                shift=bool(modifiers & SHIFT),
                alt=bool(modifiers & ALT),
                tree_focus=self.tree.hasFocus(),
                editor_focus=self._editor_active(),
            )
            if shortcut is not None:
                self._perform_legacy_shortcut_action(shortcut.action)
                event.accept()
                return
            super().keyPressEvent(event)

        def changeEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            super().changeEvent(event)
            if event.type() == _enum(QtCore.QEvent, "Type", "WindowStateChange"):
                if self.isMinimized():
                    decision = self.tray_hide_decision()
                    if decision.hide_to_tray:
                        QtCore.QTimer.singleShot(0, self.hide)
                    elif decision.gnome_session:
                        self.statusBar().showMessage(decision.reason)

        def closeEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            if not self.maybe_save_changes():
                event.ignore()
                return
            self._store_window_settings()
            self.close_all_desktop_notes()
            if getattr(self, "tray_icon", None):
                self.tray_icon.hide()
            event.accept()


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    legacy = parse_legacy_startup_args(raw_argv)
    startup_validation = validate_legacy_startup_target(legacy)
    legacy = startup_validation.options
    if startup_validation.missing_file:
        print(f"alx file does not exist: {startup_validation.missing_file}", file=sys.stderr)

    parser = argparse.ArgumentParser(description="Notizen.NET Python/Qt port")
    parser.add_argument("file", nargs="?", help="ALX/Notizen-Datei oder ftp://-URL zum Öffnen")
    parser.add_argument("--password", help="Passwort für geschützte ALX-Dateien")
    parser.add_argument("--minimized", action="store_true", help="Minimiert starten")
    parser.add_argument(
        "--show",
        "--visible",
        dest="show",
        action="store_true",
        help="Sichtbar starten und gespeicherten/minimierten Startzustand ignorieren",
    )
    parser.add_argument("--no-tray", action="store_true", help="Trayicon deaktivieren und nie unsichtbar starten")
    parser.add_argument("--reset-window", action="store_true", help="Fensterposition/-größe verwerfen und sichtbar im aktuellen Arbeitsbereich starten")
    parser.add_argument("--force-tray-start", action="store_true", help="Auch unter GNOME verborgen ins Tray starten")
    parser.add_argument("--smoke-test", action="store_true", help="Nur initialisieren und sofort beenden")
    if legacy.help_requested:
        parser.print_help()
        return 0
    args = parser.parse_args(list(legacy.cleaned_args))

    if QT_IMPORT_ERROR is not None:
        print(str(QT_IMPORT_ERROR), file=sys.stderr)
        return 2

    os.environ.setdefault("RESOURCE_NAME", APP_DESKTOP_ID)
    configure_qt_application_identity(None)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([APP_DESKTOP_ID])
    configure_qt_application_identity(app)
    try:
        try:
            from . import __version__ as _runtime_version
        except Exception:
            _runtime_version = "?"
        append_startup_log(
            "APP_RUNTIME version=%s module=%s binding=%s qpa=%s display=%s wayland=%s env=%s"
            % (
                _runtime_version,
                Path(__file__).resolve(),
                BINDING,
                app.platformName() if hasattr(app, "platformName") else "",
                os.environ.get("DISPLAY", ""),
                os.environ.get("WAYLAND_DISPLAY", ""),
                _DISPLAY_ENV_DECISION.summary(),
            )
        )
    except Exception:
        pass
    icon = app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    startup_file = args.file or legacy.file
    window = MainWindow(
        startup_file,
        password=args.password,
        disable_tray=args.no_tray,
        force_tray_start=args.force_tray_start,
        reset_window_geometry=bool(args.reset_window or env_requests_window_reset()),
    )
    reset_window = bool(args.reset_window or env_requests_window_reset())
    start_minimized = should_start_minimized(
        explicit_minimized=args.minimized,
        legacy_minimized=legacy.minimized,
        stored_window_state=normalize_window_state(window.settings.window_state),
        force_visible=args.show,
        reset_window=reset_window,
        stored_state_restorable=legacy_window_state_is_restorable(window.settings.window_x, window.settings.window_y),
    )
    if args.smoke_test:
        return 0
    if start_minimized:
        decision = window.tray_hide_decision()
        if decision.hide_to_tray:
            window.hide()
        else:
            # GNOME often has no visible legacy tray.  Show the main window
            # instead of creating an inaccessible hidden process.
            window.ensure_main_window_visible(reset_window=reset_window)
            if decision.reason:
                window.statusBar().showMessage(decision.reason)
    else:
        window.ensure_main_window_visible(reset_window=reset_window or args.show)
    try:
        append_startup_log(
            "WINDOW_REQUEST visible=%s minimized=%s reset=%s geometry=%s"
            % (window.isVisible(), window.isMinimized(), bool(reset_window or args.show), window.geometry().getRect())
        )
    except Exception:
        pass
    # A second pass after the event loop starts prevents GNOME/Wayland from
    # keeping a restored/minimized legacy state invisible.
    QtCore.QTimer.singleShot(150, lambda: window.ensure_main_window_visible(reset_window=False))
    QtCore.QTimer.singleShot(750, lambda: window.ensure_main_window_visible(reset_window=False))
    QtCore.QTimer.singleShot(1200, lambda: append_startup_log("WINDOW_AFTER_EVENTLOOP visible=%s minimized=%s active=%s geometry=%s" % (window.isVisible(), window.isMinimized(), window.isActiveWindow(), window.geometry().getRect())))
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
