from __future__ import annotations

import random

from notizen_py_qt import NoteNode, legacy_new_next_node, legacy_new_next_parent
from notizen_py_qt.legacy_colors import (
    LEGACY_RANDOM_LIGHT_COLOR_ARGB,
    LIGHT_COLOR_ARGB,
    legacy_light_color_argb,
)


def test_neu_neben_knoten_appends_sibling_to_parent_end_like_winforms() -> None:
    root = NoteNode("root")
    first = root.add_child(NoteNode("first"))
    current = root.add_child(NoteNode("current"))
    last = root.add_child(NoteNode("last"))

    parent, index = legacy_new_next_parent(current)
    assert parent is root
    assert index == 3

    created = legacy_new_next_node(current, title="...")
    assert created.parent is root
    assert [node.title for node in root.children] == ["first", "current", "last", "..."]


def test_neu_neben_knoten_on_root_adds_child_to_root_end() -> None:
    root = NoteNode("root")
    root.add_child(NoteNode("A"))

    parent, index = legacy_new_next_parent(root)
    assert parent is root
    assert index == 1

    created = legacy_new_next_node(root, title="child")
    assert created.parent is root
    assert [node.title for node in root.children] == ["A", "child"]


def test_legacy_random_light_color_range_matches_random_next_0_14() -> None:
    # The VB source listed Case 14 and Else, but Random.Next(0, 14) only returns
    # 0..13.  Automatically assigned desktop-note colors must therefore never
    # pick the final two documented fallback colors.
    assert LEGACY_RANDOM_LIGHT_COLOR_ARGB == LIGHT_COLOR_ARGB[:14]
    assert LIGHT_COLOR_ARGB[14] not in LEGACY_RANDOM_LIGHT_COLOR_ARGB
    assert LIGHT_COLOR_ARGB[15] not in LEGACY_RANDOM_LIGHT_COLOR_ARGB

    rng = random.Random(12345)
    for _ in range(100):
        assert legacy_light_color_argb(rng) in LEGACY_RANDOM_LIGHT_COLOR_ARGB
