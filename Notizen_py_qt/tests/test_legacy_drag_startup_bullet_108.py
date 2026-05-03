from __future__ import annotations

from pathlib import Path

from notizen_py_qt.editor_legacy import legacy_clipboard_bullet_text, qt_bullet_insert_text
from notizen_py_qt.models import NoteNode, legacy_can_move_before_target, legacy_move_before_target
from notizen_py_qt.startup import parse_legacy_startup_args, validate_legacy_startup_target


def _tree() -> tuple[NoteNode, NoteNode, NoteNode, NoteNode, NoteNode]:
    root = NoteNode(title="root")
    alpha = root.add_child(NoteNode(title="alpha"))
    alpha_child = alpha.add_child(NoteNode(title="alpha child"))
    beta = root.add_child(NoteNode(title="beta"))
    gamma = root.add_child(NoteNode(title="gamma"))
    return root, alpha, alpha_child, beta, gamma


def _titles(node: NoteNode) -> list[str]:
    return [child.title for child in node.children]


def test_legacy_drag_rejects_root_self_and_descendant_targets() -> None:
    root, alpha, alpha_child, beta, _gamma = _tree()

    assert not legacy_can_move_before_target(root, beta)
    assert not legacy_can_move_before_target(alpha, root)
    assert not legacy_can_move_before_target(alpha, alpha)
    assert not legacy_can_move_before_target(alpha, alpha_child)
    assert legacy_move_before_target(alpha, alpha_child) is None
    assert _titles(root) == ["alpha", "beta", "gamma"]


def test_legacy_drag_moves_existing_subtree_before_target() -> None:
    root, alpha, alpha_child, beta, gamma = _tree()

    moved = legacy_move_before_target(gamma, beta)

    assert moved is gamma
    assert gamma.parent is root
    assert _titles(root) == ["alpha", "gamma", "beta"]
    assert alpha.children == [alpha_child]
    assert alpha_child.parent is alpha


def test_legacy_drag_same_parent_index_adjustment() -> None:
    root, alpha, _alpha_child, beta, gamma = _tree()

    assert legacy_move_before_target(alpha, gamma) is alpha

    assert _titles(root) == ["beta", "alpha", "gamma"]
    assert alpha.parent is root


def test_legacy_drag_cross_parent_keeps_node_identity() -> None:
    root, alpha, alpha_child, beta, _gamma = _tree()

    moved = legacy_move_before_target(beta, alpha_child)

    assert moved is beta
    assert beta.parent is alpha
    assert _titles(root) == ["alpha", "gamma"]
    assert _titles(alpha) == ["beta", "alpha child"]


def test_legacy_bullet_clipboard_text_and_qt_normalization() -> None:
    assert legacy_clipboard_bullet_text() == "\r•   "
    assert qt_bullet_insert_text() == "\n•   "


def test_legacy_startup_validation_clears_missing_local_alx() -> None:
    options = parse_legacy_startup_args(["-min", "missing.alx"])

    result = validate_legacy_startup_target(options, exists=lambda _path: False)

    assert result.missing_file == "missing.alx"
    assert result.options.file is None
    assert result.options.minimized is True


def test_legacy_startup_validation_keeps_existing_local_alx(tmp_path: Path) -> None:
    target = tmp_path / "ok.alx"
    target.write_text("", encoding="utf-8")
    options = parse_legacy_startup_args([str(target)])

    result = validate_legacy_startup_target(options)

    assert result.missing_file is None
    assert result.options.file == str(target)


def test_legacy_startup_validation_keeps_ftp_without_local_check() -> None:
    options = parse_legacy_startup_args(["ftp://example.invalid/notizen.alx"])

    result = validate_legacy_startup_target(options, exists=lambda _path: False)

    assert result.missing_file is None
    assert result.options.file == "ftp://example.invalid/notizen.alx"
