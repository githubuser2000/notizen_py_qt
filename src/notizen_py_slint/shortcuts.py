from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class Shortcut:
    """Keyboard shortcut ported from Notizen.NET's tastendruck handlers."""

    keys: str
    action: str
    scope: str
    legacy_source: str
    notes: str = ""

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


# The original WinForms application routed key handling through Notizen.tastendruck
# from the main form, the tree and selected editor paths.  Slint does not expose
# the same global accelerator API in this portable port, so this table documents
# the preserved intent and gives the CLI/tests a stable compatibility manifest.
SHORTCUTS: tuple[Shortcut, ...] = (
    Shortcut("Ctrl+Space", "Wecker öffnen", "global", "Notizen.tastendruck", "im Port über alarm-* CLI abgebildet"),
    Shortcut("Ctrl+S", "Datei speichern", "global", "Notizen.tastendruck"),
    Shortcut("Ctrl+O", "Datei öffnen", "global", "Notizen.tastendruck"),
    Shortcut("Ctrl+N", "Neue Datei", "global", "Notizen.tastendruck"),
    Shortcut("Ctrl+Q", "Schließen/Beenden", "global", "Notizen.tastendruck"),
    Shortcut("Ctrl+C", "Knoten kopieren", "Baum", "Notizen.tastendruck"),
    Shortcut("Ctrl+V", "Knoten einfügen", "Baum", "Notizen.tastendruck"),
    Shortcut("Ctrl+X", "Knoten ausschneiden", "Baum", "Notizen.tastendruck"),
    Shortcut("Ctrl+U", "Knoten umbenennen", "Baum", "Notizen.tastendruck"),
    Shortcut("Ctrl+F", "Suche öffnen", "global", "Notizen.tastendruck"),
    Shortcut("Ctrl++", "Schrift vergrößern", "Editor", "Notizen.tastendruck"),
    Shortcut("Ctrl+-", "Schrift verkleinern", "Editor", "Notizen.tastendruck"),
    Shortcut("Shift+Insert", "Knoten einfügen", "Baum", "Notizen.tastendruck"),
    Shortcut("Shift+Delete", "Knoten ausschneiden", "Baum", "Notizen.tastendruck"),
    Shortcut("Delete", "Knoten löschen", "Baum", "Notizen.tastendruck"),
    Shortcut("Insert", "Neuen Unterknoten anlegen", "Baum", "Notizen.tastendruck"),
    Shortcut("Enter", "Neuen Nachbarknoten anlegen", "Baum", "Notizen.tastendruck"),
)


def shortcut_manifest() -> list[dict[str, str]]:
    return [shortcut.as_dict() for shortcut in SHORTCUTS]


def format_shortcuts() -> str:
    width = max(len(shortcut.keys) for shortcut in SHORTCUTS)
    lines = ["Alte Notizen.NET-Tastenkürzel:"]
    for shortcut in SHORTCUTS:
        scope = f" [{shortcut.scope}]" if shortcut.scope else ""
        notes = f" — {shortcut.notes}" if shortcut.notes else ""
        lines.append(f"  {shortcut.keys.ljust(width)}  {shortcut.action}{scope}{notes}")
    return "\n".join(lines)
