from __future__ import annotations

import base64
import struct
from pathlib import Path

from notizen_py_qt import bmp_to_dib_bytes, dib_to_bmp_bytes
from notizen_py_qt.exporters import tree_to_rtf
from notizen_py_qt.models import NoteNode
from notizen_py_qt.rtf_utils import RtfImage, html_to_rtf, rtf_to_content_parts, rtf_to_html


def tiny_dib() -> bytes:
    # BITMAPINFOHEADER, 1x1 pixel, 24-bit BGR with a padded scanline.
    return struct.pack(
        "<IiiHHIIiiII",
        40,
        1,
        1,
        1,
        24,
        0,
        4,
        0,
        0,
        0,
        0,
    ) + b"\x00\x00\xff\x00"


def test_dib_payload_is_wrapped_as_bmp_file() -> None:
    dib = tiny_dib()
    bmp = dib_to_bmp_bytes(dib)

    assert bmp is not None
    assert bmp.startswith(b"BM")
    assert int.from_bytes(bmp[2:6], "little") == len(bmp)
    assert int.from_bytes(bmp[10:14], "little") == 54
    assert bmp_to_dib_bytes(bmp) == dib


def test_legacy_rtf_dibitmap_is_preserved_as_html_image() -> None:
    dib = tiny_dib()
    rtf = r"{\rtf1\ansi " + r"{\pict\dibitmap0\picwgoal15\pichgoal15 " + dib.hex() + "}" + "}"

    parts = rtf_to_content_parts(rtf)
    images = [part for part in parts if isinstance(part, RtfImage)]
    html = rtf_to_html(rtf)

    assert len(images) == 1
    assert images[0].mime_type == "image/bmp"
    assert images[0].data.startswith(b"BM")
    assert "data:image/bmp;base64," in html


def test_combined_tree_rtf_keeps_legacy_bitmap_picture() -> None:
    dib = tiny_dib()
    legacy_rtf = r"{\rtf1\ansi Text " + r"{\pict\dibitmap0 " + dib.hex() + "}" + "}"
    root = NoteNode(title="Root", rtf=legacy_rtf)

    combined = tree_to_rtf(root)

    assert r"\dibitmap0" in combined
    assert dib.hex()[:32] in combined


def test_html_bmp_data_uri_becomes_dibitmap_rtf() -> None:
    bmp = dib_to_bmp_bytes(tiny_dib())
    assert bmp is not None
    src = "data:image/bmp;base64," + base64.b64encode(bmp).decode("ascii")

    rtf = html_to_rtf(f'<p>Vorher <img src="{src}" width="1" height="1"/> Nachher</p>')

    assert r"\dibitmap0" in rtf
    assert bmp_to_dib_bytes(bmp).hex()[:32] in rtf


def test_bmp_file_source_becomes_dibitmap_rtf(tmp_path: Path) -> None:
    bmp = dib_to_bmp_bytes(tiny_dib())
    assert bmp is not None
    image_path = tmp_path / "legacy.bmp"
    image_path.write_bytes(bmp)

    rtf = html_to_rtf(f'<img src="{image_path}"/>')

    assert r"\dibitmap0" in rtf
