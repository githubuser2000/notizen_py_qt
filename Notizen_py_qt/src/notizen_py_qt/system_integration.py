from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

LEGACY_ALX_EXTENSION = ".alx"
LEGACY_ALX_PROG_ID = "notizenfile"
LEGACY_ALX_EXTENSION_DEFAULT = "Notizenfile"
LEGACY_OPEN_WITH_EXE = "Notizen.exe"
WINDOWS_CLASSES_ROOT_USER = r"Software\Classes"


@dataclass(frozen=True, slots=True)
class WindowsRegistryEntry:
    """One registry value used by the old Notizen.NET file association.

    The VB.NET program wrote to ``HKEY_CLASSES_ROOT``.  The Python port exposes
    the same keys below ``HKCU\\Software\\Classes`` so users do not need admin
    rights and existing system-wide associations are not overwritten by merely
    starting the app.
    """

    key: str
    name: str
    value: str
    write_if_missing: bool = False

    @property
    def display_name(self) -> str:
        return "(Default)" if self.name == "" else self.name


def quote_windows_argument(value: str | os.PathLike[str]) -> str:
    """Return a Windows command-line-safe quoted argument."""

    return subprocess.list2cmdline([os.fspath(value)])


def build_windows_module_open_command(
    *,
    python_executable: str | Path | None = None,
    module: str = "notizen_py_qt",
    visible: bool = True,
    no_tray: bool = True,
    reset_window: bool = True,
) -> str:
    """Build the registry ``open`` command for ``*.alx`` files.

    Notizen.NET registered ``"Notizen.exe" "%1"``.  The source-tree Python
    equivalent is ``python -m notizen_py_qt [visible flags] "%1"``.  ``%1`` is
    deliberately quoted even though ``subprocess.list2cmdline`` would not quote
    it by default; old Windows paths often contain spaces.
    """

    executable = os.fspath(python_executable or sys.executable or "python")
    args: list[str] = [executable, "-m", module]
    if visible:
        args.append("--show")
    if no_tray:
        args.append("--no-tray")
    if reset_window:
        args.append("--reset-window")
    return subprocess.list2cmdline(args) + ' "%1"'


def build_windows_script_open_command(
    launcher: str | Path,
    *,
    visible: bool = True,
    no_tray: bool = True,
    reset_window: bool = True,
) -> str:
    """Build an ``open`` command using a checked-out ``.cmd`` launcher."""

    args: list[str] = [os.fspath(launcher)]
    if visible:
        args.append("--show")
    if no_tray:
        args.append("--no-tray")
    if reset_window:
        args.append("--reset-window")
    return subprocess.list2cmdline(args) + ' "%1"'


def legacy_windows_alx_registry_entries(
    *,
    open_command: str,
    icon_path: str | Path | None = None,
    classes_root: str = WINDOWS_CLASSES_ROOT_USER,
    prog_id: str = LEGACY_ALX_PROG_ID,
) -> tuple[WindowsRegistryEntry, ...]:
    """Return the registry values mirroring ``Notizen.Designer.vb``.

    Original VB.NET logic, simplified:

    - ``HKCR\\.alx`` default = ``Notizenfile`` only when missing.
    - ``HKCR\\.alx\\OpenWithList\\Notizen.exe`` exists.
    - ``HKCR\\.alx\\OpenWithProgIds\\notizenfile`` exists.
    - ``HKCR\\notizenfile\\Shell`` default = ``Open``.
    - ``HKCR\\notizenfile\\Shell\\Open\\Command`` always updated.
    - ``HKCR\\notizenfile\\DefaultIcon`` always updated.

    The port uses the per-user ``HKCU\\Software\\Classes`` root by default.
    """

    root = classes_root.rstrip("\\")
    extension_key = f"{root}\\{LEGACY_ALX_EXTENSION}"
    prog_key = f"{root}\\{prog_id}"
    icon = os.fspath(icon_path) if icon_path is not None else ""
    return (
        WindowsRegistryEntry(extension_key, "", LEGACY_ALX_EXTENSION_DEFAULT, write_if_missing=True),
        WindowsRegistryEntry(f"{extension_key}\\OpenWithList", "", "", write_if_missing=True),
        WindowsRegistryEntry(f"{extension_key}\\OpenWithList\\{LEGACY_OPEN_WITH_EXE}", "", "", write_if_missing=True),
        WindowsRegistryEntry(f"{extension_key}\\OpenWithProgIds", "", "", write_if_missing=True),
        WindowsRegistryEntry(f"{extension_key}\\OpenWithProgIds", prog_id, "", write_if_missing=True),
        WindowsRegistryEntry(prog_key, "", "", write_if_missing=True),
        WindowsRegistryEntry(f"{prog_key}\\Shell", "", "Open", write_if_missing=True),
        WindowsRegistryEntry(f"{prog_key}\\Shell\\Open", "", "", write_if_missing=True),
        WindowsRegistryEntry(f"{prog_key}\\Shell\\Open\\Command", "", open_command, write_if_missing=False),
        WindowsRegistryEntry(f"{prog_key}\\DefaultIcon", "", icon, write_if_missing=False),
    )


def windows_association_preview_lines(entries: Sequence[WindowsRegistryEntry]) -> tuple[str, ...]:
    """Return stable human-readable lines for logs/tests."""

    result: list[str] = []
    for entry in entries:
        mode = "if-missing" if entry.write_if_missing else "set"
        result.append(f"{mode} {entry.key} [{entry.display_name}] = {entry.value}")
    return tuple(result)


def apply_windows_registry_entries(entries: Iterable[WindowsRegistryEntry]) -> int:
    """Write the per-user Windows registry entries.

    Returns the number of values changed/created.  This is intentionally a small
    adapter around ``winreg`` so the legacy mapping remains unit-testable on
    Linux/macOS.  On non-Windows systems it raises ``RuntimeError``.
    """

    if os.name != "nt":
        raise RuntimeError("Windows-Registry-Dateizuordnung kann nur unter Windows geschrieben werden.")
    import winreg  # type: ignore[import-not-found]

    changed = 0
    for entry in entries:
        key_name = entry.key
        prefix = WINDOWS_CLASSES_ROOT_USER + "\\"
        if key_name.startswith(prefix):
            key_name = key_name[len(prefix) :]
        elif key_name == WINDOWS_CLASSES_ROOT_USER:
            key_name = ""
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, WINDOWS_CLASSES_ROOT_USER + ("\\" + key_name if key_name else "")) as key:
            if entry.write_if_missing:
                try:
                    winreg.QueryValueEx(key, entry.name)
                    continue
                except FileNotFoundError:
                    pass
            winreg.SetValueEx(key, entry.name, 0, winreg.REG_SZ, entry.value)
            changed += 1
    return changed


def build_linux_desktop_exec(
    module: str = "notizen_py_qt",
    *,
    python_executable: str | Path = "python3",
    reset_window_env: bool = True,
    visible: bool = True,
    no_tray: bool = True,
    reset_window: bool = True,
    file_placeholder: str = "%f",
) -> str:
    """Build the direct GNOME ``Exec=`` line for the Linux launcher.

    GNOME menu activation proved unreliable with shell wrappers and nested
    quoting.  The menu entry therefore starts the Python module directly and
    leaves only the reset-window environment override in front of it.
    """

    args: list[str] = ["env"]
    if reset_window_env:
        args.append("NOTIZEN_RESET_WINDOW=1")
    args.extend([os.fspath(python_executable), "-m", module])
    if visible:
        args.append("--show")
    if no_tray:
        args.append("--no-tray")
    if reset_window:
        args.append("--reset-window")
    args.append(file_placeholder)
    return " ".join(quote_windows_argument(part) if " " in part else part for part in args)
