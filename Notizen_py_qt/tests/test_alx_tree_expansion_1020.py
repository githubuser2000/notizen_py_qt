from __future__ import annotations

import gzip
from pathlib import Path
import xml.etree.ElementTree as ET

from notizen_py_qt.alx_io import dump_alx_bytes, load_alx_bytes
from notizen_py_qt.models import NoteDocument, NoteNode
from notizen_py_qt.rtf_utils import plain_text_to_rtf


def _expanded_by_title(node: NoteNode) -> dict[str, bool]:
    return {child.title: child.expanded for child in node.walk()}


def test_alx_isexpanded_state_roundtrips_for_nested_nodes() -> None:
    root = NoteNode(title="root", rtf=plain_text_to_rtf("root"), expanded=False)
    open_child = root.add_child(NoteNode(title="open", rtf=plain_text_to_rtf("open"), expanded=True))
    closed_grandchild = open_child.add_child(
        NoteNode(title="closed-grandchild", rtf=plain_text_to_rtf("closed"), expanded=False)
    )
    closed_child = root.add_child(NoteNode(title="closed", rtf=plain_text_to_rtf("closed"), expanded=False))
    doc = NoteDocument(root=root)

    loaded = load_alx_bytes(dump_alx_bytes(doc))

    assert loaded.root is not None
    assert _expanded_by_title(loaded.root) == {
        "root": False,
        "open": True,
        "closed-grandchild": False,
        "closed": False,
    }
    assert closed_grandchild.expanded is False
    assert closed_child.expanded is False


def test_alx_xml_writer_keeps_isexpanded_attributes_on_save() -> None:
    root = NoteNode(title="root", rtf="", expanded=False)
    root.add_child(NoteNode(title="child", rtf="", expanded=True))
    payload = dump_alx_bytes(NoteDocument(root=root))
    xml_bytes = gzip.decompress(payload)
    xml = xml_bytes.decode("utf-16")
    tree = ET.fromstring(xml)

    root_element = tree.find("Notiz")
    assert root_element is not None
    child_element = root_element.find("Notiz")
    assert child_element is not None
    assert root_element.get("isexpanded") == "False"
    assert child_element.get("isexpanded") == "True"


def test_qt_tree_expansion_is_applied_after_items_are_inserted() -> None:
    source = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")
    assert "def _apply_tree_expansion_state" in source
    add_index = source.index("self.tree.addTopLevelItem(root_item)")
    apply_index = source.index("self._apply_tree_expansion_state(root_item)")
    current_index = source.index("self.tree.setCurrentItem(root_item)", add_index)
    assert add_index < apply_index < current_index
