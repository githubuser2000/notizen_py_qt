from __future__ import annotations

import os
from pathlib import Path

LEGACY_DEFAULT_FILENAME = "unbenannt.alx"


def legacy_documents_notizen_dir(home: str | os.PathLike[str] | None = None) -> Path:
    """Return the old Notizen.NET default directory.

    ``Datei.vb`` used ``MyDocuments\\Notizen`` as startup directory and
    created it on construction.  The Python/Qt port keeps that convention as a
    platform-neutral ``Documents/Notizen`` path while avoiding any directory
    creation in this pure helper.
    """

    base = Path(home) if home is not None else Path.home()
    return base / "Documents" / "Notizen"


def ensure_legacy_documents_notizen_dir(home: str | os.PathLike[str] | None = None) -> Path:
    """Create and return the legacy ``Documents/Notizen`` directory if possible."""

    path = legacy_documents_notizen_dir(home)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _legacy_default_directory(default_directory: str | os.PathLike[str] | None = None) -> str:
    if default_directory is None:
        return str(legacy_documents_notizen_dir())
    value = os.fspath(default_directory).strip()
    return value if len(value) >= 2 else str(legacy_documents_notizen_dir())


def split_legacy_file_location(
    value: str | os.PathLike[str] | None,
    default_directory: str | os.PathLike[str] | None = None,
) -> tuple[str, str]:
    """Split a Notizen.NET file value into ``(directory, filename)``.

    The original VB setter split on backslashes because it ran on Windows.
    This helper accepts both Windows and POSIX separators even on non-Windows
    systems, so a legacy config entry like ``C:\\Users\\me\\Notizen\\x.alx``
    is not collapsed into a single filename on Linux/macOS.
    """

    directory = _legacy_default_directory(default_directory)
    raw = "" if value is None else os.fspath(value).strip()
    if not raw:
        return directory, LEGACY_DEFAULT_FILENAME

    # Preserve URL-like sources; ftp sync code still owns real URL parsing.
    # Only split after the final slash so ftp://host/path/file.alx remains
    # useful as an open target in recent files/configs.
    slash_index = max(raw.rfind("/"), raw.rfind("\\"))
    if slash_index >= 0:
        candidate_dir = raw[:slash_index]
        candidate_file = raw[slash_index + 1 :]
        return (candidate_dir if len(candidate_dir) >= 2 else directory), (candidate_file or LEGACY_DEFAULT_FILENAME)

    return directory, raw or LEGACY_DEFAULT_FILENAME
