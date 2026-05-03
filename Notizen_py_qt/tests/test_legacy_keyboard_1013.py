from __future__ import annotations

from notizen_py_qt.keyboard_legacy import legacy_shortcut_action


def action(name: str, **kwargs: object) -> str | None:
    result = legacy_shortcut_action(name, **kwargs)  # type: ignore[arg-type]
    return None if result is None else result.action


def test_global_ctrl_shortcuts_from_notizen_vb_tastendruck() -> None:
    assert action("Space", control=True) == "alarm"
    assert action("S", control=True) == "save"
    assert action("O", control=True) == "open"
    assert action("N", control=True) == "new_document"
    assert action("Q", control=True) == "quit"
    assert action("C", control=True) == "copy"
    assert action("V", control=True) == "paste"
    assert action("X", control=True) == "cut"
    assert action("U", control=True) == "rename"
    assert action("F", control=True) == "search"


def test_font_shortcuts_are_editor_scoped_like_lastfocus_inhalt() -> None:
    assert action("Plus", control=True, editor_focus=True) == "font_bigger"
    assert action("=", control=True, editor_focus=True) == "font_bigger"
    assert action("Minus", control=True, editor_focus=True) == "font_smaller"
    assert action("Plus", control=True, editor_focus=False) is None


def test_tree_only_shift_and_plain_shortcuts_from_baum_and_notizen() -> None:
    assert action("Insert", shift=True, tree_focus=True) == "paste_node"
    assert action("Delete", shift=True, tree_focus=True) == "cut_node"
    assert action("Insert", tree_focus=True) == "add_child"
    assert action("Delete", tree_focus=True) == "delete_node"
    assert action("Return", tree_focus=True) == "add_sibling"
    assert action("Enter", tree_focus=True) == "add_sibling"
    assert action("Insert", shift=True, tree_focus=False) is None
    assert action("Delete", tree_focus=False) is None


def test_alt_or_unknown_shortcuts_are_left_to_qt_default_handling() -> None:
    assert action("S", control=True, alt=True) is None
    assert action("B", control=True) is None
