from __future__ import annotations

from pathlib import Path

from notizen_py_qt.alx_io import dump_alx_bytes, load_alx, load_alx_bytes

FIXTURES = Path(__file__).parent / "fixtures"


def titles(document) -> list[str]:
    return [node.title for node in document.walk()]


def test_sanitized_legacy_desktop_fixture_loads_with_desktop_notes() -> None:
    document = load_alx(FIXTURES / "legacy_sanitized_desktop.alx")
    assert document.root is not None
    assert document.root.title == "Notes"
    nodes = list(document.walk())
    assert titles(document) == ["Notes", "Desktop Eins", "Ordner", "Desktop Zwei"]
    desktop_titles = [node.title for node in nodes if node.desktop_note is not None]
    assert desktop_titles == ["Desktop Eins", "Desktop Zwei"]
    first_state = next(node.desktop_note for node in nodes if node.title == "Desktop Eins")
    assert first_state is not None
    assert first_state.width == 220
    assert first_state.height == 180
    assert first_state.visible is True
    assert 0.1 <= first_state.opacity <= 1.0
    second_state = next(node.desktop_note for node in nodes if node.title == "Desktop Zwei")
    assert second_state is not None
    assert second_state.visible is False
    assert second_state.opacity == 0.55


def test_sanitized_legacy_fixture_roundtrip_preserves_tree_titles_and_desktop_notes() -> None:
    document = load_alx(FIXTURES / "legacy_sanitized_desktop.alx")
    before_titles = titles(document)
    before_desktop = {
        node.title: (node.desktop_note.x, node.desktop_note.y, node.desktop_note.width, node.desktop_note.height, node.desktop_note.visible)
        for node in document.walk()
        if node.desktop_note is not None
    }
    payload = dump_alx_bytes(document)
    reloaded = load_alx_bytes(payload)
    assert titles(reloaded) == before_titles
    assert {
        node.title: (node.desktop_note.x, node.desktop_note.y, node.desktop_note.width, node.desktop_note.height, node.desktop_note.visible)
        for node in reloaded.walk()
        if node.desktop_note is not None
    } == before_desktop


def test_real_notizen_net_unbenannt_fixture_loads_default_start_node() -> None:
    document = load_alx(FIXTURES / "legacy_unbenannt.alx")
    assert document.root is not None
    assert document.root.title == "start"
    assert [node.title for node in document.walk()] == ["start"]
