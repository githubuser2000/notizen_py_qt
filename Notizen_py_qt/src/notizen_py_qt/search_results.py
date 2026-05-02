from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import NoteNode
from .rtf_utils import rtf_to_plain_text
from .search_logic import SearchResult


@dataclass(slots=True)
class SearchHitView:
    """Display-ready view of a legacy search result.

    The old WinForms helper ``suchergebnisse.vb`` stored the target TreeNode and
    SelectionStart.  The Qt dialog keeps those raw positions in ``SearchResult``
    and adds a node path plus snippet for the visible result list.
    """

    result: SearchResult
    node_path: str
    snippet: str
    label: str


def node_path(node: NoteNode, *, separator: str = " / ") -> str:
    parts: list[str] = []
    current: NoteNode | None = node
    while current is not None:
        title = current.title.strip() or "..."
        parts.append(title)
        current = current.parent
    return separator.join(reversed(parts))


def legacy_search_snippet(text: str, start: int, length: int, *, radius: int = 36) -> str:
    """Create a compact one-line snippet around a selection start.

    ``SelectionStart`` comes from the plain RichTextBox text in the legacy app.
    The snippet keeps the selected text visible while replacing hard line breaks
    with spaces, which makes list entries readable in Qt.
    """

    safe_start = max(0, min(start, len(text)))
    safe_end = max(safe_start, min(safe_start + max(0, length), len(text)))
    left_start = max(0, safe_start - max(0, radius))
    right_end = min(len(text), safe_end + max(0, radius))
    raw = text[left_start:right_end]
    compact = " ".join(raw.replace("\r", "\n").replace("\t", " ").split())
    if not compact:
        compact = text[safe_start:safe_end] or "..."
    if left_start > 0:
        compact = "…" + compact
    if right_end < len(text):
        compact += "…"
    return compact


def legacy_search_result_label(result: SearchResult, *, context_chars: int = 36) -> str:
    text = rtf_to_plain_text(result.node.rtf)
    path = node_path(result.node)
    snippet = legacy_search_snippet(text, result.start, result.length, radius=context_chars)
    # RichTextBox SelectionStart is zero-based internally, but the visible list
    # should be human-friendly.
    return f"{path} · {result.start + 1}: {snippet}"


def build_search_hit_views(results: Iterable[SearchResult], *, context_chars: int = 36) -> list[SearchHitView]:
    views: list[SearchHitView] = []
    for result in results:
        text = rtf_to_plain_text(result.node.rtf)
        path = node_path(result.node)
        snippet = legacy_search_snippet(text, result.start, result.length, radius=context_chars)
        label = f"{path} · {result.start + 1}: {snippet}"
        views.append(SearchHitView(result=result, node_path=path, snippet=snippet, label=label))
    return views
