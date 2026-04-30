from __future__ import annotations

"""Compatibility diagnostics for migrated Notizen.NET files."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
import gzip
import json
import xml.etree.ElementTree as ET

from .des_compat import is_blank_password
from .model import Note, NoteDocument, argb_to_hex
from .rtf import extract_pictures, is_rtf
from .storage import NotizenFileError, load_document_from_bytes, read_raw_xml


@dataclass(slots=True)
class CompatibilityIssue:
    severity: str
    code: str
    path: list[str]
    message: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class CompatibilityReport:
    source: str | None
    format: str
    encrypted: bool | None
    notes: int
    leaves: int
    max_depth: int
    characters: int
    rtf_notes: int
    plain_or_empty_notes: int
    picture_count: int
    sticky_notes: int
    visible_sticky_notes: int
    colored_notes: int
    collapsed_notes: int
    issues: list[CompatibilityIssue] = field(default_factory=list)

    @property
    def warnings(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def errors(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def format_name(self) -> str:
        """Backward-compatible alias for callers that say ``format_name``."""
        return self.format

    @property
    def summary(self) -> dict[str, int]:
        return {
            "notes": self.notes,
            "leaves": self.leaves,
            "max_depth": self.max_depth,
            "characters": self.characters,
            "rtf_notes": self.rtf_notes,
            "plain_or_empty_notes": self.plain_or_empty_notes,
            "picture_count": self.picture_count,
            "sticky_notes": self.sticky_notes,
            "visible_sticky_notes": self.visible_sticky_notes,
            "colored_notes": self.colored_notes,
            "collapsed_notes": self.collapsed_notes,
        }

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["format_name"] = self.format
        payload["summary"] = self.summary
        payload["warnings"] = self.warnings
        payload["errors"] = self.errors
        return payload


def analyze_document(document: NoteDocument, *, source: str | None = None, encrypted: bool | None = None, format_name: str = "notizen-alx2") -> CompatibilityReport:
    stats = document.stats()
    rtf_notes = plain_notes = picture_count = visible_sticky = colored = collapsed = 0
    issues: list[CompatibilityIssue] = []
    for note in document.iter_notes():
        path = note.path_titles()
        if is_rtf(note.rtf):
            rtf_notes += 1
        else:
            plain_notes += 1
            if note.rtf:
                issues.append(CompatibilityIssue("warning", "plain-body", path, "Notizinhalt ist kein RTF; der Port kann ihn als Text retten."))
        pictures = extract_pictures(note.rtf)
        picture_count += len(pictures)
        if not (note.title or "").strip():
            issues.append(CompatibilityIssue("warning", "empty-title", path, "Leerer Titel wird im alten Baum schwer auswählbar."))
        if note.sticky is not None:
            if note.sticky.visible:
                visible_sticky += 1
            _check_sticky(note, issues)
        if note.bg_color not in (None, 0) or note.fg_color not in (None, 0):
            colored += 1
            _check_color(note.bg_color, "bgcolor", path, issues)
            _check_color(note.fg_color, "fgcolor", path, issues)
        if not note.expanded:
            collapsed += 1
    return CompatibilityReport(
        source=source or document.path,
        format=format_name,
        encrypted=encrypted,
        notes=stats.notes,
        leaves=stats.leaves,
        max_depth=stats.max_depth,
        characters=stats.characters,
        rtf_notes=rtf_notes,
        plain_or_empty_notes=plain_notes,
        picture_count=picture_count,
        sticky_notes=stats.sticky_notes,
        visible_sticky_notes=visible_sticky,
        colored_notes=colored,
        collapsed_notes=collapsed,
        issues=issues,
    )


def analyze_file(path: str | Path, *, password: str | None = None) -> CompatibilityReport:
    target = Path(path)
    raw = target.read_bytes()
    encrypted = _looks_encrypted(raw, password)
    fmt = _detect_format(raw, password=password)
    doc = load_document_from_bytes(raw, source=str(target), password=password)
    return analyze_document(doc, source=str(target), encrypted=encrypted, format_name=fmt)


def format_report(report: CompatibilityReport) -> str:
    lines = [
        f"Quelle: {report.source or '-'}",
        f"Format: {report.format}",
        f"Verschlüsselt: {_tri(report.encrypted)}",
        f"Notizen: {report.notes} ({report.leaves} Blätter, Tiefe {report.max_depth})",
        f"Zeichen: {report.characters}",
        f"RTF-Notizen: {report.rtf_notes}; Plain/leer: {report.plain_or_empty_notes}; Bilder: {report.picture_count}",
        f"Sticky: {report.sticky_notes} ({report.visible_sticky_notes} sichtbar); Farben: {report.colored_notes}; zugeklappt: {report.collapsed_notes}",
        f"Hinweise: {report.warnings}; Fehler: {report.errors}",
    ]
    if report.issues:
        lines.append("Probleme/Hinweise:")
        for issue in report.issues:
            path = " / ".join(issue.path) if issue.path else "-"
            lines.append(f"- {issue.severity}: {issue.code}: {path}: {issue.message}")
    return "\n".join(lines)


def report_json(report: CompatibilityReport) -> str:
    return json.dumps(report.as_dict(), indent=2, ensure_ascii=False)


def _check_color(value: int | None, attr: str, path: list[str], issues: list[CompatibilityIssue]) -> None:
    if value in (None, 0):
        return
    unsigned = int(value) & 0xFFFFFFFF
    alpha = (unsigned >> 24) & 0xFF
    if alpha == 0:
        issues.append(CompatibilityIssue("warning", f"transparent-{attr}", path, f"{attr} hat Alpha 0 ({argb_to_hex(value)})."))


def _check_sticky(note: Note, issues: list[CompatibilityIssue]) -> None:
    sticky = note.sticky
    if sticky is None:
        return
    path = note.path_titles()
    if sticky.width is not None and sticky.width <= 0:
        issues.append(CompatibilityIssue("warning", "sticky-width", path, "Sticky-Breite ist kleiner/gleich 0."))
    if sticky.height is not None and sticky.height <= 0:
        issues.append(CompatibilityIssue("warning", "sticky-height", path, "Sticky-Höhe ist kleiner/gleich 0."))
    if sticky.opacity is not None and not (0.05 <= sticky.opacity <= 1.0):
        issues.append(CompatibilityIssue("warning", "sticky-opacity", path, f"Sticky-Deckkraft liegt außerhalb 0.05..1.0: {sticky.opacity}."))


def _looks_encrypted(raw: bytes, password: str | None) -> bool | None:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff") or raw.lstrip()[:1] == b"<":
        return False
    try:
        gzip.decompress(raw)
        return False if is_blank_password(password) else None
    except Exception:
        return True


def _detect_format(raw: bytes, *, password: str | None) -> str:
    try:
        xml_text = read_raw_xml_bytes(raw, password=password)
        root = ET.fromstring(xml_text)
        return root.tag
    except Exception:
        return "unbekannt"


def read_raw_xml_bytes(raw: bytes, *, password: str | None = None) -> str:
    # ``read_raw_xml`` is path based; for diagnostics we need the same effect on a
    # bytes object without creating temp files.  Reuse the public loader and writer
    # semantics by importing the private helpers only here, with a narrow fallback.
    from .storage import _decode_payload, _decode_xml  # type: ignore[attr-defined]

    xml_bytes, _ = _decode_payload(raw, password)
    return _decode_xml(xml_bytes)


def _tri(value: bool | None) -> str:
    if value is True:
        return "ja"
    if value is False:
        return "nein"
    return "unbekannt"
