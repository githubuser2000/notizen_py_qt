from __future__ import annotations

from notizen_py_qt.rtf_utils import html_to_rtf, rtf_to_content_parts, rtf_to_html, rtf_to_text_segments


def test_rtf_paragraph_alignment_is_emitted_on_p_element() -> None:
    html = rtf_to_html(r"{\rtf1\ansi\pard\qc Zentriert\par}")

    assert '<p style="' in html
    assert "text-align:center" in html
    assert "Zentriert" in html


def test_rtf_paragraph_spacing_and_line_height_survive_parser() -> None:
    rtf = r"{\rtf1\ansi\pard\sb240\sa120\sl360 Abstand\par}"

    html = rtf_to_html(rtf)
    assert "margin-top:12pt" in html
    assert "margin-bottom:6pt" in html
    assert "line-height:18pt" in html

    segments = rtf_to_text_segments(rtf)
    assert segments
    assert segments[0].style.space_before_twips == 240
    assert segments[0].style.space_after_twips == 120
    assert segments[0].style.line_spacing_twips == 360


def test_html_paragraph_align_spacing_and_line_height_emit_rtf_controls() -> None:
    rtf = html_to_rtf(
        '<p align="center" style="margin-top: 12pt; margin-bottom: 6pt; line-height: 18pt">Hallo</p>'
    )

    assert r"\qc" in rtf
    assert r"\sb240" in rtf
    assert r"\sa120" in rtf
    assert r"\sl360" in rtf
    assert "Hallo" in rtf


def test_rtf_up_dn_offsets_map_to_super_and_subscript() -> None:
    html = rtf_to_html(r"{\rtf1\ansi Basis {\up6 Hoch}{\dn6 Tief}\par}")

    assert "vertical-align:super" in html
    assert "vertical-align:sub" in html

    parts = rtf_to_content_parts(r"{\rtf1\ansi Basis {\up6 Hoch}{\dn6 Tief}\par}")
    text_styles = [(getattr(part, "text", ""), getattr(part, "style", None)) for part in parts]
    assert any(text == "Hoch" and style is not None and style.vertical == "super" for text, style in text_styles)
    assert any(text == "Tief" and style is not None and style.vertical == "sub" for text, style in text_styles)


def test_html_heading_and_qt_block_indent_have_rtf_equivalents() -> None:
    rtf = html_to_rtf('<h2 align="right">Titel</h2><p style="-qt-block-indent: 2">Eingerückt</p>')

    assert r"\qr" in rtf
    assert r"\b" in rtf
    assert r"\fs36" in rtf
    assert r"\li1440" in rtf
