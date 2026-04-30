from __future__ import annotations

import random

from notizen_py_qt.exporters import tree_to_text_bytes
from notizen_py_qt.i18n import resolve_language, tr
from notizen_py_qt.legacy_colors import LIGHT_COLOR_ARGB, legacy_light_color_argb
from notizen_py_qt.models import NoteNode, legacy_paste_clone
from notizen_py_qt.rtf_utils import plain_text_to_rtf
from notizen_py_qt.startup import parse_legacy_startup_args


def test_legacy_paste_clone_inserts_before_selected_sibling() -> None:
    root = NoteNode("root")
    root.add_child(NoteNode("a"))
    selected = root.add_child(NoteNode("b"))
    source = NoteNode("copy")
    source.add_child(NoteNode("copy-child"))

    pasted = legacy_paste_clone(source, selected)

    assert [child.title for child in root.children] == ["a", "copy", "b"]
    assert pasted.parent is root
    assert pasted.children[0].title == "copy-child"
    assert source.parent is None


def test_legacy_paste_clone_root_pastes_as_first_child() -> None:
    root = NoteNode("root")
    root.add_child(NoteNode("old"))

    pasted = legacy_paste_clone(NoteNode("copy"), root)

    assert pasted.parent is root
    assert [child.title for child in root.children] == ["copy", "old"]


def test_tree_to_text_bytes_encodings_and_crlf() -> None:
    root = NoteNode("r", rtf=plain_text_to_rtf("ä € 😀"))

    utf8 = tree_to_text_bytes(root, encoding="utf-8")
    assert b"\r\n" in utf8
    assert utf8.decode("utf-8").startswith("r\r\n")

    ansi = tree_to_text_bytes(root, encoding="ansi").decode("cp1252")
    assert "ä € ?" in ansi

    unicode_bytes = tree_to_text_bytes(root, encoding="unicode")
    assert unicode_bytes.startswith(b"\xff\xfe")
    assert "😀" in unicode_bytes.decode("utf-16")


def test_i18n_legacy_keys_and_auto_resolution() -> None:
    assert tr("Deutsch", "Strip1_1") == "&Menü"
    assert tr("English", "Strip1_1") == "&Menu"
    assert tr("spanish", "Strip1_8")
    assert resolve_language("Auto", locale_name="fr_FR") == "français"
    assert resolve_language("Auto", locale_name="ru_RU") == "russian"
    assert resolve_language("Auto", locale_name="en_US") == "English"


def test_startup_parser_accepts_legacy_flags_and_ftp_file() -> None:
    legacy = parse_legacy_startup_args([
        "/min",
        "ftp://user:pw@example.org/path/notes.alx",
        "--password",
        "secret",
    ])

    assert legacy.minimized is True
    assert legacy.file == "ftp://user:pw@example.org/path/notes.alx"
    assert legacy.cleaned_args == ("--password", "secret")


def test_startup_parser_help_and_local_file() -> None:
    legacy = parse_legacy_startup_args(["/?", r"C:\\notes\\demo.alx", "--smoke-test"])

    assert legacy.help_requested is True
    assert legacy.file == r"C:\\notes\\demo.alx"
    assert legacy.cleaned_args == ("--smoke-test",)


def test_legacy_light_color_argb_is_signed_argb_from_legacy_palette() -> None:
    value = legacy_light_color_argb(random.Random(0))

    assert value in LIGHT_COLOR_ARGB
    assert isinstance(value, int)
    assert -(2**31) <= value < 2**31
