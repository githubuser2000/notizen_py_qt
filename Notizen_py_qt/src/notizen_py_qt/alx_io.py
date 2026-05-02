from __future__ import annotations

import gzip
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from .legacy_colors import legacy_light_color_argb
from .models import DesktopNoteState, NoteDocument, NoteNode
from .rtf_utils import plain_text_to_rtf

GZIP_MAGIC = b"\x1f\x8b"
BLANK_PASSWORD_24 = " " * 24


@dataclass(frozen=True, slots=True)
class BackupEntry:
    """One Notizen.NET-style safety copy next to the saved ALX file."""

    path: Path
    created: datetime | None
    size: int


def backup_directory_for(path: str | Path) -> Path:
    """Return the legacy backup directory for an ALX file.

    Notizen.NET created safety copies in a sibling directory named like the
    document without the ``.alx`` suffix.  Example: ``notes.alx`` stores
    backups below ``notes/``.
    """

    return Path(path).with_suffix("")


def backup_file_pattern(path: str | Path) -> str:
    original = Path(path)
    suffix = original.suffix or ".alx"
    return f"{original.stem}-*{suffix}"


def parse_legacy_backup_timestamp(backup_path: str | Path, original_path: str | Path) -> datetime | None:
    """Parse ``name-YYYY-MM-DD-HH-MM-SS-ms.alx`` timestamps used by Notizen.NET."""

    backup = Path(backup_path)
    original = Path(original_path)
    suffix = original.suffix or backup.suffix
    prefix = f"{original.stem}-"
    name = backup.name
    if not name.startswith(prefix) or (suffix and not name.endswith(suffix)):
        return None
    stamp = name[len(prefix): -len(suffix) if suffix else None]
    parts = stamp.split("-")
    if len(parts) != 7:
        return None
    try:
        year, month, day, hour, minute, second, millisecond = (int(part) for part in parts)
        return datetime(year, month, day, hour, minute, second, millisecond * 1000)
    except ValueError:
        return None


def _backup_sort_value(entry: BackupEntry) -> tuple[datetime, str]:
    if entry.created is not None:
        return entry.created, entry.path.name
    try:
        return datetime.fromtimestamp(entry.path.stat().st_mtime), entry.path.name
    except OSError:
        return datetime.min, entry.path.name


def list_backups(path: str | Path) -> list[BackupEntry]:
    """List legacy safety copies, oldest first."""

    original = Path(path)
    backup_dir = backup_directory_for(original)
    if not backup_dir.exists():
        return []
    entries: list[BackupEntry] = []
    for candidate in backup_dir.glob(backup_file_pattern(original)):
        if not candidate.is_file():
            continue
        try:
            size = candidate.stat().st_size
        except OSError:
            continue
        entries.append(
            BackupEntry(
                path=candidate,
                created=parse_legacy_backup_timestamp(candidate, original),
                size=size,
            )
        )
    return sorted(entries, key=_backup_sort_value)


def prune_backups(path: str | Path, keep: int = 30) -> list[Path]:
    """Delete old safety copies and return the removed files."""

    if keep < 0:
        keep = 0
    entries = list_backups(path)
    if keep == 0:
        stale = entries
    else:
        stale = entries[:-keep]
    removed: list[Path] = []
    for entry in stale:
        try:
            entry.path.unlink()
            removed.append(entry.path)
        except OSError:
            pass
    return removed


class AlxError(Exception):
    """Base class for Notizen ALX file errors."""


class PasswordRequired(AlxError):
    """The file is encrypted and no password was supplied."""


class InvalidPassword(AlxError):
    """The supplied password could not decrypt the file."""


def normalize_password(password: str | None) -> str:
    password = password or ""
    if len(password) > 24:
        return password[:24]
    return password.ljust(24)


def _ascii_key(text: str) -> bytes:
    return text.encode("ascii", errors="replace")


def _password_keys(password: str | None) -> tuple[bytes, bytes, bytes]:
    p = normalize_password(password)
    return (
        _ascii_key(p[0:8]),
        _ascii_key(p[7:15]),
        _ascii_key(p[15:23]),
    )


def _des_module():
    try:
        from Crypto.Cipher import DES  # type: ignore
        from Crypto.Util.Padding import pad, unpad  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional package
        raise AlxError(
            "Encrypted ALX files need pycryptodome. Install with: "
            "python -m pip install 'notizen-py-qt[crypto]'"
        ) from exc
    return DES, pad, unpad


def _decrypt_legacy_bytes(data: bytes, password: str | None) -> bytes:
    if not password:
        raise PasswordRequired("This ALX file is encrypted. Please provide the Notizen.NET password.")
    DES, _pad, unpad = _des_module()
    out = data
    for key in _password_keys(password):
        cipher = DES.new(key, DES.MODE_CBC, iv=key)
        out = unpad(cipher.decrypt(out), DES.block_size)
    return out


def _encrypt_legacy_bytes(data: bytes, password: str | None) -> bytes:
    p = normalize_password(password)
    if p == BLANK_PASSWORD_24:
        return data
    DES, pad, _unpad = _des_module()
    out = data
    # Write order in VB: GZip -> DES3 -> DES2 -> DES1 -> file.
    for key in reversed(_password_keys(p)):
        cipher = DES.new(key, DES.MODE_CBC, iv=key)
        out = cipher.encrypt(pad(out, DES.block_size))
    return out


def _maybe_decompress(data: bytes, password: str | None) -> bytes:
    if data.startswith(GZIP_MAGIC):
        return gzip.decompress(data)
    if data.startswith(b"\xff\xfe<") or data.startswith(b"\xfe\xff\x00<") or data.lstrip().startswith(b"<"):
        return data
    try:
        decrypted = _decrypt_legacy_bytes(data, password)
        return gzip.decompress(decrypted)
    except PasswordRequired:
        raise
    except Exception as exc:
        raise InvalidPassword("Could not decrypt or decompress the ALX file with the supplied password.") from exc


def _decode_xml(data: bytes) -> str:
    for encoding in ("utf-16", "utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _bool_attr(value: str | None, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"true", "1", "yes", "ja"}


def _int_attr(element: ET.Element, name: str, default: int = 0) -> int:
    value = element.get(name)
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except ValueError:
        return default


def _float_attr(element: ET.Element, name: str, default: float = 0.85) -> float:
    value = element.get(name)
    if value is None or value == "":
        return default
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return default


def _desktop_state_from_element(element: ET.Element) -> DesktopNoteState | None:
    if not element.get("x"):
        return None
    return DesktopNoteState(
        x=_int_attr(element, "x", 80),
        y=_int_attr(element, "y", 80),
        width=_int_attr(element, "width", 260),
        height=_int_attr(element, "height", 220),
        visible=_bool_attr(element.get("visible"), True),
        opacity=_float_attr(element, "opacity", 0.85),
        argb=_int_attr(element, "argb", legacy_light_color_argb()),
    )


def _parse_notiz(element: ET.Element) -> NoteNode:
    node = NoteNode(
        title=element.get("name") or element.get("title") or "...",
        rtf=element.text or "",
        expanded=_bool_attr(element.get("isexpanded"), True),
        bg_argb=_int_attr(element, "bgcolor", 0),
        fg_argb=_int_attr(element, "fgcolor", 0),
        desktop_note=_desktop_state_from_element(element),
    )
    for child_element in element:
        if child_element.tag == "Notiz":
            node.add_child(_parse_notiz(child_element))
    return node


def _parse_legacy_leaf_text(element: ET.Element) -> str:
    paragraphs: list[str] = []
    for paragraph in element.findall(".//p"):
        if paragraph.text:
            paragraphs.append(paragraph.text)
    if not paragraphs and element.text:
        paragraphs.append(element.text)
    return plain_text_to_rtf("\n".join(paragraphs))


def _parse_legacy_node(element: ET.Element) -> NoteNode:
    node = NoteNode(title=element.get("title") or element.get("name") or "...")
    for child_element in element:
        if child_element.tag == "leaf_text":
            node.rtf = _parse_legacy_leaf_text(child_element)
        elif child_element.tag in {"node", "leaf"}:
            node.add_child(_parse_legacy_node(child_element))
    return node


def parse_alx_xml(xml_text: str) -> NoteDocument:
    root_element = ET.fromstring(xml_text)
    document = NoteDocument()
    if root_element.tag == "notizen-alx2":
        first = next((child for child in root_element if child.tag == "Notiz"), None)
        if first is not None:
            document.root = _parse_notiz(first)
    elif root_element.tag == "notes_doc":
        first = next((child for child in root_element if child.tag in {"node", "leaf"}), None)
        if first is not None:
            document.root = _parse_legacy_node(first)
    else:
        raise AlxError(f"Unsupported Notizen XML root: {root_element.tag!r}")
    if document.root is None:
        document.root = NoteNode(title="start", rtf="")
    document.changed = False
    return document


def load_alx_bytes(data: bytes, password: str | None = None, *, path: str | Path | None = None) -> NoteDocument:
    xml_bytes = _maybe_decompress(data, password)
    xml_text = _decode_xml(xml_bytes)
    document = parse_alx_xml(xml_text)
    document.path = Path(path) if path is not None else None
    document.password = password or ""
    return document


def load_alx(path: str | Path, password: str | None = None) -> NoteDocument:
    path = Path(path)
    return load_alx_bytes(path.read_bytes(), password=password, path=path)


def _element_from_note(node: NoteNode) -> ET.Element:
    element = ET.Element("Notiz")
    element.set("name", node.title)
    element.set("isexpanded", "True" if node.expanded else "False")
    element.set("bgcolor", str(node.bg_argb))
    element.set("fgcolor", str(node.fg_argb))
    if node.desktop_note is not None:
        desk = node.desktop_note
        element.set("visible", "True" if desk.visible else "False")
        element.set("x", str(desk.x))
        element.set("y", str(desk.y))
        element.set("width", str(desk.width))
        element.set("height", str(desk.height))
        element.set("opacity", str(desk.opacity))
        if desk.argb is not None:
            element.set("argb", str(desk.argb))
    element.text = node.rtf or ""
    for child in node.children:
        element.append(_element_from_note(child))
    return element


def document_to_xml_bytes(document: NoteDocument) -> bytes:
    root = ET.Element("notizen-alx2")
    root.append(_element_from_note(document.ensure_root()))
    tree = ET.ElementTree(root)
    import io

    buffer = io.BytesIO()
    tree.write(buffer, encoding="utf-16", xml_declaration=True, short_empty_elements=True)
    return buffer.getvalue()


def create_backup(path: str | Path, keep: int = 30) -> Path | None:
    """Create one legacy safety copy before overwriting a saved ALX file."""

    target = Path(path)
    if keep <= 0 or not target.exists():
        return None
    backup_dir = backup_directory_for(target)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3]
    suffix = target.suffix or ".alx"
    backup = backup_dir / f"{target.stem}-{stamp}{suffix}"
    shutil.copy2(target, backup)
    prune_backups(target, keep=keep)
    return backup


def dump_alx_bytes(document: NoteDocument, password: str | None = None) -> bytes:
    xml_bytes = document_to_xml_bytes(document)
    gzipped = gzip.compress(xml_bytes, compresslevel=6, mtime=0)
    return _encrypt_legacy_bytes(gzipped, password if password is not None else document.password)


def save_alx(
    document: NoteDocument,
    path: str | Path | None = None,
    password: str | None = None,
    *,
    backup: bool = True,
    backup_keep: int = 30,
) -> Path:
    target = Path(path or document.path or "unbenannt.alx")
    if target.suffix.lower() != ".alx":
        target = target.with_suffix(".alx")
    target.parent.mkdir(parents=True, exist_ok=True)
    if backup:
        create_backup(target, keep=backup_keep)
    target.write_bytes(dump_alx_bytes(document, password=password))
    document.mark_saved(target)
    if password is not None:
        document.password = password
    return target
