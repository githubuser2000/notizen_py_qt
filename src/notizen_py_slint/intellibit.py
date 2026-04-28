from __future__ import annotations

"""Import/export helpers for the older ``notes_doc`` outline XML variant.

``Notizen.vb`` could read another XML format with a top-level ``notes_doc``
element, ``node``/``leaf`` entries and ``leaf_text`` paragraphs.  The old app
only used it as an import compatibility path; this module makes the conversion
explicit so users can round-trip or audit legacy outliner data from the CLI.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from .model import Note, NoteDocument


@dataclass(slots=True, frozen=True)
class NotesDocOptions:
    leaf_terminal_nodes: bool = True
    include_empty_paragraphs: bool = False
    encoding: str = "utf-8"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def document_to_notes_doc_xml(
    document: NoteDocument,
    *,
    start: Note | None = None,
    leaf_terminal_nodes: bool = True,
    include_empty_paragraphs: bool = False,
    encoding: str = "utf-8",
) -> bytes:
    """Serialize a Notizen tree as legacy ``notes_doc`` XML bytes."""
    root = ET.Element("notes_doc")
    root.append(
        _note_to_legacy_element(
            start or document.root,
            leaf_terminal_nodes=leaf_terminal_nodes,
            include_empty_paragraphs=include_empty_paragraphs,
        )
    )
    return ET.tostring(root, encoding=encoding, xml_declaration=True, short_empty_elements=False)


def write_notes_doc(
    document: NoteDocument,
    path: str | Path,
    *,
    start: Note | None = None,
    leaf_terminal_nodes: bool = True,
    include_empty_paragraphs: bool = False,
    encoding: str = "utf-8",
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(
        document_to_notes_doc_xml(
            document,
            start=start,
            leaf_terminal_nodes=leaf_terminal_nodes,
            include_empty_paragraphs=include_empty_paragraphs,
            encoding=encoding,
        )
    )
    return target


def _note_to_legacy_element(note: Note, *, leaf_terminal_nodes: bool, include_empty_paragraphs: bool) -> ET.Element:
    tag = "leaf" if leaf_terminal_nodes and not note.children else "node"
    el = ET.Element(tag, {"title": note.title or "..."})
    text = note.text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = text.split("\n") if text else []
    if paragraphs or include_empty_paragraphs:
        leaf_text = ET.SubElement(el, "leaf_text")
        if not paragraphs:
            ET.SubElement(leaf_text, "p").text = ""
        else:
            for paragraph in paragraphs:
                if paragraph or include_empty_paragraphs:
                    ET.SubElement(leaf_text, "p").text = paragraph
    for child in note.children:
        el.append(_note_to_legacy_element(child, leaf_terminal_nodes=leaf_terminal_nodes, include_empty_paragraphs=include_empty_paragraphs))
    return el
