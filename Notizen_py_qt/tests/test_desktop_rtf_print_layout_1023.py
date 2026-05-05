from __future__ import annotations

from pathlib import Path

from notizen_py_qt.rtf_utils import html_to_rtf, rtf_to_html, rtf_to_plain_text


APP_SOURCE = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")


def test_rtf_line_controls_do_not_create_browser_paragraph_spacing() -> None:
    rtf = r"{\rtf1\ansi\pard Erste\line Zweite\par Dritte\par}"

    html = rtf_to_html(rtf)

    assert 'body style="white-space: pre-wrap; margin:0;"' in html
    assert 'style="margin-top:0; margin-bottom:0"' in html
    assert "Erste<br/>Zweite" in html
    assert "<p" in html
    assert rtf_to_plain_text(rtf) == "Erste\nZweite\nDritte"


def test_html_br_roundtrips_as_richtextbox_soft_line_break() -> None:
    rtf = html_to_rtf("Erste<br/>Zweite")

    assert r"\line " in rtf
    assert rtf_to_plain_text(rtf) == "Erste\nZweite"
    html = rtf_to_html(rtf)
    assert "Erste" in html and "Zweite" in html
    assert "<br/>" in html


def test_desktop_note_transparency_and_minimize_semantics_are_legacy_safe() -> None:
    assert "flags = WINDOW | FRAMELESS" in APP_SOURCE
    assert "super().__init__(None, flags)" in APP_SOURCE
    assert "WA_TranslucentBackground" in APP_SOURCE
    assert "def _apply_user_opacity" in APP_SOURCE
    assert "legacy_desknote_opacity_for_inactive(self._desired_opacity)" in APP_SOURCE
    assert "self.setWindowOpacity(legacy_desknote_opacity_for_active" not in APP_SOURCE
    assert "def _hide_desktop_note" in APP_SOURCE
    assert "self._store_geometry(visible=True)" in APP_SOURCE
    assert "self.node.desktop_note.visible = True" in APP_SOURCE
    assert "self.showMinimized()" in APP_SOURCE


def test_desktop_note_text_layout_has_no_extra_qtextedit_padding() -> None:
    assert "def _apply_desktop_note_text_layout" in APP_SOURCE
    assert "setDocumentMargin(0)" in APP_SOURCE
    assert "QTextEdit { " in APP_SOURCE
    assert "background-color: {css_color}" in APP_SOURCE
    assert "padding: 0px" in APP_SOURCE
    assert "margin: 0px" in APP_SOURCE
    assert "self.setAutoFillBackground(False)" in APP_SOURCE
    assert "WA_StyledBackground" in APP_SOURCE


def test_net_like_main_layout_and_rtf_toolbar_are_present() -> None:
    assert 'self.tree.setHeaderHidden(True)' in APP_SOURCE
    assert 'QLabel("Baum")' not in APP_SOURCE
    assert 'QLabel("Titel:")' not in APP_SOURCE
    assert 'font_bar = self.addToolBar("RTF-Formatierung")' in APP_SOURCE
    assert 'font_bar.setObjectName("ToolStrip_fontstyle")' in APP_SOURCE
    for object_name in (
        "ToolStrip_regular",
        "ToolStrip_bold",
        "ToolStrip_italic",
        "ToolStrip_underline",
        "ToolStrip_strikeout",
        "ToolStrip_bigger",
        "ToolStrip_smaller",
        "ToolStrip_dot",
        "ToolStrip_whatscroll",
        "ToolStrip_fonts",
        "ToolStrip_fontsizenumber",
        "fgcolorToolStripMenuItem",
        "bgcolorToolStripMenuItem",
    ):
        assert object_name in APP_SOURCE
    assert "ToolButtonTextOnly" in APP_SOURCE


def test_print_uses_pyside_compatible_print_method() -> None:
    assert 'print_method = getattr(document, "print_", None) or getattr(document, "print", None)' in APP_SOURCE
    assert "print_method(printer)" in APP_SOURCE
