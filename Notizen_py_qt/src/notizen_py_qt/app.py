from __future__ import annotations

import argparse
import base64
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .alarms import AlarmSpec, describe_recurrence, next_occurrence
from .alx_io import AlxError, InvalidPassword, PasswordRequired, backup_directory_for, create_backup, dump_alx_bytes, list_backups, load_alx, load_alx_bytes, save_alx, normalize_password
from .exporters import create_unified_note, tree_to_plain_text, tree_to_rtf, tree_to_text_bytes
from .html_export import HtmlExportOptions, tree_to_html_bytes
from .ftp_sync import FtpSyncError, FtpTarget
from .i18n import available_languages, tr
from .legacy_colors import legacy_light_color_argb
from .legacy_paths import LEGACY_DEFAULT_FILENAME, ensure_legacy_documents_notizen_dir
from .models import DesktopNoteState, NoteDocument, NoteNode, legacy_delete_fallback_node, legacy_new_next_node, legacy_paste_clone
from .desktop_note_legacy import legacy_transparency_menu_options
from .node_clipboard import NODE_MIME_TYPE, looks_like_node_clipboard_xml, node_from_clipboard_xml, node_to_clipboard_xml
from .startup import apply_windows_autostart_script, parse_legacy_startup_args
from .tray_support import decide_startup_tray_visibility, gnome_tray_install_hint
from .rtf_utils import html_to_rtf, plain_text_to_rtf, rtf_to_html, rtf_to_plain_text
from .search_logic import SearchResult, search_nodes
from .search_results import SearchHitView, build_search_hit_views
from .settings import AppSettings, legacy_autosave_should_save, normalize_autosave_seconds, normalize_window_state
from .stats import collect_tree_stats

try:  # Importing is optional so tests and CLI helpers work without Qt installed.
    from .qt_compat import load_qt

    BINDING, QtCore, QtGui, QtWidgets = load_qt()
    QT_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - exercised on systems without Qt
    BINDING = ""
    QtCore = QtGui = QtWidgets = None  # type: ignore[assignment]
    QT_IMPORT_ERROR = exc


def _load_qt_print_support() -> Any:
    """Load QtPrintSupport from the active binding only when printing is used."""
    if BINDING == "PySide6":
        from PySide6 import QtPrintSupport  # type: ignore

        return QtPrintSupport
    if BINDING == "PyQt6":
        from PyQt6 import QtPrintSupport  # type: ignore

        return QtPrintSupport
    raise RuntimeError("QtPrintSupport is unavailable because no Qt binding is loaded.")


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
    WINDOW = _enum(QtCore.Qt, "WindowType", "Window")
    TOOL = _enum(QtCore.Qt, "WindowType", "Tool")
    FRAMELESS = _enum(QtCore.Qt, "WindowType", "FramelessWindowHint")
    CTRL = _enum(QtCore.Qt, "KeyboardModifier", "ControlModifier")
    SHIFT = _enum(QtCore.Qt, "KeyboardModifier", "ShiftModifier")
    CUSTOM_CONTEXT_MENU = _enum(QtCore.Qt, "ContextMenuPolicy", "CustomContextMenu")

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

    class DesktopNoteWindow(QtWidgets.QWidget):
        def __init__(self, main_window: "MainWindow", node: NoteNode) -> None:
            flags = TOOL | WINDOW
            if not main_window.settings.show_desknote_borders:
                flags |= FRAMELESS
            super().__init__(main_window, flags)
            self.main_window = main_window
            self.node = node
            if self.node.desktop_note is None:
                self.node.desktop_note = main_window.default_desktop_note_state()
            self.setWindowTitle(node.title)
            self.setAttribute(_enum(QtCore.Qt, "WidgetAttribute", "WA_DeleteOnClose"), False)
            self._loading = False

            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(6, 6, 6, 6)
            self.title_label = QtWidgets.QLabel(node.title)
            self.title_label.setTextInteractionFlags(_enum(QtCore.Qt, "TextInteractionFlag", "TextSelectableByMouse"))
            self.editor = QtWidgets.QTextEdit()
            self.editor.setAcceptRichText(True)
            self.editor.setHtml(rtf_to_html(node.rtf))
            self.editor.setContextMenuPolicy(CUSTOM_CONTEXT_MENU)
            self.editor.customContextMenuRequested.connect(
                lambda pos: self._show_context_menu(self.editor.mapToGlobal(pos))
            )
            self.setContextMenuPolicy(CUSTOM_CONTEXT_MENU)
            self.customContextMenuRequested.connect(lambda pos: self._show_context_menu(self.mapToGlobal(pos)))
            close_button = QtWidgets.QPushButton("Schließen")
            close_button.clicked.connect(self.close)
            layout.addWidget(self.title_label)
            layout.addWidget(self.editor, 1)
            layout.addWidget(close_button)
            self.editor.textChanged.connect(self._editor_changed)
            self._restore_geometry()

        def _apply_background(self) -> None:
            state = self.node.desktop_note or DesktopNoteState()
            if state.argb:
                self.editor.setStyleSheet(f"background-color: {color_from_argb(state.argb).name()};")
            else:
                self.editor.setStyleSheet("")

        def _restore_geometry(self) -> None:
            state = self.node.desktop_note or DesktopNoteState()
            self.setGeometry(state.x, state.y, max(120, state.width), max(100, state.height))
            try:
                self.setWindowOpacity(float(state.opacity))
            except Exception:
                pass
            self._apply_background()

        def _store_geometry(self) -> None:
            geo = self.geometry()
            if self.node.desktop_note is None:
                self.node.desktop_note = DesktopNoteState()
            self.node.desktop_note.x = geo.x()
            self.node.desktop_note.y = geo.y()
            self.node.desktop_note.width = geo.width()
            self.node.desktop_note.height = geo.height()
            self.node.desktop_note.visible = self.isVisible()
            try:
                self.node.desktop_note.opacity = float(self.windowOpacity())
            except Exception:
                pass

        def reload_from_node(self) -> None:
            self._loading = True
            self.setWindowTitle(self.node.title)
            self.title_label.setText(self.node.title)
            self.editor.setHtml(rtf_to_html(self.node.rtf))
            self._apply_background()
            self._loading = False

        def _show_context_menu(self, global_pos: Any) -> None:
            menu = QtWidgets.QMenu(self)
            menu.addAction("Ausschneiden", self.editor.cut)
            menu.addAction("Kopieren", self.editor.copy)
            menu.addAction("Einfügen", self.editor.paste)
            menu.addSeparator()
            menu.addAction("Hintergrundfarbe", self._choose_background_color)
            opacity_menu = menu.addMenu("Transparenz")
            for label, opacity_percent in legacy_transparency_menu_options():
                action = opacity_menu.addAction(label)
                action.triggered.connect(lambda checked=False, v=opacity_percent: self._set_opacity_percent(v))
            menu.addSeparator()
            menu.addAction("Im Hauptfenster öffnen", self._activate_main_window_node)
            menu.addAction("Ausblenden", self.close)
            menu.addAction("Desktop-Notiz schließen", self._remove_desktop_note)
            menu.exec(global_pos)

        def _choose_background_color(self) -> None:
            color = QtWidgets.QColorDialog.getColor(parent=self)
            if not color.isValid():
                return
            if self.node.desktop_note is None:
                self.node.desktop_note = DesktopNoteState()
            self.node.desktop_note.argb = argb_from_color(color)
            self._apply_background()
            self.main_window.document.mark_changed()
            self.main_window.update_title()

        def _set_opacity_percent(self, value: int) -> None:
            if self.node.desktop_note is None:
                self.node.desktop_note = DesktopNoteState()
            opacity = max(0.1, min(1.0, value / 100.0))
            self.node.desktop_note.opacity = opacity
            try:
                self.setWindowOpacity(opacity)
            except Exception:
                pass
            self.main_window.document.mark_changed()
            self.main_window.update_title()

        def _activate_main_window_node(self) -> None:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            self.main_window.select_node(self.node)

        def _remove_desktop_note(self) -> None:
            self.main_window.close_desktop_note(self.node)
            self.main_window.document.mark_changed()
            self.main_window.update_title()

        def mouseDoubleClickEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._activate_main_window_node()
            super().mouseDoubleClickEvent(event)

        def _editor_changed(self) -> None:
            if self._loading:
                return
            self.node.rtf = html_to_rtf(self.editor.toHtml())
            self.main_window.document.mark_changed()
            self.main_window.update_title()
            self.main_window._reload_desktop_note_windows(self.node, source_window=self)
            if self.main_window.current_node_ref is self.node:
                self.main_window.load_editor_from_node(self.node, preserve_focus=True)

        def moveEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._store_geometry()
            super().moveEvent(event)

        def resizeEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._store_geometry()
            super().resizeEvent(event)

        def closeEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            self._store_geometry()
            if self.node.desktop_note is not None:
                self.node.desktop_note.visible = False
            self.main_window.document.mark_changed()
            self.main_window.update_tray_menu()
            self.hide()
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
            for index, label in enumerate(("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")):
                box = QtWidgets.QCheckBox(label)
                box.setChecked(index == current_day)
                self.weekday_checks.append(box)
                weekday_layout.addWidget(box)
            weekday_layout.addStretch(1)

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
            self._update_repeat_controls()

        def _update_repeat_controls(self) -> None:
            kind = self.repeat.currentData()
            self.interval.setEnabled(kind != "none")
            self.weekday_container.setVisible(kind == "weekly")

        def accept(self) -> None:  # noqa: N802 - Qt override
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
        ) -> None:
            super().__init__()
            self.disable_tray = bool(disable_tray)
            self.force_tray_start = bool(force_tray_start)
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

            self.tree = QtWidgets.QTreeWidget()
            self.tree.setObjectName("Baum")
            self.tree.setHeaderLabel("Notizen")
            self.tree.setSelectionBehavior(SELECT_ROWS)
            self.tree.setSelectionMode(EXTENDED_SELECTION)
            self.tree.setDragDropMode(INTERNAL_MOVE)
            self.tree.setDefaultDropAction(MOVE_ACTION)
            self.tree.setAlternatingRowColors(True)
            self.tree.setMinimumSize(240, 260)
            self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
            self.tree.itemChanged.connect(self.on_item_changed)
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
            tree_label = QtWidgets.QLabel("Baum")
            tree_label.setObjectName("treeCaption")
            left_layout.addWidget(tree_label)
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
            title_row.setSpacing(6)
            title_label = QtWidgets.QLabel("Titel:")
            title_label.setObjectName("titleCaption")
            title_label.setBuddy(self.node_title_edit)
            self.editor_mode_label = QtWidgets.QLabel("Modus: RTF/Text")
            self.editor_mode_label.setObjectName("modeCaption")
            title_row.addWidget(title_label)
            title_row.addWidget(self.node_title_edit, 1)
            title_row.addWidget(self.title_apply_button)
            title_row.addSpacing(8)
            title_row.addWidget(self.editor_mode_label)
            title_row.addStretch(0)

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

            self.cut_action = self._act("Ausschneiden", self.cut_anything, "Ctrl+X")
            self.copy_action = self._act("Kopieren", self.copy_anything, "Ctrl+C")
            self.paste_action = self._act("Einfügen", self.paste_anything, "Ctrl+V")
            self.paste_child_action = self._act("Einfügen als Unterknoten", self.paste_node_as_child)
            self.delete_text_action = self._act("Text löschen", self.delete_selection_text)
            self.insert_image_action = self._act("Bild einfügen", self.insert_image)
            self.insert_date_action = self._act("Datum einfügen", self.insert_current_date_time)
            self.search_action = self._act("Suchen", self.show_search, "Ctrl+F")
            self.alarm_action = self._act("Wecker", self.show_alarm_dialog, "Ctrl+Space")

            self.bold_action = self._act("Fett", self.toggle_bold, "Ctrl+B")
            self.italic_action = self._act("Kursiv", self.toggle_italic, "Ctrl+I")
            self.underline_action = self._act("Unterstrichen", self.toggle_underline)
            self.strike_action = self._act("Durchgestrichen", self.toggle_strike)
            self.regular_action = self._act("Normal", self.reset_char_format)
            self.bigger_action = self._act("Schrift größer", lambda: self.change_font_size(+1), "Ctrl++")
            self.smaller_action = self._act("Schrift kleiner", lambda: self.change_font_size(-1), "Ctrl+-")
            self.text_color_action = self._act("Textfarbe", self.choose_text_color)
            self.highlight_color_action = self._act("Texthintergrund", self.choose_text_background)
            self.bullet_action = self._act("Aufzählungspunkt", self.insert_bullet)

            self.cycle_scrollbars_action = self._act("Scrollleisten wechseln", self.cycle_scrollbars)
            self.import_config_action = self._act("Alt-Config importieren", self.import_legacy_config_dialog)
            self.stats_action = self._act("Statistik", self.show_stats_dialog)
            self.about_action = self._act("Info", self.show_about)
            self.settings_action = self._act("Einstellungen", self.show_settings_dialog)

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
                self.text_color_action,
                self.highlight_color_action,
                self.bullet_action,
            ):
                self.editor.addAction(action)

        def _create_toolbars(self) -> None:
            file_bar = self.addToolBar("Datei")
            for action in (
                self.new_action,
                self.open_action,
                self.ftp_action,
                self.save_action,
                self.save_as_action,
                self.backup_now_action,
                self.open_backup_action,
                self.close_doc_action,
                self.print_note_action,
                self.export_txt_action,
                self.export_rtf_action,
                self.export_html_action,
            ):
                file_bar.addAction(action)
            node_bar = self.addToolBar("Neu/Entf.")
            for action in (
                self.add_child_action,
                self.add_sibling_action,
                self.rename_action,
                self.delete_action,
                self.copy_action,
                self.cut_action,
                self.paste_action,
                self.move_up_action,
                self.move_down_action,
                self.expand_current_action,
                self.expand_all_action,
                self.collapse_all_action,
                self.unify_action,
                self.unify_root_action,
                self.desk_note_action,
            ):
                node_bar.addAction(action)
            edit_bar = self.addToolBar("Import/Suche")
            for action in (
                self.import_txt_action,
                self.import_rtf_action,
                self.insert_image_action,
                self.insert_date_action,
                self.search_action,
                self.alarm_action,
                self.stats_action,
                self.import_config_action,
            ):
                edit_bar.addAction(action)
            font_bar = self.addToolBar("Schrift")
            self.font_family_combo = QtWidgets.QFontComboBox()
            self.font_family_combo.setToolTip("Schriftart")
            self.font_family_combo.currentFontChanged.connect(self.apply_font_family)
            font_bar.addWidget(self.font_family_combo)
            self.font_size_spin = QtWidgets.QSpinBox()
            self.font_size_spin.setRange(6, 99)
            self.font_size_spin.setValue(10)
            self.font_size_spin.setToolTip("Schriftgröße")
            self.font_size_spin.valueChanged.connect(self.apply_font_size)
            font_bar.addWidget(self.font_size_spin)
            for action in (
                self.bold_action,
                self.italic_action,
                self.underline_action,
                self.strike_action,
                self.regular_action,
                self.bigger_action,
                self.smaller_action,
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
            self.tree.setHeaderLabel(self.tr("Info1", "Notizen"))
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
            self.about_action.setText("Info")
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
            self.resize(max(640, self.settings.window_width), max(420, self.settings.window_height))
            x = int(self.settings.window_x)
            y = int(self.settings.window_y)
            try:
                screen = QtGui.QGuiApplication.primaryScreen()
                available = screen.availableGeometry() if screen is not None else None
                if available is not None and (x > available.right() - 50 or y > available.bottom() - 50):
                    x = max(available.left(), 60)
                    y = max(available.top(), 60)
            except Exception:
                pass
            self.move(x, y)
            if normalize_window_state(self.settings.window_state) == "Maximized":
                self.showMaximized()

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
            """Open a legacy recent-file entry after the same save prompt as the old menu."""
            path = Path(path_text)
            if not path.exists():
                QtWidgets.QMessageBox.warning(self, "Zuletzt geöffnet", f"Datei nicht gefunden:\n{path}")
                return False
            if not self.maybe_save_changes():
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
            item.setExpanded(node.expanded)
            return item

        def build_tree(self) -> None:
            self._loading_tree = True
            self.node_items.clear()
            self.tree.clear()
            if self.document.root is not None:
                root_item = self._make_item(self.document.root)
                self.tree.addTopLevelItem(root_item)
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

        def rename_node(self) -> None:
            item = self.tree.currentItem()
            if item is not None:
                self.tree.editItem(item, 0)

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
            win.show()
            win.raise_()
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
                printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.PrinterMode.HighResolution)
                printer.setDocName(title or "Notizen")
                dialog = QtPrintSupport.QPrintDialog(printer, self)
                if dialog.exec() != ACCEPTED:
                    return
                document = QtGui.QTextDocument()
                document.setDefaultFont(self.editor.font())
                document.setHtml(html)
                document.print(printer)
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
            finally:
                self._updating_format_controls = False

        def toggle_bold(self) -> None:
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
            fmt.setFontWeight(normal_weight if _weight_value(current) >= _weight_value(bold_weight) else bold_weight)
            self.merge_editor_format(fmt)

        def toggle_italic(self) -> None:
            fmt = self.editor.currentCharFormat()
            fmt.setFontItalic(not fmt.fontItalic())
            self.merge_editor_format(fmt)

        def toggle_underline(self) -> None:
            fmt = self.editor.currentCharFormat()
            fmt.setFontUnderline(not fmt.fontUnderline())
            self.merge_editor_format(fmt)

        def toggle_strike(self) -> None:
            fmt = self.editor.currentCharFormat()
            fmt.setFontStrikeOut(not fmt.fontStrikeOut())
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
            prefix = "" if cursor.position() == 0 else "\n"
            cursor.insertText(prefix + "•   ")
            self.editor.setTextCursor(cursor)

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
            try:
                from . import __version__
            except Exception:
                __version__ = "0.10.7"
            QtWidgets.QMessageBox.information(
                self,
                "Notizen Python/Qt",
                (
                    f"Notizen.NET Weitertranspilierung nach Python/Qt {__version__}\n\n"
                    "Portiert: ALX-Dateiformat, Notizbaum, lokale/FTP-Speicherung, Suche, "
                    "Knotenoperationen, Desktop-Notizen, RichText-Brücke, Teilbaum-Export, "
                    "Sprachdateien, legacy Startparameter, alte Tastaturbedienung, "
                    "systemweites Knoten-Clipboard, wiederholende Wecker, "
                    "Qt-Druckpfade, TXT/RTF-Import, HTML-Export, Statistik, "
                    "Knoten-Verschieben, Auf-/Zu-Funktionen, sichere Recent-Dateien, "
                    "aktuelle/ganze Baum-Zusammenfassung, Sicherungsverwaltung "
                    "und Desktop-Notiz-Startwerte nach Notizen.NET.\n\n"
                    f"Qt-Binding: {BINDING}"
                ),
            )

        def keyPressEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            # Keep legacy shortcuts from Notizen.vb/tastendruck focus-aware.
            key = event.key()
            modifiers = event.modifiers()
            if modifiers & CTRL:
                if key == _enum(QtCore.Qt, "Key", "Key_Space"):
                    self.show_alarm_dialog()
                    return
            if self.tree.hasFocus() and modifiers & SHIFT and not (modifiers & CTRL):
                if key == _enum(QtCore.Qt, "Key", "Key_Insert"):
                    self.paste_node()
                    return
                if key == _enum(QtCore.Qt, "Key", "Key_Delete"):
                    self.cut_node()
                    return
            if self.tree.hasFocus() and not (modifiers & (CTRL | SHIFT)):
                if key == _enum(QtCore.Qt, "Key", "Key_Insert"):
                    self.add_child_node()
                    return
                if key == _enum(QtCore.Qt, "Key", "Key_Delete"):
                    self.delete_node()
                    return
                if key in {_enum(QtCore.Qt, "Key", "Key_Return"), _enum(QtCore.Qt, "Key", "Key_Enter")}:
                    self.add_sibling_node()
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
    parser.add_argument("--force-tray-start", action="store_true", help="Auch unter GNOME verborgen ins Tray starten")
    parser.add_argument("--smoke-test", action="store_true", help="Nur initialisieren und sofort beenden")
    if legacy.help_requested:
        parser.print_help()
        return 0
    args = parser.parse_args(list(legacy.cleaned_args))

    if QT_IMPORT_ERROR is not None:
        print(str(QT_IMPORT_ERROR), file=sys.stderr)
        return 2

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv[:1])
    icon = app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    startup_file = args.file or legacy.file
    window = MainWindow(
        startup_file,
        password=args.password,
        disable_tray=args.no_tray,
        force_tray_start=args.force_tray_start,
    )
    start_minimized = bool(
        not args.show
        and (args.minimized or legacy.minimized or normalize_window_state(window.settings.window_state) == "Minimized")
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
            window.show()
            if decision.reason:
                window.statusBar().showMessage(decision.reason)
    else:
        window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
