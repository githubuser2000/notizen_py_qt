from __future__ import annotations

import base64
import codecs
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Iterable
from urllib.parse import unquote, urlparse

_HEX_RE = re.compile(r"\\'([0-9a-fA-F]{2})")
_ANSICPG_RE = re.compile(r"\\ansicpg(\d+)")
_COLOR_RE = re.compile(r"\\red(-?\d+)\\green(-?\d+)\\blue(-?\d+)")
_DATA_IMAGE_RE = re.compile(r"^data:(image/[a-zA-Z0-9.+-]+)(?:;[^,]*)?;base64,(.*)$", re.DOTALL)
_SKIP_DESTINATIONS = {
    "fonttbl",
    "colortbl",
    "stylesheet",
    "info",
    "pict",
    "object",
    "objclass",
    "objdata",
    "header",
    "footer",
    "generator",
    "datastore",
    "themedata",
    "colorschememapping",
}

# RichTextBox/WPF list labels are often wrapped in ignorable destinations such
# as ``{\*\pntext ...}`` or ``{\*\listtext ...}``.  They look optional to a
# strict RTF reader, but they are the only readable bullet/number prefix for
# Notizen.NET exports and copied content.  Keep these groups textual instead of
# dropping them with other ``\*`` destinations.
_TEXTUAL_IGNORABLE_DESTINATIONS = {"pntext", "listtext"}
LEGACY_OBJECT_PLACEHOLDER = "[Objekt]"
_RTF_SOFT_LINE_BREAK = "\u2028"


@dataclass(frozen=True, slots=True)
class RtfImage:
    r"""Embedded image extracted from an RTF ``\pict`` group."""

    mime_type: str
    data: bytes
    width_twips: int | None = None
    height_twips: int | None = None
    rtf_control: str = ""


@dataclass(frozen=True, slots=True)
class RtfHyperlink:
    """Hyperlink extracted from an RTF ``\field`` group."""

    url: str
    text: str
    style: "RtfTextStyle | None" = None


_TEXT_CONTROLS = {
    "par": "\n",
    "line": _RTF_SOFT_LINE_BREAK,
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
    # RichTextBox tables use cell/row separators.  The Qt bridge does not try to
    # recreate table layout here, but preserving tab/newline boundaries keeps
    # pasted legacy table content readable in search, statistics and exports.
    "cell": "\t",
    "nestcell": "\t",
    "row": "\n",
}


def rtf_ansi_encoding(rtf: str) -> str:
    """Return the Python codec implied by an RTF ``\ansicpg`` header.

    Notizen.NET's WinForms RichTextBox usually wrote ``\ansicpg1252`` for
    German/English text, but older Russian/Chinese content can contain escaped
    bytes for other Windows code pages.  Falling back to cp1252 keeps malformed
    fragments readable without throwing during search/export.
    """

    match = _ANSICPG_RE.search(rtf or "")
    if not match:
        return "cp1252"
    codec = f"cp{match.group(1)}"
    try:
        codecs.lookup(codec)
    except LookupError:
        return "cp1252"
    return codec


def _decode_hex_byte(hex_text: str, encoding: str = "cp1252") -> str:
    return bytes([int(hex_text, 16)]).decode(encoding, errors="replace")


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


def _peek_ignorable_destination(text: str, backslash_index: int) -> str:
    r"""Return the control word after a ``\*`` marker, if one follows."""

    j = backslash_index + 2
    while j < len(text) and text[j].isspace():
        j += 1
    if j < len(text) and text[j] == "\\":
        word, _number, _new_index, _space = _parse_control(text, j + 1)
        return word
    return ""


def _escape_html_text_with_breaks(text: str) -> str:
    return escape(text).replace(_RTF_SOFT_LINE_BREAK, "<br/>").replace("\n", "<br/>").replace("\t", "\t")


def _rtf_escape_field_url(url: str) -> str:
    return (url or "").replace("\\", r"\\").replace('"', r'\"')


def _rtf_hyperlink_field(url: str, display_text: str, prefix: str = "") -> str:
    url = _rtf_escape_field_url(url)
    display = _rtf_escape_text(display_text or url)
    result = "{" + prefix + " " + display + "}" if prefix else display
    return r'{\field{\*\fldinst HYPERLINK "' + url + r'"}{\fldrslt ' + result + '}}'


def _extract_balanced_destination(rtf: str, index: int, destination: str) -> str | None:
    if not rtf.startswith("{\\" + destination, index):
        return None
    end = _find_group_end(rtf, index)
    return None if end < 0 else rtf[index : end + 1]


def _extract_object_at(rtf: str, index: int) -> tuple[str, int] | None:
    if not rtf.startswith(r"{\object", index):
        return None
    end = _find_group_end(rtf, index)
    if end < 0:
        return None
    return LEGACY_OBJECT_PLACEHOLDER, end + 1


def _extract_field_at(rtf: str, index: int) -> tuple[RtfHyperlink, int] | None:
    if not rtf.startswith(r"{\field", index):
        return None
    end = _find_group_end(rtf, index)
    if end < 0:
        return None
    group = rtf[index : end + 1]
    inst_match = re.search(r'HYPERLINK\s+(?:"((?:\\.|[^"\\])*)"|([^\\{}\s]+))', group, re.IGNORECASE)
    if not inst_match:
        return None
    url = (inst_match.group(1) or inst_match.group(2) or "").replace(r'\"', '"').replace(r"\\", "\\")
    result_start = group.find(r"{\fldrslt")
    display = ""
    if result_start >= 0:
        result_end = _find_group_end(group, result_start)
        if result_end >= 0:
            display = _rtf_fragment_to_plain(group[result_start : result_end + 1], rtf_ansi_encoding(group)).strip()
    if not display:
        display = url
    return RtfHyperlink(url=url, text=display), end + 1


@dataclass(slots=True)
class _RtfStyle:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    fs_half_points: int | None = None
    fg_index: int = 0
    bg_index: int = 0
    font_family: str = ""
    hyperlink_url: str = ""
    vertical: str = ""
    all_caps: bool = False
    small_caps: bool = False
    hidden: bool = False
    direction: str = ""
    letter_spacing_twips: int | None = None
    align: str = ""
    left_indent_twips: int | None = None
    right_indent_twips: int | None = None
    first_indent_twips: int | None = None
    space_before_twips: int | None = None
    space_after_twips: int | None = None
    line_spacing_twips: int | None = None
    line_spacing_multiple: bool | None = None

    def copy(self) -> "_RtfStyle":
        return _RtfStyle(
            bold=self.bold,
            italic=self.italic,
            underline=self.underline,
            strike=self.strike,
            fs_half_points=self.fs_half_points,
            fg_index=self.fg_index,
            bg_index=self.bg_index,
            font_family=self.font_family,
            hyperlink_url=self.hyperlink_url,
            vertical=self.vertical,
            all_caps=self.all_caps,
            small_caps=self.small_caps,
            hidden=self.hidden,
            direction=self.direction,
            letter_spacing_twips=self.letter_spacing_twips,
            align=self.align,
            left_indent_twips=self.left_indent_twips,
            right_indent_twips=self.right_indent_twips,
            first_indent_twips=self.first_indent_twips,
            space_before_twips=self.space_before_twips,
            space_after_twips=self.space_after_twips,
            line_spacing_twips=self.line_spacing_twips,
            line_spacing_multiple=self.line_spacing_multiple,
        )


def _reset_rtf_character_style(style: _RtfStyle) -> None:
    r"""Reset only character attributes like RichTextBox/RTF ``\plain``."""

    style.bold = False
    style.italic = False
    style.underline = False
    style.strike = False
    style.fs_half_points = None
    style.fg_index = 0
    style.bg_index = 0
    style.font_family = ""
    style.hyperlink_url = ""
    style.vertical = ""
    style.all_caps = False
    style.small_caps = False
    style.hidden = False
    style.letter_spacing_twips = None


def _reset_rtf_paragraph_style(style: _RtfStyle) -> None:
    r"""Reset paragraph attributes like RTF ``\pard`` without touching text style."""

    style.align = ""
    style.left_indent_twips = None
    style.right_indent_twips = None
    style.first_indent_twips = None
    style.space_before_twips = None
    style.space_after_twips = None
    style.line_spacing_twips = None
    style.line_spacing_multiple = None


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
    font_family: str = ""
    vertical: str = ""
    all_caps: bool = False
    small_caps: bool = False
    hidden: bool = False
    direction: str = ""
    letter_spacing_twips: int | None = None
    align: str = ""
    left_indent_twips: int | None = None
    right_indent_twips: int | None = None
    first_indent_twips: int | None = None
    space_before_twips: int | None = None
    space_after_twips: int | None = None
    line_spacing_twips: int | None = None
    line_spacing_multiple: bool | None = None


@dataclass(frozen=True, slots=True)
class RtfTextSegment:
    """Plain text plus resolved style extracted from an RTF document."""

    text: str
    style: RtfTextStyle


RtfContentPart = RtfTextSegment | RtfImage | RtfHyperlink


@dataclass(slots=True)
class _RtfState:
    skip: bool = False
    uc: int = 1
    fallback_chars_to_skip: int = 0
    ignorable_destination: bool = False
    hidden: bool = False
    style: _RtfStyle | None = None

    def copy(self) -> "_RtfState":
        return _RtfState(
            skip=self.skip,
            uc=self.uc,
            fallback_chars_to_skip=self.fallback_chars_to_skip,
            ignorable_destination=self.ignorable_destination,
            hidden=self.hidden,
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


def _find_group_end(text: str, start: int) -> int:
    """Return the inclusive end index of a balanced RTF group."""
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
                return index
    return -1


def _control_number(group: str, name: str) -> int | None:
    match = re.search(rf"\\{re.escape(name)}(-?\d+)", group)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None



def dib_to_bmp_bytes(dib: bytes) -> bytes | None:
    r"""Wrap a DIB payload from an RTF ``\dibitmap`` picture as a BMP file.

    WinForms RichTextBox commonly serializes pasted bitmap clipboard images as
    ``{\pict\dibitmap...}``. RTF stores only the DIB payload there, while HTML
    and Qt's image bridge need an ordinary BMP file header. The calculation below
    covers the BITMAPCOREHEADER and BITMAPINFOHEADER variants used by old
    RichTextBox content and degrades safely for uncommon headers.
    """
    if not dib:
        return None
    if dib.startswith(b"BM"):
        return dib
    if len(dib) < 4:
        return None
    header_size = int.from_bytes(dib[:4], "little", signed=False)
    if header_size < 12 or header_size > len(dib):
        return None

    palette_size = 0
    if header_size == 12:  # BITMAPCOREHEADER, RGBTRIPLE palette entries.
        if len(dib) < 12:
            return None
        bit_count = int.from_bytes(dib[10:12], "little", signed=False)
        if 0 < bit_count <= 8:
            palette_size = (1 << bit_count) * 3
    else:  # BITMAPINFOHEADER and later, RGBQUAD palette entries.
        bit_count = int.from_bytes(dib[14:16], "little", signed=False) if len(dib) >= 16 else 0
        compression = int.from_bytes(dib[16:20], "little", signed=False) if len(dib) >= 20 else 0
        colors_used = int.from_bytes(dib[32:36], "little", signed=False) if len(dib) >= 36 else 0
        if colors_used:
            palette_size = colors_used * 4
        elif 0 < bit_count <= 8:
            palette_size = (1 << bit_count) * 4
        if compression == 3 and header_size == 40 and bit_count in {16, 32}:
            # BI_BITFIELDS masks are stored directly after a 40-byte header.
            palette_size += 12

    pixel_offset = 14 + min(len(dib), header_size + palette_size)
    file_size = 14 + len(dib)
    return b"BM" + file_size.to_bytes(4, "little") + b"\x00\x00\x00\x00" + pixel_offset.to_bytes(4, "little") + dib


def bmp_to_dib_bytes(data: bytes) -> bytes:
    r"""Return the DIB payload used by RTF ``\dibitmap`` from BMP-like bytes."""
    if len(data) >= 14 and data.startswith(b"BM"):
        return data[14:]
    return data


def _parse_pict_group(group: str) -> RtfImage | None:
    r"""Parse a practical WinForms/Qt-compatible RTF picture group.

    Notizen.NET inserted images through a WinForms RichTextBox. PNG/JPEG RTF
    pictures were already handled by the port; 0.10.9 also accepts legacy
    ``\dibitmap``/``\wbitmap`` payloads so old BMP clipboard pictures survive
    HTML display, search-independent tree summaries and combined RTF export.
    Binary ``\bin`` picture payloads are intentionally still ignored.
    """
    mime_type = ""
    rtf_control = ""
    wants_bmp_wrap = False
    if "\\pngblip" in group:
        mime_type = "image/png"
        rtf_control = "pngblip"
    elif "\\jpegblip" in group or "\\jpgblip" in group:
        mime_type = "image/jpeg"
        rtf_control = "jpegblip"
    elif "\\dibitmap" in group or "\\wbitmap" in group:
        mime_type = "image/bmp"
        rtf_control = "dibitmap0"
        wants_bmp_wrap = True
    elif "\\emfblip" in group:
        mime_type = "image/x-emf"
        rtf_control = "emfblip"
    else:
        wmf = re.search(r"\\wmetafile(-?\d+)?", group)
        if wmf:
            mime_type = "image/wmf"
            rtf_control = "wmetafile" + (wmf.group(1) or "8")
        else:
            return None

    scrubbed = re.sub(r"\\'[0-9a-fA-F]{2}", " ", group)
    scrubbed = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", scrubbed)
    hex_text = re.sub(r"[^0-9a-fA-F]", "", scrubbed)
    if len(hex_text) % 2:
        hex_text = hex_text[:-1]
    if not hex_text:
        return None
    try:
        data = bytes.fromhex(hex_text)
    except ValueError:
        return None
    if wants_bmp_wrap:
        wrapped = dib_to_bmp_bytes(data)
        if wrapped is None:
            return None
        data = wrapped
    return RtfImage(
        mime_type=mime_type,
        data=data,
        width_twips=_control_number(group, "picwgoal"),
        height_twips=_control_number(group, "pichgoal"),
        rtf_control=rtf_control,
    )


def _extract_pict_at(rtf: str, index: int) -> tuple[RtfImage, int] | None:
    """Return ``(image, next_index)`` if an RTF image group starts here."""
    if not (
        rtf.startswith(r"{\pict", index)
        or rtf.startswith(r"{\*\shppict", index)
        or rtf.startswith(r"{\nonshppict", index)
    ):
        return None
    end = _find_group_end(rtf, index)
    if end < 0:
        return None
    group = rtf[index : end + 1]
    pict_group = group
    if not group.startswith(r"{\pict"):
        inner_start = group.find(r"{\pict")
        if inner_start < 0:
            return None
        inner_end = _find_group_end(group, inner_start)
        if inner_end < 0:
            return None
        pict_group = group[inner_start : inner_end + 1]
    image = _parse_pict_group(pict_group)
    if image is None:
        return None
    return image, end + 1


def _image_to_html(image: RtfImage) -> str:
    data = base64.b64encode(image.data).decode("ascii")
    attrs = [f'src="data:{image.mime_type};base64,{data}"']
    if image.width_twips and image.width_twips > 0:
        attrs.append(f'width="{max(1, round(image.width_twips / 15))}"')
    if image.height_twips and image.height_twips > 0:
        attrs.append(f'height="{max(1, round(image.height_twips / 15))}"')
    return "<img " + " ".join(attrs) + "/>"


def _clean_font_name(raw: str, encoding: str = "cp1252") -> str:
    raw = _HEX_RE.sub(lambda m: _decode_hex_byte(m.group(1), encoding), raw)
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", raw)
    raw = re.sub(r"\\.", " ", raw)
    raw = raw.replace(";", " ").replace("{", " ").replace("}", " ")
    return " ".join(raw.split())


def _strip_font_alias_groups(raw: str) -> str:
    """Remove nested font-table alias/fallback groups before cleaning a name."""

    raw = re.sub(r"\{\\\*\\falt[^{};]*;\}", " ", raw)
    return re.sub(r"\{[^{}]*\}", " ", raw)


def extract_font_table(rtf: str) -> list[str]:
    r"""Return RTF font-table names by ``\fN`` index.

    WordPad/Word and some clipboard paths put fallback aliases inside the font
    entry, for example ``{\f1 ... Times New Roman{\*\falt Times};}``.  A flat
    regex drops these entries.  This parser walks balanced font groups instead.
    """

    encoding = rtf_ansi_encoding(rtf)
    group = _find_group(rtf, "fonttbl")
    fonts = [""]
    if not group:
        return fonts
    pos = 0
    while True:
        match = re.search(r"\{\\f(\d+)\b", group[pos:])
        if not match:
            break
        start = pos + match.start()
        end = _find_group_end(group, start)
        if end < 0:
            pos = start + 1
            continue
        chunk = group[start : end + 1]
        pos = end + 1
        try:
            index = int(match.group(1))
        except ValueError:
            continue
        body = re.sub(r"^\{\\f\d+\b", "", chunk)
        semi = body.rfind(";")
        if semi >= 0:
            body = body[:semi]
        name = _clean_font_name(_strip_font_alias_groups(body), encoding)
        if not name:
            continue
        while len(fonts) <= index:
            fonts.append("")
        fonts[index] = name
    return fonts


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
    entries = body.split(";")
    # Some imported RTF omits the leading automatic-color slot.  RichTextBox
    # writes it, so add it when the first entry already contains a color.
    if entries and _COLOR_RE.search(entries[0]):
        entries.insert(0, "")
    colors: list[str] = []
    for entry in entries:
        match = _COLOR_RE.search(entry)
        if match:
            red, green, blue = (max(0, min(255, int(v))) for v in match.groups())
            colors.append(f"#{red:02x}{green:02x}{blue:02x}")
        else:
            colors.append("")
    if not colors:
        colors.append("")
    return colors


def _rtf_iter_plain(rtf: str, encoding: str = "cp1252") -> Iterable[str]:
    stack: list[_RtfState] = [_RtfState(skip=False, uc=1)]
    i = 0
    while i < len(rtf):
        state = stack[-1]
        ch = rtf[i]
        if ch == "{":
            field_result = _extract_field_at(rtf, i)
            if field_result is not None and not state.skip and not state.hidden:
                hyperlink, i = field_result
                yield hyperlink.text
                continue
            object_result = _extract_object_at(rtf, i)
            if object_result is not None:
                placeholder, i = object_result
                if not state.skip and not state.hidden:
                    yield placeholder
                continue
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
                destination = _peek_ignorable_destination(rtf, i)
                if destination in _TEXTUAL_IGNORABLE_DESTINATIONS:
                    stack[-1].ignorable_destination = False
                    stack[-1].skip = False
                else:
                    stack[-1].ignorable_destination = True
                    stack[-1].skip = True
                i += 2
                continue
            if nxt in "{}\\":
                i += 2
                if state.skip or state.hidden:
                    continue
                if state.fallback_chars_to_skip > 0:
                    state.fallback_chars_to_skip -= 1
                else:
                    yield nxt
                continue
            if nxt == "'" and i + 3 < len(rtf):
                text_ch = _decode_hex_byte(rtf[i + 2 : i + 4], encoding)
                i += 4
                if state.skip or state.hidden:
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
                if replacement and not state.skip and not state.hidden:
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
            if word == "v":
                state.hidden = number != 0
                continue
            if word == "plain":
                state.hidden = False
                continue
            if word == "u" and number is not None:
                if not state.hidden:
                    yield _signed_16_to_char(number)
                state.fallback_chars_to_skip = state.uc
                continue
            if state.hidden:
                continue
            replacement = _TEXT_CONTROLS.get(word)
            if replacement is not None:
                yield replacement
            continue
        i += 1
        if state.skip or state.hidden:
            continue
        if ch in "\r\n":
            continue
        if state.fallback_chars_to_skip > 0:
            state.fallback_chars_to_skip -= 1
            continue
        yield ch


def _rtf_fragment_to_plain(fragment: str, encoding: str = "cp1252") -> str:
    text = _combine_surrogate_pairs("".join(_rtf_iter_plain(fragment, encoding))).replace(_RTF_SOFT_LINE_BREAK, "\n").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n"))


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
        encoding = rtf_ansi_encoding(rtf)
        return _HEX_RE.sub(lambda m: _decode_hex_byte(m.group(1), encoding), rtf).replace(_RTF_SOFT_LINE_BREAK, "\n").replace("\r\n", "\n").replace("\r", "\n")
    encoding = rtf_ansi_encoding(rtf)
    text = _combine_surrogate_pairs("".join(_rtf_iter_plain(rtf, encoding))).replace(_RTF_SOFT_LINE_BREAK, "\n").replace("\r\n", "\n").replace("\r", "\n")
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


def _inline_style_to_css(style: _RtfStyle, colors: list[str]) -> str:
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
    if style.font_family:
        family = style.font_family.replace("\\", "\\\\").replace('"', r'\"')
        rules.append(f'font-family:"{family}"')
    if style.vertical in {"super", "sub"}:
        rules.append(f"vertical-align:{style.vertical}")
    if style.all_caps:
        rules.append("text-transform:uppercase")
    if style.small_caps:
        rules.append("font-variant:small-caps")
    if style.hidden:
        rules.append("display:none")
    if style.direction in {"rtl", "ltr"}:
        rules.append(f"direction:{style.direction}")
        rules.append("unicode-bidi:embed")
    if style.letter_spacing_twips is not None:
        rules.append(f"letter-spacing:{style.letter_spacing_twips / 20:g}pt")
    if 0 <= style.fg_index < len(colors) and colors[style.fg_index]:
        rules.append(f"color:{colors[style.fg_index]}")
    if 0 <= style.bg_index < len(colors) and colors[style.bg_index]:
        rules.append(f"background-color:{colors[style.bg_index]}")
    return "; ".join(rules)


def _paragraph_style_to_css(style: _RtfStyle | None) -> str:
    if style is None:
        return ""
    rules: list[str] = []
    if style.align in {"left", "center", "right", "justify"}:
        rules.append(f"text-align:{style.align}")
    if style.direction in {"rtl", "ltr"}:
        rules.append(f"direction:{style.direction}")
    if style.left_indent_twips is not None:
        rules.append(f"margin-left:{style.left_indent_twips / 20:g}pt")
    if style.right_indent_twips is not None:
        rules.append(f"margin-right:{style.right_indent_twips / 20:g}pt")
    if style.first_indent_twips is not None:
        rules.append(f"text-indent:{style.first_indent_twips / 20:g}pt")
    if style.space_before_twips is not None:
        rules.append(f"margin-top:{style.space_before_twips / 20:g}pt")
    if style.space_after_twips is not None:
        rules.append(f"margin-bottom:{style.space_after_twips / 20:g}pt")
    if style.line_spacing_twips is not None and style.line_spacing_twips > 0:
        if style.line_spacing_multiple:
            rules.append(f"line-height:{style.line_spacing_twips / 240:g}")
        else:
            rules.append(f"line-height:{style.line_spacing_twips / 20:g}pt")
    return "; ".join(rules)


def _style_to_css(style: _RtfStyle, colors: list[str]) -> str:
    """Return combined CSS for callers/tests that do not distinguish blocks."""

    rules = [chunk for chunk in (_inline_style_to_css(style, colors), _paragraph_style_to_css(style)) if chunk]
    return "; ".join(rules)


def _rtf_iter_html_tokens(rtf: str, encoding: str = "cp1252") -> Iterable[tuple[str | RtfImage | RtfHyperlink, _RtfStyle]]:
    fonts = extract_font_table(rtf)
    stack: list[_RtfState] = [_RtfState(skip=False, uc=1, style=_RtfStyle())]
    i = 0
    while i < len(rtf):
        state = stack[-1]
        ch = rtf[i]
        if ch == "{":
            image_result = _extract_pict_at(rtf, i)
            if image_result is not None and not state.skip and state.style is not None:
                image, i = image_result
                yield image, state.style.copy()
                continue
            field_result = _extract_field_at(rtf, i)
            if field_result is not None and not state.skip and state.style is not None:
                hyperlink, i = field_result
                yield hyperlink, state.style.copy()
                continue
            object_result = _extract_object_at(rtf, i)
            if object_result is not None:
                placeholder, i = object_result
                if not state.skip and state.style is not None:
                    yield placeholder, state.style.copy()
                continue
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
                destination = _peek_ignorable_destination(rtf, i)
                if destination in _TEXTUAL_IGNORABLE_DESTINATIONS:
                    stack[-1].ignorable_destination = False
                    stack[-1].skip = False
                else:
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
                text_ch = _decode_hex_byte(rtf[i + 2 : i + 4], encoding)
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
            elif word in {
                "ul",
                "ulw",
                "uldb",
                "uld",
                "uldash",
                "uldashd",
                "uldashdd",
                "ulth",
                "ulthd",
                "ulthdash",
                "ulthdashd",
                "ulthdashdd",
                "ulwave",
                "ululdbwave",
                "ulhwave",
                "ulhair",
            }:
                style.underline = number != 0
            elif word in {"ulnone", "ul0"}:
                style.underline = False
            elif word in {"strike", "striked", "strikedl"}:
                style.strike = number != 0
            elif word in {"strike0", "striked0"}:
                style.strike = False
            elif word == "super":
                style.vertical = "" if number == 0 else "super"
            elif word == "sub":
                style.vertical = "" if number == 0 else "sub"
            elif word in {"up", "dn"}:
                if number == 0:
                    style.vertical = ""
                else:
                    style.vertical = "super" if word == "up" else "sub"
            elif word == "nosupersub":
                style.vertical = ""
            elif word == "caps":
                style.all_caps = number != 0
            elif word == "scaps":
                style.small_caps = number != 0
            elif word == "v":
                style.hidden = number != 0
            elif word in {"rtlch", "rtlpar"}:
                style.direction = "rtl"
            elif word in {"ltrch", "ltrpar"}:
                style.direction = "ltr"
            elif word == "expndtw" and number is not None:
                style.letter_spacing_twips = number
            elif word == "expnd" and number is not None:
                style.letter_spacing_twips = number * 5
            elif word == "fs" and number is not None:
                style.fs_half_points = max(1, number)
            elif word == "f" and number is not None:
                style.font_family = fonts[number] if 0 <= number < len(fonts) else ""
            elif word == "cf" and number is not None:
                style.fg_index = max(0, number)
            elif word in {"highlight", "cb", "cbpat", "chcbpat"} and number is not None:
                style.bg_index = max(0, number)
            elif word in {"ql", "qc", "qr", "qj"}:
                style.align = {"ql": "left", "qc": "center", "qr": "right", "qj": "justify"}[word]
            elif word == "li" and number is not None:
                style.left_indent_twips = number
            elif word == "ri" and number is not None:
                style.right_indent_twips = number
            elif word == "fi" and number is not None:
                style.first_indent_twips = number
            elif word == "sb" and number is not None:
                style.space_before_twips = max(0, number)
            elif word == "sa" and number is not None:
                style.space_after_twips = max(0, number)
            elif word == "sl" and number is not None:
                style.line_spacing_twips = abs(number)
            elif word == "slmult" and number is not None:
                style.line_spacing_multiple = bool(number)
            elif word == "pard":
                _reset_rtf_paragraph_style(style)
            elif word == "plain":
                _reset_rtf_character_style(style)
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


def _rtf_iter_html(rtf: str, encoding: str = "cp1252") -> Iterable[tuple[str, _RtfStyle]]:
    for token, style in _rtf_iter_html_tokens(rtf, encoding):
        if isinstance(token, str):
            yield token, style


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
        font_family=style.font_family,
        vertical=style.vertical,
        all_caps=style.all_caps,
        small_caps=style.small_caps,
        hidden=style.hidden,
        direction=style.direction,
        letter_spacing_twips=style.letter_spacing_twips,
        align=style.align,
        left_indent_twips=style.left_indent_twips,
        right_indent_twips=style.right_indent_twips,
        first_indent_twips=style.first_indent_twips,
        space_before_twips=style.space_before_twips,
        space_after_twips=style.space_after_twips,
        line_spacing_twips=style.line_spacing_twips,
        line_spacing_multiple=style.line_spacing_multiple,
    )


def _text_style_with_underline(style: RtfTextStyle) -> RtfTextStyle:
    """Return ``style`` with RichTextBox hyperlink underline applied."""

    return RtfTextStyle(
        bold=style.bold,
        italic=style.italic,
        underline=True,
        strike=style.strike,
        fs_half_points=style.fs_half_points,
        fg_color=style.fg_color,
        bg_color=style.bg_color,
        font_family=style.font_family,
        vertical=style.vertical,
        all_caps=style.all_caps,
        small_caps=style.small_caps,
        hidden=style.hidden,
        direction=style.direction,
        letter_spacing_twips=style.letter_spacing_twips,
        align=style.align,
        left_indent_twips=style.left_indent_twips,
        right_indent_twips=style.right_indent_twips,
        first_indent_twips=style.first_indent_twips,
        space_before_twips=style.space_before_twips,
        space_after_twips=style.space_after_twips,
        line_spacing_twips=style.line_spacing_twips,
        line_spacing_multiple=style.line_spacing_multiple,
    )


def rtf_to_content_parts(rtf: str) -> list[RtfContentPart]:
    """Extract ordered text and image parts from a practical subset of RTF.

    This is the dependency-free equivalent of what the old WinForms
    ``fasse_zusammen`` workflow did with a temporary RichTextBox: preserve the
    order of styled text and embedded pictures instead of reducing everything to
    plain text. Unsupported RTF destinations are still skipped by the shared
    parser.
    """
    if not rtf:
        return []
    if "{\\rtf" not in rtf[:32]:
        text = rtf.replace("\r\n", "\n").replace("\r", "\n")
        return [RtfTextSegment(text=_combine_surrogate_pairs(text), style=RtfTextStyle())] if text else []

    colors = extract_color_table(rtf)
    parts: list[RtfContentPart] = []
    current_style: RtfTextStyle | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_text
        if current_style is None or not current_text:
            current_text = []
            return
        text = _combine_surrogate_pairs("".join(current_text)).replace(_RTF_SOFT_LINE_BREAK, "\n")
        current_text = []
        if not text:
            return
        if parts and isinstance(parts[-1], RtfTextSegment) and parts[-1].style == current_style:
            previous = parts[-1]
            parts[-1] = RtfTextSegment(previous.text + text, previous.style)
        else:
            parts.append(RtfTextSegment(text, current_style))

    for token, style in _rtf_iter_html_tokens(rtf, rtf_ansi_encoding(rtf)):
        if isinstance(token, RtfImage):
            flush()
            parts.append(token)
            current_style = None
            continue
        resolved = _resolve_style(style, colors)
        if isinstance(token, RtfHyperlink):
            flush()
            link_style = resolved if resolved.underline else _text_style_with_underline(resolved)
            parts.append(RtfHyperlink(url=token.url, text=token.text, style=link_style))
            current_style = None
            continue
        if resolved != current_style:
            flush()
            current_style = resolved
        current_text.append(token)
    flush()
    return parts


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
        text = _combine_surrogate_pairs("".join(current_text)).replace(_RTF_SOFT_LINE_BREAK, "\n")
        current_text = []
        if text:
            if segments and segments[-1].style == current_style:
                previous = segments[-1]
                segments[-1] = RtfTextSegment(previous.text + text, previous.style)
            else:
                segments.append(RtfTextSegment(text, current_style))

    for token, style in _rtf_iter_html_tokens(rtf, rtf_ansi_encoding(rtf)):
        if isinstance(token, RtfImage):
            flush()
            current_style = None
            continue
        resolved = _resolve_style(style, colors)
        text = token.text if isinstance(token, RtfHyperlink) else token
        if isinstance(token, RtfHyperlink) and not resolved.underline:
            resolved = _text_style_with_underline(resolved)
        if resolved != current_style:
            flush()
            current_style = resolved
        current_text.append(text)
    flush()
    return segments


def rtf_to_html(rtf: str) -> str:
    """Convert a useful subset of RTF to Qt-friendly HTML.

    This preserves the common formatting used by Notizen.NET's RichTextBox:
    bold, italic, underline, strikeout, font size, font family, foreground and
    highlight colors, embedded images, hyperlinks and paragraph-level alignment
    and indents. Paragraph controls are emitted on ``<p>`` elements rather than
    only on inline spans, because QTextEdit and most window-manager previews
    ignore text alignment on a plain ``<span>``.
    """
    if not rtf:
        return ""
    if "{\\rtf" not in rtf[:32]:
        return '<html><body style="white-space: pre-wrap; margin:0;">' + escape(rtf).replace("\n", "<br/>") + "</body></html>"

    colors = extract_color_table(rtf)
    out: list[str] = ['<html><body style="white-space: pre-wrap; margin:0;">']
    paragraph_parts: list[str] = []
    current_paragraph_style: _RtfStyle | None = None
    current_inline_css: str | None = None
    current_text: list[str] = []

    def ensure_paragraph(style: _RtfStyle) -> None:
        nonlocal current_paragraph_style
        if current_paragraph_style is None:
            current_paragraph_style = style.copy()

    def flush_text() -> None:
        nonlocal current_text
        if not current_text:
            return
        text = _combine_surrogate_pairs("".join(current_text)).replace(_RTF_SOFT_LINE_BREAK, "\n")
        current_text = []
        if current_inline_css:
            paragraph_parts.append(f'<span style="{escape(current_inline_css, quote=True)}">')
            paragraph_parts.append(text)
            paragraph_parts.append("</span>")
        else:
            paragraph_parts.append(text)

    def finish_paragraph(style: _RtfStyle | None = None) -> None:
        nonlocal current_paragraph_style, current_inline_css, paragraph_parts
        if current_paragraph_style is None and style is not None:
            current_paragraph_style = style.copy()
        flush_text()
        # RichTextBox paragraphs do not have the browser/Qt HTML default top and
        # bottom margins.  Keep explicit RTF spacing (\sb/\sa), but force zero
        # margins when the source did not ask for paragraph spacing.
        paragraph_css_parts: list[str] = []
        if current_paragraph_style is None or current_paragraph_style.space_before_twips is None:
            paragraph_css_parts.append("margin-top:0")
        if current_paragraph_style is None or current_paragraph_style.space_after_twips is None:
            paragraph_css_parts.append("margin-bottom:0")
        paragraph_css = _paragraph_style_to_css(current_paragraph_style)
        if paragraph_css:
            paragraph_css_parts.append(paragraph_css)
        out.append(f'<p style="{escape("; ".join(paragraph_css_parts), quote=True)}">')
        if paragraph_parts:
            out.extend(paragraph_parts)
        else:
            out.append("<br/>")
        out.append("</p>")
        paragraph_parts = []
        current_paragraph_style = None
        current_inline_css = None

    for token, style in _rtf_iter_html_tokens(rtf, rtf_ansi_encoding(rtf)):
        if isinstance(token, RtfImage):
            ensure_paragraph(style)
            flush_text()
            paragraph_parts.append(_image_to_html(token))
            current_inline_css = None
            continue
        if isinstance(token, RtfHyperlink):
            ensure_paragraph(style)
            flush_text()
            css = _inline_style_to_css(style, colors)
            if "text-decoration" not in css:
                css = (css + "; " if css else "") + "text-decoration:underline"
            href = escape(token.url, quote=True)
            style_attr = f' style="{escape(css, quote=True)}"' if css else ""
            paragraph_parts.append(f'<a href="{href}"{style_attr}>')
            paragraph_parts.append(_escape_html_text_with_breaks(token.text))
            paragraph_parts.append("</a>")
            current_inline_css = None
            continue

        ch = token
        if ch == "\n":
            finish_paragraph(style)
            continue
        if ch == _RTF_SOFT_LINE_BREAK:
            ensure_paragraph(style)
            flush_text()
            paragraph_parts.append("<br/>")
            current_inline_css = None
            continue
        ensure_paragraph(style)
        css = _inline_style_to_css(style, colors)
        if css != current_inline_css:
            flush_text()
            current_inline_css = css
        if ch == "\t":
            current_text.append("\t")
        else:
            current_text.append(escape(ch))

    if current_text or paragraph_parts or current_paragraph_style is not None:
        finish_paragraph()
    elif len(out) == 1:
        out.append("<p><br/></p>")
    out.append("</body></html>")
    return "".join(out)

def _rtf_escape_text(text: str) -> str:
    parts: list[str] = []
    for ch in text:
        if ch == _RTF_SOFT_LINE_BREAK:
            parts.append(r"\line ")
        elif ch == "\\":
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


_CSS_NAMED_COLORS = {
    "black": "#000000", "silver": "#c0c0c0", "gray": "#808080", "grey": "#808080",
    "white": "#ffffff", "maroon": "#800000", "red": "#ff0000", "purple": "#800080",
    "fuchsia": "#ff00ff", "magenta": "#ff00ff", "green": "#008000", "lime": "#00ff00",
    "olive": "#808000", "yellow": "#ffff00", "navy": "#000080", "blue": "#0000ff",
    "teal": "#008080", "aqua": "#00ffff", "cyan": "#00ffff", "orange": "#ffa500",
    "aliceblue": "#f0f8ff", "antiquewhite": "#faebd7", "aquamarine": "#7fffd4",
    "azure": "#f0ffff", "beige": "#f5f5dc", "bisque": "#ffe4c4",
    "blanchedalmond": "#ffebcd", "blueviolet": "#8a2be2", "brown": "#a52a2a",
    "burlywood": "#deb887", "cadetblue": "#5f9ea0", "chartreuse": "#7fff00",
    "chocolate": "#d2691e", "coral": "#ff7f50", "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc", "crimson": "#dc143c", "darkblue": "#00008b",
    "darkcyan": "#008b8b", "darkgoldenrod": "#b8860b", "darkgray": "#a9a9a9",
    "darkgreen": "#006400", "darkgrey": "#a9a9a9", "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b", "darkolivegreen": "#556b2f", "darkorange": "#ff8c00",
    "darkorchid": "#9932cc", "darkred": "#8b0000", "darksalmon": "#e9967a",
    "darkseagreen": "#8fbc8f", "darkslateblue": "#483d8b", "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f", "darkturquoise": "#00ced1", "darkviolet": "#9400d3",
    "deeppink": "#ff1493", "deepskyblue": "#00bfff", "dimgray": "#696969",
    "dimgrey": "#696969", "dodgerblue": "#1e90ff", "firebrick": "#b22222",
    "floralwhite": "#fffaf0", "forestgreen": "#228b22", "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff", "gold": "#ffd700", "goldenrod": "#daa520",
    "greenyellow": "#adff2f", "honeydew": "#f0fff0", "hotpink": "#ff69b4",
    "indianred": "#cd5c5c", "indigo": "#4b0082", "ivory": "#fffff0",
    "khaki": "#f0e68c", "lavender": "#e6e6fa", "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00", "lemonchiffon": "#fffacd", "lightblue": "#add8e6",
    "lightcoral": "#f08080", "lightcyan": "#e0ffff", "lightgoldenrodyellow": "#fafad2",
    "lightgray": "#d3d3d3", "lightgreen": "#90ee90", "lightgrey": "#d3d3d3",
    "lightpink": "#ffb6c1", "lightsalmon": "#ffa07a", "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa", "lightslategray": "#778899", "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de", "lightyellow": "#ffffe0", "limegreen": "#32cd32",
    "linen": "#faf0e6", "mediumaquamarine": "#66cdaa", "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3", "mediumpurple": "#9370db", "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee", "mediumspringgreen": "#00fa9a", "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585", "midnightblue": "#191970", "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1", "moccasin": "#ffe4b5", "navajowhite": "#ffdead",
    "oldlace": "#fdf5e6", "olivedrab": "#6b8e23", "orangered": "#ff4500",
    "orchid": "#da70d6", "palegoldenrod": "#eee8aa", "palegreen": "#98fb98",
    "paleturquoise": "#afeeee", "palevioletred": "#db7093", "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9", "peru": "#cd853f", "pink": "#ffc0cb",
    "plum": "#dda0dd", "powderblue": "#b0e0e6", "rebeccapurple": "#663399",
    "rosybrown": "#bc8f8f", "royalblue": "#4169e1", "saddlebrown": "#8b4513",
    "salmon": "#fa8072", "sandybrown": "#f4a460", "seagreen": "#2e8b57",
    "seashell": "#fff5ee", "sienna": "#a0522d", "skyblue": "#87ceeb",
    "slateblue": "#6a5acd", "slategray": "#708090", "slategrey": "#708090",
    "snow": "#fffafa", "springgreen": "#00ff7f", "steelblue": "#4682b4",
    "tan": "#d2b48c", "thistle": "#d8bfd8", "tomato": "#ff6347",
    "turquoise": "#40e0d0", "violet": "#ee82ee", "wheat": "#f5deb3",
    "whitesmoke": "#f5f5f5", "yellowgreen": "#9acd32",
}


def _css_channel_to_byte(value: str) -> int:
    value = value.strip()
    if value.endswith("%"):
        return max(0, min(255, int(round(float(value[:-1]) * 255.0 / 100.0))))
    return max(0, min(255, int(float(value))))


def _css_color(value: str) -> str | None:
    value = value.strip().lower()
    if not value or value in {"transparent", "none", "inherit", "initial", "unset"}:
        return None
    if value.startswith("#"):
        hex_value = re.sub(r"[^0-9a-f]", "", value[1:])
        if len(hex_value) == 3:
            return "#" + "".join(ch * 2 for ch in hex_value)
        if len(hex_value) == 6:
            return "#" + hex_value
        if len(hex_value) >= 8:
            # Qt may emit #AARRGGBB; RTF has no alpha, so keep the visible RGB part.
            return "#" + hex_value[-6:]
    rgb = re.search(
        r"rgba?\(\s*([0-9]+(?:\.[0-9]+)?%?)\s*,\s*([0-9]+(?:\.[0-9]+)?%?)\s*,\s*([0-9]+(?:\.[0-9]+)?%?)",
        value,
    )
    if rgb:
        red, green, blue = (_css_channel_to_byte(v) for v in rgb.groups())
        return f"#{red:02x}{green:02x}{blue:02x}"
    hex_match = re.search(r"#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})\b", value)
    if hex_match:
        return _css_color("#" + hex_match.group(1))
    for token in re.split(r"[\s,]+", value):
        if token in _CSS_NAMED_COLORS:
            return _CSS_NAMED_COLORS[token]
    return _CSS_NAMED_COLORS.get(value)


def _css_font_family(value: str) -> str:
    if not value:
        return ""
    # Qt HTML usually writes a comma-separated CSS family list. Notizen.NET
    # stored one selected FontFamily at a time, so the first usable entry is the
    # closest representation.
    first = value.split(",", 1)[0].strip().strip('"\'')
    first = re.sub(r"\s+", " ", first)
    return first[:128]


def _set_color_index(color: str | None, color_names: dict[str, int], style: _RtfStyle, *, background: bool) -> None:
    if not color:
        return
    index = color_names.setdefault(color, len(color_names) + 1)
    if background:
        style.bg_index = index
    else:
        style.fg_index = index


def _css_box_values(value: str) -> tuple[str, str, str, str] | None:
    parts = [part for part in value.replace(",", " ").split() if part]
    if not parts:
        return None
    if len(parts) == 1:
        top = right = bottom = left = parts[0]
    elif len(parts) == 2:
        top = bottom = parts[0]
        right = left = parts[1]
    elif len(parts) == 3:
        top, right, bottom = parts
        left = right
    else:
        top, right, bottom, left = parts[:4]
    return top, right, bottom, left


def _apply_margin_shorthand(raw_value: str, style: _RtfStyle) -> None:
    values = _css_box_values(raw_value)
    if values is None:
        return
    top, right, bottom, left = values
    top_twips = _dimension_to_twips(top)
    bottom_twips = _dimension_to_twips(bottom)
    left_twips = _dimension_to_twips(left)
    right_twips = _dimension_to_twips(right)
    if top_twips is not None:
        style.space_before_twips = max(0, top_twips)
    if bottom_twips is not None:
        style.space_after_twips = max(0, bottom_twips)
    if left_twips is not None:
        style.left_indent_twips = left_twips
    if right_twips is not None:
        style.right_indent_twips = right_twips


def _parse_style_attribute(style_attr: str, style: _RtfStyle, color_names: dict[str, int]) -> None:
    for chunk in style_attr.split(";"):
        if ":" not in chunk:
            continue
        key, raw_value = chunk.split(":", 1)
        key = key.strip().lower()
        raw_value = raw_value.strip()
        value_lower = raw_value.lower()
        if key == "font-weight":
            numeric_weight = re.search(r"\d+", value_lower)
            style.bold = "bold" in value_lower or (numeric_weight is not None and int(numeric_weight.group(0)) >= 600)
        elif key == "font-style":
            style.italic = "italic" in value_lower or "oblique" in value_lower
        elif key == "font-variant":
            style.small_caps = "small-caps" in value_lower
        elif key == "text-transform":
            style.all_caps = "uppercase" in value_lower
            if value_lower in {"none", "initial", "unset"}:
                style.all_caps = False
        elif key == "text-decoration":
            style.underline = "underline" in value_lower
            style.strike = "line-through" in value_lower
        elif key == "font-size":
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)", raw_value)
            if match:
                points = float(match.group(1))
                if "px" in value_lower:
                    points = points * 72.0 / 96.0
                style.fs_half_points = max(1, int(round(points * 2)))
        elif key == "font-family":
            style.font_family = _css_font_family(raw_value)
        elif key in {"color", "-qt-user-state"}:
            _set_color_index(_css_color(raw_value), color_names, style, background=False)
        elif key in {"background-color", "background"}:
            _set_color_index(_css_color(raw_value), color_names, style, background=True)
        elif key == "vertical-align":
            if value_lower in {"super", "sub"}:
                style.vertical = value_lower
            elif value_lower in {"baseline", "initial", "inherit", "unset"}:
                style.vertical = ""
        elif key == "direction" and value_lower in {"rtl", "ltr"}:
            style.direction = value_lower
        elif key == "display" and value_lower == "none":
            style.hidden = True
        elif key == "visibility":
            style.hidden = value_lower == "hidden"
        elif key == "letter-spacing":
            if value_lower in {"normal", "initial", "inherit", "unset"}:
                style.letter_spacing_twips = None
            else:
                twips = _dimension_to_twips(raw_value)
                if twips is not None:
                    style.letter_spacing_twips = twips
        elif key == "text-align" and value_lower in {"left", "center", "right", "justify"}:
            style.align = value_lower
        elif key == "margin-left":
            twips = _dimension_to_twips(raw_value)
            if twips is not None:
                style.left_indent_twips = twips
        elif key in {"padding-left"}:
            twips = _dimension_to_twips(raw_value)
            if twips is not None:
                style.left_indent_twips = (style.left_indent_twips or 0) + twips
        elif key in {"-qt-block-indent", "-qt-list-indent"}:
            match = re.search(r"(-?[0-9]+)", raw_value)
            if match and style.left_indent_twips is None:
                level = max(0, int(match.group(1)))
                if level:
                    # QTextEdit serializes logical block indent levels, not a CSS
                    # length. RichTextBox used twips; half-inch per level is the
                    # closest stable compatibility mapping.
                    style.left_indent_twips = level * 720
        elif key == "margin-right":
            twips = _dimension_to_twips(raw_value)
            if twips is not None:
                style.right_indent_twips = twips
        elif key == "margin-top":
            twips = _dimension_to_twips(raw_value)
            if twips is not None:
                style.space_before_twips = max(0, twips)
        elif key == "margin-bottom":
            twips = _dimension_to_twips(raw_value)
            if twips is not None:
                style.space_after_twips = max(0, twips)
        elif key == "margin":
            _apply_margin_shorthand(raw_value, style)
        elif key == "line-height":
            parsed = _line_height_to_rtf(raw_value, style)
            if parsed is not None:
                style.line_spacing_twips, style.line_spacing_multiple = parsed
        elif key == "text-indent":
            twips = _dimension_to_twips(raw_value)
            if twips is not None:
                style.first_indent_twips = twips


def _dimension_to_twips(value: str) -> int | None:
    value = value.strip().lower()
    match = re.search(r"(-?[0-9]+(?:\.[0-9]+)?)", value)
    if not match:
        return None
    number = float(match.group(1))
    if "px" in value:
        points = number * 72.0 / 96.0
    elif "cm" in value:
        points = number * 72.0 / 2.54
    elif "mm" in value:
        points = number * 72.0 / 25.4
    elif "in" in value:
        points = number * 72.0
    else:
        points = number
    return int(round(points * 20))


def _line_height_to_rtf(value: str, style: _RtfStyle) -> tuple[int, bool] | None:
    value = value.strip().lower()
    if not value or value in {"normal", "inherit", "initial", "unset"}:
        return None
    percent = re.fullmatch(r"(-?[0-9]+(?:\.[0-9]+)?)\s*%", value)
    if percent:
        # RTF ``\slmult1`` stores a multiple in 240ths of a line.
        multiple = max(1, int(round(float(percent.group(1)) / 100.0 * 240)))
        return multiple, True
    if re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value):
        multiple = max(1, int(round(float(value) * 240)))
        return multiple, True
    twips = _dimension_to_twips(value)
    if twips is None:
        return None
    return abs(twips), False


def _dimension_to_px(value: str) -> int | None:
    value = value.strip().lower()
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", value)
    if not match:
        return None
    number = float(match.group(1))
    if "pt" in value:
        number = number * 96.0 / 72.0
    elif "cm" in value:
        number = number * 96.0 / 2.54
    elif "mm" in value:
        number = number * 96.0 / 25.4
    elif "in" in value:
        number = number * 96.0
    return max(1, int(round(number)))


def _image_type_from_bytes(data: bytes, fallback: str = "") -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"BM"):
        return "image/bmp"
    if data.startswith(bytes.fromhex("d7cdc69a")):
        return "image/wmf"
    if len(data) > 44 and data[:4] == b"\x01\x00\x00\x00" and b" EMF" in data[:128]:
        return "image/x-emf"
    return fallback.lower()


def _image_data_from_src(src: str) -> tuple[str, bytes] | None:
    src = src.strip()
    if not src:
        return None
    match = _DATA_IMAGE_RE.match(src)
    if match:
        mime_type = match.group(1).lower()
        try:
            return mime_type, base64.b64decode(match.group(2), validate=False)
        except Exception:
            return None
    parsed = urlparse(src)
    if parsed.scheme and parsed.scheme not in {"file"}:
        return None
    if parsed.scheme == "file":
        path_text = unquote(parsed.path)
        if parsed.netloc and not path_text.startswith("/"):
            path_text = f"//{parsed.netloc}/{path_text}"
    else:
        path_text = unquote(src)
    try:
        data = Path(path_text).expanduser().read_bytes()
    except OSError:
        return None
    mime_type = _image_type_from_bytes(data)
    if not mime_type:
        suffix = Path(path_text).suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            mime_type = "image/jpeg"
        elif suffix == ".png":
            mime_type = "image/png"
        elif suffix == ".bmp":
            mime_type = "image/bmp"
        elif suffix == ".wmf":
            mime_type = "image/wmf"
        elif suffix == ".emf":
            mime_type = "image/x-emf"
    return (mime_type, data) if mime_type else None


def _rtf_picture_from_source(src: str, width_px: int | None = None, height_px: int | None = None) -> str | None:
    image = _image_data_from_src(src)
    if image is None:
        return None
    mime_type, data = image
    mime_type = _image_type_from_bytes(data, mime_type)
    if mime_type == "image/png":
        blip = "pngblip"
        payload = data
    elif mime_type == "image/jpeg":
        blip = "jpegblip"
        payload = data
    elif mime_type == "image/bmp":
        blip = "dibitmap0"
        payload = bmp_to_dib_bytes(data)
    elif mime_type in {"image/wmf", "image/x-wmf"}:
        blip = "wmetafile8"
        payload = data
    elif mime_type in {"image/x-emf", "image/emf"}:
        blip = "emfblip"
        payload = data
    else:
        return None
    controls = [rf"\pict\{blip}"]
    if width_px:
        controls.append(rf"\picwgoal{max(1, int(round(width_px * 15)))}")
    if height_px:
        controls.append(rf"\pichgoal{max(1, int(round(height_px * 15)))}")
    hex_data = payload.hex()
    lines = [hex_data[i : i + 64] for i in range(0, len(hex_data), 64)]
    return "{" + "".join(controls) + "\n" + "\n".join(lines) + "}"


@dataclass(slots=True)
class _HtmlSegment:
    text: str
    style: _RtfStyle


@dataclass(slots=True)
class _HtmlImage:
    src: str
    width_px: int | None = None
    height_px: int | None = None


class _HtmlToSegments(HTMLParser):
    _BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "center"}
    _HEADING_SIZES = {"h1": 48, "h2": 36, "h3": 28, "h4": 24, "h5": 20, "h6": 18}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.color_names: dict[str, int] = {}
        self.font_names: dict[str, int] = {}
        self.stack: list[_RtfStyle] = [_RtfStyle()]
        self.segments: list[_HtmlSegment | _HtmlImage] = []
        self.skip_depth = 0
        self.list_stack: list[dict[str, int | str]] = []
        self.table_row_has_cell: list[bool] = []

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
        elif tag == "sup":
            style.vertical = "super"
        elif tag == "sub":
            style.vertical = "sub"
        elif tag in {"code", "kbd", "samp", "pre"}:
            style.font_family = "Courier New"
        elif tag == "small":
            base = style.fs_half_points or 24
            style.fs_half_points = max(1, int(round(base * 0.83)))
        elif tag == "big":
            base = style.fs_half_points or 24
            style.fs_half_points = max(1, int(round(base * 1.2)))
        elif tag in self._HEADING_SIZES:
            style.bold = True
            style.fs_half_points = self._HEADING_SIZES[tag]
            style.space_before_twips = 240 if style.space_before_twips is None else style.space_before_twips
            style.space_after_twips = 120 if style.space_after_twips is None else style.space_after_twips
        elif tag == "blockquote":
            style.left_indent_twips = (style.left_indent_twips or 0) + 720
            style.right_indent_twips = (style.right_indent_twips or 0) + 720
        elif tag == "center":
            style.align = "center"
        elif tag == "a":
            href = attr.get("href", "").strip()
            if href:
                style.hyperlink_url = href
                # WinForms/RichTextBox shows field links underlined even when the
                # imported HTML did not explicitly specify text-decoration.
                style.underline = True
        elif tag == "font":
            _set_color_index(_css_color(attr.get("color", "")), self.color_names, style, background=False)
            face = _css_font_family(attr.get("face", ""))
            if face:
                style.font_family = face
            size = attr.get("size", "").strip()
            if size and re.fullmatch(r"[+-]?\d+", size):
                value = int(size)
                if size.startswith(("+", "-")):
                    value = 3 + value
                # HTML font size 3 ~= 12pt; keep it conservative.
                style.fs_half_points = max(1, min(96, value * 8))
        if tag == "body":
            _set_color_index(_css_color(attr.get("text", "")), self.color_names, style, background=False)
        align_attr = attr.get("align", "").strip().lower()
        if align_attr in {"left", "center", "right", "justify"}:
            style.align = align_attr
        _set_color_index(_css_color(attr.get("bgcolor", "")), self.color_names, style, background=True)
        if "style" in attr:
            _parse_style_attribute(attr["style"], style, self.color_names)
        if style.font_family:
            self.font_names.setdefault(style.font_family, len(self.font_names) + 1)
        self.stack.append(style)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"style", "script"}:
            self.skip_depth += 1
            return
        if tag == "br":
            self._append(_RTF_SOFT_LINE_BREAK)
            return
        if tag == "img":
            attr = {k.lower(): v or "" for k, v in attrs}
            width = _dimension_to_px(attr.get("width", ""))
            height = _dimension_to_px(attr.get("height", ""))
            if "style" in attr:
                for chunk in attr["style"].split(";"):
                    if ":" not in chunk:
                        continue
                    key, value = chunk.split(":", 1)
                    if key.strip().lower() == "width" and width is None:
                        width = _dimension_to_px(value)
                    elif key.strip().lower() == "height" and height is None:
                        height = _dimension_to_px(value)
            src = attr.get("src", "")
            if src:
                self.segments.append(_HtmlImage(src=src, width_px=width, height_px=height))
            else:
                self._append("[Bild]")
            return
        if tag in {"ul", "ol"}:
            if self._needs_paragraph_break():
                self._append("\n")
            self.list_stack.append({"type": tag, "counter": 0})
            self._push(tag, attrs)
            return
        if tag == "li":
            if self._needs_paragraph_break():
                self._append("\n")
            if self.list_stack and self.list_stack[-1].get("type") == "ol":
                self.list_stack[-1]["counter"] = int(self.list_stack[-1].get("counter", 0)) + 1
                self._append(f"{self.list_stack[-1]['counter']}. ")
            else:
                self._append("• ")
            self._push(tag, attrs)
            return
        if tag in {"table", "tbody", "thead", "tfoot"}:
            if self._needs_paragraph_break():
                self._append("\n")
            self._push(tag, attrs)
            return
        if tag == "tr":
            if self._needs_paragraph_break():
                self._append("\n")
            self.table_row_has_cell.append(False)
            self._push(tag, attrs)
            return
        if tag in {"td", "th"}:
            if self.table_row_has_cell:
                if self.table_row_has_cell[-1]:
                    self._append("\t")
                self.table_row_has_cell[-1] = True
            self._push(tag, attrs)
            return
        if tag in self._BLOCK_TAGS and self._needs_paragraph_break():
            self._append("\n")
        self._push(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"style", "script"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if tag in {"br", "img"}:
            return
        if tag in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            if len(self.stack) > 1:
                self.stack.pop()
            if self._needs_paragraph_break():
                self._append("\n")
            return
        if tag == "tr":
            if len(self.stack) > 1:
                self.stack.pop()
            if self.table_row_has_cell:
                self.table_row_has_cell.pop()
            self._append("\n")
            return
        if tag in self._BLOCK_TAGS or tag == "li":
            # Keep the paragraph break inside the paragraph's style scope so
            # alignment and indentation controls are attached to the same RTF
            # paragraph rather than a short grouped text run before ``\par``.
            self._append("\n")
            if len(self.stack) > 1:
                self.stack.pop()
            return
        if tag in {"td", "th", "table", "tbody", "thead", "tfoot", "a"}:
            if len(self.stack) > 1:
                self.stack.pop()
            if tag in {"table", "tbody", "thead", "tfoot"} and self._needs_paragraph_break():
                self._append("\n")
            return
        if len(self.stack) > 1:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        self._append(data)

    def _needs_paragraph_break(self) -> bool:
        last = self.segments[-1] if self.segments else None
        return bool(last and (isinstance(last, _HtmlImage) or not last.text.endswith("\n")))

    def _append(self, text: str) -> None:
        if not text:
            return
        style = self.stack[-1].copy()
        if self.segments and isinstance(self.segments[-1], _HtmlSegment) and self.segments[-1].style == style:
            self.segments[-1].text += text
        else:
            self.segments.append(_HtmlSegment(text, style))


def _style_prefix(style: _RtfStyle, font_names: dict[str, int] | None = None) -> str:
    parts: list[str] = []
    if style.align in {"left", "center", "right", "justify"}:
        parts.append({"left": r"\ql", "center": r"\qc", "right": r"\qr", "justify": r"\qj"}[style.align])
    if style.left_indent_twips is not None:
        parts.append(rf"\li{style.left_indent_twips}")
    if style.right_indent_twips is not None:
        parts.append(rf"\ri{style.right_indent_twips}")
    if style.first_indent_twips is not None:
        parts.append(rf"\fi{style.first_indent_twips}")
    if style.space_before_twips is not None:
        parts.append(rf"\sb{max(0, style.space_before_twips)}")
    if style.space_after_twips is not None:
        parts.append(rf"\sa{max(0, style.space_after_twips)}")
    if style.line_spacing_twips is not None and style.line_spacing_twips > 0:
        parts.append(rf"\sl{style.line_spacing_twips}")
    if style.line_spacing_multiple is not None:
        parts.append(rf"\slmult{1 if style.line_spacing_multiple else 0}")
    if style.direction == "rtl":
        parts.append(r"\rtlpar\rtlch")
    elif style.direction == "ltr":
        parts.append(r"\ltrpar\ltrch")
    if style.font_family and font_names and style.font_family in font_names:
        parts.append(rf"\f{font_names[style.font_family]}")
    if style.bold:
        parts.append(r"\b")
    if style.italic:
        parts.append(r"\i")
    if style.underline:
        parts.append(r"\ul")
    if style.strike:
        parts.append(r"\strike")
    if style.all_caps:
        parts.append(r"\caps")
    if style.small_caps:
        parts.append(r"\scaps")
    if style.hidden:
        parts.append(r"\v")
    if style.letter_spacing_twips is not None:
        parts.append(rf"\expndtw{style.letter_spacing_twips}")
    if style.vertical == "super":
        parts.append(r"\super")
    elif style.vertical == "sub":
        parts.append(r"\sub")
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


def _escape_font_table_name(name: str) -> str:
    return re.sub(r"[{};\\]", " ", name).strip() or "Microsoft Sans Serif"


def _font_table(font_names: dict[str, int]) -> str:
    entries = [r"{\f0\fnil\fcharset0 Microsoft Sans Serif;}" ]
    for family, _index in sorted(font_names.items(), key=lambda item: item[1]):
        entries.append(r"{\f" + str(_index) + r"\fnil\fcharset0 " + _escape_font_table_name(family) + ";}")
    return r"{\fonttbl" + "".join(entries) + "}" + "\n"


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
    font_table = _font_table(parser.font_names)
    body_parts: list[str] = []
    for segment in parser.segments:
        if isinstance(segment, _HtmlImage):
            pict = _rtf_picture_from_source(segment.src, segment.width_px, segment.height_px)
            body_parts.append(pict if pict is not None else _rtf_escape_text("[Bild]"))
            continue
        text = segment.text.replace("\r\n", "\n").replace("\r", "\n")
        if not text:
            continue
        prefix = _style_prefix(segment.style, parser.font_names)
        if segment.style.hyperlink_url:
            body_parts.append(_rtf_hyperlink_field(segment.style.hyperlink_url, text, prefix))
            continue
        escaped_text = _rtf_escape_text(text)
        if prefix:
            body_parts.append("{" + prefix + " " + escaped_text + "}")
        else:
            body_parts.append(escaped_text)
    body = "".join(body_parts).strip()
    if body and not re.search(r"\\par\s*(?:\}+)?$", body):
        body += r"\par" + "\n"
    return (
        r"{\rtf1\ansi\ansicpg1252\deff0\deflang1031"
        + font_table
        + color_table
        + r"\viewkind4\uc1\pard\f0\fs17 "
        + body
        + "}\n"
    )
