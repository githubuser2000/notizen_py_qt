from __future__ import annotations

import gzip
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

from .des_compat import NotizenCryptoError, decrypt_notizen_payload, encrypt_notizen_payload, is_blank_password
from .model import Note, NoteDocument, StickyWindow
from .rtf import text_to_rtf


class NotizenFileError(Exception):
    pass


class EncryptedFileError(NotizenFileError):
    pass


class WrongPasswordError(NotizenFileError):
    pass


def load_document(path: str | Path, password: str | None = None) -> NoteDocument:
    path = Path(path)
    raw = path.read_bytes()
    xml_bytes: bytes
    used_password = password

    try:
        xml_bytes = gzip.decompress(raw)
        used_password = None if is_blank_password(password) else password
    except Exception as gzip_error:
        if is_blank_password(password):
            raise EncryptedFileError("Die Datei ist wahrscheinlich passwortgeschützt.") from gzip_error
        try:
            decrypted = decrypt_notizen_payload(raw, password)
            xml_bytes = gzip.decompress(decrypted)
        except NotizenCryptoError as exc:
            raise WrongPasswordError("Passwort falsch oder Datei beschädigt.") from exc
        except Exception as exc:
            raise WrongPasswordError("Passwort falsch oder Datei beschädigt.") from exc

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

    document = NoteDocument(root=root, path=str(path), password=used_password, modified=False, selected_id=root.note_id)
    return document


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

    root_el = ET.Element("notizen-alx2")
    root_el.append(_note_to_element(document.root))
    xml_bytes = ET.tostring(root_el, encoding="utf-16", xml_declaration=True, short_empty_elements=False)
    gzip_payload = gzip.compress(xml_bytes, compresslevel=9)
    payload = encrypt_notizen_payload(gzip_payload, effective_password if isinstance(effective_password, str) else None)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    document.path = str(target)
    document.password = effective_password if isinstance(effective_password, str) and not is_blank_password(effective_password) else None
    document.modified = False
    return target


def export_text(document: NoteDocument, path: str | Path) -> Path:
    path = Path(path)
    lines: list[str] = []

    def visit(note: Note, level: int) -> None:
        indent = "    " * level
        lines.append(f"{indent}{note.title}")
        plain = note.text.strip("\n")
        if plain:
            for line in plain.splitlines():
                lines.append(f"{indent}  {line}")
        lines.append("")

    document.walk_with_level(visit)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def export_rtf(document: NoteDocument, path: str | Path) -> Path:
    path = Path(path)
    lines: list[str] = []

    def visit(note: Note, level: int) -> None:
        lines.append(f"{'    ' * level}{note.title}")
        plain = note.text.strip("\n")
        if plain:
            for line in plain.splitlines():
                lines.append(f"{'    ' * level}  {line}")
        lines.append("")

    document.walk_with_level(visit)
    path.write_text(text_to_rtf("\n".join(lines).rstrip() + "\n"), encoding="utf-8")
    return path


def _decode_xml(xml_bytes: bytes) -> str:
    for encoding in ("utf-16", "utf-8-sig", "utf-8", "cp1252"):
        try:
            return xml_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise NotizenFileError("Datei-Encoding konnte nicht erkannt werden.")


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
    }
    if note.bg_color not in (None, 0):
        attrs["bgcolor"] = str(note.bg_color)
    if note.fg_color not in (None, 0):
        attrs["fgcolor"] = str(note.fg_color)
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
