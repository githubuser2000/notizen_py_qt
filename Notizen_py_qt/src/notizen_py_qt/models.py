from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Iterable


@dataclass(slots=True)
class DesktopNoteState:
    """Persisted state of a Notizen.NET floating desktop note.

    The legacy VB form serializes these values as attributes on a ``Notiz`` XML
    element: x, y, width, height, visible, opacity and argb.
    """

    x: int = 80
    y: int = 80
    width: int = 260
    height: int = 220
    visible: bool = True
    opacity: float = 0.85
    argb: int | None = None


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
            )
        copied = NoteNode(
            title=self.title,
            rtf=self.rtf,
            expanded=self.expanded,
            bg_argb=self.bg_argb,
            fg_argb=self.fg_argb,
            desktop_note=desktop_note,
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
