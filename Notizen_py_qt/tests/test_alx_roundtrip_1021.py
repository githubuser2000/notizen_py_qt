from __future__ import annotations

from notizen_py_qt.alx_io import dump_alx_bytes, load_alx_bytes
from notizen_py_qt.models import DesktopNoteState, NoteDocument, NoteNode
from notizen_py_qt.rtf_utils import plain_text_to_rtf


def test_alx_roundtrip_preserves_core_legacy_node_state() -> None:
    root = NoteNode(
        title="Wurzel",
        rtf=plain_text_to_rtf("RTF bleibt roh"),
        expanded=False,
        bg_argb=-123,
        fg_argb=-456,
        extra_attrs={"legacyAttr": "wird-behalten"},
        desktop_note=DesktopNoteState(
            visible=False,
            x=11,
            y=22,
            width=333,
            height=144,
            opacity=0.42,
            argb=-789,
        ),
    )
    child = root.add_child(NoteNode(title="Kind", rtf=plain_text_to_rtf("Kind"), expanded=True))
    child.add_child(NoteNode(title="Enkel", rtf=plain_text_to_rtf("Enkel"), expanded=False))

    loaded = load_alx_bytes(dump_alx_bytes(NoteDocument(root=root)))
    loaded_root = loaded.ensure_root()

    assert loaded_root.title == "Wurzel"
    assert loaded_root.rtf == root.rtf
    assert loaded_root.expanded is False
    assert loaded_root.bg_argb == -123
    assert loaded_root.fg_argb == -456
    assert loaded_root.extra_attrs == {"legacyAttr": "wird-behalten"}
    assert loaded_root.desktop_note is not None
    assert loaded_root.desktop_note.visible is False
    assert loaded_root.desktop_note.x == 11
    assert loaded_root.desktop_note.y == 22
    assert loaded_root.desktop_note.width == 333
    assert loaded_root.desktop_note.height == 144
    assert loaded_root.desktop_note.opacity == 0.42
    assert loaded_root.desktop_note.argb == -789
    assert [node.title for node in loaded_root.walk()] == ["Wurzel", "Kind", "Enkel"]
    assert [node.expanded for node in loaded_root.walk()] == [False, True, False]
