from __future__ import annotations

import gzip
from xml.etree import ElementTree as ET

from notizen_py_qt.alx_io import dump_alx_bytes, load_alx_bytes
from notizen_py_qt.models import DesktopNoteState, NoteNode
from notizen_py_qt.node_clipboard import node_from_clipboard_xml, node_to_clipboard_xml
from notizen_py_qt.rtf_utils import plain_text_to_rtf


def _legacy_payload(xml: str) -> bytes:
    return gzip.compress(xml.encode("utf-16"), compresslevel=6, mtime=0)


def _xml_from_payload(payload: bytes) -> ET.Element:
    return ET.fromstring(gzip.decompress(payload).decode("utf-16"))


def test_legacy_notiz_unknown_attributes_survive_alx_roundtrip() -> None:
    xml = (
        '<?xml version="1.0" encoding="utf-16"?>'
        '<notizen-alx2><Notiz name="root" legacy-id="42" vendor="kept">'
        + plain_text_to_rtf("root")
        + '<Notiz name="child" custom-flag="yes">'
        + plain_text_to_rtf("child")
        + '</Notiz></Notiz></notizen-alx2>'
    )
    document = load_alx_bytes(_legacy_payload(xml))

    assert document.root is not None
    assert document.root.extra_attrs == {"legacy-id": "42", "vendor": "kept"}
    assert document.root.children[0].extra_attrs == {"custom-flag": "yes"}

    saved = _xml_from_payload(dump_alx_bytes(document))
    root = next(child for child in saved if child.tag == "Notiz")
    assert root.get("legacy-id") == "42"
    assert root.get("vendor") == "kept"
    child = next(child for child in root if child.tag == "Notiz")
    assert child.get("custom-flag") == "yes"


def test_sparse_legacy_desktop_note_does_not_gain_optional_attrs_on_noop_save() -> None:
    xml = (
        '<?xml version="1.0" encoding="utf-16"?>'
        '<notizen-alx2><Notiz name="root"><Notiz name="desk" visible="True" x="7" y="8" width="90" height="91">'
        + plain_text_to_rtf("desk")
        + '</Notiz></Notiz></notizen-alx2>'
    )
    document = load_alx_bytes(_legacy_payload(xml))
    desk = document.root.children[0].desktop_note  # type: ignore[union-attr]
    assert desk is not None
    assert desk.legacy_sparse is True
    assert "opacity" not in desk.legacy_attr_names
    assert "argb" not in desk.legacy_attr_names
    assert desk.argb is None

    saved = _xml_from_payload(dump_alx_bytes(document))
    saved_desk = next(next(child for child in saved if child.tag == "Notiz") for _ in [0])
    saved_desk = next(child for child in saved_desk if child.tag == "Notiz")
    assert saved_desk.get("x") == "7"
    assert saved_desk.get("visible") == "True"
    assert saved_desk.get("opacity") is None
    assert saved_desk.get("argb") is None


def test_sparse_legacy_desktop_note_writes_optional_attrs_after_user_changes() -> None:
    xml = (
        '<?xml version="1.0" encoding="utf-16"?>'
        '<notizen-alx2><Notiz name="root"><Notiz name="desk" visible="True" x="7" y="8" width="90" height="91" /></Notiz></notizen-alx2>'
    )
    document = load_alx_bytes(_legacy_payload(xml))
    desk = document.root.children[0].desktop_note  # type: ignore[union-attr]
    assert desk is not None
    desk.opacity = 0.5
    desk.argb = -123

    saved = _xml_from_payload(dump_alx_bytes(document))
    root = next(child for child in saved if child.tag == "Notiz")
    saved_desk = next(child for child in root if child.tag == "Notiz")
    assert saved_desk.get("opacity") == "0.5"
    assert saved_desk.get("argb") == "-123"


def test_new_desktop_note_still_writes_canonical_attrs() -> None:
    node = NoteNode("desk", desktop_note=DesktopNoteState(x=1, y=2, width=3, height=4, opacity=0.85, argb=-5))
    xml = node_to_clipboard_xml(node, include_desktop_note=True)
    assert 'opacity="0.85"' in xml
    assert 'argb="-5"' in xml


def test_clipboard_roundtrip_preserves_unknown_notiz_attributes_and_sparse_desktop() -> None:
    xml = '<Notiz name="desk" custom="yes" visible="True" x="1" y="2" width="3" height="4">{\\rtf1}</Notiz>'
    node = node_from_clipboard_xml(xml, include_desktop_note=True)
    assert node.extra_attrs == {"custom": "yes"}
    assert node.desktop_note is not None
    assert node.desktop_note.legacy_sparse is True
    exported = node_to_clipboard_xml(node, include_desktop_note=True)
    assert 'custom="yes"' in exported
    assert 'opacity=' not in exported
    assert 'argb=' not in exported
