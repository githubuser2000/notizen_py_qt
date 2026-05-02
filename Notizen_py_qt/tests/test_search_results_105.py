from __future__ import annotations

from pathlib import Path

from notizen_py_qt.models import NoteNode
from notizen_py_qt.rtf_utils import plain_text_to_rtf
from notizen_py_qt.search_logic import find_in_text, search_nodes
from notizen_py_qt.search_results import build_search_hit_views, legacy_search_snippet, node_path


def test_legacy_whole_word_search_uses_space_cr_lf_tokens_only() -> None:
    text = "alpha alpha,beta (alpha) alpha\nbeta\talpha alpha"

    assert find_in_text(text, "alpha", whole_words=True) == [(0, 5), (25, 5), (42, 5)]
    assert find_in_text(text, "alpha", whole_words=True, case_sensitive=True) == [(0, 5), (25, 5), (42, 5)]


def test_legacy_whole_word_search_keeps_tabs_and_punctuation_inside_token() -> None:
    # Notizen.NET's suche.vb only separated whole-word tokens on space/CR/LF.
    # Regex word boundaries would incorrectly match these two cases.
    assert find_in_text("alpha,beta", "alpha", whole_words=True) == []
    assert find_in_text("beta\talpha", "alpha", whole_words=True) == []
    assert find_in_text("beta\ralpha", "alpha", whole_words=True) == [(5, 5)]


def test_search_hit_views_match_legacy_suchergebnisse_shape() -> None:
    root = NoteNode("root", rtf=plain_text_to_rtf("Root text"))
    child = root.add_child(NoteNode("child", rtf=plain_text_to_rtf("before target after")))

    results = search_nodes([root, child], "target")
    views = build_search_hit_views(results, context_chars=8)

    assert len(views) == 1
    assert views[0].result.node is child
    assert views[0].result.start == len("before ")
    assert views[0].node_path == "root / child"
    assert "target" in views[0].snippet
    assert views[0].label.startswith("root / child · 8:")


def test_search_snippet_compacts_line_breaks_and_marks_truncation() -> None:
    text = "0123456789\r\nAlpha target Omega\n0123456789"

    snippet = legacy_search_snippet(text, text.index("target"), len("target"), radius=6)

    assert "target" in snippet
    assert "\n" not in snippet
    assert snippet.startswith("…")
    assert snippet.endswith("…")


def test_search_dialog_contains_visible_legacy_result_list() -> None:
    source = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")

    assert 'setObjectName("Suchliste")' in source
    assert "QListWidget" in source
    assert "itemActivated" in source
    assert "search_previous" in source
    assert "build_search_hit_views" in source
