from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from notizen_py_qt.alx_io import document_to_xml_bytes, load_alx, normalize_password, parse_alx_xml, save_alx
from notizen_py_qt.models import DesktopNoteState, NoteDocument, NoteNode
from notizen_py_qt.rtf_utils import plain_text_to_rtf, rtf_to_plain_text
from notizen_py_qt.search_logic import find_in_text, search_nodes


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "legacy_alx"
FIXTURE = FIXTURE_DIR / "unbenannt.alx"
LEGACY_TEST_FIXTURE = FIXTURE_DIR / "test.alx"


def test_parse_v2_nested_xml_roundtrip(tmp_path: Path) -> None:
    root = NoteNode(title="Notes", rtf=plain_text_to_rtf("Hallo"), expanded=False, bg_argb=-1)
    child = root.add_child(NoteNode(title="todo", rtf=plain_text_to_rtf("eins\nzwei")))
    child.desktop_note = DesktopNoteState(x=11, y=12, width=300, height=200, opacity=0.75, argb=-256)
    doc = NoteDocument(root=root)

    out = tmp_path / "demo.alx"
    save_alx(doc, out, backup=False)
    loaded = load_alx(out)

    assert loaded.root is not None
    assert loaded.root.title == "Notes"
    assert loaded.root.expanded is False
    assert rtf_to_plain_text(loaded.root.rtf) == "Hallo"
    assert loaded.root.children[0].title == "todo"
    assert rtf_to_plain_text(loaded.root.children[0].rtf) == "eins\nzwei"
    assert loaded.root.children[0].desktop_note is not None
    assert loaded.root.children[0].desktop_note.x == 11


def test_load_legacy_unencrypted_fixture_if_present() -> None:
    if not FIXTURE.exists():
        pytest.skip("legacy fixture not included")
    doc = load_alx(FIXTURE)
    assert doc.root is not None
    assert doc.root.title == "start"


def test_load_real_notizen_net_test_fixture() -> None:
    if not LEGACY_TEST_FIXTURE.exists():
        pytest.skip("legacy Notizen.NET test.alx fixture not included")
    doc = load_alx(LEGACY_TEST_FIXTURE)
    assert doc.root is not None
    assert doc.root.title == "Notes"
    assert len(doc.root.children) == 8
    desktop_notes = sum(1 for node in doc.root.walk() if node.desktop_note is not None)
    assert desktop_notes == 3
    assert sum(1 for _ in doc.root.walk()) == 65


def test_parse_legacy_notes_doc() -> None:
    xml = """<?xml version='1.0'?><notes_doc><node title='root'><leaf title='leaf'><leaf_text><p>alpha</p><p>beta</p></leaf_text></leaf></node></notes_doc>"""
    doc = parse_alx_xml(xml)
    assert doc.root is not None
    assert doc.root.title == "root"
    assert doc.root.children[0].title == "leaf"
    assert rtf_to_plain_text(doc.root.children[0].rtf) == "alpha\nbeta"


def test_normalize_password_uses_legacy_24_char_rule() -> None:
    assert normalize_password("abc") == "abc" + " " * 21
    assert normalize_password("x" * 30) == "x" * 24


def test_search_modes() -> None:
    assert find_in_text("Alpha beta alpha", "alpha") == [(0, 5), (11, 5)]
    assert find_in_text("Alpha beta alpha", "alpha", case_sensitive=True) == [(11, 5)]
    assert find_in_text("alphabet alpha", "alpha", whole_words=True) == [(9, 5)]
    node = NoteNode(title="n", rtf=plain_text_to_rtf("alpha beta"))
    assert len(search_nodes([node], "beta")) == 1


def test_document_xml_is_utf16_and_gzip_compatible() -> None:
    doc = NoteDocument(root=NoteNode(title="start", rtf=""))
    xml = document_to_xml_bytes(doc)
    assert xml.startswith(b"\xff\xfe") or xml.startswith(b"\xfe\xff")
    payload = gzip.compress(xml)
    assert gzip.decompress(payload).startswith(xml[:2])


def test_alx_bytes_roundtrip_without_files() -> None:
    doc = NoteDocument(root=NoteNode(title="bytes", rtf=plain_text_to_rtf("payload")))
    from notizen_py_qt.alx_io import dump_alx_bytes, load_alx_bytes

    payload = dump_alx_bytes(doc)
    loaded = load_alx_bytes(payload)
    assert loaded.root is not None
    assert loaded.root.title == "bytes"
    assert rtf_to_plain_text(loaded.root.rtf) == "payload"


def test_encrypted_alx_roundtrip_if_crypto_available() -> None:
    try:
        import Crypto.Cipher.DES  # noqa: F401
    except Exception:
        pytest.skip("pycryptodome not installed")
    from notizen_py_qt.alx_io import InvalidPassword, PasswordRequired, dump_alx_bytes, load_alx_bytes

    doc = NoteDocument(root=NoteNode(title="secret", rtf=plain_text_to_rtf("top secret")))
    payload = dump_alx_bytes(doc, password="abcdef")
    with pytest.raises(PasswordRequired):
        load_alx_bytes(payload)
    with pytest.raises(InvalidPassword):
        load_alx_bytes(payload, password="wrong")
    loaded = load_alx_bytes(payload, password="abcdef")
    assert loaded.root is not None
    assert loaded.root.title == "secret"
    assert rtf_to_plain_text(loaded.root.rtf) == "top secret"


def test_ftp_target_normalizes_legacy_fields() -> None:
    from notizen_py_qt.ftp_sync import FtpSyncError, FtpTarget

    target = FtpTarget.from_fields("ftp://user:pw@example.org/", "notes/demo.alx")
    assert target.host == "example.org"
    assert target.username == "user"
    assert target.password == "pw"
    assert target.remote_path == "/notes/demo.alx"
    assert target.display_url == "ftp://user@example.org/notes/demo.alx"
    with pytest.raises(FtpSyncError):
        FtpTarget.from_fields("example.org", "notes/demo.txt")
