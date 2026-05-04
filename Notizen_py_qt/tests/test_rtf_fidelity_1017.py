from __future__ import annotations

from notizen_py_qt.exporters import tree_to_rtf
from notizen_py_qt.models import NoteNode
from notizen_py_qt.rtf_utils import (
    LEGACY_OBJECT_PLACEHOLDER,
    RtfHyperlink,
    html_to_rtf,
    rtf_to_content_parts,
    rtf_to_html,
    rtf_to_plain_text,
)


def test_ignorable_pntext_list_marker_is_kept_as_visible_text() -> None:
    rtf = r"{\rtf1\ansi{\*\pntext\f0 \'b7\tab}Legacy item\par}"
    assert rtf_to_plain_text(rtf) == "·\tLegacy item"


def test_ignorable_listtext_number_is_kept_as_visible_text() -> None:
    rtf = r"{\rtf1\ansi{\*\listtext 1.\tab}Alpha\par{\*\listtext 2.\tab}Beta\par}"
    assert rtf_to_plain_text(rtf) == "1.\tAlpha\n2.\tBeta"


def test_html_table_roundtrip_preserves_cell_and_row_boundaries() -> None:
    rtf = html_to_rtf("<table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr></table>")
    assert r"\tab" in rtf
    assert rtf_to_plain_text(rtf) == "A\tB\nC\tD"


def test_html_ordered_list_roundtrip_preserves_number_prefixes() -> None:
    rtf = html_to_rtf("<ol><li>Alpha</li><li>Beta</li></ol>")
    assert rtf_to_plain_text(rtf) == "1. Alpha\n2. Beta"


def test_rtf_hyperlink_field_is_preserved_in_html_and_content_parts() -> None:
    rtf = r'{\rtf1\ansi Text {\field{\*\fldinst HYPERLINK "https://example.com"}{\fldrslt Example}} Ende}'
    assert rtf_to_plain_text(rtf) == "Text Example Ende"
    html = rtf_to_html(rtf)
    assert '<a href="https://example.com"' in html
    assert ">Example</a>" in html
    parts = rtf_to_content_parts(rtf)
    assert any(isinstance(part, RtfHyperlink) and part.url == "https://example.com" and part.text == "Example" for part in parts)


def test_html_hyperlink_roundtrip_writes_rtf_field() -> None:
    rtf = html_to_rtf('<a href="https://example.com/?a=1&amp;b=2">Example</a>')
    assert r'HYPERLINK "https://example.com/?a=1&b=2"' in rtf
    assert rtf_to_plain_text(rtf) == "Example"
    assert '<a href="https://example.com/?a=1&amp;b=2"' in rtf_to_html(rtf)


def test_tree_export_keeps_hyperlink_fields() -> None:
    node = NoteNode(title="Root", rtf=r'{\rtf1\ansi {\field{\*\fldinst HYPERLINK "https://example.com"}{\fldrslt Link}}}')
    exported = tree_to_rtf(node)
    assert r'HYPERLINK "https://example.com"' in exported
    assert "Link" in rtf_to_plain_text(exported)


def test_ole_object_group_gets_visible_placeholder_instead_of_disappearing() -> None:
    rtf = r"{\rtf1\ansi Hallo {\object\objemb{\*\objclass Package}{\objdata 010203}} Ende}"
    assert rtf_to_plain_text(rtf) == f"Hallo {LEGACY_OBJECT_PLACEHOLDER} Ende"
    assert LEGACY_OBJECT_PLACEHOLDER in rtf_to_html(rtf)
