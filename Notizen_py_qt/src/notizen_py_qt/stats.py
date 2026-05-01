from __future__ import annotations

from dataclasses import dataclass
import re

from .models import NoteNode
from .rtf_utils import rtf_to_plain_text

_WORD_RE = re.compile(r"\w+", re.UNICODE)
_PICT_RE = re.compile(r"\\pict\b")


@dataclass(slots=True)
class TreeStats:
    """Aggregated counters for a Notizen.NET note tree."""

    nodes: int = 0
    leaves: int = 0
    max_depth: int = 0
    desktop_notes: int = 0
    characters: int = 0
    characters_no_space: int = 0
    words: int = 0
    lines: int = 0
    images: int = 0
    rtf_bytes: int = 0

    def as_legacy_lines(self) -> list[tuple[str, str]]:
        """Return German label/value rows suitable for the old stats dialog."""
        return [
            ("Knoten", str(self.nodes)),
            ("Blätter", str(self.leaves)),
            ("Maximale Tiefe", str(self.max_depth)),
            ("Desktop-Notizen", str(self.desktop_notes)),
            ("Zeichen", str(self.characters)),
            ("Zeichen ohne Leerraum", str(self.characters_no_space)),
            ("Wörter", str(self.words)),
            ("Zeilen", str(self.lines)),
            ("Bilder", str(self.images)),
            ("RTF-Bytes", str(self.rtf_bytes)),
        ]


def _count_text_lines(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + 1


def collect_tree_stats(root: NoteNode | None) -> TreeStats:
    """Collect practical statistics for a full tree or a subtree.

    The legacy program exposed several small status/readout fields and users
    often relied on them before exporting.  This pure helper keeps the numbers
    deterministic and independent of Qt.
    """
    stats = TreeStats()
    if root is None:
        return stats

    def visit(node: NoteNode, depth: int) -> None:
        stats.nodes += 1
        stats.max_depth = max(stats.max_depth, depth)
        if not node.children:
            stats.leaves += 1
        if node.desktop_note is not None:
            stats.desktop_notes += 1
        rtf = node.rtf or ""
        stats.rtf_bytes += len(rtf.encode("utf-8", errors="replace"))
        stats.images += len(_PICT_RE.findall(rtf))
        text = rtf_to_plain_text(rtf)
        stats.characters += len(text)
        stats.characters_no_space += sum(1 for ch in text if not ch.isspace())
        stats.words += len(_WORD_RE.findall(text))
        stats.lines += _count_text_lines(text)
        for child in node.children:
            visit(child, depth + 1)

    visit(root, 1)
    return stats
