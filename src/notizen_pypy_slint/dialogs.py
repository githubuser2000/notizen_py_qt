from __future__ import annotations

import getpass
from pathlib import Path


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


def ask_open_file(title: str = "Notizen-Datei öffnen", initial_dir: str | None = None) -> Path | None:
    root = _tk_root()
    if root is not None:
        try:
            from tkinter import filedialog

            result = filedialog.askopenfilename(
                parent=root,
                initialdir=initial_dir or str(Path.home()),
                title=title,
                filetypes=[("Notizen .alx", "*.alx"), ("XML", "*.xml"), ("Alle Dateien", "*.*")],
            )
            return Path(result) if result else None
        finally:
            root.destroy()
    value = input("Dateipfad zum Öffnen (.alx/.xml), leer = abbrechen: ").strip()
    return Path(value) if value else None


def ask_save_file(
    title: str = "Notizen-Datei speichern",
    suggested: str | None = None,
    suffix: str = ".alx",
    initial_dir: str | None = None,
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
                filetypes=[("Notizen", f"*{suffix}"), ("Alle Dateien", "*.*")],
            )
            return Path(result) if result else None
        finally:
            root.destroy()
    value = input("Dateipfad zum Speichern, leer = abbrechen: ").strip()
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


def ask_text(prompt: str, default: str = "") -> str | None:
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
    return value if value else default
