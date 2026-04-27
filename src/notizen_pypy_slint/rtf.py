from __future__ import annotations

import re

_HEX_RE = re.compile(r"^[0-9a-fA-F]{2}$")


def text_to_rtf(text: str, font_size_half_points: int = 18) -> str:
    """Create a small RTF document compatible with the original Notizen.NET files.

    The old application stored each node as RichTextBox.Rtf. Slint's TextEdit is
    plain text, so edited notes are written as simple but valid RTF.
    """
    text = text or ""
    body_parts: list[str] = []
    for ch in text:
        if ch == "\\":
            body_parts.append(r"\\")
        elif ch == "{":
            body_parts.append(r"\{")
        elif ch == "}":
            body_parts.append(r"\}")
        elif ch == "\n":
            body_parts.append(r"\par" + "\n")
        elif ch == "\r":
            continue
        else:
            code = ord(ch)
            if 32 <= code < 127:
                body_parts.append(ch)
            else:
                try:
                    encoded = ch.encode("cp1252")
                except UnicodeEncodeError:
                    signed = code if code <= 32767 else code - 65536
                    body_parts.append(rf"\u{signed}?")
                else:
                    body_parts.extend(rf"\'{byte:02x}" for byte in encoded)
    body = "".join(body_parts)
    return (
        r"{\rtf1\ansi\ansicpg1252\deff0"
        r"{\fonttbl{\f0\fnil\fcharset0 Sans Serif;}}"
        rf"\viewkind4\uc1\pard\f0\fs{font_size_half_points} "
        + body
        + r"\par" + "\n}"
    )


def rtf_to_text(rtf: str) -> str:
    r"""Best-effort conversion from RTF to plain text.

    It understands the constructs that Notizen.NET/RichTextBox emitted most often:
    \par, \tab, escaped braces/backslashes, CP1252 hex escapes, and \uN unicode
    escapes. Unknown formatting groups are ignored.
    """
    if not rtf:
        return ""
    stripped = rtf.lstrip()
    if not stripped.startswith("{") and "\\rtf" not in stripped[:20]:
        return rtf

    out: list[str] = []
    stack: list[bool] = []
    ignorable = False
    i = 0
    n = len(rtf)
    uc_skip = 1
    pending_unicode_skip = 0

    def current_ignorable() -> bool:
        return ignorable or any(stack)

    while i < n:
        ch = rtf[i]
        if pending_unicode_skip:
            pending_unicode_skip -= 1
            i += 1
            continue
        if ch == "{":
            # Groups such as font tables, color tables, pictures and style sheets
            # should not leak their metadata into the note text.
            group_ignorable = False
            lookahead = rtf[i + 1 : i + 40]
            if lookahead.startswith("\\*"):
                group_ignorable = True
            for prefix in ("\\fonttbl", "\\colortbl", "\\stylesheet", "\\info", "\\pict", "\\object"):
                if lookahead.startswith(prefix):
                    group_ignorable = True
                    break
            stack.append(group_ignorable)
            i += 1
            continue
        if ch == "}":
            if stack:
                stack.pop()
            i += 1
            continue
        if ch != "\\":
            if not current_ignorable():
                out.append(ch)
            i += 1
            continue

        # Control symbol or control word.
        i += 1
        if i >= n:
            break
        sym = rtf[i]
        if sym in "{}\\":
            if not current_ignorable():
                out.append(sym)
            i += 1
            continue
        if sym == "'" and i + 2 < n:
            hx = rtf[i + 1 : i + 3]
            if _HEX_RE.match(hx):
                if not current_ignorable():
                    out.append(bytes([int(hx, 16)]).decode("cp1252", errors="replace"))
                i += 3
                continue
        if not sym.isalpha():
            # Common control symbols. Treat line breaks generously.
            if not current_ignorable() and sym in "~_":
                out.append(" ")
            i += 1
            continue

        start = i
        while i < n and rtf[i].isalpha():
            i += 1
        word = rtf[start:i]
        sign = 1
        if i < n and rtf[i] in "+-":
            if rtf[i] == "-":
                sign = -1
            i += 1
        num_start = i
        while i < n and rtf[i].isdigit():
            i += 1
        arg: int | None = None
        if num_start != i:
            arg = sign * int(rtf[num_start:i])
        if i < n and rtf[i] in " \n\r":
            i += 1

        if current_ignorable():
            continue
        if word in {"par", "line"}:
            out.append("\n")
        elif word == "tab":
            out.append("\t")
        elif word == "emdash":
            out.append("—")
        elif word == "endash":
            out.append("–")
        elif word == "bullet":
            out.append("•")
        elif word == "lquote":
            out.append("‘")
        elif word == "rquote":
            out.append("’")
        elif word == "ldblquote":
            out.append("“")
        elif word == "rdblquote":
            out.append("”")
        elif word == "uc" and arg is not None:
            uc_skip = max(0, arg)
        elif word == "u" and arg is not None:
            code = arg if arg >= 0 else arg + 65536
            out.append(chr(code))
            pending_unicode_skip = uc_skip

    text = "".join(out)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip("\n")
