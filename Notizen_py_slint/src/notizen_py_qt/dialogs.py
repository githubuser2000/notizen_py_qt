from __future__ import annotations

import getpass
from pathlib import Path
from typing import Sequence

FileTypes = Sequence[tuple[str, str]]


def _tk_root():
    try:
        import tkinter as tk
    except Exception:
        return None
    try:
        root = tk.Tk()
        root.withdraw()
        root.update()
        return root
    except Exception:
        return None


def ask_open_file(
    title: str = "Notizen-Datei öffnen",
    initial_dir: str | None = None,
    filetypes: FileTypes | None = None,
) -> Path | None:
    root = _tk_root()
    if root is not None:
        try:
            from tkinter import filedialog

            result = filedialog.askopenfilename(
                parent=root,
                initialdir=initial_dir or str(Path.home()),
                title=title,
                filetypes=list(filetypes or [("Notizen .alx", "*.alx"), ("XML", "*.xml"), ("Alle Dateien", "*.*")]),
            )
            return Path(result) if result else None
        finally:
            root.destroy()
    value = input(f"{title} - Dateipfad, leer = abbrechen: ").strip()
    return Path(value) if value else None


def ask_save_file(
    title: str = "Notizen-Datei speichern",
    suggested: str | None = None,
    suffix: str = ".alx",
    initial_dir: str | None = None,
    filetypes: FileTypes | None = None,
) -> Path | None:
    root = _tk_root()
    if root is not None:
        try:
            from tkinter import filedialog

            result = filedialog.asksaveasfilename(
                parent=root,
                initialdir=initial_dir or str(Path.home()),
                initialfile=suggested or f"unbenannt{suffix}",
                defaultextension=suffix,
                title=title,
                filetypes=list(filetypes or [("Notizen", f"*{suffix}"), ("Alle Dateien", "*.*")]),
            )
            return Path(result) if result else None
        finally:
            root.destroy()
    value = input(f"{title} - Dateipfad, leer = abbrechen: ").strip()
    return Path(value) if value else None


def ask_directory(
    title: str = "Ordner auswählen",
    initial_dir: str | None = None,
) -> Path | None:
    root = _tk_root()
    if root is not None:
        try:
            from tkinter import filedialog

            result = filedialog.askdirectory(
                parent=root,
                initialdir=initial_dir or str(Path.home()),
                title=title,
                mustexist=False,
            )
            return Path(result) if result else None
        finally:
            root.destroy()
    value = input(f"{title} - Ordnerpfad, leer = abbrechen: ").strip()
    return Path(value) if value else None


def ask_password(prompt: str = "Passwort", empty_is_none: bool = True) -> str | None:
    root = _tk_root()
    if root is not None:
        try:
            from tkinter import simpledialog

            result = simpledialog.askstring("Notizen", prompt, parent=root, show="*")
            if result == "" and empty_is_none:
                return None
            return result
        finally:
            root.destroy()
    value = getpass.getpass(prompt + ": ")
    return None if value == "" and empty_is_none else value


def ask_text(prompt: str, default: str = "", *, empty_is_none: bool = False) -> str | None:
    root = _tk_root()
    if root is not None:
        try:
            from tkinter import simpledialog

            result = simpledialog.askstring("Notizen", prompt, initialvalue=default, parent=root)
            if result == "" and empty_is_none:
                return None
            return result
        finally:
            root.destroy()
    value = input(f"{prompt} [{default}]: ").strip()
    if value == "" and empty_is_none:
        return None
    return value if value else default


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    root = _tk_root()
    if root is not None:
        try:
            from tkinter import messagebox

            return bool(messagebox.askyesno("Notizen", prompt, default="yes" if default else "no", parent=root))
        finally:
            root.destroy()
    suffix = "J/n" if default else "j/N"
    value = input(f"{prompt} ({suffix}): ").strip().lower()
    if not value:
        return default
    return value in {"j", "ja", "y", "yes"}
