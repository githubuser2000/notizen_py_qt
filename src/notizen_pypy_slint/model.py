from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable
import itertools

from .rtf import rtf_to_text, text_to_rtf

_id_counter = itertools.count(1)


def _next_id() -> int:
    return next(_id_counter)


@dataclass(slots=True)
class StickyWindow:
    """Persisted metadata from the old WinForms desktop-note windows."""

    visible: bool = False
    x: int | None = None
    y: int | None = None
    width: int | None = None
    height: int | None = None
    opacity: float | None = None
    argb: int | None = None

    @classmethod
    def from_attrs(cls, attrs: dict[str, str]) -> "StickyWindow | None":
        if not any(key in attrs for key in ("visible", "x", "y", "width", "height", "opacity", "argb")):
            return None

        def as_int(name: str) -> int | None:
            try:
                return int(attrs[name])
            except Exception:
                return None

        def as_float(name: str) -> float | None:
            try:
                return float(attrs[name])
            except Exception:
                return None

        visible_raw = attrs.get("visible", "False")
        return cls(
            visible=visible_raw.lower() in {"true", "1", "yes", "ja"},
            x=as_int("x"),
            y=as_int("y"),
            width=as_int("width"),
            height=as_int("height"),
            opacity=as_float("opacity"),
            argb=as_int("argb"),
        )

    def to_attrs(self) -> dict[str, str]:
        attrs: dict[str, str] = {}
        attrs["visible"] = "True" if self.visible else "False"
        for name in ("x", "y", "width", "height"):
            value = getattr(self, name)
            if value is not None:
                attrs[name] = str(value)
        if self.opacity is not None:
            attrs["opacity"] = str(self.opacity)
        if self.argb is not None:
            attrs["argb"] = str(self.argb)
        return attrs


@dataclass(slots=True)
class Note:
    title: str = "..."
    rtf: str = ""
    children: list["Note"] = field(default_factory=list)
    expanded: bool = True
    bg_color: int | None = None
    fg_color: int | None = None
    sticky: StickyWindow | None = None
    note_id: int = field(default_factory=_next_id)
    parent: "Note | None" = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        for child in self.children:
            child.parent = self
        if self.rtf is None:
            self.rtf = ""

    @property
    def text(self) -> str:
        return rtf_to_text(self.rtf)

    def set_text(self, text: str) -> None:
        self.rtf = text_to_rtf(text)

    def add_child(self, child: "Note | None" = None) -> "Note":
        child = child or Note()
        child.parent = self
        self.children.append(child)
        return child

    def insert_after(self, sibling: "Note | None" = None) -> "Note":
        if self.parent is None:
            return self.add_child(sibling)
        sibling = sibling or Note()
        sibling.parent = self.parent
        siblings = self.parent.children
        siblings.insert(siblings.index(self) + 1, sibling)
        return sibling

    def remove_from_parent(self) -> "Note | None":
        if self.parent is None:
            return None
        siblings = self.parent.children
        idx = siblings.index(self)
        siblings.remove(self)
        self.parent = None
        if siblings:
            return siblings[min(idx, len(siblings) - 1)]
        return None

    def clone_deep(self) -> "Note":
        clone = Note(
            title=self.title,
            rtf=self.rtf,
            expanded=self.expanded,
            bg_color=self.bg_color,
            fg_color=self.fg_color,
            sticky=self.sticky,
        )
        clone.children = [child.clone_deep() for child in self.children]
        for child in clone.children:
            child.parent = clone
        return clone


@dataclass(slots=True)
class FlatNote:
    note: Note
    level: int

    @property
    def label(self) -> str:
        marker = "▾" if self.note.children and self.note.expanded else "▸" if self.note.children else "•"
        return f"{'   ' * self.level}{marker} {self.note.title}"


@dataclass(slots=True)
class NoteDocument:
    root: Note
    path: str | None = None
    password: str | None = None
    modified: bool = False
    selected_id: int | None = None

    @classmethod
    def empty(cls) -> "NoteDocument":
        root = Note("start", text_to_rtf(""))
        return cls(root=root, selected_id=root.note_id)

    def iter_notes(self) -> Iterable[Note]:
        yield from _iter_notes(self.root)

    def flatten(self, include_collapsed: bool = False) -> list[FlatNote]:
        rows: list[FlatNote] = []

        def rec(note: Note, level: int) -> None:
            rows.append(FlatNote(note, level))
            if include_collapsed or note.expanded:
                for child in note.children:
                    rec(child, level + 1)

        rec(self.root, 0)
        return rows

    def note_by_id(self, note_id: int | None) -> Note | None:
        if note_id is None:
            return None
        for note in self.iter_notes():
            if note.note_id == note_id:
                return note
        return None

    @property
    def selected_note(self) -> Note:
        note = self.note_by_id(self.selected_id)
        if note is not None:
            return note
        self.selected_id = self.root.note_id
        return self.root

    def select_by_flat_index(self, index: int) -> Note | None:
        rows = self.flatten()
        if not 0 <= index < len(rows):
            return None
        self.selected_id = rows[index].note.note_id
        return rows[index].note

    def selected_flat_index(self) -> int:
        for i, row in enumerate(self.flatten()):
            if row.note.note_id == self.selected_id:
                return i
        return 0

    def add_child_to_selected(self) -> Note:
        note = self.selected_note.add_child(Note("...", text_to_rtf("")))
        self.selected_note.expanded = True
        self.selected_id = note.note_id
        self.modified = True
        return note

    def add_sibling_after_selected(self) -> Note:
        selected = self.selected_note
        if selected.parent is None:
            note = selected.add_child(Note("...", text_to_rtf("")))
            selected.expanded = True
        else:
            note = selected.insert_after(Note("...", text_to_rtf("")))
        self.selected_id = note.note_id
        self.modified = True
        return note

    def delete_selected(self) -> Note:
        selected = self.selected_note
        if selected.parent is None:
            selected.children.clear()
            selected.title = "start"
            selected.rtf = text_to_rtf("")
            self.modified = True
            return selected
        replacement = selected.remove_from_parent()
        if replacement is None:
            replacement = selected.parent or self.root
        self.selected_id = replacement.note_id
        self.modified = True
        return replacement

    def toggle_selected_expanded(self) -> None:
        note = self.selected_note
        if note.children:
            note.expanded = not note.expanded
            self.modified = True

    def find_next(self, needle: str) -> Note | None:
        needle = (needle or "").casefold()
        if not needle:
            return None
        flat = [row.note for row in self.flatten(include_collapsed=True)]
        if not flat:
            return None
        current_index = next((i for i, note in enumerate(flat) if note.note_id == self.selected_id), -1)
        ordered = flat[current_index + 1 :] + flat[: current_index + 1]
        for note in ordered:
            if needle in note.title.casefold() or needle in note.text.casefold():
                self.selected_id = note.note_id
                self._expand_ancestors(note)
                return note
        return None

    def _expand_ancestors(self, note: Note) -> None:
        parent = note.parent
        while parent is not None:
            parent.expanded = True
            parent = parent.parent

    def walk_with_level(self, visit: Callable[[Note, int], None]) -> None:
        def rec(note: Note, level: int) -> None:
            visit(note, level)
            for child in note.children:
                rec(child, level + 1)

        rec(self.root, 0)


def _iter_notes(root: Note) -> Iterable[Note]:
    yield root
    for child in root.children:
        yield from _iter_notes(child)
