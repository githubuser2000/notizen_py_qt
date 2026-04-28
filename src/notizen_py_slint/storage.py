from __future__ import annotations

from dataclasses import dataclass
import gzip
import json
from html import escape
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

from .des_compat import NotizenCryptoError, decrypt_notizen_payload, encrypt_notizen_payload, is_blank_password
from .model import Note, NoteDocument, StickyWindow
from .legacy_colors import argb_to_signed
from .rtf import (
    append_picture_to_rtf,
    append_text_to_rtf,
    change_rtf_font_size,
    extract_pictures,
    is_rtf,
    replace_rtf_text_range,
    restyle_rtf_with_defaults,
    rtf_to_html_fragment,
    rtf_to_text,
    set_rtf_font_size,
    style_rtf_text_range,
    text_to_rtf,
    write_extracted_pictures,
)


class NotizenFileError(Exception):
    pass


class EncryptedFileError(NotizenFileError):
    pass


class WrongPasswordError(NotizenFileError):
    pass


class NotizenExportError(NotizenFileError):
    pass


@dataclass(slots=True, frozen=True)
class BackupInfo:
    path: Path
    created: float
    size: int

    @property
    def name(self) -> str:
        return self.path.name

    def as_dict(self) -> dict[str, object]:
        return {"path": str(self.path), "name": self.name, "created": self.created, "size": self.size}


def load_document(path: str | Path, password: str | None = None) -> NoteDocument:
    path = Path(path)
    return load_document_from_bytes(path.read_bytes(), source=str(path), password=password)


def load_document_from_bytes(raw: bytes, *, source: str | None = None, password: str | None = None) -> NoteDocument:
    xml_bytes, used_password = _decode_payload(raw, password)
    xml_text = _decode_xml(xml_bytes)
    try:
        root_el = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise NotizenFileError(f"XML konnte nicht gelesen werden: {exc}") from exc

    if root_el.tag == "notizen-alx2":
        note_elements = [child for child in list(root_el) if child.tag == "Notiz"]
        if not note_elements:
            root = Note("start", text_to_rtf(""))
        else:
            root = _parse_notiz(note_elements[0])
            # Defensive: preserve additional top-level notes by attaching them under
            # the first one. The original app expected one root node, but malformed
            # files sometimes carry more.
            for extra in note_elements[1:]:
                root.add_child(_parse_notiz(extra))
    elif root_el.tag == "notes_doc":
        root = _parse_intellibit_document(root_el)
    else:
        raise NotizenFileError(f"Unbekanntes Notizen-Format: <{root_el.tag}>")

    return NoteDocument(root=root, path=source, password=used_password, modified=False, selected_id=root.note_id)


def save_document(
    document: NoteDocument,
    path: str | Path | None = None,
    password: str | None | object = ...,  # ellipsis means keep existing password
    backup_count: int = 30,
) -> Path:
    target = Path(path or document.path or "unbenannt.alx")
    if password is ...:
        effective_password = document.password
    else:
        effective_password = password  # type: ignore[assignment]

    if target.exists() and backup_count > 0:
        _make_backup(target, backup_count)

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() == ".xml":
        target.write_bytes(document_to_xml_bytes(document))
        document.password = None
    else:
        payload = save_document_to_bytes(document, password=effective_password if isinstance(effective_password, str) else None)
        target.write_bytes(payload)
        document.password = effective_password if isinstance(effective_password, str) and not is_blank_password(effective_password) else None
    document.path = str(target)
    document.modified = False
    return target


def save_document_to_bytes(document: NoteDocument, password: str | None | object = ...) -> bytes:
    if password is ...:
        effective_password = document.password
    else:
        effective_password = password  # type: ignore[assignment]
    xml_bytes = document_to_xml_bytes(document)
    gzip_payload = gzip.compress(xml_bytes, compresslevel=9)
    return encrypt_notizen_payload(gzip_payload, effective_password if isinstance(effective_password, str) else None)


def document_to_xml_bytes(document: NoteDocument) -> bytes:
    root_el = ET.Element("notizen-alx2")
    root_el.append(_note_to_element(document.root))
    return ET.tostring(root_el, encoding="utf-16", xml_declaration=True, short_empty_elements=False)


def read_raw_xml(path: str | Path, password: str | None = None) -> str:
    """Return the uncompressed/decrypted XML text from .alx or plain .xml."""
    xml_bytes, _ = _decode_payload(Path(path).read_bytes(), password)
    return _decode_xml(xml_bytes)


def write_raw_xml(xml: str | bytes, output: str | Path, password: str | None = None, backup_count: int = 0) -> Path:
    """Normalize raw Notizen XML into an .alx/.xml output file."""
    raw = xml.encode("utf-16") if isinstance(xml, str) else xml
    document = load_document_from_bytes(raw)
    return save_document(document, path=output, password=password, backup_count=backup_count)


def export_text(document: NoteDocument, path: str | Path, *, start: Note | None = None, numbered: bool = False) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(outline_text(document, start=start, numbered=numbered), encoding="utf-8")
    return path


def export_rtf(document: NoteDocument, path: str | Path, *, start: Note | None = None, numbered: bool = False) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text_to_rtf(outline_text(document, start=start, numbered=numbered)), encoding="utf-8")
    return path


def legacy_export_text(document: NoteDocument, *, start: Note | None = None, numbered: bool = True) -> str:
    """Return text close to the old Notizen.NET TXT export.

    The original ``export_txt`` path converted the RichTextBox text through the
    system default codepage and normalized line endings to CRLF.  The portable
    version keeps the same outline semantics and CRLF normalization while letting
    callers choose the target encoding explicitly.
    """
    text = outline_text(document, start=start, numbered=numbered)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\r\n")


def export_legacy_text(
    document: NoteDocument,
    path: str | Path,
    *,
    start: Note | None = None,
    numbered: bool = True,
    encoding: str = "cp1252",
    errors: str = "replace",
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(legacy_export_text(document, start=start, numbered=numbered).encode(encoding, errors=errors))
    return path


def export_unity_rtf(document: NoteDocument, path: str | Path, *, start: Note | None = None, numbered: bool = True) -> Path:
    """Export a subtree in the spirit of the old Einheit/Zusammenfassen RTF flow."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text_to_rtf(
            outline_text(document, start=start, numbered=numbered),
            font_family="Arial",
            font_size_half_points=20,
        ),
        encoding="utf-8",
    )
    return path


def export_html(document: NoteDocument, path: str | Path, *, start: Note | None = None, title: str | None = None) -> Path:
    """Export a print-friendly HTML outline.

    The old WinForms app had print/export flows tied to RichTextBox. HTML gives
    the Python/Slint port a portable preview/print target without extra packages.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(outline_html(document, start=start, title=title), encoding="utf-8")
    return path


def export_markdown(document: NoteDocument, path: str | Path, *, start: Note | None = None, title: str | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(outline_markdown(document, start=start, title=title), encoding="utf-8")
    return path


def export_json(document: NoteDocument, path: str | Path, *, start: Note | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "notizen-py-slint-subtree",
        "version": 1,
        "note": note_to_dict(start or document.root),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path



def apply_toolbar_style_to_note(
    note: Note,
    style: str = "regular",
    *,
    font_family: str | None = None,
    font_size_half_points: int | None = None,
    fg_color: int | None = None,
    bg_color: int | None = None,
) -> None:
    """Apply the old toolbar-style action to the whole note.

    The WinForms app applied bold/italic/underline/strike/regular to the current
    RichTextBox selection, or to the whole note when nothing was selected. Slint's
    editor is plain text, so this portable version deliberately formats the whole
    note while preserving unspecified global font defaults.
    """
    style_key = (style or "regular").strip().lower()
    styles = {
        "bold": dict(bold=True, italic=False, underline=False, strike=False),
        "b": dict(bold=True, italic=False, underline=False, strike=False),
        "italic": dict(bold=False, italic=True, underline=False, strike=False),
        "i": dict(bold=False, italic=True, underline=False, strike=False),
        "underline": dict(bold=False, italic=False, underline=True, strike=False),
        "u": dict(bold=False, italic=False, underline=True, strike=False),
        "strike": dict(bold=False, italic=False, underline=False, strike=True),
        "strikeout": dict(bold=False, italic=False, underline=False, strike=True),
        "s": dict(bold=False, italic=False, underline=False, strike=True),
        "regular": dict(bold=False, italic=False, underline=False, strike=False),
        "normal": dict(bold=False, italic=False, underline=False, strike=False),
    }
    if style_key not in styles:
        raise ValueError(f"Unbekannter Stil: {style}")
    note.rtf = restyle_rtf_with_defaults(
        note.rtf,
        font_family=font_family,
        font_size_half_points=font_size_half_points,
        fg_color=fg_color,
        bg_color=bg_color,
        **styles[style_key],
    )


def apply_font_family_to_note(note: Note, font_family: str) -> None:
    note.rtf = restyle_rtf_with_defaults(note.rtf, font_family=font_family or "Sans Serif")

def export_note_images(note: Note, directory: str | Path) -> list[Path]:
    return write_extracted_pictures(note.rtf, directory)


def export_document_images(document: NoteDocument, directory: str | Path) -> list[Path]:
    """Extract all embedded RTF pictures into a directory tree."""
    directory = Path(directory)
    paths: list[Path] = []
    for note in document.iter_notes():
        pictures = extract_pictures(note.rtf)
        if not pictures:
            continue
        note_dir = directory / _safe_path_part(note.path_string())
        note_dir.mkdir(parents=True, exist_ok=True)
        for picture in pictures:
            target = note_dir / picture.filename
            target.write_bytes(picture.data)
            paths.append(target)
    return paths


def export_sticky_html(document: NoteDocument, path: str | Path, *, visible_only: bool = True, title: str | None = None) -> Path:
    """Export sticky note metadata as a small desktop-board HTML file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(outline_sticky_html(document, visible_only=visible_only, title=title), encoding="utf-8")
    return path


def sticky_manifest(document: NoteDocument, *, visible_only: bool = True) -> list[dict[str, object]]:
    """Return sticky-note metadata in a serialisable form.

    Notizen.NET opened desktop note windows from the same attributes that are
    stored in the XML. Slint cannot recreate the WinForms floating windows without
    a platform-specific shell layer, but this manifest is enough for HTML export,
    tests, and future native integration while preserving the original data.
    """
    items: list[dict[str, object]] = []
    for note in document.iter_notes():
        sticky = note.sticky
        if sticky is None:
            continue
        if visible_only and not sticky.visible:
            continue
        items.append(
            {
                "path": note.path_titles(),
                "path_string": note.path_string(),
                "title": note.title,
                "text": note.text,
                "html": rtf_to_html_fragment(note.rtf),
                "visible": sticky.visible,
                "x": sticky.x,
                "y": sticky.y,
                "width": sticky.width,
                "height": sticky.height,
                "opacity": sticky.opacity,
                "argb": sticky.argb,
                "background": _argb_to_css(sticky.argb) or _argb_to_css(note.bg_color),
                "foreground": _argb_to_css(note.fg_color),
            }
        )
    return items


def outline_sticky_html(document: NoteDocument, *, visible_only: bool = True, title: str | None = None) -> str:
    """Create an HTML board from sticky metadata and note content."""
    doc_title = title or "Sticky-Notizen"
    items = sticky_manifest(document, visible_only=visible_only)
    parts = [
        "<!doctype html>",
        '<html lang="de">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>{escape(doc_title)}</title>",
        "<style>",
        "body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f3f4f6;color:#111827;}",
        ".board{position:relative;min-height:100vh;padding:24px;}",
        ".sticky{position:absolute;box-sizing:border-box;overflow:auto;padding:.7rem .8rem;border:1px solid rgba(0,0,0,.18);border-radius:.45rem;box-shadow:0 10px 22px rgba(0,0,0,.18);}",
        ".sticky h2{font-size:1rem;margin:.05rem 0 .45rem 0;}",
        ".sticky .path{font-size:.72rem;opacity:.65;margin-bottom:.35rem;}",
        ".sticky .note-text p{white-space:pre-wrap;margin:.25rem 0 .5rem 0;}",
        ".sticky .note-text img{max-width:100%;height:auto;border:1px solid rgba(0,0,0,.12);}",
        ".empty{position:static;margin:2rem;padding:1rem;background:white;border-radius:.4rem;}",
        "</style>",
        "</head>",
        "<body>",
        '<main class="board">',
    ]
    if not items:
        parts.append('<div class="empty">Keine sichtbaren Sticky-Notizen gefunden.</div>')
    for index, item in enumerate(items):
        x = _css_px(item.get("x"), 32 + (index % 4) * 290)
        y = _css_px(item.get("y"), 32 + (index // 4) * 230)
        width = _css_px(item.get("width"), 260)
        height = _css_px(item.get("height"), 180)
        opacity = _css_opacity(item.get("opacity"))
        bg = str(item.get("background") or "#FFF8B8")
        fg = str(item.get("foreground") or "#111827")
        style = f"left:{x};top:{y};width:{width};min-height:{height};opacity:{opacity};background:{bg};color:{fg};"
        parts.append(f'<article class="sticky" data-index="{index}" style="{style}">')
        parts.append(f"<h2>{escape(str(item.get('title') or '...'))}</h2>")
        parts.append(f'<div class="path">{escape(str(item.get("path_string") or ""))}</div>')
        fragment = str(item.get("html") or "")
        if fragment:
            parts.append(f'<div class="note-text">{fragment}</div>')
        else:
            parts.append('<div class="note-text"><p></p></div>')
        parts.append("</article>")
    parts.extend(["</main>", "</body>", "</html>", ""])
    return "\n".join(parts)


def autosize_sticky(
    note: Note,
    *,
    min_width: int = 180,
    max_width: int = 560,
    min_height: int = 120,
    max_height: int = 760,
) -> StickyWindow:
    """Estimate sticky window size from title/text and store it on the note."""
    sticky = note.sticky or StickyWindow(visible=True, x=100, y=100, opacity=0.85, argb=note.bg_color)
    text_lines = (note.text or "").splitlines() or [""]
    longest = max([len(note.title or ""), *[len(line) for line in text_lines]])
    width = max(min_width, min(max_width, longest * 8 + 54))
    chars_per_line = max(18, (width - 54) // 8)
    visual_lines = 0
    for line in text_lines:
        visual_lines += max(1, (len(line) + chars_per_line - 1) // chars_per_line)
    height = max(min_height, min(max_height, visual_lines * 21 + 74))
    sticky.visible = True
    sticky.width = width
    sticky.height = height
    if sticky.x is None:
        sticky.x = 100
    if sticky.y is None:
        sticky.y = 100
    if sticky.opacity is None:
        sticky.opacity = 0.85
    if sticky.argb is None and note.bg_color not in (None, 0):
        sticky.argb = note.bg_color
    note.sticky = sticky
    return sticky


def set_note_font_size(note: Note, half_points: int) -> Note:
    note.rtf = set_rtf_font_size(note.rtf, half_points)
    return note


def change_note_font_size(note: Note, delta_half_points: int) -> Note:
    note.rtf = change_rtf_font_size(note.rtf, delta_half_points)
    return note


def outline_html(document: NoteDocument, *, start: Note | None = None, title: str | None = None) -> str:
    root = start or document.root
    doc_title = title or root.title or "Notizen"
    parts = [
        "<!doctype html>",
        '<html lang="de">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>{escape(doc_title)}</title>",
        "<style>",
        "body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.45;margin:2rem;}",
        "article{margin:0 0 1.2rem 0;padding:.35rem .55rem;border-radius:.35rem;}",
        "h1,h2,h3,h4,h5,h6{margin:.7rem 0 .2rem;}",
        ".note-text{white-space:normal;margin:.2rem 0 .7rem 0;}",
        ".note-text p{white-space:pre-wrap;margin:.2rem 0 .55rem 0;}",
        ".note-text figure{margin:.4rem 0;}",
        ".note-text img{max-width:100%;height:auto;border:1px solid #ddd;}",
        ".embedded-object,.meta{color:#666;font-size:.85rem;}",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{escape(doc_title)}</h1>",
    ]

    def visit(note: Note, level: int) -> None:
        heading = min(level + 2, 6)
        style = _note_html_style(note)
        parts.append(f'<article data-depth="{level}"{style}>')
        parts.append(f"<h{heading}>{escape(note.title or '...')}</h{heading}>")
        meta: list[str] = []
        if note.sticky is not None:
            meta.append("Sticky: " + note.sticky.summary())
        if note.bg_color not in (None, 0):
            meta.append(f"bgcolor={note.bg_color}")
        if note.fg_color not in (None, 0):
            meta.append(f"fgcolor={note.fg_color}")
        if meta:
            parts.append(f'<div class="meta">{escape(" | ".join(meta))}</div>')
        fragment = rtf_to_html_fragment(note.rtf)
        if fragment:
            parts.append(f'<div class="note-text">{fragment}</div>')
        parts.append("</article>")

    document.walk_with_level(visit, start=root)
    parts.extend(["</body>", "</html>", ""])
    return "\n".join(parts)


def outline_markdown(document: NoteDocument, *, start: Note | None = None, title: str | None = None) -> str:
    root = start or document.root
    doc_title = title or root.title or "Notizen"
    parts: list[str] = [f"# {doc_title}", ""]

    def visit(note: Note, level: int) -> None:
        heading = "#" * min(level + 2, 6)
        parts.append(f"{heading} {note.title or '...'}")
        meta: list[str] = []
        if note.sticky is not None:
            meta.append("Sticky: " + note.sticky.summary())
        if note.bg_color not in (None, 0):
            meta.append(f"bgcolor={note.bg_color}")
        if note.fg_color not in (None, 0):
            meta.append(f"fgcolor={note.fg_color}")
        if meta:
            parts.append("_")
            parts.append(" | ".join(meta))
            parts.append("_")
        text = note.text.strip("\n")
        if text:
            parts.append("")
            parts.extend(text.splitlines())
        pictures = extract_pictures(note.rtf)
        if pictures:
            parts.append("")
            for picture in pictures:
                parts.append(f"[eingebettetes Bild/Objekt: {picture.filename}]")
        parts.append("")

    document.walk_with_level(visit, start=root)
    return "\n".join(parts).rstrip() + "\n"


def combine_subtree_to_new_note(
    document: NoteDocument,
    *,
    start: Note | None = None,
    title: str | None = None,
    numbered: bool = True,
    attach_to_root: bool = True,
) -> Note:
    """Create a new note containing a flattened outline of a subtree.

    This ports Notizen.NET's old "Einheit/Zusammenfassen" action in a
    Slint-friendly way. The original built a temporary RichTextBox and pasted all
    nodes into a new node. Here we generate simple RTF from the same outline so
    the operation works without a GUI or clipboard.
    """
    root = start or document.selected_note
    note_title = title or f"Zusammenfassung: {root.title or 'Notizen'}"
    new_note = Note(note_title, text_to_rtf(outline_text(document, start=root, numbered=numbered)))
    parent = document.root if attach_to_root else root
    parent.add_child(new_note)
    parent.expanded = True
    document.select(new_note)
    document.modified = True
    return new_note


def note_to_dict(note: Note) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": note.title,
        "text": note.text,
        "rtf": note.rtf,
        "expanded": note.expanded,
        "bg_color": note.bg_color,
        "fg_color": note.fg_color,
        "children": [note_to_dict(child) for child in note.children],
    }
    if note.sticky is not None:
        payload["sticky"] = {
            "visible": note.sticky.visible,
            "x": note.sticky.x,
            "y": note.sticky.y,
            "width": note.sticky.width,
            "height": note.sticky.height,
            "opacity": note.sticky.opacity,
            "argb": note.sticky.argb,
        }
    return payload


def note_from_dict(data: dict[str, object]) -> Note:
    if not isinstance(data, dict):
        raise NotizenFileError("JSON-Notiz ist kein Objekt.")
    sticky_data = data.get("sticky")
    sticky = None
    if isinstance(sticky_data, dict):
        sticky = StickyWindow(
            visible=bool(sticky_data.get("visible", False)),
            x=_json_optional_int(sticky_data.get("x")),
            y=_json_optional_int(sticky_data.get("y")),
            width=_json_optional_int(sticky_data.get("width")),
            height=_json_optional_int(sticky_data.get("height")),
            opacity=_json_optional_float(sticky_data.get("opacity")),
            argb=_json_optional_int(sticky_data.get("argb")),
        )
    rtf_value = data.get("rtf")
    if rtf_value in (None, "") and data.get("text") not in (None, ""):
        rtf_value = text_to_rtf(str(data.get("text") or ""))
    note = Note(
        title=str(data.get("title") or "..."),
        rtf=str(rtf_value or ""),
        expanded=bool(data.get("expanded", True)),
        bg_color=_json_optional_int(data.get("bg_color")),
        fg_color=_json_optional_int(data.get("fg_color")),
        sticky=sticky,
    )
    children = data.get("children", [])
    if not isinstance(children, list):
        raise NotizenFileError("JSON-Kinderliste ist ungültig.")
    for child_data in children:
        if not isinstance(child_data, dict):
            raise NotizenFileError("JSON-Kindnotiz ist ungültig.")
        note.add_child(note_from_dict(child_data))
    return note


def load_note_json(path: str | Path) -> Note:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NotizenFileError(f"JSON konnte nicht gelesen werden: {exc}") from exc
    if isinstance(data, dict) and data.get("format") == "notizen-py-slint-subtree":
        data = data.get("note")
    if not isinstance(data, dict):
        raise NotizenFileError("JSON enthält keine Notiz.")
    return note_from_dict(data)


def import_json_into_document(document: NoteDocument, path: str | Path, *, target: Note | None = None, where: str = "child") -> Note:
    imported = load_note_json(path)
    return import_note_into_document(document, imported, target=target, where=where)


def import_note_into_document(document: NoteDocument, note: Note, *, target: Note | None = None, where: str = "child") -> Note:
    """Insert a detached note/subtree into a document.

    The inserted tree is cloned so callers can pass notes from another loaded
    document without cross-linking parents between documents.
    """
    imported = note.clone_deep()
    target = target or document.selected_note
    if where == "child":
        created = target.add_child(imported)
        target.expanded = True
    elif where == "before":
        created = target.insert_before(imported)
    elif where == "after":
        created = target.insert_after(imported)
    else:
        raise NotizenFileError(f"Ungültige Importposition: {where}")
    document.select(created)
    document.modified = True
    return created


def import_document_root_into_document(document: NoteDocument, imported_document: NoteDocument, *, target: Note | None = None, where: str = "child") -> Note:
    """Import the root note of another Notizen document as a subtree."""
    return import_note_into_document(document, imported_document.root, target=target, where=where)


def _json_optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _json_optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _note_html_style(note: Note) -> str:
    styles: list[str] = []
    bg = _argb_to_css(note.bg_color)
    fg = _argb_to_css(note.fg_color)
    if bg:
        styles.append(f"background-color:{bg}")
    if fg:
        styles.append(f"color:{fg}")
    if not styles:
        return ""
    return ' style="' + ";".join(styles) + '"'


def _argb_to_css(value: int | None) -> str:
    if value in (None, 0):
        return ""
    unsigned = int(value) & 0xFFFFFFFF
    # XML stores ARGB, CSS wants RGB. Alpha is ignored for broad browser support.
    rgb = unsigned & 0x00FFFFFF
    return f"#{rgb:06X}"


def _css_px(value: object, fallback: int) -> str:
    try:
        numeric = int(value) if value not in (None, "") else int(fallback)
    except (TypeError, ValueError):
        numeric = int(fallback)
    return f"{max(0, numeric)}px"


def _css_opacity(value: object) -> str:
    try:
        numeric = float(value) if value not in (None, "") else 1.0
    except (TypeError, ValueError):
        numeric = 1.0
    numeric = max(0.05, min(1.0, numeric))
    return f"{numeric:.3g}"


def export_note_rtf(note: Note, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(note.rtf or text_to_rtf(""), encoding="utf-8")
    return path


def import_text_into_note(note: Note, path: str | Path) -> None:
    raw = Path(path).read_bytes()
    text = _decode_text_file(raw)
    note.set_text(text)




def append_text_into_note(note: Note, text: str) -> Note:
    note.rtf = append_text_to_rtf(note.rtf, text)
    return note


def append_current_date_into_note(note: Note) -> Note:
    from datetime import datetime

    stamp = datetime.now().strftime(" %d.%m.%Y %H:%M ")
    return append_text_into_note(note, stamp)


def append_bullet_into_note(note: Note) -> Note:
    return append_text_into_note(note, "\n•   ")


def insert_text_into_note(note: Note, text: str, at: int) -> Note:
    """Insert plain text at a RichTextBox-style character offset.

    Offsets refer to the note's plain text after best-effort RTF conversion.  The
    result is intentionally rewritten as simple RTF because Slint's editor has no
    RichTextBox selection object.
    """
    note.rtf = replace_rtf_text_range(note.rtf, at, 0, text)
    return note


def replace_note_text_range(
    note: Note,
    start: int,
    length: int | None,
    replacement: str,
    *,
    end: int | None = None,
) -> Note:
    note.rtf = replace_rtf_text_range(note.rtf, start, length, replacement, end=end)
    return note


def delete_note_text_range(note: Note, start: int, length: int | None, *, end: int | None = None) -> Note:
    return replace_note_text_range(note, start, length, "", end=end)


def style_note_text_range(
    note: Note,
    start: int,
    length: int | None,
    *,
    end: int | None = None,
    style: str | None = None,
    font_family: str | None = None,
    font_size_half_points: int | None = None,
    fg_color: int | None = None,
    bg_color: int | None = None,
) -> Note:
    """Apply a toolbar-like style to a selected plain-text range."""
    bold = italic = underline = strike = None
    style_key = (style or "").strip().lower()
    if style_key:
        styles = {
            "bold": dict(bold=True, italic=None, underline=None, strike=None),
            "b": dict(bold=True, italic=None, underline=None, strike=None),
            "italic": dict(bold=None, italic=True, underline=None, strike=None),
            "i": dict(bold=None, italic=True, underline=None, strike=None),
            "underline": dict(bold=None, italic=None, underline=True, strike=None),
            "u": dict(bold=None, italic=None, underline=True, strike=None),
            "strike": dict(bold=None, italic=None, underline=None, strike=True),
            "strikeout": dict(bold=None, italic=None, underline=None, strike=True),
            "s": dict(bold=None, italic=None, underline=None, strike=True),
            "regular": dict(bold=False, italic=False, underline=False, strike=False),
            "normal": dict(bold=False, italic=False, underline=False, strike=False),
        }
        if style_key not in styles:
            raise ValueError(f"Unbekannter Stil: {style}")
        selected = styles[style_key]
        bold = selected["bold"]
        italic = selected["italic"]
        underline = selected["underline"]
        strike = selected["strike"]
    note.rtf = style_rtf_text_range(
        note.rtf,
        start,
        length,
        end=end,
        font_family=font_family,
        font_size_half_points=font_size_half_points,
        bold=bold,
        italic=italic,
        underline=underline,
        strike=strike,
        fg_color=fg_color,
        bg_color=bg_color,
    )
    return note


def insert_current_date_into_note(note: Note, at: int) -> Note:
    from datetime import datetime

    stamp = datetime.now().strftime(" %d.%m.%Y %H:%M ")
    return insert_text_into_note(note, stamp, at)


def insert_bullet_into_note(note: Note, at: int) -> Note:
    return insert_text_into_note(note, "\n•   ", at)


def insert_image_into_note(note: Note, image_path: str | Path, *, width_twips: int | None = None, height_twips: int | None = None) -> Note:
    note.rtf = append_picture_to_rtf(note.rtf, image_path, width_twips=width_twips, height_twips=height_twips)
    return note

def import_rtf_into_note(note: Note, path: str | Path) -> None:
    raw = Path(path).read_bytes()
    text = _decode_text_file(raw)
    if is_rtf(text):
        note.set_rtf(text)
    else:
        note.set_text(text)


def outline_text(document: NoteDocument, *, start: Note | None = None, numbered: bool = False) -> str:
    lines: list[str] = []
    counters: list[int] = []

    def visit(note: Note, level: int) -> None:
        indent = "    " * level
        if numbered:
            while len(counters) <= level:
                counters.append(0)
            counters[level] += 1
            del counters[level + 1 :]
            number = ".".join(str(x) for x in counters) + ". "
        else:
            number = ""
        lines.append(f"{indent}{number}{note.title}")
        plain = note.text.strip("\n")
        if plain:
            for line in plain.splitlines():
                lines.append(f"{indent}  {line}")
        lines.append("")

    document.walk_with_level(visit, start=start)
    return "\n".join(lines).rstrip() + "\n"


def selected_outline_text(document: NoteDocument, *, numbered: bool = False) -> str:
    return outline_text(document, start=document.selected_note, numbered=numbered)


def _looks_like_plain_xml(raw: bytes) -> bool:
    sample = raw[:200].lstrip()
    if sample.startswith((b"<", b"\xef\xbb\xbf<", b"\xff\xfe", b"\xfe\xff")):
        return True
    return len(raw) > 4 and raw[0] == ord("<") and raw[1] == 0


def _decode_payload(raw: bytes, password: str | None) -> tuple[bytes, str | None]:
    if _looks_like_plain_xml(raw):
        return raw, None
    try:
        return gzip.decompress(raw), None if is_blank_password(password) else password
    except Exception as gzip_error:
        if is_blank_password(password):
            raise EncryptedFileError("Die Datei ist wahrscheinlich passwortgeschützt oder kein gültiges .alx/.xml.") from gzip_error
        try:
            decrypted = decrypt_notizen_payload(raw, password)
            return gzip.decompress(decrypted), password
        except NotizenCryptoError as exc:
            raise WrongPasswordError("Passwort falsch oder Datei beschädigt.") from exc
        except Exception as exc:
            raise WrongPasswordError("Passwort falsch oder Datei beschädigt.") from exc


def _decode_xml(xml_bytes: bytes) -> str:
    stripped = xml_bytes[:200].lstrip()
    if xml_bytes.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings = ("utf-16", "utf-8-sig", "utf-8", "cp1252")
    elif stripped.startswith((b"<", b"\xef\xbb\xbf<")):
        encodings = ("utf-8-sig", "utf-8", "cp1252", "utf-16")
    else:
        encodings = ("utf-16", "utf-8-sig", "utf-8", "cp1252")
    for encoding in encodings:
        try:
            return xml_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise NotizenFileError("Datei-Encoding konnte nicht erkannt werden.")


def _decode_text_file(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "utf-8", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "ja"}


def _parse_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_notiz(element: ET.Element) -> Note:
    attrs = element.attrib
    note = Note(
        title=attrs.get("name", "..."),
        rtf=element.text or "",
        expanded=_parse_bool(attrs.get("isexpanded"), True),
        bg_color=_parse_int(attrs.get("bgcolor")),
        fg_color=_parse_int(attrs.get("fgcolor")),
        sticky=StickyWindow.from_attrs(attrs),
    )
    for child_el in list(element):
        if child_el.tag == "Notiz":
            note.add_child(_parse_notiz(child_el))
    return note


def _note_to_element(note: Note) -> ET.Element:
    attrs: dict[str, str] = {
        "name": note.title or "...",
        "isexpanded": "True" if note.expanded else "False",
        "bgcolor": str(argb_to_signed(note.bg_color) or 0),
        "fgcolor": str(argb_to_signed(note.fg_color) or 0),
    }
    if note.sticky is not None:
        attrs.update(note.sticky.to_attrs())
    el = ET.Element("Notiz", attrs)
    el.text = note.rtf or ""
    for child in note.children:
        el.append(_note_to_element(child))
    return el


def _parse_intellibit_document(root_el: ET.Element) -> Note:
    candidates = [child for child in list(root_el) if child.tag in {"node", "leaf"}]
    if not candidates:
        return Note("start", text_to_rtf(""))
    root = _parse_intellibit_node(candidates[0])
    for extra in candidates[1:]:
        root.add_child(_parse_intellibit_node(extra))
    return root


def _parse_intellibit_node(element: ET.Element) -> Note:
    title = element.attrib.get("title") or element.attrib.get("name") or "..."
    text_parts: list[str] = []
    for leaf_text in element.findall("leaf_text"):
        for p in leaf_text.findall("p"):
            if p.text:
                text_parts.append(p.text)
    note = Note(title=title, rtf=text_to_rtf("\n".join(text_parts)))
    for child in list(element):
        if child.tag in {"node", "leaf"}:
            note.add_child(_parse_intellibit_node(child))
    return note


def _safe_path_part(value: str) -> str:
    cleaned = "__".join(part.strip() for part in value.replace("\\", "/").split("/") if part.strip())
    cleaned = "".join(ch if ch.isalnum() or ch in " ._-" else "_" for ch in cleaned)
    return cleaned[:160] or "notiz"


def backup_directory_for(target: str | Path) -> Path:
    return Path(target).with_suffix("")


def list_backups(target: str | Path) -> list[BackupInfo]:
    target_path = Path(target)
    directory = backup_directory_for(target_path)
    if not directory.exists():
        return []
    backups: list[BackupInfo] = []
    for path in sorted(directory.glob(f"{target_path.stem}-*{target_path.suffix}"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            stat = path.stat()
        except OSError:
            continue
        backups.append(BackupInfo(path=path, created=stat.st_mtime, size=stat.st_size))
    return backups


def restore_backup(backup: str | Path, target: str | Path | None = None, *, backup_current: bool = True) -> Path:
    backup_path = Path(backup)
    if not backup_path.exists():
        raise NotizenFileError(f"Backup nicht gefunden: {backup_path}")
    if target is None:
        target_path = backup_path.parent.with_suffix(backup_path.suffix)
    else:
        target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if backup_current and target_path.exists():
        _make_backup(target_path, keep=9999)
    shutil.copy2(backup_path, target_path)
    return target_path


def _make_backup(target: Path, keep: int) -> None:
    backup_dir = target.with_suffix("")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    backup_name = f"{target.stem}-{stamp}-{int((time.time() % 1) * 1000):03d}{target.suffix}"
    backup_path = backup_dir / backup_name
    try:
        shutil.copy2(target, backup_path)
    except OSError:
        return
    backups = sorted(backup_dir.glob(f"{target.stem}-*{target.suffix}"), key=lambda p: p.stat().st_mtime)
    excess = len(backups) - keep
    for old in backups[: max(0, excess)]:
        try:
            old.unlink()
        except OSError:
            pass
