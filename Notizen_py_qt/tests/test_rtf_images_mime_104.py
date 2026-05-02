from __future__ import annotations

from pathlib import Path

from notizen_py_qt.exporters import create_unified_note, tree_to_rtf
from notizen_py_qt.models import NoteNode
from notizen_py_qt.rtf_utils import RtfImage, RtfTextSegment, html_to_rtf, rtf_to_content_parts, rtf_to_html, rtf_to_plain_text


_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0l"
    "EQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def test_rtf_content_parts_keep_legacy_picture_order() -> None:
    rtf = html_to_rtf(f'<p>A<img width="1" height="1" src="data:image/png;base64,{_ONE_PIXEL_PNG}"/>B</p>')

    parts = rtf_to_content_parts(rtf)

    assert len(parts) == 3
    assert isinstance(parts[0], RtfTextSegment)
    assert parts[0].text == "A"
    assert isinstance(parts[1], RtfImage)
    assert isinstance(parts[2], RtfTextSegment)
    assert parts[2].text.rstrip() == "B"


def test_combined_rtf_export_preserves_embedded_png() -> None:
    root = NoteNode(title="root", rtf=html_to_rtf(f'<p>vor<img width="1" height="1" src="data:image/png;base64,{_ONE_PIXEL_PNG}"/>nach</p>'))
    root.add_child(NoteNode(title="child", rtf=html_to_rtf("<p>Text</p>")))

    rtf = tree_to_rtf(root)

    assert r"\pict\pngblip" in rtf
    assert rtf_to_plain_text(rtf).replace("\n", " ").find("vor nach") == -1
    html = rtf_to_html(rtf)
    assert "data:image/png;base64" in html
    assert "vor" in html and "nach" in html

    unified = create_unified_note(root, "Gesamt")
    assert r"\pict\pngblip" in unified.rtf


def test_linux_launcher_installer_registers_alx_mime_type() -> None:
    installer = Path("scripts/install_linux_launcher.sh").read_text(encoding="utf-8")
    desktop = Path("Notizen PyQt.desktop").read_text(encoding="utf-8")

    assert "notizen-py-qt.xml" in installer
    assert "update-mime-database" in installer
    assert "xdg-mime default notizen-py-qt.desktop application/x-notizen-alx" in installer
    assert '<glob pattern="*.alx"/>' in installer
    assert '<glob pattern="*.ALX"/>' in installer
    assert "MimeType=application/x-notizen-alx;" in desktop
