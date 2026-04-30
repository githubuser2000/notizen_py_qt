from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Iterable

from .legacy_colors import argb_to_signed
from .model import Note, NoteDocument
from .rtf import is_rtf, text_to_rtf


@dataclass(slots=True)
class RepairReport:
    """Summary of compatibility normalization applied to a document."""

    empty_titles_fixed: int = 0
    plain_text_converted: int = 0
    transparent_colors_cleared: int = 0
    sticky_sizes_fixed: int = 0
    sticky_opacity_fixed: int = 0
    argb_normalized: int = 0
    notes_touched: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return (
            self.empty_titles_fixed
            + self.plain_text_converted
            + self.transparent_colors_cleared
            + self.sticky_sizes_fixed
            + self.sticky_opacity_fixed
            + self.argb_normalized
        )

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["total_changes"] = self.total_changes
        return payload

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, ensure_ascii=False)


def repair_document(
    document: NoteDocument,
    *,
    fix_empty_titles: bool = True,
    convert_plain_text: bool = True,
    clear_transparent_colors: bool = True,
    fix_sticky: bool = True,
    normalize_argb: bool = True,
) -> RepairReport:
    """Normalize old or malformed note metadata before saving.

    The original reader tolerated several odd XML states.  This function keeps a
    deterministic Python repair path for migrations: titles are made visible,
    plain bodies can be wrapped as RTF, fully transparent WinForms colors are
    removed, sticky geometry is clamped to usable values, and ARGB integers are
    normalized to signed WinForms-compatible 32-bit values.
    """

    report = RepairReport()
    touched: set[int] = set()
    for note in document.iter_notes():
        changed = False
        if fix_empty_titles and not (note.title or "").strip():
            note.title = "..."
            report.empty_titles_fixed += 1
            changed = True
        if convert_plain_text and note.rtf and not is_rtf(note.rtf):
            note.rtf = text_to_rtf(note.rtf)
            report.plain_text_converted += 1
            changed = True
        if clear_transparent_colors:
            if _is_transparent(note.bg_color):
                note.bg_color = None
                report.transparent_colors_cleared += 1
                changed = True
            if _is_transparent(note.fg_color):
                note.fg_color = None
                report.transparent_colors_cleared += 1
                changed = True
        if normalize_argb:
            for attr in ("bg_color", "fg_color"):
                value = getattr(note, attr)
                if value is not None:
                    normalized = argb_to_signed(value)
                    if normalized != value:
                        setattr(note, attr, normalized)
                        report.argb_normalized += 1
                        changed = True
        sticky = note.sticky
        if sticky is not None:
            if fix_sticky:
                if sticky.width is not None and sticky.width < 80:
                    sticky.width = 80
                    report.sticky_sizes_fixed += 1
                    changed = True
                if sticky.height is not None and sticky.height < 60:
                    sticky.height = 60
                    report.sticky_sizes_fixed += 1
                    changed = True
                if sticky.opacity is not None:
                    new_opacity = min(1.0, max(0.05, sticky.opacity))
                    if new_opacity != sticky.opacity:
                        sticky.opacity = new_opacity
                        report.sticky_opacity_fixed += 1
                        changed = True
            if clear_transparent_colors and _is_transparent(sticky.argb):
                sticky.argb = None
                report.transparent_colors_cleared += 1
                changed = True
            if normalize_argb and sticky.argb is not None:
                normalized = argb_to_signed(sticky.argb)
                if normalized != sticky.argb:
                    sticky.argb = normalized
                    report.argb_normalized += 1
                    changed = True
        if changed:
            touched.add(note.note_id)
    report.notes_touched = len(touched)
    if document.root.parent is not None:
        document.root.parent = None
        report.warnings.append("Root-Parent-Zeiger wurde auf None gesetzt.")
    if report.total_changes:
        document.modified = True
    return report


def format_repair_report(report: RepairReport) -> str:
    lines = [
        f"Änderungen: {report.total_changes}",
        f"Betroffene Notizen: {report.notes_touched}",
        f"Leere Titel repariert: {report.empty_titles_fixed}",
        f"Plain-Text nach RTF gewandelt: {report.plain_text_converted}",
        f"Transparente Farben entfernt: {report.transparent_colors_cleared}",
        f"Sticky-Größen repariert: {report.sticky_sizes_fixed}",
        f"Sticky-Deckkraft repariert: {report.sticky_opacity_fixed}",
        f"ARGB normalisiert: {report.argb_normalized}",
    ]
    for warning in report.warnings:
        lines.append("Warnung: " + warning)
    return "\n".join(lines)


def _is_transparent(value: int | None) -> bool:
    if value is None:
        return False
    return ((int(value) & 0xFFFFFFFF) >> 24) == 0
