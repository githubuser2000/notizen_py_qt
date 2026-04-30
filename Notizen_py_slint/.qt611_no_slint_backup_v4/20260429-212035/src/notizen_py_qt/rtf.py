from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from html import escape
from pathlib import Path
import re

_HEX_RE = re.compile(r"^[0-9a-fA-F]{2}$")
_PICT_CONTROL_RE = re.compile(r"\\([a-zA-Z]+)(-?\d+)? ?")
_FS_CONTROL_RE = re.compile(r"(\\fs)(\d+)")
_FONT0_RE = re.compile(r"\{\\f0(?:[^;{}]*)\s([^;{}]+);\}")
_IMAGE_KIND_BY_SUFFIX = {
    ".png": ("png", "pngblip"),
    ".jpg": ("jpg", "jpegblip"),
    ".jpeg": ("jpg", "jpegblip"),
    ".bmp": ("bmp", "dibitmap"),
    ".dib": ("bmp", "dibitmap"),
}


@dataclass(slots=True, frozen=True)
class RtfPicture:
    r"""A picture blob extracted from a RichTextBox/RTF ``\pict`` group."""

    index: int
    kind: str
    extension: str
    data: bytes
    width_twips: int | None = None
    height_twips: int | None = None

    @property
    def filename(self) -> str:
        return f"bild-{self.index:03d}.{self.extension}"


@dataclass(slots=True, frozen=True)
class RtfStyle:
    """Whole-note style used when Slint cannot address a text selection."""

    font_family: str = "Sans Serif"
    font_size_half_points: int = 18
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    fg_color: int | None = None
    bg_color: int | None = None


@dataclass(slots=True, frozen=True)
class TextRange:
    """Plain-text character range inside a note.

    WinForms RichTextBox actions were usually selection based.  Slint's Python
    binding does not expose a rich-text selection, but CLI/editor helpers can
    still address a note by plain-text character offsets.  The range is always
    normalized to Python string indices after RTF has been converted to text.
    """

    start: int
    end: int

    @property
    def length(self) -> int:
        return max(0, self.end - self.start)

    def as_dict(self) -> dict[str, int]:
        return {"start": self.start, "end": self.end, "length": self.length}


def is_rtf(value: str | bytes | None) -> bool:
    """Return True when a value looks like an RTF document."""
    if value is None:
        return False
    if isinstance(value, bytes):
        for encoding in ("utf-8-sig", "utf-16", "cp1252"):
            try:
                value = value.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            return False
    stripped = value.lstrip()
    return stripped.startswith(r"{\rtf") or r"\rtf" in stripped[:32]


def text_to_rtf(
    text: str,
    font_size_half_points: int = 18,
    *,
    font_family: str = "Sans Serif",
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strike: bool = False,
    fg_color: int | None = None,
    bg_color: int | None = None,
) -> str:
    """Create a small RTF document compatible with old Notizen.NET files.

    The old application stored each node as RichTextBox.Rtf. Slint's TextEdit is
    plain text, so edited notes are written as simple but valid RTF. Optional
    style arguments format the *whole* note, which is the portable replacement
    for WinForms selection formatting in this port.
    """
    text = text or ""
    font_size_half_points = max(2, int(font_size_half_points or 18))
    font_family = _escape_font_name(font_family or "Sans Serif")

    color_entries: list[str] = []
    fg_index = bg_index = 0
    if fg_color is not None:
        fg_index = len(color_entries) + 1
        color_entries.append(_rtf_color_entry(fg_color))
    if bg_color is not None:
        bg_index = len(color_entries) + 1
        color_entries.append(_rtf_color_entry(bg_color))
    color_table = ""
    if color_entries:
        color_table = r"{\colortbl ;" + "".join(color_entries) + "}"

    controls: list[str] = [r"\viewkind4", r"\uc1", r"\pard", r"\f0", rf"\fs{font_size_half_points}"]
    if fg_index:
        controls.append(rf"\cf{fg_index}")
    if bg_index:
        controls.append(rf"\highlight{bg_index}")
    if bold:
        controls.append(r"\b")
    if italic:
        controls.append(r"\i")
    if underline:
        controls.append(r"\ul")
    if strike:
        controls.append(r"\strike")

    body = _escape_rtf_text(text)
    return (
        r"{\rtf1\ansi\ansicpg1252\deff0"
        + rf"{{\fonttbl{{\f0\fnil\fcharset0 {font_family};}}}}"
        + color_table
        + "".join(controls)
        + " "
        + body
        + r"\par"
        + "\n}"
    )


def normalize_text_range(text: str, start: int, length: int | None = None, *, end: int | None = None) -> TextRange:
    """Clamp a RichTextBox-style selection range to a Python string.

    ``start`` and ``length`` are character offsets in the note's plain text.  A
    missing length means an insertion point; callers that want "to end" can pass
    ``end=len(text)``.  Negative values are clamped rather than crashing because
    the old UI was forgiving around selection state.
    """
    total = len(text or "")
    left = max(0, min(total, int(start or 0)))
    if end is not None:
        right = max(left, min(total, int(end)))
    elif length is None:
        right = left
    else:
        right = max(left, min(total, left + max(0, int(length))))
    return TextRange(left, right)


def replace_rtf_text_range(rtf_or_text: str, start: int, length: int | None, replacement: str, *, end: int | None = None) -> str:
    """Replace a plain-text range and rewrite the note as simple styled RTF."""
    current = detect_rtf_style(rtf_or_text)
    text = rtf_to_text(rtf_or_text)
    selected = normalize_text_range(text, start, length, end=end)
    new_text = text[: selected.start] + str(replacement or "") + text[selected.end :]
    return text_to_rtf(
        new_text,
        font_family=current.font_family,
        font_size_half_points=current.font_size_half_points,
        bold=current.bold,
        italic=current.italic,
        underline=current.underline,
        strike=current.strike,
    )


def style_rtf_text_range(
    rtf_or_text: str,
    start: int,
    length: int | None,
    *,
    end: int | None = None,
    font_family: str | None = None,
    font_size_half_points: int | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    strike: bool | None = None,
    fg_color: int | None = None,
    bg_color: int | None = None,
) -> str:
    """Apply simple RTF formatting to a plain-text range.

    This is the closest portable equivalent to the old RichTextBox selection
    toolbar.  It converts the note to plain text, keeps the detected global style
    for unselected text and wraps the selected character range in a local RTF
    group.  Embedded images and complex prior per-character styles are not
    preserved by this helper; callers that need raw RTF should keep using the
    Raw-RTF mode.
    """
    current = detect_rtf_style(rtf_or_text)
    text = rtf_to_text(rtf_or_text)
    selected = normalize_text_range(text, start, length, end=end)
    if selected.length == 0:
        return text_to_rtf(
            text,
            font_family=font_family or current.font_family,
            font_size_half_points=font_size_half_points or current.font_size_half_points,
            bold=current.bold if bold is None else bold,
            italic=current.italic if italic is None else italic,
            underline=current.underline if underline is None else underline,
            strike=current.strike if strike is None else strike,
            fg_color=fg_color,
            bg_color=bg_color,
        )
    selected_style = RtfStyle(
        font_family=font_family or current.font_family,
        font_size_half_points=max(2, int(font_size_half_points or current.font_size_half_points)),
        bold=current.bold if bold is None else bold,
        italic=current.italic if italic is None else italic,
        underline=current.underline if underline is None else underline,
        strike=current.strike if strike is None else strike,
        fg_color=fg_color,
        bg_color=bg_color,
    )
    return text_to_rtf_with_styled_range(text, selected, base_style=current, selected_style=selected_style)


def text_to_rtf_with_styled_range(text: str, selected: TextRange, *, base_style: RtfStyle | None = None, selected_style: RtfStyle | None = None) -> str:
    """Create simple RTF with one locally styled text range."""
    base = base_style or RtfStyle()
    sel = selected_style or base
    text = text or ""
    selected = normalize_text_range(text, selected.start, selected.length)
    base_family = _escape_font_name(base.font_family or "Sans Serif")
    selected_family = _escape_font_name(sel.font_family or base.font_family or "Sans Serif")
    font_table = rf"{{\fonttbl{{\f0\fnil\fcharset0 {base_family};}}"
    selected_uses_f1 = selected_family != base_family
    if selected_uses_f1:
        font_table += rf"{{\f1\fnil\fcharset0 {selected_family};}}"
    font_table += "}"

    color_entries: list[str] = []
    fg_index = bg_index = 0
    if sel.fg_color is not None:
        fg_index = len(color_entries) + 1
        color_entries.append(_rtf_color_entry(sel.fg_color))
    if sel.bg_color is not None:
        bg_index = len(color_entries) + 1
        color_entries.append(_rtf_color_entry(sel.bg_color))
    color_table = r"{\colortbl ;" + "".join(color_entries) + "}" if color_entries else ""

    base_controls = [r"\viewkind4", r"\uc1", r"\pard", r"\f0", rf"\fs{max(2, int(base.font_size_half_points or 18))}"]
    if base.bold:
        base_controls.append(r"\b")
    if base.italic:
        base_controls.append(r"\i")
    if base.underline:
        base_controls.append(r"\ul")
    if base.strike:
        base_controls.append(r"\strike")

    selected_controls = [r"\f1" if selected_uses_f1 else r"\f0", rf"\fs{max(2, int(sel.font_size_half_points or base.font_size_half_points or 18))}"]
    selected_controls.append(r"\b" if sel.bold else r"\b0")
    selected_controls.append(r"\i" if sel.italic else r"\i0")
    selected_controls.append(r"\ul" if sel.underline else r"\ul0")
    selected_controls.append(r"\strike" if sel.strike else r"\strike0")
    if fg_index:
        selected_controls.append(rf"\cf{fg_index}")
    if bg_index:
        selected_controls.append(rf"\highlight{bg_index}")

    prefix = _escape_rtf_text(text[: selected.start])
    middle = _escape_rtf_text(text[selected.start : selected.end])
    suffix = _escape_rtf_text(text[selected.end :])
    body = prefix + "{" + "".join(selected_controls) + " " + middle + "}" + suffix
    return (
        r"{\rtf1\ansi\ansicpg1252\deff0"
        + font_table
        + color_table
        + "".join(base_controls)
        + " "
        + body
        + r"\par"
        + "\n}"
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
    text = _collapse_surrogates(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip("\n")




def rtf_to_html_fragment(rtf: str, *, include_images: bool = True) -> str:
    """Convert stored RTF into a small safe HTML fragment.

    This is intentionally conservative: text is escaped, line breaks are kept,
    and embedded RichTextBox pictures are emitted as data-URI images. It does not
    try to be a full RTF renderer, but it preserves much more than the plain text
    export and gives old image-heavy notes a useful print/preview path.
    """
    parts: list[str] = []
    text = rtf_to_text(rtf).strip("\n")
    if text:
        paragraphs = re.split(r"\n{2,}", text)
        for paragraph in paragraphs:
            paragraph = paragraph.strip("\n")
            if not paragraph:
                continue
            parts.append("<p>" + escape(paragraph).replace("\n", "<br>\n") + "</p>")
    if include_images:
        for picture in extract_pictures(rtf):
            mime = _picture_mime_type(picture.extension)
            if mime.startswith("image/"):
                encoded = b64encode(picture.data).decode("ascii")
                alt = escape(picture.filename)
                attrs = [f'src="data:{mime};base64,{encoded}"', f'alt="{alt}"']
                if picture.width_twips:
                    attrs.append(f'data-width-twips="{picture.width_twips}"')
                if picture.height_twips:
                    attrs.append(f'data-height-twips="{picture.height_twips}"')
                parts.append("<figure><img " + " ".join(attrs) + "></figure>")
            else:
                parts.append(f'<p class="embedded-object">[eingebettetes Objekt: {escape(picture.filename)}]</p>')
    return "\n".join(parts)


def _picture_mime_type(extension: str) -> str:
    ext = (extension or "").lower().lstrip(".")
    if ext in {"jpg", "jpeg"}:
        return "image/jpeg"
    if ext == "png":
        return "image/png"
    if ext == "bmp":
        return "image/bmp"
    if ext == "gif":
        return "image/gif"
    if ext == "svg":
        return "image/svg+xml"
    if ext == "wmf":
        return "image/wmf"
    if ext == "emf":
        return "image/emf"
    return "application/octet-stream"

def restyle_rtf_as_plain(
    rtf_or_text: str,
    *,
    font_family: str = "Sans Serif",
    font_size_half_points: int = 18,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strike: bool = False,
    fg_color: int | None = None,
    bg_color: int | None = None,
) -> str:
    """Convert existing note content to plain text and write it back as styled RTF."""
    return text_to_rtf(
        rtf_to_text(rtf_or_text),
        font_size_half_points=font_size_half_points,
        font_family=font_family,
        bold=bold,
        italic=italic,
        underline=underline,
        strike=strike,
        fg_color=fg_color,
        bg_color=bg_color,
    )



def detect_rtf_style(rtf_or_text: str, *, default_family: str = "Sans Serif", default_half_points: int = 18) -> RtfStyle:
    """Best-effort style inspection for old RichTextBox RTF.

    It intentionally returns only the first/global-ish style values. This matches
    the Python/Slint port's whole-note formatting model and gives toolbar actions
    sensible defaults without pretending to be a full RTF layout engine.
    """
    value = rtf_or_text or ""
    if not is_rtf(value):
        return RtfStyle(font_family=default_family, font_size_half_points=max(2, int(default_half_points or 18)))
    family = default_family
    match = _FONT0_RE.search(value)
    if match is not None:
        family = match.group(1).strip() or default_family
    return RtfStyle(
        font_family=family,
        font_size_half_points=first_rtf_font_size(value, default_half_points=default_half_points),
        bold=_has_rtf_switch(value, "b"),
        italic=_has_rtf_switch(value, "i"),
        underline=_has_rtf_switch(value, "ul"),
        strike=_has_rtf_switch(value, "strike"),
    )


def restyle_rtf_with_defaults(
    rtf_or_text: str,
    *,
    font_family: str | None = None,
    font_size_half_points: int | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    strike: bool | None = None,
    fg_color: int | None = None,
    bg_color: int | None = None,
) -> str:
    """Rewrite a note as simple RTF while preserving unspecified global style bits."""
    current = detect_rtf_style(rtf_or_text)
    return restyle_rtf_as_plain(
        rtf_or_text,
        font_family=font_family if font_family is not None else current.font_family,
        font_size_half_points=font_size_half_points if font_size_half_points is not None else current.font_size_half_points,
        bold=current.bold if bold is None else bold,
        italic=current.italic if italic is None else italic,
        underline=current.underline if underline is None else underline,
        strike=current.strike if strike is None else strike,
        fg_color=fg_color,
        bg_color=bg_color,
    )


def _has_rtf_switch(value: str, name: str) -> bool:
    # True for ``\b``/``\b ``/``\b\i`` but false for ``\b0`` and words like ``\blue``.
    return re.search(rf"\\{re.escape(name)}(?![a-zA-Z0-9])", value or "") is not None

def first_rtf_font_size(rtf_or_text: str, *, default_half_points: int = 18) -> int:
    """Return the first RTF ``\fs`` font size in half-points.

    The old WinForms application had toolbar/shortcut actions for larger and
    smaller text. RichTextBox represented that as ``\fsN`` control words. This
    helper gives the Python port a lightweight way to inspect the same state
    without depending on a GUI text widget.
    """
    if not is_rtf(rtf_or_text):
        return max(2, int(default_half_points or 18))
    match = _FS_CONTROL_RE.search(rtf_or_text or "")
    if match is None:
        return max(2, int(default_half_points or 18))
    return int(match.group(2))


def set_rtf_font_size(
    rtf_or_text: str,
    half_points: int,
    *,
    min_half_points: int = 2,
    max_half_points: int = 400,
) -> str:
    """Set all RTF font-size control words to ``half_points``.

    Existing RTF is preserved as far as possible. When no RTF size marker exists,
    the content is rewritten as simple RTF using the same plain text.
    """
    target = _clamp_half_points(half_points, min_half_points, max_half_points)
    if not is_rtf(rtf_or_text):
        return text_to_rtf(str(rtf_or_text or ""), font_size_half_points=target)
    value = rtf_or_text or ""
    if _FS_CONTROL_RE.search(value):
        return _FS_CONTROL_RE.sub(lambda match: f"{match.group(1)}{target}", value)
    return restyle_rtf_as_plain(value, font_size_half_points=target)


def change_rtf_font_size(
    rtf_or_text: str,
    delta_half_points: int,
    *,
    default_half_points: int = 18,
    min_half_points: int = 2,
    max_half_points: int = 400,
) -> str:
    """Increase/decrease all RTF font-size control words by half-points.

    Notizen.NET changed the RichTextBox selection size through Ctrl+Plus and
    Ctrl+Minus. Slint's plain TextEdit cannot do selection-level rich text, so the
    port applies the change to every ``\fs`` marker in the note. That keeps old
    rich notes mostly intact and still gives the same one-click workflow.
    """
    delta = int(delta_half_points or 0)
    if not is_rtf(rtf_or_text):
        base = _clamp_half_points(default_half_points + delta, min_half_points, max_half_points)
        return text_to_rtf(str(rtf_or_text or ""), font_size_half_points=base)

    value = rtf_or_text or ""
    if not _FS_CONTROL_RE.search(value):
        base = _clamp_half_points(default_half_points + delta, min_half_points, max_half_points)
        return restyle_rtf_as_plain(value, font_size_half_points=base)

    def replace(match: re.Match[str]) -> str:
        current = int(match.group(2))
        changed = _clamp_half_points(current + delta, min_half_points, max_half_points)
        return f"{match.group(1)}{changed}"

    return _FS_CONTROL_RE.sub(replace, value)


def _clamp_half_points(value: int, low: int, high: int) -> int:
    return max(int(low), min(int(high), int(value)))




def picture_bytes_to_rtf_group(data: bytes, *, suffix: str = ".png", width_twips: int | None = None, height_twips: int | None = None) -> str:
    r"""Return an RTF ``\pict`` group for PNG/JPEG/BMP bytes.

    This is the portable replacement for the old RichTextBox image paste path.
    It does not need Pillow and therefore works in the dependency-free Python core.
    Unsupported formats should be converted to PNG/JPEG/BMP before insertion.
    """
    if not data:
        raise ValueError("Bilddatei ist leer.")
    suffix = (suffix or "").lower()
    if not suffix.startswith("."):
        suffix = "." + suffix
    if suffix not in _IMAGE_KIND_BY_SUFFIX:
        detected = _detect_image_suffix(data)
        if detected is None:
            raise ValueError("Nur PNG-, JPEG- und BMP-Bilder können direkt als RTF-Bild eingefügt werden.")
        suffix = detected
    _, control = _IMAGE_KIND_BY_SUFFIX[suffix]
    attrs = [control]
    if width_twips is not None:
        attrs.append(f"picwgoal{int(width_twips)}")
    if height_twips is not None:
        attrs.append(f"pichgoal{int(height_twips)}")
    hexdata = data.hex().upper()
    wrapped = "\n".join(hexdata[i : i + 128] for i in range(0, len(hexdata), 128))
    return "{\\pict\\" + "\\".join(attrs) + "\n" + wrapped + "}"


def picture_file_to_rtf_group(path: str | Path, *, width_twips: int | None = None, height_twips: int | None = None) -> str:
    path = Path(path)
    return picture_bytes_to_rtf_group(path.read_bytes(), suffix=path.suffix, width_twips=width_twips, height_twips=height_twips)


def append_picture_to_rtf(rtf_or_text: str, path: str | Path, *, width_twips: int | None = None, height_twips: int | None = None) -> str:
    """Append a picture group to an existing note RTF document.

    If the current content is plain text, it is first converted to normal RTF.
    Existing RTF is left intact and the picture group is inserted before the
    outer closing brace.
    """
    base = rtf_or_text if is_rtf(rtf_or_text) else text_to_rtf(rtf_or_text or "")
    picture = picture_file_to_rtf_group(path, width_twips=width_twips, height_twips=height_twips)
    insert = r"\par " + picture + r"\par "
    idx = _outer_group_end_index(base)
    if idx is None:
        return text_to_rtf(rtf_to_text(base))[:-2] + insert + "}"
    return base[:idx] + insert + base[idx:]


def append_text_to_rtf(rtf_or_text: str, text: str) -> str:
    """Append plain text to a note while preserving the outer RTF document."""
    base = rtf_or_text if is_rtf(rtf_or_text) else text_to_rtf(rtf_or_text or "")
    escaped = _escape_rtf_text(text)
    insert = escaped + r"\par "
    idx = _outer_group_end_index(base)
    if idx is None:
        return text_to_rtf(rtf_to_text(base) + text)
    return base[:idx] + insert + base[idx:]

def extract_pictures(rtf: str) -> list[RtfPicture]:
    r"""Extract ``\pict`` blobs from RTF.

    RichTextBox stores pasted images as RTF picture groups. Slint cannot render or
    edit those pictures, but this helper preserves access to them via the CLI/UI.
    """
    if not rtf or "\\pict" not in rtf:
        return []
    pictures: list[RtfPicture] = []
    i = 0
    while True:
        start = rtf.find("{\\pict", i)
        if start < 0:
            # Some writers wrap the picture group as {\*\...{\pict...}}. Fall
            # back to a slower search for any group containing \pict.
            break
        end = _find_group_end(rtf, start)
        if end is None:
            break
        group = rtf[start : end + 1]
        pic = _picture_from_group(group, len(pictures) + 1)
        if pic is not None:
            pictures.append(pic)
        i = end + 1

    if pictures:
        return pictures

    # Fallback: scan every group start and inspect short candidates. This keeps
    # odd RichTextBox output readable without hurting normal files.
    for start in [m.start() for m in re.finditer(r"\{", rtf)]:
        end = _find_group_end(rtf, start)
        if end is None:
            continue
        group = rtf[start : end + 1]
        if "\\pict" not in group[:300]:
            continue
        pic = _picture_from_group(group, len(pictures) + 1)
        if pic is not None:
            pictures.append(pic)
    return pictures


def write_extracted_pictures(rtf: str, directory: str | Path) -> list[Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for picture in extract_pictures(rtf):
        path = directory / picture.filename
        path.write_bytes(picture.data)
        paths.append(path)
    return paths




def _outer_group_end_index(value: str) -> int | None:
    start = value.find("{")
    if start < 0:
        return None
    return _find_group_end(value, start)


def _detect_image_suffix(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"BM"):
        return ".bmp"
    return None

def _find_group_end(value: str, start: int) -> int | None:
    depth = 0
    i = start
    n = len(value)
    while i < n:
        ch = value[i]
        if ch == "\\":
            # Escaped brace/backslash or a control word; either way the next
            # character cannot start/end a group.
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _picture_from_group(group: str, index: int) -> RtfPicture | None:
    controls = {m.group(1): m.group(2) for m in _PICT_CONTROL_RE.finditer(group[:1000])}
    kind, extension = _picture_kind(controls)
    data = _extract_picture_hex(group)
    if not data:
        return None
    return RtfPicture(
        index=index,
        kind=kind,
        extension=extension,
        data=data,
        width_twips=_optional_int(controls.get("picwgoal") or controls.get("picw")),
        height_twips=_optional_int(controls.get("pichgoal") or controls.get("pich")),
    )


def _picture_kind(controls: dict[str, str | None]) -> tuple[str, str]:
    if "pngblip" in controls:
        return "png", "png"
    if "jpegblip" in controls:
        return "jpeg", "jpg"
    if "emfblip" in controls:
        return "emf", "emf"
    if "wmetafile" in controls:
        return "wmf", "wmf"
    if "macpict" in controls:
        return "pict", "pict"
    if "dibitmap" in controls or "wbitmap" in controls:
        return "bitmap", "bmp"
    return "unknown", "bin"


def _extract_picture_hex(group: str) -> bytes:
    digits: list[str] = []
    i = 0
    n = len(group)
    while i < n:
        ch = group[i]
        if ch == "\\":
            i += 1
            if i >= n:
                break
            if group[i].isalpha():
                while i < n and group[i].isalpha():
                    i += 1
                if i < n and group[i] in "+-":
                    i += 1
                while i < n and group[i].isdigit():
                    i += 1
                if i < n and group[i] == " ":
                    i += 1
            else:
                i += 1
            continue
        if ch in "{}\r\n\t ":
            i += 1
            continue
        if ch in "0123456789abcdefABCDEF":
            digits.append(ch)
        i += 1
    if len(digits) < 2:
        return b""
    if len(digits) % 2:
        digits.pop()
    try:
        return bytes.fromhex("".join(digits))
    except ValueError:
        return b""


def _optional_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _escape_rtf_text(text: str) -> str:
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
                    if code <= 0xFFFF:
                        signed = code if code <= 32767 else code - 65536
                        body_parts.append(rf"\u{signed}?")
                    else:
                        # RTF \u is 16-bit. Emit UTF-16 surrogate pairs.
                        encoded16 = ch.encode("utf-16-le")
                        units = [int.from_bytes(encoded16[i : i + 2], "little") for i in range(0, len(encoded16), 2)]
                        for unit in units:
                            signed = unit if unit <= 32767 else unit - 65536
                            body_parts.append(rf"\u{signed}?")
                else:
                    body_parts.extend(rf"\'{byte:02x}" for byte in encoded)
    return "".join(body_parts)


def _escape_font_name(value: str) -> str:
    return value.replace("\\", "").replace(";", "").replace("{", "").replace("}", "").strip() or "Sans Serif"


def _rtf_color_entry(argb_or_rgb: int) -> str:
    value = int(argb_or_rgb) & 0xFFFFFFFF
    r = (value >> 16) & 0xFF
    g = (value >> 8) & 0xFF
    b = value & 0xFF
    return rf"\red{r}\green{g}\blue{b};"


def _collapse_surrogates(text: str) -> str:
    try:
        return text.encode("utf-16-le", "surrogatepass").decode("utf-16-le")
    except UnicodeError:
        return text
