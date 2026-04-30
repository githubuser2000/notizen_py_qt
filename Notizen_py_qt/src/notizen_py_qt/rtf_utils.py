from __future__ import annotations

from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
import re
from typing import Iterable
from urllib.parse import unquote, urlparse

_HEX_RE = re.compile(r"\\'([0-9a-fA-F]{2})")
_COLOR_RE = re.compile(r"\\red(-?\d+)\\green(-?\d+)\\blue(-?\d+)")
_SKIP_DESTINATIONS = {
    "fonttbl",
    "colortbl",
    "stylesheet",
    "info",
    "pict",
    "object",
    "header",
    "footer",
    "generator",
    "datastore",
    "themedata",
    "colorschememapping",
}
_TEXT_CONTROLS = {
    "par": "\n",
    "line": "\n",
    "tab": "\t",
    "bullet": "•",
    "emdash": "—",
    "endash": "–",
    "emspace": " ",
    "enspace": " ",
    "qmspace": " ",
    "lquote": "‘",
    "rquote": "’",
    "ldblquote": "“",
    "rdblquote": "”",
}


def _decode_hex_byte(hex_text: str) -> str:
    return bytes([int(hex_text, 16)]).decode("cp1252", errors="replace")


def _signed_16_to_char(value: int) -> str:
    if value < 0:
        value += 65536
    try:
        return chr(value)
    except ValueError:
        return ""


def _combine_surrogate_pairs(text: str) -> str:
    try:
        return text.encode("utf-16", "surrogatepass").decode("utf-16")
    except UnicodeError:
        return text


def _parse_control(text: str, index: int) -> tuple[str, int | None, int, bool]:
    """Parse an RTF control word beginning at ``index`` after the backslash.

    Returns ``(word, numeric_parameter, new_index, consumed_space)``.
    """
    j = index
    while j < len(text) and text[j].isalpha():
        j += 1
    word = text[index:j]
    sign = 1
    if j < len(text) and text[j] == "-":
        sign = -1
        j += 1
    number_start = j
    while j < len(text) and text[j].isdigit():
        j += 1
    number: int | None = None
    if j > number_start:
        number = sign * int(text[number_start:j])
    consumed_space = False
    if j < len(text) and text[j] == " ":
        j += 1
        consumed_space = True
    return word, number, j, consumed_space


@dataclass(slots=True)
class _RtfStyle:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    fs_half_points: int | None = None
    fg_index: int = 0
    bg_index: int = 0

    def copy(self) -> "_RtfStyle":
        return _RtfStyle(
            bold=self.bold,
            italic=self.italic,
            underline=self.underline,
            strike=self.strike,
            fs_half_points=self.fs_half_points,
            fg_index=self.fg_index,
            bg_index=self.bg_index,
        )




@dataclass(frozen=True, slots=True)
class RtfTextStyle:
    """Resolved text style for dependency-free RTF transformations."""

    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    fs_half_points: int | None = None
    fg_color: str = ""
    bg_color: str = ""


@dataclass(frozen=True, slots=True)
class RtfTextSegment:
    """Plain text plus resolved style extracted from an RTF document."""

    text: str
    style: RtfTextStyle

@dataclass(slots=True)
class _RtfState:
    skip: bool = False
    uc: int = 1
    fallback_chars_to_skip: int = 0
    ignorable_destination: bool = False
    style: _RtfStyle | None = None

    def copy(self) -> "_RtfState":
        return _RtfState(
            skip=self.skip,
            uc=self.uc,
            fallback_chars_to_skip=self.fallback_chars_to_skip,
            ignorable_destination=self.ignorable_destination,
            style=self.style.copy() if self.style is not None else None,
        )


def _find_group(text: str, control_word: str) -> str | None:
    start = text.find("{\\" + control_word)
    if start < 0:
        return None
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        ch = text[index]
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def extract_color_table(rtf: str) -> list[str]:
    """Return RTF color-table entries as ``#rrggbb`` strings.

    Index 0 is intentionally the automatic/default color, matching RTF's
    color-table indexing. Unknown entries are represented by an empty string.
    """
    group = _find_group(rtf, "colortbl")
    if not group:
        return [""]
    # Remove group delimiters and the destination control word. Empty entries
    # are meaningful because RTF color indexes are 1-based after the first ';'.
    body = group.strip()[2:-1]
    body = re.sub(r"^colortbl\s*", "", body)
    colors: list[str] = []
    for entry in body.split(";"):
        match = _COLOR_RE.search(entry)
        if match:
            red, green, blue = (max(0, min(255, int(v))) for v in match.groups())
            colors.append(f"#{red:02x}{green:02x}{blue:02x}")
        else:
            colors.append("")
    if not colors:
        colors.append("")
    return colors


def _rtf_iter_plain(rtf: str) -> Iterable[str]:
    stack: list[_RtfState] = [_RtfState(skip=False, uc=1)]
    i = 0
    while i < len(rtf):
        state = stack[-1]
        ch = rtf[i]
        if ch == "{":
            stack.append(state.copy())
            i += 1
            continue
        if ch == "}":
            if len(stack) > 1:
                stack.pop()
            i += 1
            continue
        if ch == "\\":
            if i + 1 >= len(rtf):
                i += 1
                continue
            nxt = rtf[i + 1]
            if nxt == "*":
                stack[-1].ignorable_destination = True
                stack[-1].skip = True
                i += 2
                continue
            if nxt in "{}\\":
                i += 2
                if state.skip:
                    continue
                if state.fallback_chars_to_skip > 0:
                    state.fallback_chars_to_skip -= 1
                else:
                    yield nxt
                continue
            if nxt == "'" and i + 3 < len(rtf):
                text_ch = _decode_hex_byte(rtf[i + 2 : i + 4])
                i += 4
                if state.skip:
                    continue
                if state.fallback_chars_to_skip > 0:
                    state.fallback_chars_to_skip -= 1
                else:
                    yield text_ch
                continue
            if not nxt.isalpha():
                symbol = nxt
                i += 2
                replacement = {"~": "\xa0", "-": "", "_": "-"}.get(symbol, "")
                if replacement and not state.skip:
                    if state.fallback_chars_to_skip > 0:
                        state.fallback_chars_to_skip -= 1
                    else:
                        yield replacement
                continue
            word, number, i, _space = _parse_control(rtf, i + 1)
            state = stack[-1]
            if word in _SKIP_DESTINATIONS or state.ignorable_destination:
                state.skip = True
                continue
            if word == "uc" and number is not None:
                state.uc = max(0, number)
                continue
            if state.skip:
                continue
            if word == "u" and number is not None:
                yield _signed_16_to_char(number)
                state.fallback_chars_to_skip = state.uc
                continue
            replacement = _TEXT_CONTROLS.get(word)
            if replacement is not None:
                yield replacement
            continue
        i += 1
        if state.skip:
            continue
        if ch in "\r\n":
            continue
        if state.fallback_chars_to_skip > 0:
            state.fallback_chars_to_skip -= 1
            continue
        yield ch


def rtf_to_plain_text(rtf: str) -> str:
    """Extract readable text from WinForms/RTF content.

    The parser intentionally stays dependency-free but now handles nested RTF
    groups, Unicode fallback characters, metadata destinations, color tables and
    embedded picture groups more accurately than the earlier regex-only bridge.
    """
    if not rtf:
        return ""
    if "{\\rtf" not in rtf[:32]:
        # Some legacy imports already contain plain text or malformed fragments.
        return _HEX_RE.sub(lambda m: _decode_hex_byte(m.group(1)), rtf).replace("\r\n", "\n").replace("\r", "\n")
    text = _combine_surrogate_pairs("".join(_rtf_iter_plain(rtf))).replace("\r\n", "\n").replace("\r", "\n")
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


def _style_to_css(style: _RtfStyle, colors: list[str]) -> str:
    rules: list[str] = []
    if style.bold:
        rules.append("font-weight:700")
    if style.italic:
        rules.append("font-style:italic")
    decorations: list[str] = []
    if style.underline:
        decorations.append("underline")
    if style.strike:
        decorations.append("line-through")
    if decorations:
        rules.append("text-decoration:" + " ".join(decorations))
    if style.fs_half_points and style.fs_half_points > 0:
        rules.append(f"font-size:{style.fs_half_points / 2:g}pt")
    if 0 <= style.fg_index < len(colors) and colors[style.fg_index]:
        rules.append(f"color:{colors[style.fg_index]}")
    if 0 <= style.bg_index < len(colors) and colors[style.bg_index]:
        rules.append(f"background-color:{colors[style.bg_index]}")
    return "; ".join(rules)


def _rtf_iter_html(rtf: str) -> Iterable[tuple[str, _RtfStyle]]:
    stack: list[_RtfState] = [_RtfState(skip=False, uc=1, style=_RtfStyle())]
    i = 0
    while i < len(rtf):
        state = stack[-1]
        ch = rtf[i]
        if ch == "{":
            stack.append(state.copy())
            i += 1
            continue
        if ch == "}":
            if len(stack) > 1:
                stack.pop()
            i += 1
            continue
        if ch == "\\":
            if i + 1 >= len(rtf):
                i += 1
                continue
            nxt = rtf[i + 1]
            if nxt == "*":
                stack[-1].ignorable_destination = True
                stack[-1].skip = True
                i += 2
                continue
            if nxt in "{}\\":
                i += 2
                if not state.skip and state.style is not None:
                    if state.fallback_chars_to_skip > 0:
                        state.fallback_chars_to_skip -= 1
                    else:
                        yield nxt, state.style.copy()
                continue
            if nxt == "'" and i + 3 < len(rtf):
                text_ch = _decode_hex_byte(rtf[i + 2 : i + 4])
                i += 4
                if not state.skip and state.style is not None:
                    if state.fallback_chars_to_skip > 0:
                        state.fallback_chars_to_skip -= 1
                    else:
                        yield text_ch, state.style.copy()
                continue
            if not nxt.isalpha():
                symbol = nxt
                i += 2
                replacement = {"~": "\xa0", "-": "", "_": "-"}.get(symbol, "")
                if replacement and not state.skip and state.style is not None:
                    if state.fallback_chars_to_skip > 0:
                        state.fallback_chars_to_skip -= 1
                    else:
                        yield replacement, state.style.copy()
                continue
            word, number, i, _space = _parse_control(rtf, i + 1)
            state = stack[-1]
            style = state.style or _RtfStyle()
            if word in _SKIP_DESTINATIONS or state.ignorable_destination:
                state.skip = True
                continue
            if word == "uc" and number is not None:
                state.uc = max(0, number)
                continue
            if state.skip:
                continue
            if word == "u" and number is not None:
                yield _signed_16_to_char(number), style.copy()
                state.fallback_chars_to_skip = state.uc
                continue
            if word == "b":
                style.bold = number != 0
            elif word == "i":
                style.italic = number != 0
            elif word == "ul":
                style.underline = number != 0
            elif word in {"ulnone", "ul0"}:
                style.underline = False
            elif word == "strike":
                style.strike = number != 0
            elif word == "fs" and number is not None:
                style.fs_half_points = max(1, number)
            elif word == "cf" and number is not None:
                style.fg_index = max(0, number)
            elif word in {"highlight", "cb"} and number is not None:
                style.bg_index = max(0, number)
            elif word == "plain":
                state.style = _RtfStyle()
            else:
                replacement = _TEXT_CONTROLS.get(word)
                if replacement is not None:
                    yield replacement, style.copy()
            continue
        i += 1
        if state.skip or state.style is None:
            continue
        if ch in "\r\n":
            continue
        if state.fallback_chars_to_skip > 0:
            state.fallback_chars_to_skip -= 1
            continue
        yield ch, state.style.copy()


def _resolve_style(style: _RtfStyle, colors: list[str]) -> RtfTextStyle:
    fg = colors[style.fg_index] if 0 <= style.fg_index < len(colors) else ""
    bg = colors[style.bg_index] if 0 <= style.bg_index < len(colors) else ""
    return RtfTextStyle(
        bold=style.bold,
        italic=style.italic,
        underline=style.underline,
        strike=style.strike,
        fs_half_points=style.fs_half_points,
        fg_color=fg,
        bg_color=bg,
    )


def rtf_to_text_segments(rtf: str) -> list[RtfTextSegment]:
    """Extract styled text runs from a practical subset of RTF.

    The function is intentionally conservative and mirrors ``rtf_to_html``: it
    resolves color-table indexes and preserves the RichTextBox formatting that
    the Python/Qt port can safely roundtrip. Unsupported destinations are
    skipped by the shared parser.
    """
    if not rtf:
        return []
    if "{\\rtf" not in rtf[:32]:
        text = rtf.replace("\r\n", "\n").replace("\r", "\n")
        return [RtfTextSegment(text=_combine_surrogate_pairs(text), style=RtfTextStyle())] if text else []
    colors = extract_color_table(rtf)
    segments: list[RtfTextSegment] = []
    current_style: RtfTextStyle | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_text
        if current_style is None or not current_text:
            current_text = []
            return
        text = _combine_surrogate_pairs("".join(current_text))
        current_text = []
        if text:
            if segments and segments[-1].style == current_style:
                previous = segments[-1]
                segments[-1] = RtfTextSegment(previous.text + text, previous.style)
            else:
                segments.append(RtfTextSegment(text, current_style))

    for ch, style in _rtf_iter_html(rtf):
        resolved = _resolve_style(style, colors)
        if resolved != current_style:
            flush()
            current_style = resolved
        current_text.append(ch)
    flush()
    return segments


def rtf_to_html(rtf: str) -> str:
    """Convert a useful subset of RTF to Qt-friendly HTML.

    This preserves the common formatting used by Notizen.NET's RichTextBox:
    bold, italic, underline, strikeout, font size, foreground color and
    background/highlight color. Unsupported embedded objects are ignored rather
    than leaking raw RTF into the editor.
    """
    if not rtf:
        return ""
    if "{\\rtf" not in rtf[:32]:
        return '<html><body style="white-space: pre-wrap;">' + escape(rtf).replace("\n", "<br/>") + "</body></html>"
    colors = extract_color_table(rtf)
    out: list[str] = ['<html><body style="white-space: pre-wrap;">']
    current_css: str | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_text
        if not current_text:
            return
        text = _combine_surrogate_pairs("".join(current_text))
        current_text = []
        if current_css:
            out.append(f'<span style="{escape(current_css, quote=True)}">')
            out.append(text)
            out.append("</span>")
        else:
            out.append(text)

    for ch, style in _rtf_iter_html(rtf):
        css = _style_to_css(style, colors)
        if css != current_css:
            flush()
            current_css = css
        if ch == "\n":
            current_text.append("<br/>")
        elif ch == "\t":
            current_text.append("\t")
        else:
            current_text.append(escape(ch))
    flush()
    out.append("</body></html>")
    return "".join(out)


def _rtf_escape_text(text: str) -> str:
    parts: list[str] = []
    for ch in text:
        if ch == "\\":
            parts.append(r"\\")
        elif ch == "{":
            parts.append(r"\{")
        elif ch == "}":
            parts.append(r"\}")
        elif ch == "\n":
            parts.append(r"\par" + "\n")
        elif ch == "\t":
            parts.append(r"\tab ")
        else:
            code = ord(ch)
            if code < 128:
                parts.append(ch)
            elif code > 0xFFFF:
                encoded = ch.encode("utf-16-le", "surrogatepass")
                for offset in range(0, len(encoded), 2):
                    unit = int.from_bytes(encoded[offset : offset + 2], "little")
                    signed = unit - 65536 if unit > 32767 else unit
                    parts.append(f"\\u{signed}?")
            else:
                if code > 32767:
                    code -= 65536
                parts.append(f"\\u{code}?")
    return "".join(parts)


def plain_text_to_rtf(text: str) -> str:
    """Create a minimal RTF document compatible with WinForms RichTextBox."""
    body = _rtf_escape_text(text)
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


def _css_color(value: str) -> str | None:
    value = value.strip().lower()
    if not value or value in {"transparent", "none"}:
        return None
    if value.startswith("#"):
        if len(value) == 4:
            return "#" + "".join(ch * 2 for ch in value[1:])
        if len(value) >= 7:
            return value[:7]
    match = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", value)
    if match:
        red, green, blue = (max(0, min(255, int(v))) for v in match.groups())
        return f"#{red:02x}{green:02x}{blue:02x}"
    # Common names used by Qt and browsers. This is intentionally small.
    names = {
        "black": "#000000",
        "white": "#ffffff",
        "red": "#ff0000",
        "green": "#008000",
        "blue": "#0000ff",
        "yellow": "#ffff00",
        "cyan": "#00ffff",
        "magenta": "#ff00ff",
        "gray": "#808080",
        "grey": "#808080",
    }
    return names.get(value)


def _parse_style_attribute(style_attr: str, style: _RtfStyle, color_names: dict[str, int]) -> None:
    for chunk in style_attr.split(";"):
        if ":" not in chunk:
            continue
        key, value = chunk.split(":", 1)
        key = key.strip().lower()
        value = value.strip().lower()
        if key == "font-weight":
            style.bold = value == "bold" or (value.isdigit() and int(value) >= 600)
        elif key == "font-style":
            style.italic = "italic" in value
        elif key == "text-decoration":
            style.underline = "underline" in value
            style.strike = "line-through" in value
        elif key == "font-size":
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)", value)
            if match:
                points = float(match.group(1))
                if "px" in value:
                    points = points * 72.0 / 96.0
                style.fs_half_points = max(1, int(round(points * 2)))
        elif key in {"color", "-qt-user-state"}:
            color = _css_color(value)
            if color:
                style.fg_index = color_names.setdefault(color, len(color_names) + 1)
        elif key in {"background-color", "background"}:
            color = _css_color(value)
            if color:
                style.bg_index = color_names.setdefault(color, len(color_names) + 1)


@dataclass(slots=True)
class _HtmlSegment:
    text: str
    style: _RtfStyle


class _HtmlToSegments(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.color_names: dict[str, int] = {}
        self.stack: list[_RtfStyle] = [_RtfStyle()]
        self.segments: list[_HtmlSegment] = []
        self.skip_depth = 0

    def _push(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        style = self.stack[-1].copy()
        attr = {k.lower(): v or "" for k, v in attrs}
        if tag in {"b", "strong"}:
            style.bold = True
        elif tag in {"i", "em"}:
            style.italic = True
        elif tag == "u":
            style.underline = True
        elif tag in {"s", "strike", "del"}:
            style.strike = True
        elif tag == "font":
            color = _css_color(attr.get("color", ""))
            if color:
                style.fg_index = self.color_names.setdefault(color, len(self.color_names) + 1)
            size = attr.get("size")
            if size and size.isdigit():
                # HTML font size 3 ~= 12pt; keep it conservative.
                style.fs_half_points = max(1, int(size) * 8)
        if "style" in attr:
            _parse_style_attribute(attr["style"], style, self.color_names)
        self.stack.append(style)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"style", "script"}:
            self.skip_depth += 1
            return
        if tag == "br":
            self._append("\n")
            return
        if tag == "img":
            # Full RTF picture roundtripping is deliberately not faked. Keeping a
            # visible marker is safer than silently swallowing user data.
            self._append("[Bild]")
            return
        if tag == "li":
            self._append("• ")
        elif tag in {"p", "div"} and self._needs_paragraph_break():
            self._append("\n")
        self._push(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"style", "script"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if tag in {"br", "img"}:
            return
        if len(self.stack) > 1:
            self.stack.pop()
        if tag in {"p", "div", "li"}:
            self._append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        self._append(data)

    def _needs_paragraph_break(self) -> bool:
        return bool(self.segments and not self.segments[-1].text.endswith("\n"))

    def _append(self, text: str) -> None:
        if not text:
            return
        style = self.stack[-1].copy()
        if self.segments and self.segments[-1].style == style:
            self.segments[-1].text += text
        else:
            self.segments.append(_HtmlSegment(text, style))


def _style_prefix(style: _RtfStyle) -> str:
    parts: list[str] = []
    if style.bold:
        parts.append(r"\b")
    if style.italic:
        parts.append(r"\i")
    if style.underline:
        parts.append(r"\ul")
    if style.strike:
        parts.append(r"\strike")
    if style.fs_half_points:
        parts.append(rf"\fs{style.fs_half_points}")
    if style.fg_index:
        parts.append(rf"\cf{style.fg_index}")
    if style.bg_index:
        parts.append(rf"\highlight{style.bg_index}")
    return "".join(parts)


def _color_table_from_indexes(color_names: dict[str, int]) -> str:
    if not color_names:
        return ""
    colors_by_index = sorted(color_names.items(), key=lambda kv: kv[1])
    entries = [""]
    for color, _idx in colors_by_index:
        red = int(color[1:3], 16)
        green = int(color[3:5], 16)
        blue = int(color[5:7], 16)
        entries.append(rf"\red{red}\green{green}\blue{blue}")
    return r"{\colortbl " + ";".join(entries) + ";}" + "\n"


def html_to_rtf(html_text: str) -> str:
    """Convert Qt/HTML editor output back to a WinForms-compatible RTF subset."""
    if not html_text:
        return plain_text_to_rtf("")
    parser = _HtmlToSegments()
    parser.feed(html_text)
    parser.close()
    if not parser.segments:
        # Accept raw plain text passed by tests or future CLI helpers.
        return plain_text_to_rtf(html_text)
    color_table = _color_table_from_indexes(parser.color_names)
    body_parts: list[str] = []
    for segment in parser.segments:
        text = segment.text.replace("\r\n", "\n").replace("\r", "\n")
        if not text:
            continue
        prefix = _style_prefix(segment.style)
        escaped_text = _rtf_escape_text(text)
        if prefix:
            body_parts.append("{" + prefix + " " + escaped_text + "}")
        else:
            body_parts.append(escaped_text)
    body = "".join(body_parts).strip()
    if body and not body.endswith(r"\par"):
        body += r"\par" + "\n"
    return (
        r"{\rtf1\ansi\ansicpg1252\deff0\deflang1031"
        r"{\fonttbl{\f0\fnil\fcharset0 Microsoft Sans Serif;}}"
        "\n"
        + color_table
        + r"\viewkind4\uc1\pard\f0\fs17 "
        + body
        + "}\n"
    )
