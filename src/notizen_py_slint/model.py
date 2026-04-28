from __future__ import annotations

from dataclasses import dataclass, field
import itertools
import re
from typing import Callable, Iterable

from .rtf import rtf_to_text, text_to_rtf
from .legacy_colors import argb_to_signed

_id_counter = itertools.count(1)


def _next_id() -> int:
    return next(_id_counter)


@dataclass(slots=True)
class StickyWindow:
    """Persisted metadata from the old WinForms desktop-note windows.

    Notizen.NET stored the state of a detached "Haftnotiz" directly as XML
    attributes on the note node.  Slint cannot recreate the exact WinForms
    borderless sticky windows portably, but keeping these fields editable means
    files round-trip cleanly and old sticky notes can be reactivated later.
    """

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
                return float(str(attrs[name]).replace(",", "."))
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

    def copy(self) -> "StickyWindow":
        return StickyWindow(
            visible=self.visible,
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            opacity=self.opacity,
            argb=self.argb,
        )

    def to_attrs(self) -> dict[str, str]:
        attrs: dict[str, str] = {"visible": "True" if self.visible else "False"}
        for name in ("x", "y", "width", "height"):
            value = getattr(self, name)
            if value is not None:
                attrs[name] = str(value)
        if self.opacity is not None:
            attrs["opacity"] = str(self.opacity)
        if self.argb is not None:
            attrs["argb"] = str(argb_to_signed(self.argb))
        return attrs

    def summary(self) -> str:
        bits = ["sichtbar" if self.visible else "verborgen"]
        if None not in (self.x, self.y, self.width, self.height):
            bits.append(f"{self.x},{self.y} {self.width}x{self.height}")
        if self.opacity is not None:
            bits.append(f"Deckkraft {self.opacity:g}")
        if self.argb is not None:
            bits.append(f"Farbe {argb_to_hex(self.argb)}")
        return ", ".join(bits)


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

    def set_rtf(self, rtf: str) -> None:
        self.rtf = rtf or ""

    def add_child(self, child: "Note | None" = None) -> "Note":
        child = child or Note()
        child.parent = self
        self.children.append(child)
        return child

    def insert_child(self, index: int, child: "Note") -> "Note":
        child.parent = self
        self.children.insert(max(0, min(index, len(self.children))), child)
        return child

    def insert_after(self, sibling: "Note | None" = None) -> "Note":
        if self.parent is None:
            return self.add_child(sibling)
        sibling = sibling or Note()
        sibling.parent = self.parent
        siblings = self.parent.children
        siblings.insert(siblings.index(self) + 1, sibling)
        return sibling

    def insert_before(self, sibling: "Note | None" = None) -> "Note":
        if self.parent is None:
            return self.add_child(sibling)
        sibling = sibling or Note()
        sibling.parent = self.parent
        siblings = self.parent.children
        siblings.insert(siblings.index(self), sibling)
        return sibling

    def remove_from_parent(self) -> tuple["Note | None", int | None]:
        if self.parent is None:
            return None, None
        parent = self.parent
        idx = parent.children.index(self)
        parent.children.pop(idx)
        self.parent = None
        return parent, idx

    def clone_deep(self) -> "Note":
        clone = Note(
            title=self.title,
            rtf=self.rtf,
            expanded=self.expanded,
            bg_color=self.bg_color,
            fg_color=self.fg_color,
            sticky=self.sticky.copy() if self.sticky is not None else None,
        )
        clone.children = [child.clone_deep() for child in self.children]
        for child in clone.children:
            child.parent = clone
        return clone

    def is_ancestor_of(self, other: "Note") -> bool:
        parent = other.parent
        while parent is not None:
            if parent is self:
                return True
            parent = parent.parent
        return False

    def path_titles(self) -> list[str]:
        result: list[str] = []
        note: Note | None = self
        while note is not None:
            result.append(note.title)
            note = note.parent
        return list(reversed(result))

    def path_string(self) -> str:
        return " / ".join(self.path_titles())


@dataclass(slots=True)
class FlatNote:
    note: Note
    level: int

    @property
    def label(self) -> str:
        marker = "▾" if self.note.children and self.note.expanded else "▸" if self.note.children else "•"
        icons = ""
        if self.note.sticky is not None and self.note.sticky.visible:
            icons += " 📌"
        if self.note.bg_color not in (None, 0) or self.note.fg_color not in (None, 0):
            icons += " ◼"
        return f"{'   ' * self.level}{marker} {self.note.title}{icons}"


@dataclass(slots=True)
class SearchHit:
    note: Note
    title_match: bool = False
    text_match: bool = False


@dataclass(slots=True)
class SearchDetail:
    note: Note
    title_matches: int = 0
    text_matches: int = 0
    snippets: list[str] = field(default_factory=list)

    @property
    def total_matches(self) -> int:
        return self.title_matches + self.text_matches


@dataclass(slots=True)
class SearchOccurrence:
    """Exact search hit with the old RichTextBox SelectionStart semantics."""

    note: Note
    field: str
    start: int
    end: int
    snippet: str = ""

    @property
    def length(self) -> int:
        return max(0, self.end - self.start)

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.note.path_titles(),
            "title": self.note.title,
            "field": self.field,
            "start": self.start,
            "end": self.end,
            "length": self.length,
            "snippet": self.snippet,
        }


@dataclass(slots=True)
class NoteStats:
    notes: int
    leaves: int
    max_depth: int
    sticky_notes: int
    characters: int


@dataclass(slots=True)
class ReplaceReport:
    notes_changed: int = 0
    title_replacements: int = 0
    text_replacements: int = 0

    @property
    def total_replacements(self) -> int:
        return self.title_replacements + self.text_replacements


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

    def iter_subtree(self, start: Note | None = None) -> Iterable[Note]:
        yield from _iter_notes(start or self.root)

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

    def first_note_by_title(self, title: str, case_sensitive: bool = False) -> Note | None:
        cmp_title = title if case_sensitive else title.casefold()
        for note in self.iter_notes():
            value = note.title if case_sensitive else note.title.casefold()
            if value == cmp_title:
                return note
        return None

    def first_note_by_path(self, path: str, case_sensitive: bool = False, separator: str = "/") -> Note | None:
        """Return the first note matching a slash-separated title path.

        CLI commands historically selected by visible tree position.  The Python
        fallback cannot point at a TreeView row, so a path such as
        ``Root/Projekt/Todo`` gives callers a deterministic way to select a
        duplicated title.  If the root title is omitted, the path may also start
        at any descendant sequence.
        """
        parts = [part.strip() for part in (path or "").split(separator) if part.strip()]
        if not parts:
            return None

        def norm(value: str) -> str:
            return value if case_sensitive else value.casefold()

        wanted = [norm(part) for part in parts]
        for note in self.iter_notes():
            titles = [norm(title) for title in note.path_titles()]
            if titles == wanted or titles[-len(wanted) :] == wanted:
                return note
        return None

    def first_note_by_title_or_path(self, value: str, case_sensitive: bool = False) -> Note | None:
        note = self.first_note_by_title(value, case_sensitive=case_sensitive)
        if note is not None:
            return note
        return self.first_note_by_path(value, case_sensitive=case_sensitive)

    @property
    def selected_note(self) -> Note:
        note = self.note_by_id(self.selected_id)
        if note is not None:
            return note
        self.selected_id = self.root.note_id
        return self.root

    def select(self, note: Note | None) -> Note:
        if note is None:
            note = self.root
        self.selected_id = note.note_id
        self._expand_ancestors(note)
        return note

    def select_by_flat_index(self, index: int) -> Note | None:
        rows = self.flatten()
        if not 0 <= index < len(rows):
            return None
        return self.select(rows[index].note)

    def selected_flat_index(self) -> int:
        for i, row in enumerate(self.flatten()):
            if row.note.note_id == self.selected_id:
                return i
        return 0

    def add_child_to_selected(self) -> Note:
        parent = self.selected_note
        note = parent.add_child(Note("...", text_to_rtf("")))
        parent.expanded = True
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

    def insert_clone_after_selected(self, source: Note) -> Note:
        clone = source.clone_deep()
        selected = self.selected_note
        if selected.parent is None:
            selected.insert_child(0, clone)
            selected.expanded = True
        else:
            selected.insert_after(clone)
        self.selected_id = clone.note_id
        self.modified = True
        return clone

    def insert_clone_before_selected(self, source: Note) -> Note:
        clone = source.clone_deep()
        selected = self.selected_note
        if selected.parent is None:
            selected.insert_child(0, clone)
            selected.expanded = True
        else:
            selected.insert_before(clone)
        self.selected_id = clone.note_id
        self.modified = True
        return clone

    def duplicate_selected(self) -> Note | None:
        selected = self.selected_note
        if selected.parent is None:
            return None
        return self.insert_clone_after_selected(selected)

    def delete_selected(self) -> Note:
        selected = self.selected_note
        if selected.parent is None:
            selected.children.clear()
            selected.title = "start"
            selected.rtf = text_to_rtf("")
            selected.expanded = True
            selected.bg_color = None
            selected.fg_color = None
            selected.sticky = None
            self.modified = True
            return selected

        parent, old_index = selected.remove_from_parent()
        assert parent is not None and old_index is not None
        if parent.children:
            replacement = parent.children[min(old_index, len(parent.children) - 1)]
        else:
            replacement = parent
        self.selected_id = replacement.note_id
        self.modified = True
        return replacement

    def move_selected_up(self) -> bool:
        note = self.selected_note
        if note.parent is None:
            return False
        siblings = note.parent.children
        idx = siblings.index(note)
        if idx <= 0:
            return False
        siblings[idx - 1], siblings[idx] = siblings[idx], siblings[idx - 1]
        self.modified = True
        return True

    def move_selected_down(self) -> bool:
        note = self.selected_note
        if note.parent is None:
            return False
        siblings = note.parent.children
        idx = siblings.index(note)
        if idx >= len(siblings) - 1:
            return False
        siblings[idx + 1], siblings[idx] = siblings[idx], siblings[idx + 1]
        self.modified = True
        return True

    def indent_selected(self) -> bool:
        """Make the selected node the last child of its previous sibling."""
        note = self.selected_note
        if note.parent is None:
            return False
        siblings = note.parent.children
        idx = siblings.index(note)
        if idx <= 0:
            return False
        new_parent = siblings[idx - 1]
        siblings.pop(idx)
        new_parent.add_child(note)
        new_parent.expanded = True
        self.selected_id = note.note_id
        self.modified = True
        return True

    def outdent_selected(self) -> bool:
        """Move selected node after its parent."""
        note = self.selected_note
        parent = note.parent
        if parent is None or parent.parent is None:
            return False
        grand = parent.parent
        parent.children.remove(note)
        parent_index = grand.children.index(parent)
        note.parent = grand
        grand.children.insert(parent_index + 1, note)
        self.selected_id = note.note_id
        self.modified = True
        return True

    def move_selected_under(self, target: Note) -> bool:
        note = self.selected_note
        if note is self.root or target is note or note.is_ancestor_of(target):
            return False
        old_parent, _ = note.remove_from_parent()
        if old_parent is None:
            return False
        target.add_child(note)
        target.expanded = True
        self.selected_id = note.note_id
        self.modified = True
        return True

    def move_selected_relative_to(self, target: Note, *, where: str = "child") -> bool:
        """Move the selected note as child/before/after a target note.

        This mirrors the old TreeView cut/paste behavior while keeping invalid
        structures out: the root cannot be moved, a node cannot be moved into
        itself or one of its descendants, and there is no sibling position around
        the root node.
        """
        note = self.selected_note
        if where not in {"child", "before", "after"}:
            raise ValueError("where muss child, before oder after sein")
        if note is self.root or target is note or note.is_ancestor_of(target):
            return False
        if where in {"before", "after"} and target.parent is None:
            return False
        old_parent, _ = note.remove_from_parent()
        if old_parent is None:
            return False
        if where == "child":
            target.add_child(note)
            target.expanded = True
        elif where == "before":
            target.insert_before(note)
        else:
            target.insert_after(note)
        self.selected_id = note.note_id
        self.modified = True
        return True

    def copy_selected_relative_to(self, target: Note, *, where: str = "child") -> Note | None:
        """Clone the selected note as child/before/after a target note."""
        source = self.selected_note
        if where not in {"child", "before", "after"}:
            raise ValueError("where muss child, before oder after sein")
        if where in {"before", "after"} and target.parent is None:
            return None
        clone = source.clone_deep()
        if where == "child":
            target.add_child(clone)
            target.expanded = True
        elif where == "before":
            target.insert_before(clone)
        else:
            target.insert_after(clone)
        self.selected_id = clone.note_id
        self.modified = True
        return clone

    def toggle_selected_expanded(self) -> None:
        note = self.selected_note
        if note.children:
            note.expanded = not note.expanded
            self.modified = True

    def expand_all(self) -> None:
        for note in self.iter_notes():
            note.expanded = True
        self.modified = True

    def collapse_all(self, keep_root_open: bool = True) -> None:
        for note in self.iter_notes():
            note.expanded = False
        if keep_root_open:
            self.root.expanded = True
        self.modified = True

    def find_next(self, needle: str, *, case_sensitive: bool = False, whole_words: bool = False, start: Note | None = None) -> Note | None:
        matches = self.find_all(needle, case_sensitive=case_sensitive, whole_words=whole_words, start=start)
        if not matches:
            return None
        flat = [row.note for row in self.flatten(include_collapsed=True)]
        allowed_ids = {note.note_id for note in self.iter_subtree(start)} if start is not None else None
        if allowed_ids is not None:
            flat = [note for note in flat if note.note_id in allowed_ids]
        current_index = next((i for i, note in enumerate(flat) if note.note_id == self.selected_id), -1)
        hit_ids = {hit.note.note_id for hit in matches}
        ordered = flat[current_index + 1 :] + flat[: current_index + 1]
        for note in ordered:
            if note.note_id in hit_ids:
                self.select(note)
                return note
        return None

    def find_all(self, needle: str, *, case_sensitive: bool = False, whole_words: bool = False, start: Note | None = None) -> list[SearchHit]:
        matcher = _make_matcher(needle, case_sensitive=case_sensitive, whole_words=whole_words)
        if matcher is None:
            return []
        hits: list[SearchHit] = []
        for note in self.iter_subtree(start):
            title_match = matcher(note.title)
            text_match = matcher(note.text)
            if title_match or text_match:
                hits.append(SearchHit(note=note, title_match=title_match, text_match=text_match))
        return hits

    def find_detailed(
        self,
        needle: str,
        *,
        case_sensitive: bool = False,
        whole_words: bool = False,
        context: int = 40,
        max_snippets_per_note: int = 3,
        start: Note | None = None,
    ) -> list[SearchDetail]:
        """Return counted search hits with short snippets.

        The old WinForms search jumped through notes and showed a separate result
        window. This pure-Python form keeps the same idea but is usable from the
        CLI, tests and Slint status line. The optional ``start`` argument mirrors
        the old "aktuelle Notiz oder alle Notizen" search scope.
        """
        pattern = _make_pattern(needle, case_sensitive=case_sensitive, whole_words=whole_words)
        if pattern is None:
            return []
        details: list[SearchDetail] = []
        for note in self.iter_subtree(start):
            title_spans = [m.span() for m in pattern.finditer(note.title or "")]
            text = note.text or ""
            text_spans = [m.span() for m in pattern.finditer(text)]
            if not title_spans and not text_spans:
                continue
            snippets: list[str] = []
            for match_start, match_end in title_spans[:max_snippets_per_note]:
                snippets.append("Titel: " + _make_snippet(note.title or "", match_start, match_end, context=context))
            remaining = max(0, max_snippets_per_note - len(snippets))
            for match_start, match_end in text_spans[:remaining]:
                snippets.append("Text: " + _make_snippet(text, match_start, match_end, context=context))
            details.append(SearchDetail(note=note, title_matches=len(title_spans), text_matches=len(text_spans), snippets=snippets))
        return details

    def find_occurrences(
        self,
        needle: str,
        *,
        case_sensitive: bool = False,
        whole_words: bool = False,
        context: int = 40,
        start: Note | None = None,
        fields: Iterable[str] = ("title", "text"),
        limit: int | None = None,
    ) -> list[SearchOccurrence]:
        """Return every title/text hit with a visible plain-text position.

        The old ``suche.vb`` stored search results as ``suchergebnisse`` with a
        ``TreeNode`` and a RichTextBox ``SelectionStart``.  Slint does not expose
        the same RichTextBox object, so the port keeps the important part: exact
        positions in the visible title/body text for jumping, range styling and
        JSON result exports.
        """
        pattern = _make_pattern(needle, case_sensitive=case_sensitive, whole_words=whole_words)
        if pattern is None:
            return []
        wanted = {field.strip().lower() for field in fields if field}
        if not wanted:
            wanted = {"title", "text"}
        max_hits = None if limit is None or limit < 1 else int(limit)
        hits: list[SearchOccurrence] = []
        for note in self.iter_subtree(start):
            if "title" in wanted:
                title = note.title or ""
                for match in pattern.finditer(title):
                    hits.append(SearchOccurrence(note, "title", match.start(), match.end(), _make_snippet(title, match.start(), match.end(), context=context)))
                    if max_hits is not None and len(hits) >= max_hits:
                        return hits
            if "text" in wanted or "body" in wanted or "inhalt" in wanted:
                text = note.text or ""
                for match in pattern.finditer(text):
                    hits.append(SearchOccurrence(note, "text", match.start(), match.end(), _make_snippet(text, match.start(), match.end(), context=context)))
                    if max_hits is not None and len(hits) >= max_hits:
                        return hits
        return hits

    def replace_all(
        self,
        needle: str,
        replacement: str,
        *,
        case_sensitive: bool = False,
        whole_words: bool = False,
        start: Note | None = None,
        include_titles: bool = True,
        include_text: bool = True,
    ) -> ReplaceReport:
        """Replace text in titles and/or note bodies.

        Body replacement intentionally rewrites the affected body as plain RTF.
        This is the same compromise as the Slint text editor: it is portable and
        deterministic, but it cannot preserve arbitrary RichTextBox formatting
        around changed ranges.
        """
        pattern = _make_pattern(needle, case_sensitive=case_sensitive, whole_words=whole_words)
        report = ReplaceReport()
        if pattern is None:
            return report
        replacement = replacement or ""
        for note in self.iter_subtree(start):
            changed = False
            if include_titles:
                new_title, count = pattern.subn(lambda _match: replacement, note.title or "")
                if count:
                    note.title = new_title or "..."
                    report.title_replacements += count
                    changed = True
            if include_text:
                body = note.text or ""
                new_body, count = pattern.subn(lambda _match: replacement, body)
                if count:
                    note.set_text(new_body)
                    report.text_replacements += count
                    changed = True
            if changed:
                report.notes_changed += 1
        if report.total_replacements:
            self.modified = True
        return report

    def stats(self) -> NoteStats:
        max_depth = 0
        notes = leaves = sticky_notes = characters = 0

        def rec(note: Note, depth: int) -> None:
            nonlocal max_depth, notes, leaves, sticky_notes, characters
            notes += 1
            max_depth = max(max_depth, depth)
            if not note.children:
                leaves += 1
            if note.sticky is not None:
                sticky_notes += 1
            characters += len(note.text)
            for child in note.children:
                rec(child, depth + 1)

        rec(self.root, 0)
        return NoteStats(notes=notes, leaves=leaves, max_depth=max_depth, sticky_notes=sticky_notes, characters=characters)

    def _expand_ancestors(self, note: Note) -> None:
        parent = note.parent
        while parent is not None:
            parent.expanded = True
            parent = parent.parent

    def walk_with_level(self, visit: Callable[[Note, int], None], *, start: Note | None = None) -> None:
        def rec(note: Note, level: int) -> None:
            visit(note, level)
            for child in note.children:
                rec(child, level + 1)

        rec(start or self.root, 0)


def _iter_notes(root: Note) -> Iterable[Note]:
    yield root
    for child in root.children:
        yield from _iter_notes(child)


def _make_matcher(needle: str, *, case_sensitive: bool, whole_words: bool) -> Callable[[str], bool] | None:
    pattern = _make_pattern(needle, case_sensitive=case_sensitive, whole_words=whole_words)
    if pattern is None:
        return None
    return lambda value: bool(pattern.search(value or ""))


def _make_pattern(needle: str, *, case_sensitive: bool, whole_words: bool) -> re.Pattern[str] | None:
    needle = needle or ""
    if not needle.strip():
        return None
    flags = 0 if case_sensitive else re.IGNORECASE
    body = re.escape(needle)
    if whole_words:
        body = rf"(?<!\w){body}(?!\w)"
    return re.compile(body, flags)


def _make_snippet(value: str, start: int, end: int, *, context: int) -> str:
    context = max(0, int(context))
    left = max(0, start - context)
    right = min(len(value), end + context)
    snippet = value[left:right].replace("\r\n", "\n").replace("\r", "\n")
    snippet = " ".join(part for part in snippet.split())
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < len(value) else ""
    return prefix + snippet + suffix


def argb_to_hex(value: int | None) -> str:
    if value is None:
        return ""
    unsigned = value & 0xFFFFFFFF
    return f"#{unsigned:08X}"


def parse_int_or_hex(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text.startswith("#"):
        text = text[1:]
        if len(text) == 6:
            text = "FF" + text
        return int(text, 16)
    if text.lower().startswith("0x"):
        return int(text, 16)
    return int(text)
