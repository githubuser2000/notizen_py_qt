from __future__ import annotations

from pathlib import Path

from notizen_py_qt.html_export import HtmlExportOptions, html_body_fragment, tree_to_html, tree_to_html_bytes
from notizen_py_qt.models import DesktopNoteState, NoteNode
from notizen_py_qt.rtf_utils import html_to_rtf, plain_text_to_rtf
from notizen_py_qt.settings import AppSettings
from notizen_py_qt.stats import collect_tree_stats


_TINY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0l"
    "EQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def test_html_export_is_standalone_numbered_and_keeps_images() -> None:
    root = NoteNode("root", rtf=plain_text_to_rtf("root body"))
    child = root.add_child(
        NoteNode(
            "child & html",
            rtf=html_to_rtf(
                '<p><b>bold</b><br/><img src="data:image/png;base64,' + _TINY_PNG_BASE64 + '"/></p>'
            ),
        )
    )
    child.add_child(NoteNode("grand", rtf=plain_text_to_rtf("grand body")))
    root.add_child(NoteNode("second", rtf=plain_text_to_rtf("second body")))

    html = tree_to_html(root, HtmlExportOptions(title="Export & Test"))

    assert html.startswith("<!doctype html>")
    assert '<meta charset="utf-8"/>' in html
    assert "Export &amp; Test" in html
    assert "root body" in html
    assert "1. child &amp; html" in html
    assert "1.1. grand" in html
    assert "2. second" in html
    assert "data:image/png;base64" in html
    assert tree_to_html_bytes(root).startswith(b"<!doctype html>")


def test_html_body_fragment_extracts_body_without_wrapper() -> None:
    assert html_body_fragment("<html><body><p>x</p></body></html>") == "<p>x</p>"
    assert html_body_fragment("<p>frei</p>") == "<p>frei</p>"


def test_tree_stats_counts_nodes_depth_desktop_note_words_and_images() -> None:
    root = NoteNode("root", rtf=plain_text_to_rtf("eins zwei"), desktop_note=DesktopNoteState())
    child = root.add_child(
        NoteNode("child", rtf=html_to_rtf('<p>drei<br/>vier<img src="data:image/png;base64,' + _TINY_PNG_BASE64 + '"/></p>'))
    )
    child.add_child(NoteNode("grand", rtf=plain_text_to_rtf("fünf")))

    stats = collect_tree_stats(root)

    assert stats.nodes == 3
    assert stats.leaves == 1
    assert stats.max_depth == 3
    assert stats.desktop_notes == 1
    assert stats.words >= 5
    assert stats.images == 1
    labels = dict(stats.as_legacy_lines())
    assert labels["Knoten"] == "3"
    assert labels["Bilder"] == "1"


def test_settings_can_import_arbitrary_legacy_config_without_changing_config_dir(tmp_path: Path) -> None:
    current_dir = tmp_path / "current"
    current_dir.mkdir()
    legacy = tmp_path / "legacy.xml"
    legacy.write_bytes(
        """<?xml version='1.0' encoding='utf-16'?>
<notizen-alx>
  <scrolls choice='2' />
  <saftycopies amount='11' />
  <autorun if='yes' minimized='no' />
  <ftp host='example.org' path='/notizen.alx' name='user' pass='pw' />
  <files a='C:\\A.alx' b='C:\\B.alx' />
  <language choice='English' />
  <open directory='C:\\Notizen' file='demo.alx' />
  <main-form x='10' y='20' width='800' height='600' windowstate='Maximized' />
  <minimized-show-in taskbar='yes' />
  <desknotes show_desknote_borders='no' />
  <x a='90' />
</notizen-alx>
""".encode("utf-16")
    )

    settings = AppSettings(config_dir=current_dir)
    settings.apply_from_file(legacy)

    assert settings.config_dir == current_dir
    assert settings.scrollbars_choice == 2
    assert settings.backup_keep == 11
    assert settings.autorun_enabled is True
    assert settings.autorun_minimized is False
    assert settings.ftp_host == "example.org"
    assert settings.recent_files == ["C:\\A.alx", "C:\\B.alx"]
    assert settings.language == "English"
    assert settings.last_file == "demo.alx"
    assert settings.window_state == "Maximized"
    assert settings.show_in_taskbar_when_minimized is True
    assert settings.show_desknote_borders is False
    assert settings.autosave_seconds == 90
