from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .models import NoteNode
from .rtf_utils import rtf_to_plain_text


@dataclass(slots=True)
class SearchResult:
    node: NoteNode
    start: int
    length: int


def _whole_word_pattern(term: str, case_sensitive: bool) -> re.Pattern[str]:
    flags = 0 if case_sensitive else re.IGNORECASE
    # The legacy implementation treats spaces/newlines as word separators. This
    # regex is slightly broader and behaves well for punctuation too.
    return re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", flags)


def find_in_text(text: str, term: str, *, whole_words: bool = False, case_sensitive: bool = False) -> list[tuple[int, int]]:
    if not term:
        return []
    if whole_words:
        return [(m.start(), len(m.group(0))) for m in _whole_word_pattern(term, case_sensitive).finditer(text)]
    haystack = text if case_sensitive else text.casefold()
    needle = term if case_sensitive else term.casefold()
    results: list[tuple[int, int]] = []
    pos = 0
    while True:
        found = haystack.find(needle, pos)
        if found < 0:
            break
        results.append((found, len(term)))
        pos = found + max(1, len(term))
    return results


def search_nodes(
    nodes: Iterable[NoteNode],
    term: str,
    *,
    whole_words: bool = False,
    case_sensitive: bool = False,
) -> list[SearchResult]:
    results: list[SearchResult] = []
    for node in nodes:
        text = rtf_to_plain_text(node.rtf)
        for start, length in find_in_text(text, term, whole_words=whole_words, case_sensitive=case_sensitive):
            results.append(SearchResult(node=node, start=start, length=length))
    return results
