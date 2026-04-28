from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

from .model import Note, NoteDocument, StickyWindow
from .rtf import text_to_rtf

_META_PREFIX = "_notizen_"


@dataclass(slots=True, frozen=True)
class OpmlOptions:
    include_metadata: bool = True
    include_rtf: bool = True
    include_plain_text: bool = True


def note_to_opml(
    note: Note,
    *,
    title: str | None = None,
    include_metadata: bool = True,
    include_rtf: bool = True,
    include_plain_text: bool = True,
) -> str:
    """Serialize a note/subtree to OPML 2.0.

    OPML is not part of the old Notizen.NET file format, but it maps well to the
    old TreeView outline and is useful for exchanging trees with outliners.  The
    private ``_notizen_*`` attributes keep enough data for round-trips back into
    ``.alx`` without forcing other OPML tools to understand RTF or sticky notes.
    """

    root = ET.Element("opml", {"version": "2.0"})
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "title").text = title or note.title or "Notizen"
    ET.SubElement(head, "dateCreated").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
    ET.SubElement(head, "generator").text = "notizen-py-slint"
    body = ET.SubElement(root, "body")
    body.append(_note_to_outline(note, include_metadata=include_metadata, include_rtf=include_rtf, include_plain_text=include_plain_text))
    _indent(root)
    return ET.tostring(root, encoding="unicode", short_empty_elements=True)


def document_to_opml(
    document: NoteDocument,
    *,
    start: Note | None = None,
    title: str | None = None,
    include_metadata: bool = True,
    include_rtf: bool = True,
    include_plain_text: bool = True,
) -> str:
    return note_to_opml(start or document.root, title=title, include_metadata=include_metadata, include_rtf=include_rtf, include_plain_text=include_plain_text)


def write_opml(
    document: NoteDocument,
    path: str | Path,
    *,
    start: Note | None = None,
    title: str | None = None,
    include_metadata: bool = True,
    include_rtf: bool = True,
    include_plain_text: bool = True,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        document_to_opml(
            document,
            start=start,
            title=title,
            include_metadata=include_metadata,
            include_rtf=include_rtf,
            include_plain_text=include_plain_text,
        ),
        encoding="utf-8",
    )
    return target


def read_opml(path: str | Path) -> Note:
    return opml_to_note(Path(path).read_text(encoding="utf-8-sig"))


def opml_to_note(xml_text: str) -> Note:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"OPML konnte nicht gelesen werden: {exc}") from exc
    if root.tag.lower() != "opml":
        raise ValueError(f"Kein OPML-Dokument: <{root.tag}>")
    body = root.find("body")
    if body is None:
        raise ValueError("OPML enthält keinen <body>.")
    outlines = [child for child in list(body) if _local_name(child.tag) == "outline"]
    if not outlines:
        return Note("OPML", text_to_rtf(""))
    notes = [_outline_to_note(item) for item in outlines]
    if len(notes) == 1:
        return notes[0]
    title = _head_title(root) or "OPML"
    synthetic = Note(title, text_to_rtf(""))
    for note in notes:
        synthetic.add_child(note)
    return synthetic


def _note_to_outline(note: Note, *, include_metadata: bool, include_rtf: bool, include_plain_text: bool) -> ET.Element:
    attrs: dict[str, str] = {
        "text": note.title or "...",
        "type": "notizen-note",
    }
    plain = note.text
    if plain and include_plain_text:
        attrs["_note"] = plain
    if include_metadata:
        attrs[_META_PREFIX + "expanded"] = "true" if note.expanded else "false"
        if note.bg_color is not None:
            attrs[_META_PREFIX + "bgcolor"] = str(int(note.bg_color))
        if note.fg_color is not None:
            attrs[_META_PREFIX + "fgcolor"] = str(int(note.fg_color))
        if include_rtf and note.rtf:
            attrs[_META_PREFIX + "rtf_b64"] = b64encode(note.rtf.encode("utf-8")).decode("ascii")
        if include_plain_text and plain:
            attrs[_META_PREFIX + "text"] = plain
        if note.sticky is not None:
            attrs[_META_PREFIX + "sticky_visible"] = "true" if note.sticky.visible else "false"
            for name in ("x", "y", "width", "height"):
                value = getattr(note.sticky, name)
                if value is not None:
                    attrs[_META_PREFIX + f"sticky_{name}"] = str(int(value))
            if note.sticky.opacity is not None:
                attrs[_META_PREFIX + "sticky_opacity"] = str(float(note.sticky.opacity))
            if note.sticky.argb is not None:
                attrs[_META_PREFIX + "sticky_argb"] = str(int(note.sticky.argb))
    el = ET.Element("outline", attrs)
    for child in note.children:
        el.append(_note_to_outline(child, include_metadata=include_metadata, include_rtf=include_rtf, include_plain_text=include_plain_text))
    return el


def _outline_to_note(element: ET.Element) -> Note:
    attrs = element.attrib
    title = attrs.get("text") or attrs.get("title") or attrs.get("name") or "..."
    rtf = ""
    raw_rtf = attrs.get(_META_PREFIX + "rtf_b64")
    if raw_rtf:
        try:
            rtf = b64decode(raw_rtf.encode("ascii"), validate=False).decode("utf-8")
        except Exception:
            rtf = ""
    if not rtf:
        text = attrs.get(_META_PREFIX + "text") or attrs.get("_note") or attrs.get("description") or ""
        rtf = text_to_rtf(text)
    note = Note(
        title=title,
        rtf=rtf,
        expanded=_parse_bool(attrs.get(_META_PREFIX + "expanded"), True),
        bg_color=_optional_int(attrs.get(_META_PREFIX + "bgcolor")),
        fg_color=_optional_int(attrs.get(_META_PREFIX + "fgcolor")),
        sticky=_sticky_from_attrs(attrs),
    )
    for child in list(element):
        if _local_name(child.tag) == "outline":
            note.add_child(_outline_to_note(child))
    return note


def _sticky_from_attrs(attrs: dict[str, str]) -> StickyWindow | None:
    keys = [
        _META_PREFIX + "sticky_visible",
        _META_PREFIX + "sticky_x",
        _META_PREFIX + "sticky_y",
        _META_PREFIX + "sticky_width",
        _META_PREFIX + "sticky_height",
        _META_PREFIX + "sticky_opacity",
        _META_PREFIX + "sticky_argb",
    ]
    if not any(key in attrs for key in keys):
        return None
    return StickyWindow(
        visible=_parse_bool(attrs.get(_META_PREFIX + "sticky_visible"), False),
        x=_optional_int(attrs.get(_META_PREFIX + "sticky_x")),
        y=_optional_int(attrs.get(_META_PREFIX + "sticky_y")),
        width=_optional_int(attrs.get(_META_PREFIX + "sticky_width")),
        height=_optional_int(attrs.get(_META_PREFIX + "sticky_height")),
        opacity=_optional_float(attrs.get(_META_PREFIX + "sticky_opacity")),
        argb=_optional_int(attrs.get(_META_PREFIX + "sticky_argb")),
    )


def _head_title(root: ET.Element) -> str | None:
    head = root.find("head")
    if head is None:
        return None
    title = head.find("title")
    return title.text if title is not None else None


def _optional_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        try:
            return int(str(value).strip(), 16)
        except ValueError:
            return None


def _optional_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "ja", "y", "j"}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _indent(elem: ET.Element, level: int = 0) -> None:
    indent = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        for child in elem:
            _indent(child, level + 1)
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = indent
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = indent


def opml_preview(xml_text: str, max_chars: int = 800) -> str:
    note = opml_to_note(xml_text)
    text = f"{note.title}\n" + "\n".join(child.title for child in note.children[:20])
    return escape(text[:max_chars])
