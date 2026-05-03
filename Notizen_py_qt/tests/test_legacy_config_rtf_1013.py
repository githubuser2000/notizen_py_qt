from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from notizen_py_qt.exporters import tree_to_rtf
from notizen_py_qt.models import NoteNode
from notizen_py_qt.rtf_utils import RtfImage, rtf_to_content_parts, rtf_to_html
from notizen_py_qt.settings import AppSettings


def test_unknown_legacy_config_root_attributes_and_elements_survive(tmp_path: Path) -> None:
    settings = AppSettings(config_dir=tmp_path / "cfg")
    root = ET.fromstring(
        '<notizen-alx legacy-version="net" custom="yes">'
        '<language choice="french" />'
        '<vendor-extra answer="42"><child keep="yes">text</child></vendor-extra>'
        '<old-form-state x="5" y="6" />'
        '</notizen-alx>'
    )

    settings.apply_xml_root(root)
    settings.save()

    saved = ET.parse(settings.path).getroot()
    assert saved.get("legacy-version") == "net"
    assert saved.get("custom") == "yes"
    extra = saved.find("vendor-extra")
    assert extra is not None
    assert extra.get("answer") == "42"
    child = extra.find("child")
    assert child is not None
    assert child.text == "text"
    assert child.get("keep") == "yes"
    assert saved.find("old-form-state") is not None


def test_rtf_wmf_images_are_preserved() -> None:
    wmf_payload = bytes.fromhex("d7cdc69a000000000000")
    rtf = "{\\rtf1{\\pict\\wmetafile8\\picwgoal30\\pichgoal15\n" + wmf_payload.hex() + "}}"

    parts = rtf_to_content_parts(rtf)
    images = [part for part in parts if isinstance(part, RtfImage)]
    assert len(images) == 1
    assert images[0].mime_type == "image/wmf"
    assert images[0].rtf_control == "wmetafile8"
    assert images[0].data == wmf_payload
    assert "data:image/wmf;base64" in rtf_to_html(rtf)

    combined = tree_to_rtf(NoteNode("Root", rtf=rtf))
    assert "\\wmetafile8" in combined
    assert wmf_payload.hex() in combined


def test_rtf_emf_images_are_preserved() -> None:
    emf_payload = b"\x01\x00\x00\x00" + (b"\x00" * 40) + b" EMF" + (b"\x00" * 8)
    rtf = "{\\rtf1{\\pict\\emfblip\n" + emf_payload.hex() + "}}"

    parts = rtf_to_content_parts(rtf)
    images = [part for part in parts if isinstance(part, RtfImage)]
    assert len(images) == 1
    assert images[0].mime_type == "image/x-emf"
    assert images[0].rtf_control == "emfblip"
    assert images[0].data == emf_payload
    assert "data:image/x-emf;base64" in rtf_to_html(rtf)

    combined = tree_to_rtf(NoteNode("Root", rtf=rtf))
    assert "\\emfblip" in combined
    assert emf_payload.hex() in "".join(combined.split())
