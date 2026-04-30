from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from notizen_py_qt.exporters import create_unified_note, tree_to_plain_text, tree_to_rtf
from notizen_py_qt.models import NoteNode
from notizen_py_qt.rtf_utils import html_to_rtf, plain_text_to_rtf, rtf_to_html, rtf_to_plain_text
from notizen_py_qt.settings import AppSettings


def test_html_to_rtf_preserves_basic_formatting_colors_and_unicode() -> None:
    rtf = html_to_rtf(
        '<p><b>Hallo</b> <i>Welt</i> '
        '<span style="color:#ff0000; background-color:#ffff00; font-size:14pt; '
        'text-decoration: underline line-through">rot</span> 😀</p>'
    )

    assert r"\b" in rtf
    assert r"\i" in rtf
    assert r"\ul" in rtf
    assert r"\strike" in rtf
    assert r"\cf1" in rtf
    assert r"\highlight2" in rtf
    assert rtf_to_plain_text(rtf) == "Hallo Welt rot 😀"

    html = rtf_to_html(rtf)
    assert "font-weight:700" in html
    assert "font-style:italic" in html
    assert "text-decoration:underline line-through" in html
    assert "color:#ff0000" in html
    assert "background-color:#ffff00" in html


def test_rtf_parser_skips_metadata_and_pictures() -> None:
    rtf = (
        r"{\rtf1\ansi{\fonttbl{\f0 Arial;}}"
        r"{\colortbl ;\red255\green0\blue0;}"
        r"{\pict\pngblip abcdef}\pard sichtbar\par}"
    )

    assert rtf_to_plain_text(rtf) == "sichtbar"
    assert "sichtbar" in rtf_to_html(rtf)
    assert "abcdef" not in rtf_to_html(rtf)


def test_plain_text_rtf_roundtrips_non_bmp_unicode() -> None:
    text = "äöü € 😀"
    assert rtf_to_plain_text(plain_text_to_rtf(text)) == text


def test_tree_export_numbering_and_unified_note() -> None:
    root = NoteNode(title="root", rtf=plain_text_to_rtf("body"))
    child = root.add_child(
        NoteNode(
            title="child",
            rtf=html_to_rtf(
                '<p><i>child body</i> <span style="color:#ff0000; background-color:#ffff00">red</span></p>'
            ),
        )
    )
    child.add_child(NoteNode(title="grand", rtf=plain_text_to_rtf("grand body")))

    text = tree_to_plain_text(root)
    assert "root" in text
    assert "1. child" in text
    assert "1.1. grand" in text
    assert "child body" in text

    rtf = tree_to_rtf(root)
    assert r"\b\fs28" in rtf
    assert r"\i" in rtf
    assert r"\cf1" in rtf
    assert r"\highlight2" in rtf
    html = rtf_to_html(rtf)
    assert "font-style:italic" in html
    assert "color:#ff0000" in html
    plain = rtf_to_plain_text(rtf)
    assert "1. child" in plain
    assert "1.1. grand" in plain
    assert "grand body" in plain

    unified = create_unified_note(root, "Gesamt")
    assert unified.title == "Gesamt"
    assert "1.1. grand" in rtf_to_plain_text(unified.rtf)


def test_legacy_settings_parse_and_save_extended_fields(tmp_path: Path) -> None:
    config = tmp_path / "notizen.config.xml"
    config.write_bytes(
        """<?xml version='1.0' encoding='utf-16'?>
<notizen-alx>
  <scrolls choice='1' />
  <saftycopies amount='7' />
  <autorun if='yes' minimized='no' />
  <language choice='Deutsch' />
  <minimized-show-in taskbar='yes' />
  <desknotes show_desknote_borders='no' />
  <x a='42' />
</notizen-alx>
""".encode("utf-16")
    )

    settings = AppSettings.load(tmp_path)
    assert settings.scrollbars_choice == 1
    assert settings.backup_keep == 7
    assert settings.autosave_seconds == 42
    assert settings.autorun_enabled is True
    assert settings.autorun_minimized is False
    assert settings.language == "Deutsch"
    assert settings.show_in_taskbar_when_minimized is True
    assert settings.show_desknote_borders is False

    settings.scrollbars_choice = 3
    settings.autorun_minimized = True
    settings.save()
    root = ET.parse(config).getroot()
    assert root.find("scrolls").get("choice") == "3"  # type: ignore[union-attr]
    assert root.find("autorun").get("minimized") == "yes"  # type: ignore[union-attr]
