from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LegacyShortcut:
    """A keyboard shortcut action ported from Notizen.vb/tastendruck.

    The old WinForms code handled most of these in a global KeyDown handler,
    but the tree-only Insert/Delete/Enter shortcuts were intentionally scoped to
    the TreeView. Keeping this mapping outside Qt makes the port auditable and
    unit-testable without a GUI binding.
    """

    action: str
    requires_tree_focus: bool = False
    requires_editor_focus: bool = False


def legacy_shortcut_action(
    key_name: str,
    *,
    control: bool = False,
    shift: bool = False,
    alt: bool = False,
    tree_focus: bool = False,
    editor_focus: bool = False,
) -> LegacyShortcut | None:
    """Return the legacy Notizen.NET shortcut action for normalized key names.

    ``key_name`` uses simple names such as ``S``, ``Insert`` or ``Return``.
    The result mirrors ``Notizen.vb``: Ctrl shortcuts are application-wide,
    Shift+Insert/Delete are tree-node clipboard operations, and plain
    Insert/Delete/Enter only affect the tree.
    """

    key = (key_name or "").strip().casefold()
    if alt:
        return None

    if control and not shift:
        mapping = {
            "space": "alarm",
            "s": "save",
            "o": "open",
            "n": "new_document",
            "q": "quit",
            "c": "copy",
            "v": "paste",
            "x": "cut",
            "u": "rename",
            "f": "search",
            "+": "font_bigger",
            "plus": "font_bigger",
            "add": "font_bigger",
            "=": "font_bigger",
            "minus": "font_smaller",
            "-": "font_smaller",
            "subtract": "font_smaller",
        }
        action = mapping.get(key)
        if action is None:
            return None
        if action in {"font_bigger", "font_smaller"}:
            return LegacyShortcut(action, requires_editor_focus=True) if editor_focus else None
        return LegacyShortcut(action)

    if shift and not control:
        if not tree_focus:
            return None
        if key == "insert":
            return LegacyShortcut("paste_node", requires_tree_focus=True)
        if key == "delete":
            return LegacyShortcut("cut_node", requires_tree_focus=True)
        return None

    if not control and not shift and tree_focus:
        if key == "insert":
            return LegacyShortcut("add_child", requires_tree_focus=True)
        if key == "delete":
            return LegacyShortcut("delete_node", requires_tree_focus=True)
        if key in {"return", "enter"}:
            return LegacyShortcut("add_sibling", requires_tree_focus=True)
    return None
