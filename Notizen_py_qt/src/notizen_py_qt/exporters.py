from __future__ import annotations

from dataclasses import dataclass

from .models import NoteNode
from .rtf_utils import (
    RtfImage,
    RtfHyperlink,
    RtfTextSegment,
    RtfTextStyle,
    bmp_to_dib_bytes,
    _rtf_escape_text,
    _rtf_hyperlink_field,
    rtf_to_content_parts,
    rtf_to_plain_text,
    rtf_to_text_segments,
)


@dataclass(slots=True)
class ExportOptions:
    """Options for the legacy-style Notizen tree export."""

    numbered_headings: bool = True
    include_root_number: bool = False
    include_empty_notes: bool = True
    title_separator_blank_lines: int = 2
    body_separator_blank_lines: int = 2


def _walk_numbered(node: NoteNode, depth: int, counters: list[int], options: ExportOptions):
    if depth >= len(counters):
        counters.extend(0 for _ in range(depth - len(counters) + 1))
    else:
        del counters[depth + 1 :]
    counters[depth] += 1
    if options.numbered_headings and (depth > 0 or options.include_root_number):
        start = 0 if options.include_root_number else 1
        number = "".join(f"{counters[i]}." for i in range(start, depth + 1))
        heading = f"{number} {node.title}"
    else:
        heading = node.title
    yield depth, heading, node
    for child in node.children:
        yield from _walk_numbered(child, depth + 1, counters, options)


def tree_to_plain_text(root: NoteNode, options: ExportOptions | None = None) -> str:
    """Create the text export used by the old ``fasse_zusammen`` workflow.

    Notizen.NET created a temporary RichTextBox and walked the tree, writing the
    root title, numbered child headings (``1.``, ``1.1.`` ...), each node body
    and blank spacing. This function reproduces the structure without relying on
    the system clipboard.
    """
    options = options or ExportOptions()
    parts: list[str] = []
    for _depth, heading, node in _walk_numbered(root, 0, [], options):
        body = rtf_to_plain_text(node.rtf)
        if heading or options.include_empty_notes:
            parts.append(heading)
            parts.extend("" for _ in range(options.title_separator_blank_lines - 1))
        body = body.rstrip()
        if body or options.include_empty_notes:
            if body:
                parts.append(body)
            parts.extend("" for _ in range(options.body_separator_blank_lines))
    text = "\n".join(parts).rstrip() + "\n"
    return text



def normalize_export_newlines(text: str) -> str:
    """Use Windows CRLF line endings like the legacy RichTextBox exports."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.replace("\n", "\r\n")


def tree_to_text_bytes(root: NoteNode, options: ExportOptions | None = None, *, encoding: str = "utf-8") -> bytes:
    """Return subtree text export bytes in legacy-compatible encodings.

    ``encoding="ansi"`` maps to Windows-1252 and replaces characters that the
    legacy ANSI export could not represent. ``encoding="unicode"``/``"utf-16"``
    writes UTF-16 with BOM, matching the old Unicode-TXT export.
    """
    text = normalize_export_newlines(tree_to_plain_text(root, options))
    normalized_encoding = encoding.casefold().replace("_", "-")
    if normalized_encoding in {"ansi", "cp1252", "windows-1252"}:
        return text.encode("cp1252", errors="replace")
    if normalized_encoding in {"unicode", "utf-16", "utf16"}:
        return text.encode("utf-16")
    return text.encode("utf-8")

def _strip_trailing_segments(segments: list[RtfTextSegment]) -> list[RtfTextSegment]:
    stripped = list(segments)
    while stripped and not stripped[-1].text.rstrip():
        stripped.pop()
    if stripped:
        last = stripped[-1]
        text = last.text.rstrip()
        if text != last.text:
            stripped[-1] = RtfTextSegment(text=text, style=last.style)
    return stripped


def _collect_body_segments(root: NoteNode, options: ExportOptions) -> list[tuple[str, list[RtfTextSegment]]]:
    entries: list[tuple[str, list[RtfTextSegment]]] = []
    for _depth, heading, node in _walk_numbered(root, 0, [], options):
        entries.append((heading, _strip_trailing_segments(rtf_to_text_segments(node.rtf))))
    return entries


def _strip_trailing_parts(parts: list[RtfTextSegment | RtfImage | RtfHyperlink]) -> list[RtfTextSegment | RtfImage | RtfHyperlink]:
    stripped = list(parts)
    while stripped and isinstance(stripped[-1], RtfTextSegment) and not stripped[-1].text.rstrip():
        stripped.pop()
    if stripped and isinstance(stripped[-1], RtfTextSegment):
        last = stripped[-1]
        text = last.text.rstrip()
        if text != last.text:
            stripped[-1] = RtfTextSegment(text=text, style=last.style)
    return stripped


def _collect_body_parts(root: NoteNode, options: ExportOptions) -> list[tuple[str, list[RtfTextSegment | RtfImage | RtfHyperlink]]]:
    entries: list[tuple[str, list[RtfTextSegment | RtfImage | RtfHyperlink]]] = []
    for _depth, heading, node in _walk_numbered(root, 0, [], options):
        entries.append((heading, _strip_trailing_parts(rtf_to_content_parts(node.rtf))))
    return entries


def _iter_text_segments(entries: list[tuple[str, list[RtfTextSegment | RtfImage | RtfHyperlink]]]):
    for _heading, parts in entries:
        for part in parts:
            if isinstance(part, RtfTextSegment):
                yield part
            elif isinstance(part, RtfHyperlink) and part.style is not None:
                yield RtfTextSegment(part.text, part.style)


def _collect_fonts(entries: list[tuple[str, list[RtfTextSegment | RtfImage | RtfHyperlink]]]) -> dict[str, int]:
    font_indexes: dict[str, int] = {}
    for segment in _iter_text_segments(entries):
        family = segment.style.font_family
        if family and family not in font_indexes:
            font_indexes[family] = len(font_indexes) + 1
    return font_indexes


def _font_table(font_indexes: dict[str, int]) -> str:
    def clean(name: str) -> str:
        return name.replace("\\", " ").replace("{", " ").replace("}", " ").replace(";", " ").strip()

    entries = [r"{\f0\fnil\fcharset0 Microsoft Sans Serif;}" ]
    for family, index in sorted(font_indexes.items(), key=lambda item: item[1]):
        entries.append(r"{\f" + str(index) + r"\fnil\fcharset0 " + (clean(family) or "Microsoft Sans Serif") + ";}")
    return r"{\fonttbl" + "".join(entries) + "}" + "\n"


def _collect_colors(entries: list[tuple[str, list[RtfTextSegment | RtfImage | RtfHyperlink]]]) -> dict[str, int]:
    color_indexes: dict[str, int] = {}
    for segment in _iter_text_segments(entries):
        for color in (segment.style.fg_color, segment.style.bg_color):
            if color and color not in color_indexes:
                color_indexes[color] = len(color_indexes) + 1
    return color_indexes


def _color_table(color_indexes: dict[str, int]) -> str:
    if not color_indexes:
        return ""
    by_index = sorted(color_indexes.items(), key=lambda item: item[1])
    entries = [""]
    for color, _index in by_index:
        red = int(color[1:3], 16)
        green = int(color[3:5], 16)
        blue = int(color[5:7], 16)
        entries.append(rf"\red{red}\green{green}\blue{blue}")
    return r"{\colortbl " + ";".join(entries) + ";}" + "\n"


def _style_prefix(style: RtfTextStyle, color_indexes: dict[str, int], font_indexes: dict[str, int]) -> str:
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
    if style.font_family in font_indexes:
        parts.append(rf"\f{font_indexes[style.font_family]}")
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
    if style.fg_color in color_indexes:
        parts.append(rf"\cf{color_indexes[style.fg_color]}")
    if style.bg_color in color_indexes:
        parts.append(rf"\highlight{color_indexes[style.bg_color]}")
    return "".join(parts)


def _emit_segment(segment: RtfTextSegment, color_indexes: dict[str, int], font_indexes: dict[str, int]) -> str:
    if not segment.text:
        return ""
    escaped_text = _rtf_escape_text(segment.text)
    prefix = _style_prefix(segment.style, color_indexes, font_indexes)
    if prefix:
        return "{" + prefix + " " + escaped_text + "}"
    return escaped_text


def _emit_image(image: RtfImage) -> str:
    mime_type = image.mime_type.casefold()
    payload = image.data
    if mime_type == "image/png":
        blip = "pngblip"
    elif mime_type in {"image/jpeg", "image/jpg"}:
        blip = "jpegblip"
    elif mime_type in {"image/bmp", "image/x-ms-bmp"}:
        # RTF stores BMP pictures as DIB payloads, not with the BMP file header.
        # This keeps old WinForms RichTextBox bitmap pictures roundtrippable.
        blip = image.rtf_control if image.rtf_control.startswith("dibitmap") else "dibitmap0"
        payload = bmp_to_dib_bytes(image.data)
    elif mime_type in {"image/wmf", "image/x-wmf"}:
        blip = image.rtf_control if image.rtf_control.startswith("wmetafile") else "wmetafile8"
    elif mime_type in {"image/x-emf", "image/emf"}:
        blip = "emfblip"
    else:
        return _rtf_escape_text("[Bild]")

    controls = [rf"\pict\{blip}"]
    if image.width_twips and image.width_twips > 0:
        controls.append(rf"\picwgoal{image.width_twips}")
    if image.height_twips and image.height_twips > 0:
        controls.append(rf"\pichgoal{image.height_twips}")
    hex_data = payload.hex()
    lines = [hex_data[index : index + 64] for index in range(0, len(hex_data), 64)]
    return "{" + "".join(controls) + "\n" + "\n".join(lines) + "}"


def _emit_hyperlink(link: RtfHyperlink, color_indexes: dict[str, int], font_indexes: dict[str, int]) -> str:
    style = link.style or RtfTextStyle(underline=True)
    prefix = _style_prefix(style, color_indexes, font_indexes)
    return _rtf_hyperlink_field(link.url, link.text, prefix)


def _emit_part(part: RtfTextSegment | RtfImage | RtfHyperlink, color_indexes: dict[str, int], font_indexes: dict[str, int]) -> str:
    if isinstance(part, RtfImage):
        return _emit_image(part)
    if isinstance(part, RtfHyperlink):
        return _emit_hyperlink(part, color_indexes, font_indexes)
    return _emit_segment(part, color_indexes, font_indexes)


def tree_to_rtf(root: NoteNode, options: ExportOptions | None = None) -> str:
    """Create a combined RTF export for a whole Notizen subtree.

    The old application clipboard-pasted each RichTextBox body into a temporary
    RichTextBox. This implementation keeps that document structure and preserves
    the formatting subset the port can safely parse: bold, italic, underline,
    strikeout, font size, font family, foreground color, background highlight
    embedded PNG/JPEG/BMP/WMF/EMF pictures, RTF hyperlink fields and visible legacy object placeholders.
    """
    options = options or ExportOptions()
    entries = _collect_body_parts(root, options)
    color_indexes = _collect_colors(entries)
    font_indexes = _collect_fonts(entries)
    body: list[str] = []
    for heading, parts in entries:
        body.append(r"{\b\fs28 " + _rtf_escape_text(heading) + r"}\par" + "\n")
        body.append(r"\par" + "\n" * max(1, options.title_separator_blank_lines - 1))
        if parts:
            body.extend(_emit_part(part, color_indexes, font_indexes) for part in parts)
            body.append(r"\par" + "\n")
        body.append(r"\par" + "\n" * max(1, options.body_separator_blank_lines - 1))
    return (
        r"{\rtf1\ansi\ansicpg1252\deff0\deflang1031"
        + _font_table(font_indexes)
        + _color_table(color_indexes)
        + r"\viewkind4\uc1\pard\f0\fs17 "
        + "".join(body).rstrip()
        + "\n}\n"
    )


def create_unified_note(source: NoteNode, title: str = "Zusammenfassung") -> NoteNode:
    """Return a new note containing a combined RTF snapshot of ``source``."""
    return NoteNode(title=title, rtf=tree_to_rtf(source))
