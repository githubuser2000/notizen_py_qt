from pathlib import Path


def test_097_legacy_menu_toolbar_features_are_wired_in_main_window_source() -> None:
    source = Path("src/notizen_py_qt/app.py").read_text(encoding="utf-8")

    # These names are intentionally kept near the WinForms command vocabulary
    # so the visible Qt port continues to converge toward Notizen.NET.
    for token in (
        "import_txt_action",
        "import_rtf_action",
        "export_html_action",
        "stats_action",
        "move_up_action",
        "move_down_action",
        "expand_current_action",
        "expand_all_action",
        "collapse_all_action",
        "cycle_scrollbars_action",
        "import_config_action",
    ):
        assert token in source

    for method in (
        "def import_txt_into_current",
        "def import_rtf_into_current",
        "def show_stats_dialog",
        "def move_node_up",
        "def move_node_down",
        "def toggle_current_expanded",
        "def expand_all_nodes",
        "def collapse_all_nodes",
        "def cycle_scrollbars",
        "def import_legacy_config_dialog",
    ):
        assert method in source
