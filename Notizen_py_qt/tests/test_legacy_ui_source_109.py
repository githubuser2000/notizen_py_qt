from __future__ import annotations

from pathlib import Path


def test_tree_double_click_starts_legacy_rename_edit() -> None:
    source = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")

    assert "itemDoubleClicked.connect(self.edit_tree_item)" in source
    assert "def edit_tree_item" in source
    assert "self.tree.editItem(target, 0)" in source
    assert "def rename_node" in source and "self.edit_tree_item()" in source
