from __future__ import annotations

from notizen_py_qt.rtf_utils import rtf_ansi_encoding, rtf_to_content_parts, rtf_to_html, rtf_to_plain_text, rtf_to_text_segments


def test_rtf_ansicpg1251_hex_escapes_decode_as_cyrillic() -> None:
    rtf = r"{\rtf1\ansi\ansicpg1251\deff0{\fonttbl{\f0 Arial;}}\f0 \'cf\'f0\'e8\'e2\'e5\'f2\par}"
    assert rtf_ansi_encoding(rtf) == "cp1251"
    assert rtf_to_plain_text(rtf) == "Привет"
    html = rtf_to_html(rtf)
    assert "Привет" in html
    assert rtf_to_text_segments(rtf)[0].text == "Привет\n"
    assert rtf_to_content_parts(rtf)[0].text == "Привет\n"


def test_rtf_unknown_ansicpg_falls_back_to_cp1252() -> None:
    rtf = r"{\rtf1\ansi\ansicpg99999 \'e4}"
    assert rtf_ansi_encoding(rtf) == "cp1252"
    assert rtf_to_plain_text(rtf) == "ä"
