from __future__ import annotations

from pathlib import Path

from notizen_py_qt.rtf_utils import rtf_to_desktop_html

APP_SOURCE = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")


def test_desktop_rtf_html_uses_inline_breaks_without_qt_paragraph_gap() -> None:
    rtf = r"{\rtf1\ansi\pard\par Erste\line Zweite\par Dritte\par}"

    html = rtf_to_desktop_html(rtf)

    assert '<body style="white-space: pre-wrap; margin:0; padding:0; line-height:100%;">' in html
    assert "<p" not in html
    assert html.endswith("Erste<br/>Zweite<br/>Dritte</body></html>")


def test_desktop_note_forces_compact_blocks_and_uses_desktop_html_bridge() -> None:
    assert "rtf_to_desktop_html(node.rtf)" in APP_SOURCE
    assert "rtf_to_desktop_html(self.node.rtf)" in APP_SOURCE
    assert "def _compact_desktop_note_blocks" in APP_SOURCE
    assert "block_format.setTopMargin(0)" in APP_SOURCE
    assert "block_format.setBottomMargin(0)" in APP_SOURCE
    assert "setDefaultStyleSheet" in APP_SOURCE
    assert "line-height:100%" in APP_SOURCE


def test_desktop_note_gnome_opacity_uses_qt_painting_not_only_window_opacity() -> None:
    assert "QGraphicsOpacityEffect(self.editor)" in APP_SOURCE
    assert "self._editor_opacity_effect.setOpacity(opacity)" in APP_SOURCE
    assert "self.setWindowOpacity(1.0)" in APP_SOURCE
    assert "QTextEdit::viewport" in APP_SOURCE
    assert "background-color: {css_color}" in APP_SOURCE


def test_desktop_note_bottom_hint_and_lowering_are_ported() -> None:
    assert "WINDOW_STAYS_ON_BOTTOM_HINT" in APP_SOURCE
    assert "flags = WINDOW | FRAMELESS" in APP_SOURCE
    assert "flags |= WINDOW_STAYS_ON_BOTTOM_HINT" in APP_SOURCE
    assert "def _send_to_back" in APP_SOURCE
    assert "self.lower()" in APP_SOURCE
    assert "self._send_to_back()" in APP_SOURCE
    assert "self.raise_()" not in APP_SOURCE.split("class DesktopNoteWindow", 1)[1].split("class SearchDialog", 1)[0]


def test_rtf_toolbar_matches_net_compact_label_order() -> None:
    for snippet in (
        'self.regular_action = self._act("N", self.reset_char_format)',
        'self.bold_action = self._act("B", self.toggle_bold, "Ctrl+B", checkable=True)',
        'self.italic_action = self._act("K", self.toggle_italic, "Ctrl+I", checkable=True)',
        'self.underline_action = self._act("U", self.toggle_underline, checkable=True)',
        'self.strike_action = self._act("D", self.toggle_strike, checkable=True)',
        'self.bigger_action = self._act("+", lambda: self.change_font_size(+1), "Ctrl++")',
        'self.smaller_action = self._act("-", lambda: self.change_font_size(-1), "Ctrl+-")',
        "font_bar.addAction(action)",
        "self.font_family_combo.setMaximumWidth(180)",
    ):
        assert snippet in APP_SOURCE
    assert "self.bold_action.setFont(bold_font)" in APP_SOURCE
    assert "self.italic_action.setFont(italic_font)" in APP_SOURCE
    assert "self.underline_action.setFont(underline_font)" in APP_SOURCE
