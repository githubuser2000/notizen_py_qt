from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

from .config import AppConfig, load_config, save_config
from .dialogs import ask_open_file, ask_password, ask_save_file, ask_text
from .model import NoteDocument
from .storage import (
    EncryptedFileError,
    NotizenFileError,
    WrongPasswordError,
    export_rtf,
    export_text,
    load_document,
    save_document,
)


class NotizenSlintApp:
    """Thin controller that binds the pure Python document model to Slint."""

    def __init__(self, initial_path: str | Path | None = None, password: str | None = None) -> None:
        import slint  # imported lazily so the non-GUI CLI/tests stay PyPy-only

        self.slint = slint
        ui_path = resources.files("notizen_pypy_slint.ui").joinpath("app-window.slint")
        components = slint.load_file(str(ui_path))
        self.window = components.AppWindow()
        self.config: AppConfig = load_config()
        self.document: NoteDocument = NoteDocument.empty()
        self._syncing = False
        self._current_password: str | None = password

        self._wire_callbacks()

        if initial_path is not None:
            self._open_path(Path(initial_path), password=password)
        elif self.config.last_file and Path(self.config.last_file).exists():
            # Match the old app's convenience without blocking start-up on encrypted files.
            try:
                self._open_path(Path(self.config.last_file), password=password)
            except EncryptedFileError:
                self._set_status(f"Zuletzt geöffnete Datei ist passwortgeschützt: {self.config.last_file}")
            except NotizenFileError as exc:
                self._set_status(f"Letzte Datei konnte nicht geladen werden: {exc}")

        self._refresh_all()

    def run(self) -> None:
        self.window.run()

    def _wire_callbacks(self) -> None:
        self.window.new_document = self.new_document
        self.window.open_document = self.open_document
        self.window.save_document = self.save_document
        self.window.save_document_as = self.save_document_as
        self.window.set_password = self.set_password
        self.window.export_text = self.export_text_file
        self.window.export_rtf = self.export_rtf_file
        self.window.add_child = self.add_child
        self.window.add_sibling = self.add_sibling
        self.window.delete_note = self.delete_note
        self.window.toggle_expand = self.toggle_expand
        self.window.select_row = self.select_row
        self.window.rename_current = self.rename_current
        self.window.editor_changed = self.editor_changed
        self.window.search_next = self.search_next

    # File actions ---------------------------------------------------------
    def new_document(self) -> None:
        self.document = NoteDocument.empty()
        self._current_password = None
        self._refresh_all()
        self._set_status("Neue Notizdatei angelegt.")

    def open_document(self) -> None:
        path = ask_open_file("Notizen-Datei öffnen")
        if path is None:
            return
        try:
            self._open_path(path)
        except NotizenFileError as exc:
            self._set_status(f"Öffnen fehlgeschlagen: {exc}")
            return
        self._refresh_all()

    def _open_path(self, path: Path, password: str | None = None) -> None:
        try:
            doc = load_document(path, password=password)
        except EncryptedFileError:
            pwd = ask_password("Passwort für die Notizen-Datei")
            if pwd is None:
                raise
            doc = load_document(path, password=pwd)
            password = pwd
        except WrongPasswordError:
            pwd = ask_password("Passwort war falsch. Bitte erneut eingeben")
            if pwd is None:
                raise
            doc = load_document(path, password=pwd)
            password = pwd

        self.document = doc
        self._current_password = password if password else doc.password
        self.config.add_recent(path)
        save_config(self.config)
        self._set_status(f"Geöffnet: {path}")

    def save_document(self) -> None:
        if not self.document.path:
            self.save_document_as()
            return
        try:
            path = save_document(self.document, password=self._current_password, backup_count=self.config.backup_count)
        except Exception as exc:  # noqa: BLE001 - show GUI-friendly message for all file failures
            self._set_status(f"Speichern fehlgeschlagen: {exc}")
            return
        self.config.add_recent(path)
        save_config(self.config)
        self._refresh_all(keep_editor=True)
        self._set_status(f"Gespeichert: {path}")

    def save_document_as(self) -> None:
        suggested = Path(self.document.path or self.config.last_file or "unbenannt.alx").name
        path = ask_save_file("Notizen-Datei speichern", suggested=suggested, suffix=".alx")
        if path is None:
            return
        try:
            saved = save_document(self.document, path=path, password=self._current_password, backup_count=self.config.backup_count)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Speichern fehlgeschlagen: {exc}")
            return
        self.config.add_recent(saved)
        save_config(self.config)
        self._refresh_all(keep_editor=True)
        self._set_status(f"Gespeichert: {saved}")

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

    def toggle_expand(self) -> None:
        self.document.toggle_selected_expanded()
        self._refresh_all(keep_editor=True)

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
        note.set_text(str(text))
        self.document.modified = True
        self._refresh_tree_only()
        self._refresh_title_dirty()

    def search_next(self, needle: str) -> None:
        found = self.document.find_next(str(needle))
        if found is None:
            self._set_status("Kein Treffer.")
        else:
            self._refresh_all()
            self._set_status(f"Treffer: {found.title}")

    # Rendering ------------------------------------------------------------
    def _refresh_all(self, keep_editor: bool = False) -> None:
        self._syncing = True
        try:
            self._refresh_tree_only()
            note = self.document.selected_note
            if not keep_editor:
                self.window.editor_text = note.text
            self.window.note_title = note.title
            self.window.selected_index = self.document.selected_flat_index()
            self._refresh_title_dirty()
        finally:
            self._syncing = False

    def _refresh_tree_only(self) -> None:
        rows: list[dict[str, Any]] = []
        selected_id = self.document.selected_id
        for row in self.document.flatten():
            rows.append({"label": row.label, "selected": row.note.note_id == selected_id})
        self.window.rows = self.slint.ListModel(rows)

    def _refresh_title_dirty(self) -> None:
        name = Path(self.document.path).name if self.document.path else "unbenannt.alx"
        locked = " 🔒" if self._current_password else ""
        marker = " *" if self.document.modified else ""
        self.window.window_title = f"Notizen PyPy Slint - {name}{locked}{marker}"
        self.window.dirty = bool(self.document.modified)

    def _set_status(self, message: str) -> None:
        self.window.status_text = message


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Notizen.NET-Port für PyPy3 mit Slint")
    parser.add_argument("file", nargs="?", help=".alx-Datei öffnen")
    parser.add_argument("--password", help="Passwort für verschlüsselte .alx-Dateien")
    args = parser.parse_args(argv)

    try:
        app = NotizenSlintApp(initial_path=args.file, password=args.password)
        app.run()
    except ModuleNotFoundError as exc:
        if exc.name == "slint":
            print("Slint ist nicht installiert. Installiere die UI-Abhängigkeit mit:")
            print('  pypy3 -m pip install -e ".[slint]"')
            return 2
        raise
    except NotizenFileError as exc:
        print(f"Dateifehler: {exc}")
        return 1
    return 0
