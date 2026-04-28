from __future__ import annotations

import gzip
from html import escape
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

from .des_compat import NotizenCryptoError, decrypt_notizen_payload, encrypt_notizen_payload, is_blank_password
from .model import Note, NoteDocument, StickyWindow
from .rtf import append_picture_to_rtf, append_text_to_rtf, extract_pictures, is_rtf, rtf_to_text, text_to_rtf, write_extracted_pictures


class NotizenFileError(Exception):
    pass


class EncryptedFileError(NotizenFileError):
    pass


class WrongPasswordError(NotizenFileError):
    pass


class NotizenExportError(NotizenFileError):
    pass


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




def export_html(document: NoteDocument, path: str | Path, *, start: Note | None = None, title: str | None = None) -> Path:
    """Export a print-friendly HTML outline.

    The old WinForms app had print/export flows tied to RichTextBox. HTML gives
    the Python/Slint port a portable preview/print target without extra packages.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(outline_html(document, start=start, title=title), encoding="utf-8")
    return path


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
        "article{margin:0 0 1.2rem 0;}",
        "h1,h2,h3,h4,h5,h6{margin:.7rem 0 .2rem;}",
        ".note-text{white-space:pre-wrap;margin:.2rem 0 .7rem 0;}",
        ".meta{color:#666;font-size:.85rem;}",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{escape(doc_title)}</h1>",
    ]

    def visit(note: Note, level: int) -> None:
        heading = min(level + 2, 6)
        parts.append(f'<article data-depth="{level}">')
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
        text = note.text.strip("\n")
        if text:
            parts.append(f'<div class="note-text">{escape(text)}</div>')
        parts.append("</article>")

    document.walk_with_level(visit, start=root)
    parts.extend(["</body>", "</html>", ""])
    return "\n".join(parts)

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
        "bgcolor": str(note.bg_color or 0),
        "fgcolor": str(note.fg_color or 0),
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
