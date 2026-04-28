from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

_HEX_RE = re.compile(r"^[0-9a-fA-F]{2}$")
_PICT_CONTROL_RE = re.compile(r"\\([a-zA-Z]+)(-?\d+)? ?")
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
