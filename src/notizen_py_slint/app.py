from __future__ import annotations

from importlib import resources
from pathlib import Path
import threading
from typing import Any

from .autostart import sync_autostart
from .alarm import AlarmRule, add_or_replace_alarm, load_alarms, next_alarm, parse_weekdays
from .config import AppConfig, load_config, save_config
from .legacy_config import import_legacy_config
from .dialogs import ask_directory, ask_open_file, ask_password, ask_save_file, ask_text
from .model import Note, NoteDocument, StickyWindow, argb_to_hex, parse_int_or_hex
from .remote import RemoteFileError, is_remote_uri, load_uri, save_uri
from .storage import (
    EncryptedFileError,
    append_bullet_into_note,
    append_current_date_into_note,
    NotizenFileError,
    WrongPasswordError,
    export_document_images,
    export_html,
    export_note_rtf,
    export_rtf,
    export_text,
    import_rtf_into_note,
    import_text_into_note,
    insert_image_into_note,
    save_document as write_document,
)
from .rtf import restyle_rtf_as_plain


class SlintUiError(RuntimeError):
    """Raised when the packaged Slint UI file cannot be compiled or loaded."""


def _read_diag_attr(diag: object, name: str) -> object | None:
    """Read Slint's PyDiagnostic attributes across old and new bindings."""
    try:
        value = getattr(diag, name)
    except Exception:
        return None
    if callable(value):
        try:
            return value()
        except TypeError:
            return value
        except Exception:
            return None
    return value


def _iter_slint_diagnostics(exc: BaseException) -> list[object]:
    diagnostics = getattr(exc, "diagnostics", None)
    if diagnostics is None:
        for arg in getattr(exc, "args", ()):  # older slint-python stores them as args[1]
            if isinstance(arg, list | tuple):
                diagnostics = arg
                break
    if diagnostics is None:
        return []
    try:
        return list(diagnostics)
    except TypeError:
        return []


def _format_slint_diagnostic(diag: object) -> str:
    message = _read_diag_attr(diag, "message")
    level = _read_diag_attr(diag, "level")
    source = _read_diag_attr(diag, "source_file")
    line_col = _read_diag_attr(diag, "line_column")
    line_number = _read_diag_attr(diag, "line_number")
    column_number = _read_diag_attr(diag, "column_number")

    location = ""
    if source:
        location = str(source)
    if isinstance(line_col, tuple) and len(line_col) >= 2:
        line_number, column_number = line_col[0], line_col[1]
    elif isinstance(line_col, list) and len(line_col) >= 2:
        line_number, column_number = line_col[0], line_col[1]
    if line_number or column_number:
        line = line_number or 0
        col = column_number or 0
        location = f"{location}:{line}:{col}" if location else f"Zeile {line}, Spalte {col}"

    level_text = str(level).split(".")[-1] if level is not None else "Fehler"
    message_text = str(message) if message else str(diag)
    if location:
        return f"{location}: {level_text}: {message_text}"
    return f"{level_text}: {message_text}"


def _format_slint_compile_error(exc: BaseException, ui_path: Path) -> str:
    diagnostics = _iter_slint_diagnostics(exc)
    if diagnostics:
        lines = [_format_slint_diagnostic(diag) for diag in diagnostics]
    else:
        lines = [str(exc)]
    return "\n".join([f"Slint konnte die UI-Datei nicht kompilieren: {ui_path}", *lines])


def _load_slint_components(slint_module: Any, ui_path: Path) -> Any:
    try:
        return slint_module.load_file(str(ui_path))
    except Exception as exc:  # noqa: BLE001 - slint exposes version-dependent exception classes
        raise SlintUiError(_format_slint_compile_error(exc, ui_path)) from exc


class NotizenSlintApp:
    """Thin controller that binds the pure Python document model to Slint."""

    def __init__(self, initial_path: str | Path | None = None, password: str | None = None) -> None:
        import slint  # imported lazily so the non-GUI CLI/tests stay Python-only

        self.slint = slint
        ui_resource = resources.files("notizen_py_slint.ui").joinpath("app-window.slint")
        with resources.as_file(ui_resource) as ui_path:
            components = _load_slint_components(slint, ui_path)
        self.window = components.AppWindow()
        self.config: AppConfig = load_config()
        self.document: NoteDocument = NoteDocument.empty()
        self._syncing = False
        self._current_password: str | None = password
        self._clipboard_note: Note | None = None
        self._raw_rtf = False
        self._autosave_timer: threading.Timer | None = None
        self._autosave_lock = threading.RLock()

        self._wire_callbacks()

        if initial_path is not None:
            self._open_location(str(initial_path), password=password)
        elif self.config.last_file and (is_remote_uri(self.config.last_file) or Path(self.config.last_file).exists()):
            # Match the old app's convenience without blocking start-up on encrypted files.
            try:
                self._open_location(self.config.last_file, password=password)
            except EncryptedFileError:
                self._set_status(f"Zuletzt geöffnete Datei ist passwortgeschützt: {self.config.last_file}")
            except NotizenFileError as exc:
                self._set_status(f"Letzte Datei konnte nicht geladen werden: {exc}")

        self._refresh_all()
        self._restart_autosave()

    def run(self) -> None:
        try:
            self.window.run()
        finally:
            self._cancel_autosave()

    def _wire_callbacks(self) -> None:
        self.window.new_document = self.new_document
        self.window.open_document = self.open_document
        self.window.open_remote_document = self.open_remote_document
        self.window.save_document = self.save_document
        self.window.save_document_as = self.save_document_as
        self.window.save_remote_document = self.save_remote_document
        self.window.set_password = self.set_password
        self.window.export_text = self.export_text_file
        self.window.export_rtf = self.export_rtf_file
        self.window.export_html = self.export_html_file
        self.window.export_subtree_text = self.export_subtree_text_file
        self.window.export_subtree_rtf = self.export_subtree_rtf_file
        self.window.export_note_rtf = self.export_note_rtf_file
        self.window.extract_images = self.extract_images_file
        self.window.import_text = self.import_text_file
        self.window.import_rtf = self.import_rtf_file
        self.window.insert_image = self.insert_image_file
        self.window.append_date = self.append_date
        self.window.append_bullet = self.append_bullet
        self.window.add_child = self.add_child
        self.window.add_sibling = self.add_sibling
        self.window.delete_note = self.delete_note
        self.window.duplicate_note = self.duplicate_note
        self.window.copy_node = self.copy_node
        self.window.cut_node = self.cut_node
        self.window.paste_node = self.paste_node
        self.window.move_up = self.move_up
        self.window.move_down = self.move_down
        self.window.indent_note = self.indent_note
        self.window.outdent_note = self.outdent_note
        self.window.toggle_expand = self.toggle_expand
        self.window.expand_all = self.expand_all
        self.window.collapse_all = self.collapse_all
        self.window.select_row = self.select_row
        self.window.rename_current = self.rename_current
        self.window.editor_changed = self.editor_changed
        self.window.search_next = self.search_next
        self.window.search_all = self.search_all
        self.window.toggle_raw_rtf = self.toggle_raw_rtf
        self.window.toggle_sticky = self.toggle_sticky
        self.window.set_sticky_geometry = self.set_sticky_geometry
        self.window.set_colors = self.set_colors
        self.window.clear_colors = self.clear_colors
        self.window.format_note = self.format_note
        self.window.open_settings = self.open_settings
        self.window.import_legacy_config = self.import_legacy_config_file
        self.window.open_alarm = self.open_alarm
        self.window.show_next_alarm = self.show_next_alarm
        self.window.show_stats = self.show_stats

    # File actions ---------------------------------------------------------
    def new_document(self) -> None:
        self.document = NoteDocument.empty()
        self._current_password = None
        self._raw_rtf = False
        self._clipboard_note = None
        self._refresh_all()
        self._set_status("Neue Notizdatei angelegt.")

    def open_document(self) -> None:
        path = ask_open_file("Notizen-Datei öffnen")
        if path is None:
            return
        try:
            self._open_location(str(path))
        except NotizenFileError as exc:
            self._set_status(f"Öffnen fehlgeschlagen: {exc}")
            return
        self._refresh_all()

    def open_remote_document(self) -> None:
        url = ask_text("FTP/FTPS-URL öffnen", default=self.config.default_remote_url() or "ftp://user:pass@example.org/pfad/datei.alx", empty_is_none=True)
        if not url:
            return
        try:
            self._open_location(url)
        except NotizenFileError as exc:
            self._set_status(f"Remote-Öffnen fehlgeschlagen: {exc}")
            return
        self._refresh_all()

    def _open_location(self, location: str, password: str | None = None) -> None:
        try:
            doc = load_uri(location, password=password)
        except EncryptedFileError:
            pwd = ask_password("Passwort für die Notizen-Datei")
            if pwd is None:
                raise
            doc = load_uri(location, password=pwd)
            password = pwd
        except WrongPasswordError:
            pwd = ask_password("Passwort war falsch. Bitte erneut eingeben")
            if pwd is None:
                raise
            doc = load_uri(location, password=pwd)
            password = pwd

        self.document = doc
        self._current_password = password if password else doc.password
        self._raw_rtf = False
        self.config.add_recent(location)
        save_config(self.config)
        self._set_status(f"Geöffnet: {location}")

    def save_document(self) -> None:
        if not self.document.path:
            self.save_document_as()
            return
        try:
            if is_remote_uri(self.document.path):
                saved = save_uri(self.document, password=self._current_password)
            else:
                saved = str(write_document(self.document, password=self._current_password, backup_count=self.config.backup_count))
        except Exception as exc:  # noqa: BLE001 - show GUI-friendly message for all file failures
            self._set_status(f"Speichern fehlgeschlagen: {exc}")
            return
        self.config.add_recent(saved)
        save_config(self.config)
        self._refresh_all(keep_editor=True)
        self._set_status(f"Gespeichert: {saved}")

    def save_document_as(self) -> None:
        suggested = Path(self.document.path or self.config.last_file or "unbenannt.alx").name
        path = ask_save_file("Notizen-Datei speichern", suggested=suggested, suffix=".alx")
        if path is None:
            return
        try:
            saved = write_document(self.document, path=path, password=self._current_password, backup_count=self.config.backup_count)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Speichern fehlgeschlagen: {exc}")
            return
        self.config.add_recent(saved)
        save_config(self.config)
        self._refresh_all(keep_editor=True)
        self._set_status(f"Gespeichert: {saved}")

    def save_remote_document(self) -> None:
        default = self.document.path if self.document.path and is_remote_uri(self.document.path) else self.config.default_remote_url() or "ftp://user:pass@example.org/pfad/datei.alx"
        url = ask_text("FTP/FTPS-URL speichern", default=default, empty_is_none=True)
        if not url:
            return
        try:
            saved = save_uri(self.document, uri=url, password=self._current_password)
        except RemoteFileError as exc:
            self._set_status(f"Remote-Speichern fehlgeschlagen: {exc}")
            return
        self.config.add_recent(saved)
        save_config(self.config)
        self._refresh_all(keep_editor=True)
        self._set_status(f"Remote gespeichert: {saved}")

    def set_password(self) -> None:
        pwd = ask_password("Neues Passwort; leer lassen, um Verschlüsselung zu entfernen", empty_is_none=False)
        if pwd is None:
            return
        self._current_password = pwd or None
        self.document.password = self._current_password
        self.document.modified = True
        self._refresh_all(keep_editor=True)
        if self._current_password:
            self._set_status("Passwort gesetzt. Die Datei wird beim nächsten Speichern verschlüsselt.")
        else:
            self._set_status("Passwort entfernt. Die Datei wird beim nächsten Speichern unverschlüsselt.")

    def export_text_file(self) -> None:
        path = ask_save_file("Als Text exportieren", suggested="notizen.txt", suffix=".txt")
        if path is None:
            return
        try:
            export_text(self.document, path)
            self._set_status(f"TXT exportiert: {path}")
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"TXT-Export fehlgeschlagen: {exc}")

    def export_rtf_file(self) -> None:
        path = ask_save_file("Als RTF exportieren", suggested="notizen.rtf", suffix=".rtf")
        if path is None:
            return
        try:
            export_rtf(self.document, path)
            self._set_status(f"RTF exportiert: {path}")
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"RTF-Export fehlgeschlagen: {exc}")

    def export_html_file(self) -> None:
        path = ask_save_file("Als HTML exportieren", suggested="notizen.html", suffix=".html")
        if path is None:
            return
        try:
            export_html(self.document, path)
            self._set_status(f"HTML exportiert: {path}")
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"HTML-Export fehlgeschlagen: {exc}")

    def export_subtree_text_file(self) -> None:
        note = self.document.selected_note
        path = ask_save_file("Teilbaum als Text exportieren", suggested=f"{_safe_filename(note.title)}.txt", suffix=".txt")
        if path is None:
            return
        try:
            export_text(self.document, path, start=note, numbered=True)
            self._set_status(f"Teilbaum exportiert: {path}")
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Teilbaum-Export fehlgeschlagen: {exc}")

    def export_subtree_rtf_file(self) -> None:
        note = self.document.selected_note
        path = ask_save_file("Teilbaum als RTF exportieren", suggested=f"{_safe_filename(note.title)}.rtf", suffix=".rtf")
        if path is None:
            return
        try:
            export_rtf(self.document, path, start=note, numbered=True)
            self._set_status(f"Teilbaum-RTF exportiert: {path}")
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Teilbaum-RTF-Export fehlgeschlagen: {exc}")

    def export_note_rtf_file(self) -> None:
        note = self.document.selected_note
        path = ask_save_file("Aktuelle Notiz-Roh-RTF exportieren", suggested=f"{_safe_filename(note.title)}.rtf", suffix=".rtf")
        if path is None:
            return
        try:
            export_note_rtf(note, path)
            self._set_status(f"Notiz-RTF exportiert: {path}")
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Notiz-RTF-Export fehlgeschlagen: {exc}")

    def extract_images_file(self) -> None:
        current = self.document.path or self.config.last_file or "notizen"
        if current and not is_remote_uri(str(current)):
            base = Path(str(current)).stem or "notizen"
        else:
            base = "notizen"
        path = ask_directory("RTF-Bilder extrahieren: Zielordner auswählen", initial_dir=str(Path.cwd() / f"{base}-bilder"))
        if path is None:
            return
        try:
            paths = export_document_images(self.document, Path(path))
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Bildextraktion fehlgeschlagen: {exc}")
            return
        self._set_status(f"{len(paths)} Bild(er) extrahiert: {path}")

    def import_text_file(self) -> None:
        path = ask_open_file("Text in aktuelle Notiz importieren", filetypes=[("Text", "*.txt"), ("Alle Dateien", "*.*")])
        if path is None:
            return
        try:
            import_text_into_note(self.document.selected_note, path)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Text-Import fehlgeschlagen: {exc}")
            return
        self.document.modified = True
        self._refresh_all()
        self._set_status(f"Text importiert: {path}")

    def import_rtf_file(self) -> None:
        path = ask_open_file("RTF in aktuelle Notiz importieren", filetypes=[("RTF", "*.rtf"), ("Text", "*.txt"), ("Alle Dateien", "*.*")])
        if path is None:
            return
        try:
            import_rtf_into_note(self.document.selected_note, path)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"RTF-Import fehlgeschlagen: {exc}")
            return
        self.document.modified = True
        self._refresh_all()
        self._set_status(f"RTF/Text importiert: {path}")

    def insert_image_file(self) -> None:
        path = ask_open_file(
            "Bild in aktuelle Notiz einfügen",
            filetypes=[("Bilder", "*.png *.jpg *.jpeg *.bmp *.dib"), ("Alle Dateien", "*.*")],
        )
        if path is None:
            return
        try:
            insert_image_into_note(self.document.selected_note, path)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Bild einfügen fehlgeschlagen: {exc}")
            return
        self.document.modified = True
        self._refresh_all()
        self._set_status(f"Bild an Notiz angehängt: {path}")

    def append_date(self) -> None:
        append_current_date_into_note(self.document.selected_note)
        self.document.modified = True
        self._refresh_all()
        self._set_status("Datum/Uhrzeit angehängt.")

    def append_bullet(self) -> None:
        append_bullet_into_note(self.document.selected_note)
        self.document.modified = True
        self._refresh_all()
        self._set_status("Aufzählungszeichen angehängt.")

    # Tree actions ---------------------------------------------------------
    def add_child(self) -> None:
        self.document.add_child_to_selected()
        self._refresh_all()
        self._set_status("Kindnotiz angelegt.")

    def add_sibling(self) -> None:
        self.document.add_sibling_after_selected()
        self._refresh_all()
        self._set_status("Nachbarnotiz angelegt.")

    def delete_note(self) -> None:
        title = self.document.selected_note.title
        self.document.delete_selected()
        self._refresh_all()
        self._set_status(f"Notiz gelöscht/zurückgesetzt: {title}")

    def duplicate_note(self) -> None:
        clone = self.document.duplicate_selected()
        if clone is None:
            self._set_status("Wurzel kann nicht dupliziert werden.")
            return
        self._refresh_all()
        self._set_status(f"Notiz dupliziert: {clone.title}")

    def copy_node(self) -> None:
        self._clipboard_note = self.document.selected_note.clone_deep()
        self._set_status(f"Knoten kopiert: {self._clipboard_note.title}")

    def cut_node(self) -> None:
        selected = self.document.selected_note
        if selected.parent is None:
            self._set_status("Wurzel kann nicht ausgeschnitten werden.")
            return
        self._clipboard_note = selected.clone_deep()
        self.document.delete_selected()
        self._refresh_all()
        self._set_status(f"Knoten ausgeschnitten: {self._clipboard_note.title}")

    def paste_node(self) -> None:
        if self._clipboard_note is None:
            self._set_status("Keine kopierte Notiz vorhanden.")
            return
        clone = self.document.insert_clone_after_selected(self._clipboard_note)
        self._refresh_all()
        self._set_status(f"Knoten eingefügt: {clone.title}")

    def move_up(self) -> None:
        if self.document.move_selected_up():
            self._refresh_all(keep_editor=True)
            self._set_status("Notiz nach oben verschoben.")
        else:
            self._set_status("Nach oben verschieben nicht möglich.")

    def move_down(self) -> None:
        if self.document.move_selected_down():
            self._refresh_all(keep_editor=True)
            self._set_status("Notiz nach unten verschoben.")
        else:
            self._set_status("Nach unten verschieben nicht möglich.")

    def indent_note(self) -> None:
        if self.document.indent_selected():
            self._refresh_all(keep_editor=True)
            self._set_status("Notiz eingerückt.")
        else:
            self._set_status("Einrücken nicht möglich.")

    def outdent_note(self) -> None:
        if self.document.outdent_selected():
            self._refresh_all(keep_editor=True)
            self._set_status("Notiz ausgerückt.")
        else:
            self._set_status("Ausrücken nicht möglich.")

    def toggle_expand(self) -> None:
        self.document.toggle_selected_expanded()
        self._refresh_all(keep_editor=True)

    def expand_all(self) -> None:
        self.document.expand_all()
        self._refresh_all(keep_editor=True)
        self._set_status("Alle Notizen aufgeklappt.")

    def collapse_all(self) -> None:
        self.document.collapse_all()
        self._refresh_all(keep_editor=True)
        self._set_status("Alle Notizen zugeklappt.")

    def select_row(self, index: int) -> None:
        note = self.document.select_by_flat_index(int(index))
        if note is not None:
            self._refresh_all()

    def rename_current(self, title: str) -> None:
        if self._syncing:
            return
        title = str(title).strip() or "..."
        note = self.document.selected_note
        if note.title != title:
            note.title = title
            self.document.modified = True
            self._refresh_all(keep_editor=True)
            self._set_status("Titel geändert.")

    def editor_changed(self, text: str) -> None:
        if self._syncing:
            return
        note = self.document.selected_note
        if self._raw_rtf:
            note.set_rtf(str(text))
        else:
            note.set_text(str(text))
        self.document.modified = True
        self._refresh_tree_only()
        self._refresh_title_dirty()
        self._refresh_metadata()

    def search_next(self, needle: str) -> None:
        found = self.document.find_next(str(needle))
        if found is None:
            self._set_status("Kein Treffer.")
        else:
            self._refresh_all()
            self._set_status(f"Treffer: {found.path_string()}")

    def search_all(self, needle: str) -> None:
        hits = self.document.find_all(str(needle))
        if not hits:
            self._set_status("Keine Treffer.")
            return
        self.document.select(hits[0].note)
        self._refresh_all()
        sample = "; ".join(hit.note.path_string() for hit in hits[:3])
        more = " …" if len(hits) > 3 else ""
        self._set_status(f"{len(hits)} Treffer: {sample}{more}")

    # Metadata / raw RTF ---------------------------------------------------
    def toggle_raw_rtf(self) -> None:
        self._raw_rtf = not self._raw_rtf
        self._refresh_all()
        self._set_status("Roh-RTF-Modus aktiv." if self._raw_rtf else "Textmodus aktiv.")

    def toggle_sticky(self) -> None:
        note = self.document.selected_note
        if note.sticky is None:
            note.sticky = StickyWindow(visible=True, x=100, y=100, width=260, height=180, opacity=0.85, argb=note.bg_color)
        else:
            note.sticky.visible = not note.sticky.visible
        self.document.modified = True
        self._refresh_all(keep_editor=True)
        self._set_status("Sticky-Metadaten aktualisiert.")

    def set_sticky_geometry(self) -> None:
        note = self.document.selected_note
        sticky = note.sticky or StickyWindow(visible=True, x=100, y=100, width=260, height=180, opacity=0.85, argb=note.bg_color)
        default = f"{sticky.x or 100},{sticky.y or 100},{sticky.width or 260},{sticky.height or 180},{sticky.opacity or 0.85},{argb_to_hex(sticky.argb) if sticky.argb is not None else ''}"
        raw = ask_text("Sticky: x,y,width,height,opacity,argb", default=default, empty_is_none=True)
        if raw is None:
            return
        try:
            parts = [part.strip() for part in raw.split(",")]
            if len(parts) < 5:
                raise ValueError("erwartet mindestens fünf Werte")
            sticky.x = int(parts[0])
            sticky.y = int(parts[1])
            sticky.width = int(parts[2])
            sticky.height = int(parts[3])
            sticky.opacity = float(parts[4].replace(",", "."))
            sticky.argb = parse_int_or_hex(parts[5]) if len(parts) > 5 and parts[5] else sticky.argb
            sticky.visible = True
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Sticky-Werte ungültig: {exc}")
            return
        note.sticky = sticky
        self.document.modified = True
        self._refresh_all(keep_editor=True)
        self._set_status("Sticky-Geometrie gesetzt.")

    def set_colors(self) -> None:
        note = self.document.selected_note
        default = f"{argb_to_hex(note.bg_color) if note.bg_color is not None else ''},{argb_to_hex(note.fg_color) if note.fg_color is not None else ''}"
        raw = ask_text("Knotenfarben als bgcolor,fgcolor (#AARRGGBB oder Integer)", default=default, empty_is_none=True)
        if raw is None:
            return
        try:
            parts = [part.strip() for part in raw.split(",")]
            note.bg_color = parse_int_or_hex(parts[0]) if parts and parts[0] else None
            note.fg_color = parse_int_or_hex(parts[1]) if len(parts) > 1 and parts[1] else None
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Farbwerte ungültig: {exc}")
            return
        self.document.modified = True
        self._refresh_all(keep_editor=True)
        self._set_status("Knotenfarben gesetzt.")

    def clear_colors(self) -> None:
        note = self.document.selected_note
        note.bg_color = None
        note.fg_color = None
        self.document.modified = True
        self._refresh_all(keep_editor=True)
        self._set_status("Knotenfarben gelöscht.")

    def format_note(self) -> None:
        note = self.document.selected_note
        default = "Sans Serif,18,false,false,false,false,,"
        raw = ask_text(
            "Format: font,halbpunkte,bold,italic,underline,strike,fg,bg",
            default=default,
            empty_is_none=True,
        )
        if raw is None:
            return
        try:
            parts = [part.strip() for part in raw.split(",")]
            while len(parts) < 8:
                parts.append("")
            note.rtf = restyle_rtf_as_plain(
                note.rtf,
                font_family=parts[0] or "Sans Serif",
                font_size_half_points=int(parts[1] or 18),
                bold=_parse_bool_text(parts[2]),
                italic=_parse_bool_text(parts[3]),
                underline=_parse_bool_text(parts[4]),
                strike=_parse_bool_text(parts[5]),
                fg_color=parse_int_or_hex(parts[6]) if parts[6] else None,
                bg_color=parse_int_or_hex(parts[7]) if parts[7] else None,
            )
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Format ungültig: {exc}")
            return
        self.document.modified = True
        self._refresh_all()
        self._set_status(f"Notiz formatiert: {note.title}")

    def open_settings(self) -> None:
        default = f"{self.config.backup_count},{self.config.autosave_seconds},{self.config.autorun},{self.config.autorun_minimized},{self.config.ftp_host},{self.config.ftp_username},{self.config.ftp_path},{self.config.ftp_use_tls}"
        raw = ask_text("Einstellungen: backups,autosave_sec,autorun,autorun_minimized,ftp_host,ftp_user,ftp_path,ftps", default=default, empty_is_none=True)
        if raw is None:
            return
        try:
            parts = [part.strip() for part in raw.split(",")]
            if len(parts) >= 1 and parts[0]:
                self.config.backup_count = max(0, int(parts[0]))
            if len(parts) >= 2 and parts[1]:
                self.config.autosave_seconds = max(0, int(parts[1]))
            if len(parts) >= 3 and parts[2]:
                self.config.autorun = _parse_bool_text(parts[2])
            if len(parts) >= 4 and parts[3]:
                self.config.autorun_minimized = _parse_bool_text(parts[3])
            if len(parts) >= 5:
                self.config.ftp_host = parts[4]
            if len(parts) >= 6:
                self.config.ftp_username = parts[5]
            if len(parts) >= 7:
                self.config.ftp_path = parts[6]
            if len(parts) >= 8 and parts[7]:
                self.config.ftp_use_tls = _parse_bool_text(parts[7])
            save_config(self.config)
            status = sync_autostart(self.config)
            self._restart_autosave()
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Einstellungen ungültig: {exc}")
            return
        note = f" Autostart: {status.message}" if status.message else ""
        self._set_status(f"Einstellungen gespeichert.{note}")

    def import_legacy_config_file(self) -> None:
        path = ask_open_file(
            "Alte notizen.config.xml importieren",
            filetypes=[("Notizen.NET config", "*.xml"), ("Alle Dateien", "*.*")],
        )
        if path is None:
            return
        try:
            self.config = import_legacy_config(path)
            status = sync_autostart(self.config)
            self._restart_autosave()
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Config-Import fehlgeschlagen: {exc}")
            return
        suffix = f" Autostart: {status.message}" if status.message else ""
        self._set_status(f"Alte Konfiguration übernommen: {path}.{suffix}")

    def show_stats(self) -> None:
        stats = self.document.stats()
        self._set_status(
            f"{stats.notes} Notizen, {stats.leaves} Blätter, Tiefe {stats.max_depth}, "
            f"{stats.sticky_notes} Sticky-Metadaten, {stats.characters} Zeichen"
        )


    # Alarm actions --------------------------------------------------------
    def open_alarm(self) -> None:
        default = "Wecker,2026-04-27 09:00,none,1,,"
        raw = ask_text(
            "Wecker: name,datetime,repeat,interval,weekdays,message",
            default=default,
            empty_is_none=True,
        )
        if raw is None:
            return
        try:
            parts = [part.strip() for part in raw.split(",", 5)]
            while len(parts) < 6:
                parts.append("")
            alarm = AlarmRule.create(
                parts[0] or "Wecker",
                parts[1] or "2026-04-27 09:00",
                repeat=parts[2] or "none",
                interval=int(parts[3] or 1),
                weekdays=parse_weekdays([parts[4]] if parts[4] else None),
                message=parts[5],
                note_title=self.document.selected_note.title,
            )
            add_or_replace_alarm(alarm)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Wecker ungültig: {exc}")
            return
        self._set_status("Wecker gespeichert: " + alarm.summary())

    def show_next_alarm(self) -> None:
        found = next_alarm(load_alarms())
        if found is None:
            self._set_status("Kein aktiver Wecker gespeichert.")
            return
        alarm, when = found
        suffix = f" für {alarm.note_title}" if alarm.note_title else ""
        message = f" – {alarm.message}" if alarm.message else ""
        self._set_status(f"Nächster Wecker: {when:%Y-%m-%d %H:%M} {alarm.name}{suffix}{message}")

    # Autosave -------------------------------------------------------------
    def _restart_autosave(self) -> None:
        self._cancel_autosave()
        seconds = int(self.config.autosave_seconds or 0)
        if seconds <= 0:
            return
        self._autosave_timer = threading.Timer(seconds, self._autosave_tick)
        self._autosave_timer.daemon = True
        self._autosave_timer.start()

    def _cancel_autosave(self) -> None:
        timer = self._autosave_timer
        self._autosave_timer = None
        if timer is not None:
            timer.cancel()

    def _autosave_tick(self) -> None:
        try:
            with self._autosave_lock:
                if self.document.modified and self.document.path and not is_remote_uri(self.document.path):
                    write_document(self.document, password=self._current_password, backup_count=self.config.backup_count)
        except Exception:
            # Background autosave must never crash the UI. Manual save still reports details.
            pass
        finally:
            self._restart_autosave()

    # Rendering ------------------------------------------------------------
    def _refresh_all(self, keep_editor: bool = False) -> None:
        self._syncing = True
        try:
            self._refresh_tree_only()
            note = self.document.selected_note
            if not keep_editor:
                self.window.editor_text = note.rtf if self._raw_rtf else note.text
            self.window.note_title = note.title
            self.window.selected_index = self.document.selected_flat_index()
            self.window.mode_label = "Modus: RTF roh" if self._raw_rtf else "Modus: Text"
            self._refresh_metadata()
            self._refresh_title_dirty()
        finally:
            self._syncing = False

    def _refresh_tree_only(self) -> None:
        rows: list[dict[str, Any]] = []
        selected_id = self.document.selected_id
        for row in self.document.flatten():
            rows.append({"label": row.label, "selected": row.note.note_id == selected_id})
        self.window.rows = self.slint.ListModel(rows)

    def _refresh_metadata(self) -> None:
        note = self.document.selected_note
        bits = [note.path_string(), f"{len(note.text)} Zeichen"]
        if note.bg_color not in (None, 0):
            bits.append(f"BG {argb_to_hex(note.bg_color)}")
        if note.fg_color not in (None, 0):
            bits.append(f"FG {argb_to_hex(note.fg_color)}")
        if note.sticky is not None:
            bits.append("Sticky " + note.sticky.summary())
        self.window.meta_text = " | ".join(bits)

    def _refresh_title_dirty(self) -> None:
        name = Path(self.document.path).name if self.document.path and not is_remote_uri(self.document.path) else self.document.path or "unbenannt.alx"
        locked = " 🔒" if self._current_password else ""
        marker = " *" if self.document.modified else ""
        self.window.window_title = f"Notizen Python Slint - {name}{locked}{marker}"
        self.window.dirty = bool(self.document.modified)

    def _set_status(self, message: str) -> None:
        self.window.status_text = message


def _parse_bool_text(value: str) -> bool:
    text = str(value).strip().lower()
    return text in {"1", "true", "wahr", "yes", "ja", "on", "y", "j"}


def _safe_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in " ._-" else "_" for ch in value).strip()
    return cleaned or "notiz"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Notizen.NET-Port für Python3 mit Slint")
    parser.add_argument("file", nargs="?", help=".alx-Datei oder ftp://-/ftps://-URL öffnen")
    parser.add_argument("--password", help="Passwort für verschlüsselte .alx-Dateien")
    parser.add_argument("--minimized", action="store_true", help="aus alter Autostart-Konfiguration akzeptiert; UI startet normal")
    args = parser.parse_args(argv)

    try:
        app = NotizenSlintApp(initial_path=args.file, password=args.password)
        app.run()
    except ModuleNotFoundError as exc:
        if exc.name == "slint":
            print("Slint ist nicht installiert. Installiere die UI-Abhängigkeit mit:")
            print('  python3 -m pip install -e ".[slint]"')
            return 2
        raise
    except SlintUiError as exc:
        print(exc)
        return 1
    except RuntimeError as exc:
        text = str(exc)
        if "Could not initialize any renderer" in text or "No renderers configured" in text:
            print("Slint konnte kein Fenster-/Renderer-Backend initialisieren.")
            print("Starte die Anwendung in einer Desktop-Sitzung oder setze ein passendes SLINT_BACKEND.")
            print(text)
            return 1
        raise
    except NotizenFileError as exc:
        print(f"Dateifehler: {exc}")
        return 1
    return 0
