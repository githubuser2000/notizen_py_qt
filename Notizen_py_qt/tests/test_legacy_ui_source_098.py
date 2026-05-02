from __future__ import annotations

from pathlib import Path


SOURCE = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")


def _method_body(name: str) -> str:
    marker = f"        def {name}"
    start = SOURCE.index(marker)
    next_method = SOURCE.find("\n        def ", start + 1)
    if next_method == -1:
        return SOURCE[start:]
    return SOURCE[start:next_method]


def test_098_whole_tree_summary_is_wired_like_the_legacy_root_command() -> None:
    for token in (
        "unify_root_action",
        "Ganzen Baum zusammenfassen",
        "def unify_root_tree",
        "def _append_unified_note",
        "create_unified_note(source, title=title)",
        "source.add_child(unified)",
        "self.select_node(unified)",
    ):
        assert token in SOURCE

    body = _method_body("unify_root_tree")
    assert "root = self.document.root" in body
    assert "self._append_unified_note(root" in body


def test_098_recent_file_menu_checks_unsaved_changes_and_missing_files() -> None:
    assert "self.open_recent_file(p)" in SOURCE
    body = _method_body("open_recent_file")
    assert "Path(path_text)" in body
    assert "path.exists()" in body
    assert "maybe_save_changes()" in body
    assert "load_path(path)" in body


def test_098_search_and_export_sync_the_live_editor_before_reading_model_data() -> None:
    assert "self.main_window.save_current_editor_to_node()" in SOURCE
    assert "def _quick_search_collect" in SOURCE

    for name in ("export_current", "export_root", "export_node_rtf"):
        body = _method_body(name)
        assert "self.save_current_editor_to_node()" in body
