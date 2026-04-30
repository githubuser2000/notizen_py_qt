from __future__ import annotations

import gzip
from pathlib import Path


class FeedbackError(ValueError):
    pass


def feedback_gzip_payload(text: str) -> bytes:
    """Return the legacy feedback payload without uploading it.

    The WinForms feedback dialog compressed ``Encoding.Unicode`` text before a
    hard-coded FTP upload.  ``Encoding.Unicode`` in .NET is UTF-16 little endian;
    the Python port keeps that byte format but intentionally leaves transport to
    the user instead of silently sending data to an old server.
    """

    value = text or ""
    if len(value.strip()) < 10:
        raise FeedbackError("Feedback braucht mindestens 10 Zeichen.")
    return gzip.compress(value.encode("utf-16le"))


def write_feedback_gzip(text: str, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(feedback_gzip_payload(text))
    return target


def read_feedback_gzip(path: str | Path) -> str:
    return gzip.decompress(Path(path).read_bytes()).decode("utf-16le")
