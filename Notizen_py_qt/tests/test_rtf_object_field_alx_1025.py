from __future__ import annotations

from notizen_py_qt.alx_io import document_to_xml_bytes, parse_alx_xml
from notizen_py_qt.exporters import tree_to_rtf
from notizen_py_qt.models import NoteNode
from notizen_py_qt.rtf_utils import (
    RtfField,
    RtfObject,
    html_to_rtf,
    rtf_to_content_parts,
    rtf_to_html,
    rtf_to_plain_text,
    rtf_to_text_segments,
)


def test_generic_rtf_field_uses_visible_result_not_instruction() -> None:
    field_group = r"{\field{\*\fldinst PAGE}{\fldrslt 7}}"
    rtf = r"{\rtf1\ansi vor " + field_group + r" nach}"

    assert rtf_to_plain_text(rtf) == "vor 7 nach"
    html = rtf_to_html(rtf)
    assert "PAGE" not in html
    assert "vor " in html
    assert ">7</span>" in html
    assert " nach" in html
    segments = rtf_to_text_segments(rtf)
    assert "".join(segment.text for segment in segments) == "vor 7 nach"
    parts = rtf_to_content_parts(rtf)
    assert any(isinstance(part, RtfField) and part.rtf == field_group and part.text == "7" for part in parts)
    assert "data-notizen-rtf-field=" in html
    assert field_group in html_to_rtf(html)
    assert field_group in tree_to_rtf(NoteNode(title="Feld", rtf=rtf))


def test_rtf_ole_object_survives_html_and_combined_rtf_roundtrip() -> None:
    object_group = r"{\object{\*\objclass Package}{\objdata 010203}}"
    rtf = r"{\rtf1\ansi " + object_group + r"}"

    assert rtf_to_plain_text(rtf) == "[Objekt]"
    parts = rtf_to_content_parts(rtf)
    assert len(parts) == 1
    assert isinstance(parts[0], RtfObject)
    assert parts[0].rtf == object_group
    assert parts[0].class_name == "Package"

    html = rtf_to_html(rtf)
    assert "data-notizen-rtf-object=" in html
    assert "[Objekt]" in html

    roundtrip = html_to_rtf(html)
    assert object_group in roundtrip
    assert roundtrip.count(r"\object") == 1

    exported = tree_to_rtf(NoteNode(title="Wurzel", rtf=rtf))
    assert object_group in exported


def test_alx_unknown_notiz_child_xml_is_preserved() -> None:
    xml = (
        '<notizen-alx2><Notiz name="root" custom="42" isexpanded="False">'
        '<legacy meta="1"><inner>ok</inner></legacy>'
        '<Notiz name="child">text</Notiz>'
        '</Notiz></notizen-alx2>'
    )

    document = parse_alx_xml(xml)
    root = document.ensure_root()

    assert root.expanded is False
    assert root.extra_attrs == {"custom": "42"}
    assert root.extra_child_xml == ['<legacy meta="1"><inner>ok</inner></legacy>']
    assert root.children[0].title == "child"

    saved = document_to_xml_bytes(document).decode("utf-16")
    assert 'custom="42"' in saved
    assert '<legacy meta="1"><inner>ok</inner></legacy>' in saved
    assert '<Notiz name="child"' in saved
