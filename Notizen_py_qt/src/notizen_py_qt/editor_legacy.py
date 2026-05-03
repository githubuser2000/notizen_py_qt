from __future__ import annotations

LEGACY_BULLET_CHARACTER = "\u2022"


def legacy_clipboard_bullet_text() -> str:
    """Return the exact text inserted by the old ``ToolStrip_dot`` action.

    The VB.NET code copied ``Chr(13) + ChrW(8226) + "   "`` to the clipboard
    and pasted it into the RichTextBox.  Keeping the carriage return here makes
    the legacy behavior explicit and regression-testable.
    """

    return "\r" + LEGACY_BULLET_CHARACTER + "   "


def qt_bullet_insert_text() -> str:
    """Return the legacy bullet text normalized for ``QTextCursor.insertText``."""

    return legacy_clipboard_bullet_text().replace("\r\n", "\n").replace("\r", "\n")
