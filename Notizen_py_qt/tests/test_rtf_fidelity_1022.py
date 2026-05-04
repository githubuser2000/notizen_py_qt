from __future__ import annotations

from notizen_py_qt.rtf_utils import (
    extract_color_table,
    extract_font_table,
    html_to_rtf,
    rtf_to_html,
    rtf_to_plain_text,
    rtf_to_text_segments,
)


def test_rtf_plain_resets_character_format_without_losing_paragraph() -> None:
    rtf = r"{\rtf1\ansi\pard\qc\li720 Titel {\b Fett}\plain Normal\par}"

    segments = rtf_to_text_segments(rtf)
    normal = next(segment for segment in segments if "Normal" in segment.text)

    assert normal.style.align == "center"
    assert normal.style.left_indent_twips == 720
    assert normal.style.bold is False

    html = rtf_to_html(rtf)
    assert "text-align:center" in html
    assert "margin-left:36pt" in html
    assert "font-weight:700" in html


def test_rtf_line_height_multiplier_cbpat_and_underline_variants() -> None:
    rtf = r"{\rtf1\ansi{\colortbl ;\red255\green255\blue224;}\pard\sl360\slmult1\cbpat1{\ulwave Welle}\par}"

    html = rtf_to_html(rtf)
    assert "line-height:1.5" in html
    assert "background-color:#ffffe0" in html
    assert "text-decoration:underline" in html

    segment = next(segment for segment in rtf_to_text_segments(rtf) if "Welle" in segment.text)
    assert segment.style.line_spacing_twips == 360
    assert segment.style.line_spacing_multiple is True
    assert segment.style.bg_color == "#ffffe0"
    assert segment.style.underline is True


def test_wordpad_font_alias_and_color_table_without_automatic_slot() -> None:
    fonts = extract_font_table(
        r"{\rtf1\ansi{\fonttbl{\f0\fnil\fcharset0 Arial;}{\f1\fswiss\fcharset0 Times New Roman{\*\falt Times};}}\f1 Text}"
    )
    assert fonts[0] == "Arial"
    assert fonts[1] == "Times New Roman"

    colors = extract_color_table(r"{\rtf1\ansi{\colortbl\red1\green2\blue3;}\cf1 Farbtext\par}")
    assert colors[0] == ""
    assert colors[1] == "#010203"

    html = rtf_to_html(r"{\rtf1\ansi{\colortbl\red1\green2\blue3;}\cf1 Farbtext\par}")
    assert "color:#010203" in html


def test_html_extended_css_emits_richtextbox_rtf_controls() -> None:
    rtf = html_to_rtf(
        '<p style="text-align:justify; margin:6pt 12pt 18pt 24pt; line-height:150%; direction:rtl">'
        '<span style="font-variant:small-caps; text-transform:uppercase; letter-spacing:2pt; '
        'display:none; background:lightyellow">Format</span></p>'
    )

    assert r"\qj" in rtf
    assert r"\li480" in rtf
    assert r"\ri240" in rtf
    assert r"\sb120" in rtf
    assert r"\sa360" in rtf
    assert r"\sl360" in rtf
    assert r"\slmult1" in rtf
    assert r"\rtlpar\rtlch" in rtf
    assert r"\caps" in rtf
    assert r"\scaps" in rtf
    assert r"\v" in rtf
    assert r"\expndtw40" in rtf
    assert r"\highlight" in rtf

    segment = next(segment for segment in rtf_to_text_segments(rtf) if segment.text == "Format")
    assert segment.style.align == "justify"
    assert segment.style.left_indent_twips == 480
    assert segment.style.right_indent_twips == 240
    assert segment.style.space_before_twips == 120
    assert segment.style.space_after_twips == 360
    assert segment.style.line_spacing_twips == 360
    assert segment.style.line_spacing_multiple is True
    assert segment.style.direction == "rtl"
    assert segment.style.all_caps is True
    assert segment.style.small_caps is True
    assert segment.style.hidden is True
    assert segment.style.letter_spacing_twips == 40
    assert segment.style.bg_color == "#ffffe0"

    assert rtf_to_plain_text(rtf) == ""


def test_html_semantic_tags_and_attributes_have_rtf_equivalents() -> None:
    rtf = html_to_rtf(
        '<body text="navy" bgcolor="lightyellow">'
        '<center><big>Groß</big></center>'
        '<blockquote><code>Code</code></blockquote>'
        '<font face="Courier New" size="+2" color="rgb(100%, 0%, 0%)">Rot</font>'
        '</body>'
    )

    assert r"\qc" in rtf
    assert r"\li720" in rtf
    assert r"\ri720" in rtf
    assert "Courier New" in rtf
    assert r"\cf" in rtf
    assert r"\highlight" in rtf

    segments = rtf_to_text_segments(rtf)
    code = next(segment for segment in segments if "Code" in segment.text)
    rot = next(segment for segment in segments if "Rot" in segment.text)
    assert code.style.font_family == "Courier New"
    assert code.style.left_indent_twips == 720
    assert rot.style.font_family == "Courier New"
    assert rot.style.fg_color == "#ff0000"
