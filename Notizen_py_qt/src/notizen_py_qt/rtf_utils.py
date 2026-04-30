from __future__ import annotations

import re

_HEX_RE = re.compile(r"\\'([0-9a-fA-F]{2})")
_UNICODE_RE = re.compile(r"\\u(-?\d+)\??")
_CONTROL_WORD_RE = re.compile(r"\\[a-zA-Z]+-?\d* ?")
_CONTROL_SYMBOL_RE = re.compile(r"\\[^a-zA-Z'{}] ?")


def _decode_hex_escapes(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return bytes([int(match.group(1), 16)]).decode("cp1252", errors="replace")

    return _HEX_RE.sub(repl, text)


def _decode_unicode_escapes(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        value = int(match.group(1))
        if value < 0:
            value += 65536
        try:
            return chr(value)
        except ValueError:
            return ""

    return _UNICODE_RE.sub(repl, text)


def rtf_to_plain_text(rtf: str) -> str:
    """Best-effort RTF-to-plain-text extraction for the editor/search path.

    This intentionally avoids a heavy dependency. It is good enough for the RTF
    emitted by the original WinForms RichTextBox and keeps the raw RTF in the
    model so no formatting is lost unless the user edits the note.
    """
    if not rtf:
        return ""
    text = rtf.replace("\r\n", "\n").replace("\r", "\n")
    text = _decode_hex_escapes(text)
    text = _decode_unicode_escapes(text)
    text = re.sub(r"\\par(?![a-zA-Z])\s*", "\n", text)
    text = re.sub(r"\\line(?![a-zA-Z])\s*", "\n", text)
    text = re.sub(r"\\tab(?![a-zA-Z]) ?", "\t", text)

    # Drop common RTF metadata groups before stripping braces.
    text = re.sub(r"\{\\fonttbl.*?\}\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\\colortbl.*?\}\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\\stylesheet.*?\}\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\\\*.*?\}\s*", "", text, flags=re.DOTALL)

    text = _CONTROL_WORD_RE.sub("", text)
    text = _CONTROL_SYMBOL_RE.sub("", text)
    text = text.replace("{", "").replace("}", "")
    text = text.replace("\\", "")
    lines = [line.rstrip() for line in text.split("\n")]
    collapsed: list[str] = []
    previous_blank = False
    for line in lines:
        blank = line == ""
        if blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = blank
    return "\n".join(collapsed).strip("\n")


def plain_text_to_rtf(text: str) -> str:
    """Create a minimal ANSI RTF document compatible with WinForms RichTextBox."""
    def esc(ch: str) -> str:
        if ch == "\\":
            return r"\\"
        if ch == "{":
            return r"\{"
        if ch == "}":
            return r"\}"
        code = ord(ch)
        if ch == "\n":
            return r"\par" + "\n"
        if code < 128:
            return ch
        # RichTextBox understands signed 16-bit \u escapes with a fallback char.
        if code > 32767:
            code -= 65536
        return f"\\u{code}?"

    body = "".join(esc(ch) for ch in text)
    if body and not body.endswith("\\par\n"):
        body += r"\par" + "\n"
    return (
        r"{\rtf1\ansi\ansicpg1252\deff0\deflang1031"
        r"{\fonttbl{\f0\fnil\fcharset0 Microsoft Sans Serif;}}"
        "\n"
        r"\viewkind4\uc1\pard\f0\fs17 "
        + body
        + "}\n"
    )
