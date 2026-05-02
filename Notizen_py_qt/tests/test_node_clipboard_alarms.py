from __future__ import annotations

from datetime import datetime

from notizen_py_qt.alarms import AlarmSpec, describe_recurrence, next_occurrence
from notizen_py_qt.models import DesktopNoteState, NoteNode, legacy_paste_clone
from notizen_py_qt.node_clipboard import (
    NODE_MIME_TYPE,
    looks_like_node_clipboard_xml,
    node_from_clipboard_xml,
    node_to_clipboard_xml,
)
from notizen_py_qt.rtf_utils import plain_text_to_rtf, rtf_to_plain_text


def test_node_clipboard_xml_roundtrip_preserves_subtree_without_desktop_note() -> None:
    root = NoteNode(
        "root",
        rtf=plain_text_to_rtf("hello"),
        expanded=False,
        bg_argb=-1,
        fg_argb=-2,
        desktop_note=DesktopNoteState(x=1, y=2, width=300, height=200, argb=-3),
    )
    root.add_child(NoteNode("child", rtf=plain_text_to_rtf("child body")))

    xml_text = node_to_clipboard_xml(root)
    loaded = node_from_clipboard_xml(xml_text)

    assert NODE_MIME_TYPE == "application/x-notizen-pyqt-node+xml"
    assert looks_like_node_clipboard_xml(xml_text)
    assert loaded.title == "root"
    assert loaded.expanded is False
    assert loaded.bg_argb == -1
    assert loaded.fg_argb == -2
    assert loaded.desktop_note is None
    assert rtf_to_plain_text(loaded.rtf) == "hello"
    assert len(loaded.children) == 1
    assert loaded.children[0].title == "child"
    assert loaded.children[0].parent is loaded
    assert rtf_to_plain_text(loaded.children[0].rtf) == "child body"


def test_node_clipboard_can_optionally_keep_desktop_note_state() -> None:
    state = DesktopNoteState(x=11, y=12, width=333, height=222, visible=True, opacity=0.5, argb=-123)
    node = NoteNode("desk", desktop_note=state)

    xml_text = node_to_clipboard_xml(node, include_desktop_note=True)
    loaded = node_from_clipboard_xml(xml_text, include_desktop_note=True)

    assert loaded.desktop_note is not None
    assert loaded.desktop_note.x == 11
    assert loaded.desktop_note.y == 12
    assert loaded.desktop_note.width == 333
    assert loaded.desktop_note.height == 222
    assert loaded.desktop_note.opacity == 0.5
    assert loaded.desktop_note.argb == -123


def test_legacy_paste_clone_drops_desktop_note_state() -> None:
    root = NoteNode("root")
    selected = root.add_child(NoteNode("selected"))
    source = NoteNode("source", desktop_note=DesktopNoteState(argb=-77))
    source.add_child(NoteNode("child", desktop_note=DesktopNoteState(argb=-88)))

    pasted = legacy_paste_clone(source, selected)

    assert pasted.parent is root
    assert pasted.desktop_note is None
    assert pasted.children[0].desktop_note is None
    assert root.children[0] is pasted
    assert root.children[1] is selected


def test_alarm_next_occurrence_one_shot_and_daily() -> None:
    start = datetime(2026, 4, 30, 8, 0)

    assert next_occurrence(AlarmSpec(start), datetime(2026, 4, 30, 7, 59)) == start
    assert next_occurrence(AlarmSpec(start), datetime(2026, 4, 30, 8, 0)) is None

    daily = AlarmSpec(start, recurrence="daily", interval=2)
    assert next_occurrence(daily, datetime(2026, 4, 30, 8, 0)) == datetime(2026, 5, 2, 8, 0)
    assert next_occurrence(daily, datetime(2026, 5, 3, 9, 0)) == datetime(2026, 5, 4, 8, 0)
    assert "täglich" in describe_recurrence(daily)


def test_alarm_next_occurrence_weekly_monthly_yearly() -> None:
    start = datetime(2024, 1, 31, 9, 30)
    weekly = AlarmSpec(start, recurrence="weekly", weekdays=(0, 2), interval=1)
    assert next_occurrence(weekly, datetime(2024, 2, 5, 9, 31)) == datetime(2024, 2, 7, 9, 30)
    assert "Mo" in describe_recurrence(weekly)

    monthly = AlarmSpec(start, recurrence="monthly", interval=1)
    assert next_occurrence(monthly, datetime(2024, 2, 1, 0, 0)) == datetime(2024, 2, 29, 9, 30)
    assert next_occurrence(monthly, datetime(2024, 4, 30, 9, 30)) == datetime(2024, 5, 31, 9, 30)

    leap = AlarmSpec(datetime(2024, 2, 29, 10, 0), recurrence="yearly", interval=1)
    assert next_occurrence(leap, datetime(2024, 3, 1, 0, 0)) == datetime(2025, 2, 28, 10, 0)
    every_four_years = AlarmSpec(datetime(2024, 2, 29, 10, 0), recurrence="yearly", interval=4)
    assert next_occurrence(every_four_years, datetime(2025, 3, 1, 0, 0)) == datetime(2028, 2, 29, 10, 0)
