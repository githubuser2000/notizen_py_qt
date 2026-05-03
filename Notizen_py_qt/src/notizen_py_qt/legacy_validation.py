from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from .alx_io import dump_alx_bytes, load_alx_bytes
from .models import DesktopNoteState, NoteDocument, NoteNode
from .rtf_utils import RtfImage, rtf_to_content_parts, rtf_to_plain_text


@dataclass(frozen=True, slots=True)
class LegacyAlxSummary:
    """Privacy-light summary of one legacy ALX document.

    The summary intentionally avoids storing note titles or note text.  It is
    meant for regression checks with real Notizen.NET files where raw personal
    notes should not be committed to tests or pasted into bug reports.
    """

    node_count: int
    max_depth: int
    desktop_note_count: int
    visible_desktop_note_count: int
    rtf_character_count: int
    plain_text_character_count: int
    embedded_image_count: int
    tree_shape_hash: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class LegacyAlxRoundtripResult:
    """Result of load → dump → load validation for a legacy ALX payload."""

    ok: bool
    before: LegacyAlxSummary
    after: LegacyAlxSummary
    differences: tuple[str, ...] = ()


def _node_depths(root: NoteNode) -> Iterable[tuple[NoteNode, int, tuple[int, ...]]]:
    def visit(node: NoteNode, depth: int, indexes: tuple[int, ...]) -> Iterable[tuple[NoteNode, int, tuple[int, ...]]]:
        yield node, depth, indexes
        for index, child in enumerate(node.children):
            yield from visit(child, depth + 1, indexes + (index,))

    yield from visit(root, 0, ())


def _desktop_signature(state: DesktopNoteState | None) -> str:
    if state is None:
        return "-"
    return "|".join(
        [
            "1" if state.visible else "0",
            str(state.x),
            str(state.y),
            str(state.width),
            str(state.height),
            f"{state.opacity:.4f}",
            "" if state.argb is None else str(state.argb),
            "s" if state.legacy_sparse else "n",
            ",".join(sorted(state.legacy_attr_names)),
        ]
    )


def summarize_document(document: NoteDocument) -> LegacyAlxSummary:
    """Return a stable, title/text-free ALX compatibility summary."""

    root = document.ensure_root()
    shape_hasher = sha256()
    content_hasher = sha256()
    node_count = 0
    max_depth = 0
    desktop_count = 0
    visible_desktop_count = 0
    rtf_chars = 0
    plain_chars = 0
    image_count = 0

    for node, depth, indexes in _node_depths(root):
        node_count += 1
        max_depth = max(max_depth, depth)
        if node.desktop_note is not None:
            desktop_count += 1
            if node.desktop_note.visible:
                visible_desktop_count += 1
        rtf = node.rtf or ""
        plain = rtf_to_plain_text(rtf)
        images = sum(1 for part in rtf_to_content_parts(rtf) if isinstance(part, RtfImage))
        rtf_chars += len(rtf)
        plain_chars += len(plain)
        image_count += images
        # Shape hash includes title/content digests but not the raw strings.
        shape_hasher.update(repr(indexes).encode("utf-8"))
        shape_hasher.update(str(len(node.children)).encode("ascii"))
        shape_hasher.update(sha256(node.title.encode("utf-8", errors="surrogatepass")).digest())
        shape_hasher.update(str(node.expanded).encode("ascii"))
        shape_hasher.update(str(node.bg_argb).encode("ascii"))
        shape_hasher.update(str(node.fg_argb).encode("ascii"))
        shape_hasher.update(_desktop_signature(node.desktop_note).encode("utf-8"))
        for key, value in sorted(node.extra_attrs.items()):
            shape_hasher.update(key.encode("utf-8", errors="surrogatepass"))
            shape_hasher.update(value.encode("utf-8", errors="surrogatepass"))
        content_hasher.update(sha256(rtf.encode("utf-8", errors="surrogatepass")).digest())
        content_hasher.update(sha256(plain.encode("utf-8", errors="surrogatepass")).digest())

    return LegacyAlxSummary(
        node_count=node_count,
        max_depth=max_depth,
        desktop_note_count=desktop_count,
        visible_desktop_note_count=visible_desktop_count,
        rtf_character_count=rtf_chars,
        plain_text_character_count=plain_chars,
        embedded_image_count=image_count,
        tree_shape_hash=shape_hasher.hexdigest(),
        content_hash=content_hasher.hexdigest(),
    )


def summarize_alx_bytes(data: bytes, password: str | None = None) -> LegacyAlxSummary:
    return summarize_document(load_alx_bytes(data, password=password))


def summarize_alx_file(path: str | Path, password: str | None = None) -> LegacyAlxSummary:
    return summarize_alx_bytes(Path(path).read_bytes(), password=password)


def validate_alx_roundtrip_bytes(data: bytes, password: str | None = None) -> LegacyAlxRoundtripResult:
    """Check whether an ALX payload keeps its structural summary after saving."""

    document = load_alx_bytes(data, password=password)
    before = summarize_document(document)
    roundtripped = load_alx_bytes(dump_alx_bytes(document, password=password), password=password)
    after = summarize_document(roundtripped)
    differences: list[str] = []
    for field in before.__dataclass_fields__:  # type: ignore[attr-defined]
        old = getattr(before, field)
        new = getattr(after, field)
        if old != new:
            differences.append(f"{field}: {old!r} -> {new!r}")
    return LegacyAlxRoundtripResult(ok=not differences, before=before, after=after, differences=tuple(differences))


def validate_alx_roundtrip_file(path: str | Path, password: str | None = None) -> LegacyAlxRoundtripResult:
    return validate_alx_roundtrip_bytes(Path(path).read_bytes(), password=password)
