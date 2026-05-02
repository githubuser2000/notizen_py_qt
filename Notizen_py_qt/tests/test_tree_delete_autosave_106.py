from pathlib import Path

from notizen_py_qt import (
    NoteNode,
    legacy_autosave_should_save,
    legacy_delete_fallback_node,
    legacy_previous_visible_node,
    legacy_visible_walk,
)


def _sample_tree() -> tuple[NoteNode, NoteNode, NoteNode, NoteNode, NoteNode]:
    root = NoteNode("root", expanded=True)
    a = root.add_child(NoteNode("A", expanded=True))
    a1 = a.add_child(NoteNode("A1", expanded=True))
    a2 = a.add_child(NoteNode("A2", expanded=True))
    b = root.add_child(NoteNode("B", expanded=True))
    return root, a, a1, a2, b


def test_legacy_visible_walk_respects_expanded_state() -> None:
    root, a, a1, a2, b = _sample_tree()
    assert [node.title for node in legacy_visible_walk(root)] == ["root", "A", "A1", "A2", "B"]

    a.expanded = False
    assert [node.title for node in legacy_visible_walk(root)] == ["root", "A", "B"]
    assert legacy_previous_visible_node(b) is a


def test_legacy_delete_fallback_matches_winforms_previous_visible_node() -> None:
    root, a, a1, a2, b = _sample_tree()
    assert legacy_delete_fallback_node(root) is None
    assert legacy_delete_fallback_node(a) is root
    assert legacy_delete_fallback_node(a1) is a
    assert legacy_delete_fallback_node(a2) is a1
    assert legacy_delete_fallback_node(b) is a2


def test_legacy_autosave_guard_requires_existing_changed_file(tmp_path: Path) -> None:
    path = tmp_path / "demo.alx"
    assert not legacy_autosave_should_save(root_exists=True, path=path, changed=True)

    path.write_bytes(b"old")
    assert legacy_autosave_should_save(root_exists=True, path=path, changed=True)
    assert not legacy_autosave_should_save(root_exists=False, path=path, changed=True)
    assert not legacy_autosave_should_save(root_exists=True, path=path, changed=False)
    assert not legacy_autosave_should_save(root_exists=True, path=None, changed=True)

    path.unlink()
    assert not legacy_autosave_should_save(root_exists=True, path=path, changed=True)
