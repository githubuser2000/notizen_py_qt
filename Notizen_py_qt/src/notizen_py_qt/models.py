from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Iterable


@dataclass(slots=True)
class DesktopNoteState:
    """Persisted state of a Notizen.NET floating desktop note.

    The legacy VB form serializes these values as attributes on a ``Notiz`` XML
    element: x, y, width, height, visible, opacity and argb.  Very old ALX
    files sometimes omit optional desktop-note attributes.  ``legacy_sparse``
    and ``legacy_attr_names`` let the serializer avoid inventing those optional
    attributes on a no-op open/save roundtrip, while still writing them when the
    user changes a note or creates a new desktop note in the PyQt port.
    """

    x: int = 80
    y: int = 80
    width: int = 260
    height: int = 220
    visible: bool = True
    opacity: float = 0.85
    argb: int | None = None
    legacy_sparse: bool = False
    legacy_attr_names: set[str] = field(default_factory=set, repr=False, compare=False)


@dataclass(slots=True)
class NoteNode:
    """One node in the Notizen.NET tree.

    ``rtf`` intentionally stores the original RTF payload. The Qt editor uses a
    plain-text view by default, but the raw RTF is preserved until the user edits
    the note. This keeps old files readable without destroying formatting on a
    mere open/save cycle.
    """

    title: str = "..."
    rtf: str = ""
    expanded: bool = True
    bg_argb: int = 0
    fg_argb: int = 0
    desktop_note: DesktopNoteState | None = None
    extra_attrs: dict[str, str] = field(default_factory=dict)
    children: list["NoteNode"] = field(default_factory=list)
    parent: "NoteNode | None" = field(default=None, repr=False, compare=False)

    def add_child(self, child: "NoteNode") -> "NoteNode":
        child.parent = self
        self.children.append(child)
        return child

    def insert_child(self, index: int, child: "NoteNode") -> "NoteNode":
        child.parent = self
        self.children.insert(index, child)
        return child

    def remove_from_parent(self) -> None:
        if self.parent is None:
            return
        self.parent.children.remove(self)
        self.parent = None

    def clone_deep(self, *, include_desktop_note: bool = True) -> "NoteNode":
        desktop_note = None
        if include_desktop_note and self.desktop_note is not None:
            desktop_note = DesktopNoteState(
                x=self.desktop_note.x,
                y=self.desktop_note.y,
                width=self.desktop_note.width,
                height=self.desktop_note.height,
                visible=self.desktop_note.visible,
                opacity=self.desktop_note.opacity,
                argb=self.desktop_note.argb,
                legacy_sparse=self.desktop_note.legacy_sparse,
                legacy_attr_names=set(self.desktop_note.legacy_attr_names),
            )
        copied = NoteNode(
            title=self.title,
            rtf=self.rtf,
            expanded=self.expanded,
            bg_argb=self.bg_argb,
            fg_argb=self.fg_argb,
            desktop_note=desktop_note,
            extra_attrs=dict(self.extra_attrs),
        )
        for child in self.children:
            copied.add_child(child.clone_deep(include_desktop_note=include_desktop_note))
        return copied

    def walk(self) -> Generator["NoteNode", None, None]:
        yield self
        for child in self.children:
            yield from child.walk()

    def index_in_parent(self) -> int:
        if self.parent is None:
            return 0
        return self.parent.children.index(self)

    def next_sibling_index(self) -> int:
        return self.index_in_parent() + 1

    def is_ancestor_of(self, other: "NoteNode") -> bool:
        node = other.parent
        while node is not None:
            if node is self:
                return True
            node = node.parent
        return False


def legacy_paste_clone(source: NoteNode, selected: NoteNode) -> NoteNode:
    """Clone ``source`` using the insertion rule from Notizen.NET.

    The old WinForms ``paste_anything(False)`` did not always append below the
    selected node. If the root was selected, the pasted subtree became the first
    child of the root. Otherwise it was inserted as a sibling directly before the
    selected node.
    """
    pasted = source.clone_deep(include_desktop_note=False)
    if selected.parent is None:
        selected.insert_child(0, pasted)
    else:
        selected.parent.insert_child(selected.index_in_parent(), pasted)
    return pasted


def legacy_visible_walk(root: NoteNode) -> list[NoteNode]:
    """Return nodes in the visible WinForms ``TreeView`` order.

    ``Baum.element_loeschen`` selected ``SelectedNode.PrevVisibleNode`` after a
    deletion.  That value is not simply the parent: if the previous sibling is
    expanded, WinForms selects the deepest visible child of that sibling.  This
    helper mirrors that preorder traversal without depending on Qt.
    """

    visible: list[NoteNode] = []

    def visit(node: NoteNode) -> None:
        visible.append(node)
        if node.expanded:
            for child in node.children:
                visit(child)

    visit(root)
    return visible


def legacy_previous_visible_node(selected: NoteNode) -> NoteNode | None:
    """Return the WinForms ``PrevVisibleNode`` equivalent for ``selected``."""

    root = selected
    while root.parent is not None:
        root = root.parent
    visible = legacy_visible_walk(root)
    try:
        index = visible.index(selected)
    except ValueError:
        return selected.parent
    if index <= 0:
        return None
    return visible[index - 1]


def legacy_delete_fallback_node(selected: NoteNode) -> NoteNode | None:
    """Return the node selected by Notizen.NET after deleting ``selected``.

    The legacy root deletion path closes the document instead of removing the
    root, so root returns ``None``.  Non-root nodes fall back to the previous
    visible node; if the tree state is inconsistent, the parent is safer than
    leaving the UI without a current node.
    """

    if selected.parent is None:
        return None
    return legacy_previous_visible_node(selected) or selected.parent


def legacy_new_next_parent(selected: NoteNode) -> tuple[NoteNode, int]:
    """Return the legacy insertion target for ``Neu daneben`` / Enter.

    ``Notizen.vb`` implements ``neu_neben_knoten`` by temporarily selecting the
    parent for non-root nodes and then calling ``Baum.element_dazu``.  Since
    ``element_dazu`` always appends a new child to the selected node, the old
    "next" command appends the new sibling at the end of the parent level
    instead of inserting it directly after the currently selected node.  If the
    root is selected, the new node is appended as a child of the root.
    """

    parent = selected if selected.parent is None else selected.parent
    return parent, len(parent.children)


def legacy_new_next_node(selected: NoteNode, title: str = "...") -> NoteNode:
    """Create the node produced by legacy ``neu_neben_knoten``.

    The helper is intentionally Qt-independent so the slightly surprising
    WinForms insertion rule stays regression-testable.
    """

    parent, _index = legacy_new_next_parent(selected)
    return parent.add_child(NoteNode(title=title, rtf=""))


def legacy_can_move_before_target(source: NoteNode, target: NoteNode) -> bool:
    """Return whether legacy tree drag/drop may move ``source`` before ``target``.

    ``Baum_MouseUp`` in the VB.NET TreeView did not drop a dragged node *into*
    the hovered node.  It inserted a clone of the dragged subtree as a sibling
    directly before the hovered target and then removed the original.  The move
    was refused for the root node, for drops onto the root, onto itself, or into
    one of the source node's descendants.
    """

    if source is target:
        return False
    if source.parent is None:
        return False
    if target.parent is None:
        return False
    if source.is_ancestor_of(target):
        return False
    return True


def legacy_move_before_target(source: NoteNode, target: NoteNode) -> NoteNode | None:
    """Move ``source`` according to the old Notizen.NET TreeView drag rule.

    The legacy code performed the move through ``Clone`` + ``Remove``.  The
    Python port keeps the same visible ordering but moves the existing object so
    desktop-note windows, tests and callers keep their node identity.
    """

    if not legacy_can_move_before_target(source, target):
        return None

    old_parent = source.parent
    new_parent = target.parent
    if old_parent is None or new_parent is None:
        return None

    old_index = old_parent.children.index(source)
    new_index = new_parent.children.index(target)
    old_parent.children.pop(old_index)
    if old_parent is new_parent and old_index < new_index:
        new_index -= 1
    source.parent = None
    new_parent.insert_child(new_index, source)
    return source


@dataclass(slots=True)
class NoteDocument:
    root: NoteNode | None = None
    path: Path | None = None
    password: str = ""
    changed: bool = False

    @classmethod
    def new(cls) -> "NoteDocument":
        return cls(root=NoteNode(title="start", rtf=""), changed=True)

    def ensure_root(self) -> NoteNode:
        if self.root is None:
            self.root = NoteNode(title="start", rtf="")
        return self.root

    def walk(self) -> Iterable[NoteNode]:
        if self.root is None:
            return []
        return self.root.walk()

    def mark_changed(self) -> None:
        self.changed = True

    def mark_saved(self, path: str | Path | None = None) -> None:
        if path is not None:
            self.path = Path(path)
        self.changed = False
