from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .alx_io import AlxError, InvalidPassword, PasswordRequired, dump_alx_bytes, load_alx, load_alx_bytes, save_alx
from .exporters import create_unified_note, tree_to_plain_text, tree_to_rtf
from .ftp_sync import FtpSyncError, FtpTarget
from .models import DesktopNoteState, NoteDocument, NoteNode
from .rtf_utils import html_to_rtf, rtf_to_html, rtf_to_plain_text
from .search_logic import SearchResult, search_nodes
from .settings import AppSettings

try:  # Importing is optional so tests and CLI helpers work without Qt installed.
    from .qt_compat import load_qt

    BINDING, QtCore, QtGui, QtWidgets = load_qt()
    QT_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - exercised on systems without Qt
    BINDING = ""
    QtCore = QtGui = QtWidgets = None  # type: ignore[assignment]
    QT_IMPORT_ERROR = exc


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
    CTRL = _enum(QtCore.Qt, "KeyboardModifier", "ControlModifier")

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
            super().__init__(main_window, TOOL | WINDOW)
            self.main_window = main_window
            self.node = node
            if self.node.desktop_note is None:
                self.node.desktop_note = DesktopNoteState()
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
            close_button = QtWidgets.QPushButton("Schließen")
            close_button.clicked.connect(self.close)
            layout.addWidget(self.title_label)
            layout.addWidget(self.editor, 1)
            layout.addWidget(close_button)
            self.editor.textChanged.connect(self._editor_changed)
            self._restore_geometry()

        def _restore_geometry(self) -> None:
            state = self.node.desktop_note or DesktopNoteState()
            self.setGeometry(state.x, state.y, max(120, state.width), max(100, state.height))
            try:
                self.setWindowOpacity(float(state.opacity))
            except Exception:
                pass
            if state.argb:
                self.editor.setStyleSheet(f"background-color: {color_from_argb(state.argb).name()};")

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
            self._loading = False

        def _editor_changed(self) -> None:
            if self._loading:
                return
            self.node.rtf = html_to_rtf(self.editor.toHtml())
            self.main_window.document.mark_changed()
            self.main_window.update_title()
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
            self.result_index = 0
            self.setWindowTitle("Suche")
            layout = QtWidgets.QGridLayout(self)
            self.term = QtWidgets.QLineEdit(main_window.last_search)
            self.all_nodes = QtWidgets.QCheckBox("Alle Knoten durchsuchen")
            self.whole_words = QtWidgets.QCheckBox("ganze Wörter")
            self.case_sensitive = QtWidgets.QCheckBox("Groß-/Klein-Schreibung beachten")
            self.count_label = QtWidgets.QLabel("")
            search_button = QtWidgets.QPushButton("Suchen / Weiter")
            close_button = QtWidgets.QPushButton("Fertig")
            search_button.clicked.connect(self.search_next)
            close_button.clicked.connect(self.accept)
            self.term.returnPressed.connect(self.search_next)
            layout.addWidget(QtWidgets.QLabel("Suchbegriff:"), 0, 0)
            layout.addWidget(self.term, 0, 1, 1, 2)
            layout.addWidget(self.all_nodes, 1, 0, 1, 3)
            layout.addWidget(self.whole_words, 2, 0, 1, 3)
            layout.addWidget(self.case_sensitive, 3, 0, 1, 3)
            layout.addWidget(QtWidgets.QLabel("Ergebnisse:"), 4, 0)
            layout.addWidget(self.count_label, 4, 1)
            layout.addWidget(search_button, 5, 1)
            layout.addWidget(close_button, 5, 2)

        def _collect_results(self) -> None:
            term = self.term.text()
            self.main_window.last_search = term
            if not term:
                self.results = []
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
            self.result_index = 0
            self.count_label.setText(str(len(self.results)))

        def search_next(self) -> None:
            previous_signature = (
                self.term.text(),
                self.all_nodes.isChecked(),
                self.whole_words.isChecked(),
                self.case_sensitive.isChecked(),
            )
            if getattr(self, "_signature", None) != previous_signature:
                self._signature = previous_signature
                self._collect_results()
            if not self.results:
                return
            result = self.results[self.result_index % len(self.results)]
            self.result_index += 1
            self.main_window.select_node(result.node)
            cursor = self.main_window.editor.textCursor()
            cursor.setPosition(result.start)
            cursor.setPosition(result.start + result.length, QtGui.QTextCursor.MoveMode.KeepAnchor)
            self.main_window.editor.setTextCursor(cursor)
            self.main_window.editor.setFocus()

    class AlarmDialog(QtWidgets.QDialog):
        def __init__(self, main_window: "MainWindow") -> None:
            super().__init__(main_window)
            self.main_window = main_window
            self.setWindowTitle("Wecker")
            layout = QtWidgets.QFormLayout(self)
            self.when = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime().addSecs(5 * 60))
            self.when.setCalendarPopup(True)
            self.message = QtWidgets.QLineEdit("Notizen-Wecker")
            layout.addRow("Zeitpunkt", self.when)
            layout.addRow("Meldung", self.message)
            buttons = QtWidgets.QDialogButtonBox(
                _enum(QtWidgets.QDialogButtonBox, "StandardButton", "Ok")
                | _enum(QtWidgets.QDialogButtonBox, "StandardButton", "Cancel")
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addRow(buttons)

        def accept(self) -> None:  # noqa: N802 - Qt override
            self.main_window.schedule_alarm(self.when.dateTime(), self.message.text())
            super().accept()


    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self, initial_path: str | None = None, password: str | None = None) -> None:
            super().__init__()
            self.settings = AppSettings.load()
            self.document = NoteDocument.new()
            self.document.password = password or ""
            self.current_node_ref: NoteNode | None = None
            self._loading_editor = False
            self._loading_tree = False
            self.node_items: dict[int, Any] = {}
            self.clipboard_node: NoteNode | None = None
            self.cut_source_node: NoteNode | None = None
            self.desktop_windows: dict[int, DesktopNoteWindow] = {}
            self.last_search = ""
            self.alarms: list[Any] = []
            self.autosave_timer = QtCore.QTimer(self)
            self.autosave_timer.timeout.connect(self.autosave)
            self._build_ui()
            self._restore_window_settings()
            self.build_tree()
            if initial_path:
                self.load_path(Path(initial_path), password=password or None)
            elif self.settings.last_directory and self.settings.last_file:
                candidate = Path(self.settings.last_directory) / self.settings.last_file
                if candidate.exists():
                    self.statusBar().showMessage(f"Letzte Datei: {candidate}")
            self.update_title()
            self.update_actions()
            self._configure_autosave()

        def _build_ui(self) -> None:
            icon = app_icon()
            if not icon.isNull():
                self.setWindowIcon(icon)

            self.tree = QtWidgets.QTreeWidget()
            self.tree.setHeaderLabel("Notizen")
            self.tree.setSelectionBehavior(SELECT_ROWS)
            self.tree.setSelectionMode(EXTENDED_SELECTION)
            self.tree.setDragDropMode(INTERNAL_MOVE)
            self.tree.setDefaultDropAction(MOVE_ACTION)
            self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
            self.tree.itemChanged.connect(self.on_item_changed)
            try:
                self.tree.model().rowsMoved.connect(lambda *_: self.on_tree_rows_moved())
            except Exception:
                pass

            self.editor = QtWidgets.QTextEdit()
            self.editor.setAcceptRichText(True)
            self._apply_scrollbar_settings()
            self.editor.textChanged.connect(self.on_editor_changed)
            self.editor.setContextMenuPolicy(_enum(QtCore.Qt, "ContextMenuPolicy", "ActionsContextMenu"))

            splitter = QtWidgets.QSplitter()
            splitter.addWidget(self.tree)
            splitter.addWidget(self.editor)
            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 3)
            self.setCentralWidget(splitter)

            self._create_actions()
            self._create_menus()
            self._create_toolbars()
            self.statusBar().showMessage("Bereit")
            self._create_tray_icon()

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
            self.close_doc_action = self._act("Schließen", self.close_document)
            self.exit_action = self._act("Beenden", self.close, "Ctrl+Q")
            self.password_action = self._act("Passwort setzen/ändern", self.change_password)
            self.ftp_action = self._act("FTP öffnen/speichern", self.show_ftp_dialog)
            self.export_rtf_action = self._act("Export als RTF", lambda: self.export_current("rtf"))
            self.export_txt_action = self._act("Export als TXT", lambda: self.export_current("txt"))

            self.add_child_action = self._act("Neu darunter", self.add_child_node)
            self.add_sibling_action = self._act("Neu daneben", self.add_sibling_node)
            self.rename_action = self._act("Umbenennen", self.rename_node, "Ctrl+U")
            self.delete_action = self._act("Löschen", self.delete_anything)
            self.unify_action = self._act("Teilbaum zusammenfassen", self.unify_current_subtree)
            self.desk_note_action = self._act("Desktop-Notiz", self.show_desktop_note)
            self.bg_color_action = self._act("Knoten-Hintergrundfarbe", lambda: self.choose_node_color("bg"))
            self.fg_color_action = self._act("Knoten-Schriftfarbe", lambda: self.choose_node_color("fg"))

            self.cut_action = self._act("Ausschneiden", self.cut_anything, "Ctrl+X")
            self.copy_action = self._act("Kopieren", self.copy_anything, "Ctrl+C")
            self.paste_action = self._act("Einfügen", self.paste_anything, "Ctrl+V")
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

            self.about_action = self._act("Info", self.show_about)
            self.settings_action = self._act("Einstellungen", self.show_settings_dialog)

        def _create_menus(self) -> None:
            menu = self.menuBar().addMenu("&Menü")
            menu.addAction(self.new_action)
            menu.addAction(self.open_action)
            menu.addAction(self.save_action)
            menu.addAction(self.save_as_action)
            menu.addAction(self.close_doc_action)
            menu.addSeparator()
            self.recent_menu = menu.addMenu("Zuletzt geöffnet")
            self.update_recent_menu()
            menu.addSeparator()
            menu.addAction(self.password_action)
            menu.addAction(self.ftp_action)
            menu.addAction(self.settings_action)
            menu.addSeparator()
            menu.addAction(self.exit_action)

            edit = self.menuBar().addMenu("Bearbeiten")
            edit.addAction(self.cut_action)
            edit.addAction(self.copy_action)
            edit.addAction(self.paste_action)
            edit.addSeparator()
            edit.addAction(self.search_action)

            node = self.menuBar().addMenu("Knoten")
            node.addAction(self.add_sibling_action)
            node.addAction(self.add_child_action)
            node.addAction(self.rename_action)
            node.addAction(self.delete_action)
            node.addSeparator()
            node.addAction(self.unify_action)
            node.addAction(self.desk_note_action)
            node.addAction(self.bg_color_action)
            node.addAction(self.fg_color_action)

            export = self.menuBar().addMenu("Export")
            export.addAction(self.export_rtf_action)
            export.addAction(self.export_txt_action)

            extras = self.menuBar().addMenu("Extras")
            extras.addAction(self.alarm_action)

            help_menu = self.menuBar().addMenu("Hilfe")
            help_menu.addAction(self.about_action)

            self.tree.setContextMenuPolicy(_enum(QtCore.Qt, "ContextMenuPolicy", "ActionsContextMenu"))
            for action in (
                self.add_sibling_action,
                self.add_child_action,
                self.rename_action,
                self.delete_action,
                self.unify_action,
                self.desk_note_action,
                self.bg_color_action,
                self.fg_color_action,
            ):
                self.tree.addAction(action)

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
            for action in (self.new_action, self.open_action, self.save_action, self.close_doc_action):
                file_bar.addAction(action)
            node_bar = self.addToolBar("Neu/Entf.")
            for action in (self.add_sibling_action, self.add_child_action, self.delete_action):
                node_bar.addAction(action)
            edit_bar = self.addToolBar("Ausschneiden/Kopieren/Einfügen")
            for action in (self.cut_action, self.copy_action, self.paste_action, self.search_action):
                edit_bar.addAction(action)
            font_bar = self.addToolBar("Schrift")
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
                font_bar.addAction(action)

        def _create_tray_icon(self) -> None:
            self.tray_icon = None
            if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
                return
            self.tray_menu = QtWidgets.QMenu(self)
            self.tray_icon = QtWidgets.QSystemTrayIcon(self.windowIcon(), self)
            self.tray_icon.setToolTip("Notizen")
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.setContextMenu(self.tray_menu)
            self.update_tray_menu()
            self.tray_icon.show()

        def update_tray_menu(self) -> None:
            if not getattr(self, "tray_icon", None):
                return
            self.tray_menu.clear()
            self.tray_menu.addAction("Beenden", self.close)
            self.tray_menu.addAction("Zeigen/Ausblenden", self.toggle_visible)
            self.tray_menu.addSeparator()
            for node in self.document.walk():
                if node.desktop_note is not None:
                    self.tray_menu.addAction(node.title, lambda checked=False, n=node: self.show_desktop_note(n))

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
            self.move(self.settings.window_x, self.settings.window_y)
            if self.settings.window_state.lower() == "maximized":
                self.showMaximized()

        def _store_window_settings(self) -> None:
            geo = self.geometry()
            if not self.isMaximized():
                self.settings.window_x = geo.x()
                self.settings.window_y = geo.y()
                self.settings.window_width = geo.width()
                self.settings.window_height = geo.height()
            self.settings.window_state = "Maximized" if self.isMaximized() else "Normal"
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
                action.triggered.connect(lambda checked=False, p=path_text: self.load_path(Path(p)))

        def update_title(self) -> None:
            name = self.document.path.name if self.document.path else "unbenannt.alx"
            marker = " *" if self.document.changed else ""
            self.setWindowTitle(f"{name}{marker} - Notizen Python/Qt")

        def update_actions(self) -> None:
            has_root = self.document.root is not None
            has_current = self.current_node() is not None
            for action in (
                self.save_action,
                self.save_as_action,
                self.close_doc_action,
                self.export_rtf_action,
                self.export_txt_action,
                self.password_action,
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
            ):
                action.setEnabled(has_current)
            self.paste_action.setEnabled(has_current and (self.clipboard_node is not None or self.editor.hasFocus()))

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
                for win in self.desktop_windows.values():
                    if win.node is self.current_node_ref:
                        win.reload_from_node()

        def on_editor_changed(self) -> None:
            if self._loading_editor or self.current_node_ref is None:
                return
            self.current_node_ref.rtf = html_to_rtf(self.editor.toHtml())
            self.document.mark_changed()
            self.update_title()

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
            start_dir = self.settings.last_directory or str(Path.home())
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
            start = str(self.document.path or Path(self.settings.last_directory or str(Path.home())) / "unbenannt.alx")
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

        def autosave(self) -> None:
            if self.document.changed and self.document.path is not None:
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
            if current is None or current.parent is None:
                self.add_child_node()
                return
            sibling = NoteNode(title="...", rtf="")
            parent = current.parent
            index = current.next_sibling_index()
            parent.insert_child(index, sibling)
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
            self.close_desktop_note(node)
            node.remove_from_parent()
            parent_item = item.parent()
            if parent_item is not None:
                parent_item.removeChild(item)
                self.tree.setCurrentItem(parent_item)
            self.document.mark_changed()
            self.update_title()

        def copy_node(self) -> None:
            node = self.current_node()
            if node is None:
                return
            self.clipboard_node = node.clone_deep()
            self.cut_source_node = None
            self.update_actions()

        def cut_node(self) -> None:
            node = self.current_node()
            if node is None or node is self.document.root:
                return
            self.clipboard_node = node.clone_deep()
            self.cut_source_node = node
            self.update_actions()

        def paste_node(self) -> None:
            target = self.current_node()
            if target is None or self.clipboard_node is None:
                return
            pasted = self.clipboard_node.clone_deep()
            target.add_child(pasted)
            if self.cut_source_node is not None:
                self.close_desktop_note(self.cut_source_node)
                self.cut_source_node.remove_from_parent()
                self.cut_source_node = None
            self.build_tree()
            self.select_node(pasted)
            self.document.mark_changed()
            self.update_title()

        def _editor_active(self) -> bool:
            return self.editor.hasFocus() or self.editor.viewport().hasFocus()

        def cut_anything(self) -> None:
            if self._editor_active():
                self.editor.cut()
                self.save_current_editor_to_node()
            else:
                self.cut_node()

        def copy_anything(self) -> None:
            if self._editor_active():
                self.editor.copy()
            else:
                self.copy_node()

        def paste_anything(self) -> None:
            if self._editor_active():
                self.editor.paste()
                self.save_current_editor_to_node()
            else:
                self.paste_node()

        def delete_anything(self) -> None:
            if self._editor_active():
                cursor = self.editor.textCursor()
                if cursor.hasSelection():
                    cursor.removeSelectedText()
                else:
                    cursor.deleteChar()
                self.editor.setTextCursor(cursor)
                self.save_current_editor_to_node()
            else:
                self.delete_node()

        def unify_current_subtree(self) -> None:
            source = self.current_node()
            if source is None:
                return
            title = f"Zusammenfassung - {source.title}"
            unified = create_unified_note(source, title=title)
            source.add_child(unified)
            self.build_tree()
            self.select_node(unified)
            self.document.mark_changed()
            self.update_title()

        def select_node(self, node: NoteNode) -> None:
            item = self.item_for_node(node)
            if item is not None:
                self.tree.setCurrentItem(item)
                self.tree.scrollToItem(item)

        def show_desktop_note(self, node: NoteNode | None = None) -> None:
            node = node or self.current_node()
            if node is None:
                return
            win = self.desktop_windows.get(id(node))
            if win is None:
                win = DesktopNoteWindow(self, node)
                self.desktop_windows[id(node)] = win
            if node.desktop_note is None:
                node.desktop_note = DesktopNoteState()
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
            msecs = QtCore.QDateTime.currentDateTime().msecsTo(when)
            if msecs < 0:
                QtWidgets.QMessageBox.warning(self, "Wecker", "Der Zeitpunkt liegt in der Vergangenheit.")
                return
            timer = QtCore.QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda t=timer, msg=message: self._trigger_alarm(t, msg))
            self.alarms.append(timer)
            timer.start(int(min(msecs, 2**31 - 1)))
            self.statusBar().showMessage(f"Wecker gestellt: {when.toString()}")

        def _trigger_alarm(self, timer: Any, message: str) -> None:
            try:
                self.alarms.remove(timer)
            except ValueError:
                pass
            self.show()
            self.raise_()
            self.activateWindow()
            QtWidgets.QMessageBox.information(self, "Wecker", message or "Notizen-Wecker")

        def export_current(self, kind: str) -> None:
            node = self.current_node()
            if node is None:
                return
            suffix = ".rtf" if kind == "rtf" else ".txt"
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export", f"{node.title}{suffix}", f"*{suffix}")
            if not file_name:
                return
            path = Path(file_name)
            if kind == "rtf":
                path.write_text(tree_to_rtf(node), encoding="utf-8", errors="replace")
            else:
                path.write_text(tree_to_plain_text(node), encoding="utf-8")
            self.statusBar().showMessage(f"Exportiert: {path}")

        def change_password(self) -> None:
            pw = self.prompt_password("Neues Passwort (leer = ohne Passwort)")
            if pw is None:
                return
            self.document.password = pw
            self.document.mark_changed()
            self.update_title()
            msg = "Passwort gesetzt." if pw else "Passwort entfernt; die nächste Speicherung ist unverschlüsselt."
            self.statusBar().showMessage(msg)

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
            self.editor.mergeCurrentCharFormat(fmt)

        def toggle_italic(self) -> None:
            fmt = self.editor.currentCharFormat()
            fmt.setFontItalic(not fmt.fontItalic())
            self.editor.mergeCurrentCharFormat(fmt)

        def toggle_underline(self) -> None:
            fmt = self.editor.currentCharFormat()
            fmt.setFontUnderline(not fmt.fontUnderline())
            self.editor.mergeCurrentCharFormat(fmt)

        def toggle_strike(self) -> None:
            fmt = self.editor.currentCharFormat()
            fmt.setFontStrikeOut(not fmt.fontStrikeOut())
            self.editor.mergeCurrentCharFormat(fmt)

        def reset_char_format(self) -> None:
            fmt = QtGui.QTextCharFormat()
            fmt.setFontWeight(QtGui.QFont.Weight.Normal)
            fmt.setFontItalic(False)
            fmt.setFontUnderline(False)
            fmt.setFontStrikeOut(False)
            self.editor.mergeCurrentCharFormat(fmt)

        def choose_text_color(self) -> None:
            color = QtWidgets.QColorDialog.getColor(parent=self)
            if color.isValid():
                fmt = QtGui.QTextCharFormat()
                fmt.setForeground(QtGui.QBrush(color))
                self.editor.mergeCurrentCharFormat(fmt)

        def choose_text_background(self) -> None:
            color = QtWidgets.QColorDialog.getColor(parent=self)
            if color.isValid():
                fmt = QtGui.QTextCharFormat()
                fmt.setBackground(QtGui.QBrush(color))
                self.editor.mergeCurrentCharFormat(fmt)

        def insert_bullet(self) -> None:
            cursor = self.editor.textCursor()
            prefix = "" if cursor.position() == 0 else "\n"
            cursor.insertText(prefix + "•   ")
            self.editor.setTextCursor(cursor)

        def change_font_size(self, delta: int) -> None:
            fmt = self.editor.currentCharFormat()
            size = fmt.fontPointSize() or self.editor.font().pointSizeF() or 10
            fmt.setFontPointSize(max(6, min(99, size + delta)))
            self.editor.mergeCurrentCharFormat(fmt)

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
            language_combo.addItems(["Auto", "Deutsch", "English", "Français", "Español", "Русский", "中文"])
            lang_index = language_combo.findText(self.settings.language)
            if lang_index >= 0:
                language_combo.setCurrentIndex(lang_index)

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
            autorun_check = QtWidgets.QCheckBox()
            autorun_check.setChecked(self.settings.autorun_enabled)
            autorun_minimized_check = QtWidgets.QCheckBox()
            autorun_minimized_check.setChecked(self.settings.autorun_minimized)

            layout.addRow("Sicherungen behalten", backup_spin)
            layout.addRow("Autosave alle Sekunden (0 = aus)", autosave_spin)
            layout.addRow("Sprache", language_combo)
            layout.addRow("Scrollleisten im Editor", scroll_combo)
            layout.addRow("Desktop-Notiz-Ränder zeigen", border_check)
            layout.addRow("Minimiert in Taskleiste zeigen", taskbar_check)
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
                self.settings.autosave_seconds = autosave_spin.value()
                self.settings.language = language_combo.currentText()
                self.settings.scrollbars_choice = int(scroll_combo.currentData())
                self.settings.show_desknote_borders = border_check.isChecked()
                self.settings.show_in_taskbar_when_minimized = taskbar_check.isChecked()
                self.settings.autorun_enabled = autorun_check.isChecked()
                self.settings.autorun_minimized = autorun_minimized_check.isChecked()
                self.settings.save()
                self._configure_autosave()
                self._apply_scrollbar_settings()

        def show_about(self) -> None:
            QtWidgets.QMessageBox.information(
                self,
                "Notizen Python/Qt",
                (
                    "Notizen.NET Weitertranspilierung nach Python/Qt\n\n"
                    "Portiert: ALX-Dateiformat, Notizbaum, lokale Speicherung, Suche, "
                    "Knotenoperationen, Desktop-Notizen, RichText-Brücke, Teilbaum-Export, "
                    "alte Tastaturbedienung und erweiterte Grundkonfiguration.\n\n"
                    f"Qt-Binding: {BINDING}"
                ),
            )

        def keyPressEvent(self, event: Any) -> None:  # noqa: N802 - Qt override
            # Keep legacy shortcuts from Notizen.vb/tastendruck focus-aware.
            key = event.key()
            if event.modifiers() & CTRL:
                if key == _enum(QtCore.Qt, "Key", "Key_Space"):
                    self.show_alarm_dialog()
                    return
            if self.tree.hasFocus() and not (event.modifiers() & CTRL):
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
                if self.isMinimized() and getattr(self, "tray_icon", None) and not self.settings.show_in_taskbar_when_minimized:
                    QtCore.QTimer.singleShot(0, self.hide)

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
    parser = argparse.ArgumentParser(description="Notizen.NET Python/Qt port")
    parser.add_argument("file", nargs="?", help="ALX/Notizen-Datei zum Öffnen")
    parser.add_argument("--password", help="Passwort für geschützte ALX-Dateien")
    parser.add_argument("--smoke-test", action="store_true", help="Nur initialisieren und sofort beenden")
    args = parser.parse_args(argv)

    if QT_IMPORT_ERROR is not None:
        print(str(QT_IMPORT_ERROR), file=sys.stderr)
        return 2

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv[:1])
    icon = app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    window = MainWindow(args.file, password=args.password)
    if args.smoke_test:
        return 0
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
