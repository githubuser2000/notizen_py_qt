from pathlib import Path


def test_legacy_split_ui_fields_are_declared_in_main_window_source() -> None:
    source = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")
    # The WinForms form had txt1 above the tree, txt2 above the rich-text editor,
    # a TreeView named Baum and a RichTextBox named Inhalt.  The Python/Qt port
    # keeps those names as Qt object names so screenshots and UI tests can find
    # the controls.
    assert 'setObjectName("txt1")' in source
    assert 'setObjectName("txt2")' in source
    assert 'setObjectName("Baum")' in source
    assert 'setObjectName("Inhalt")' in source
    assert "commit_title_box" in source
    assert "update_node_text_boxes" in source
