from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import NoteNode
from .rtf_utils import rtf_to_plain_text


LEGACY_WHOLE_WORD_SEPARATORS = frozenset({" ", "\r", "\n"})


@dataclass(slots=True)
class SearchResult:
    node: NoteNode
    start: int
    length: int


def _same_text(left: str, right: str, *, case_sensitive: bool) -> bool:
    if case_sensitive:
        return left == right
    return left.casefold() == right.casefold()


def _legacy_whole_word_matches(text: str, term: str, *, case_sensitive: bool = False) -> list[tuple[int, int]]:
    """Return matches using the old ``suche.vb`` whole-word rule.

    Notizen.NET did not use a regular-expression word boundary.  When the
    ``wholewords`` checkbox was active, ``suche.vb`` collected characters until
    it saw a plain space or CR/LF.  Punctuation and tabs therefore remained part
    of the token.  This helper keeps that quirk intentionally, so old searches
    behave the same in the Python/Qt port.
    """

    if not term:
        return []
    results: list[tuple[int, int]] = []
    token_start: int | None = None
    token_chars: list[str] = []

    def flush(end_index: int) -> None:
        nonlocal token_start, token_chars
        if token_start is not None:
            token = "".join(token_chars)
            if _same_text(token, term, case_sensitive=case_sensitive):
                results.append((token_start, len(term)))
        token_start = None
        token_chars = []

    for index, char in enumerate(text):
        if char in LEGACY_WHOLE_WORD_SEPARATORS:
            flush(index)
        else:
            if token_start is None:
                token_start = index
            token_chars.append(char)
    flush(len(text))
    return results


def find_in_text(text: str, term: str, *, whole_words: bool = False, case_sensitive: bool = False) -> list[tuple[int, int]]:
    if not term:
        return []
    if whole_words:
        return _legacy_whole_word_matches(text, term, case_sensitive=case_sensitive)
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
