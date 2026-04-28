from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Iterable

from .legacy_sticky import legacy_opacity_choices
from .translations import normalize_language, translate


@dataclass(slots=True, frozen=True)
class LegacyContextAction:
    """One user-visible action from the old WinForms context menus."""

    menu: str
    index: int
    key: str | None
    fallback: str
    action: str
    source: str
    ported_to: str

    def label(self, language: str = "de") -> str:
        return translate(self.key, language) if self.key else self.fallback

    def as_dict(self, language: str = "de") -> dict[str, object]:
        payload = asdict(self)
        payload["label"] = self.label(language)
        return payload


# From kontext_inhalt.vb: RichTextBox context menu.
CONTENT_CONTEXT: tuple[LegacyContextAction, ...] = (
    LegacyContextAction("content", 0, "kontext1", "Kopieren", "copy selection", "kontext_inhalt.vb", "GUI editor / system clipboard"),
    LegacyContextAction("content", 1, "kontext2", "Ausschneiden", "cut selection", "kontext_inhalt.vb", "delete-range + clipboard"),
    LegacyContextAction("content", 2, "kontext3", "Einfügen", "paste selection", "kontext_inhalt.vb", "insert-text/import-text/import-rtf"),
    LegacyContextAction("content", 3, "kontext6", "Bild einfügen", "insert image", "kontext_inhalt.vb", "insert-image / Bilder"),
    LegacyContextAction("content", 4, "kontext7", "Datum einfügen", "insert date", "kontext_inhalt.vb", "insert-text --date / Datum+"),
    LegacyContextAction("content", 5, "kontext4", "Löschen", "delete selected range", "kontext_inhalt.vb", "delete-range"),
    LegacyContextAction("content", 6, "kontext5", "Suchen", "search", "kontext_inhalt.vb", "search/search-next/search-all"),
)

# From Baum_Kontext_.vb: TreeNode context menu.
TREE_CONTEXT: tuple[LegacyContextAction, ...] = (
    LegacyContextAction("tree", 0, "kontext2_1", "Neu darunter", "new child", "Baum_Kontext_.vb", "add-note --where child / + Kind"),
    LegacyContextAction("tree", 1, "kontext11", "Neu daneben", "new sibling", "Baum_Kontext_.vb", "add-note --where after / + Daneben"),
    LegacyContextAction("tree", 2, "kontext2_2", "Umbenennen", "rename", "Baum_Kontext_.vb", "rename / Umbenennen"),
    LegacyContextAction("tree", 3, "kontext2_6", "Kopieren", "copy subtree", "Baum_Kontext_.vb", "copy-node"),
    LegacyContextAction("tree", 4, "kontext2_7", "Ausschneiden", "cut subtree", "Baum_Kontext_.vb", "cut-node"),
    LegacyContextAction("tree", 5, "kontext2_8", "Einfügen", "paste subtree", "Baum_Kontext_.vb", "paste-node/import-json/import-file"),
    LegacyContextAction("tree", 6, "kontext2_3", "Löschen", "delete node", "Baum_Kontext_.vb", "delete-note / Löschen"),
    LegacyContextAction("tree", 7, "kontext2_4", "Speichern", "save current note as RTF", "Baum_Kontext_.vb", "export-note-rtf"),
    LegacyContextAction("tree", 8, "kontext2_5", "Desktop-Notiz", "create sticky note", "Baum_Kontext_.vb", "sticky/sticky-run/Sticky"),
    LegacyContextAction("tree", 9, "kontext2_9", "Hintergrundfarbe", "node background color", "Baum_Kontext_.vb", "color-note --bg-color / Farben"),
    LegacyContextAction("tree", 10, "kontext2_10", "Schriftfarbe", "node foreground color", "Baum_Kontext_.vb", "color-note --fg-color / Farben"),
)

# From desknote_kontext.vb: sticky-window context menu.
STICKY_CONTEXT: tuple[LegacyContextAction, ...] = (
    LegacyContextAction("sticky", 0, "kontext8", "Hintergrundfarbe", "sticky background color", "desknote_kontext.vb", "sticky --argb / color-note"),
    LegacyContextAction("sticky", 1, "kontext9", "Minimieren", "hide sticky window", "desknote_kontext.vb", "sticky --hide"),
    LegacyContextAction("sticky", 2, "kontext10", "Schließen", "close sticky window", "desknote_kontext.vb", "sticky --hide or --clear"),
)


def iter_context_actions(menu: str | None = None) -> Iterable[LegacyContextAction]:
    wanted = (menu or "all").strip().lower()
    for item in (*CONTENT_CONTEXT, *TREE_CONTEXT, *STICKY_CONTEXT):
        if wanted in {"", "all", item.menu}:
            yield item


def context_actions_payload(menu: str | None = None, language: str = "de") -> list[dict[str, object]]:
    normalized = normalize_language(language)
    return [item.as_dict(normalized) for item in iter_context_actions(menu)]


def sticky_opacity_payload() -> list[dict[str, object]]:
    return [choice.as_dict() for choice in legacy_opacity_choices()]


def format_context_actions(menu: str | None = None, language: str = "de", *, include_opacity: bool = False) -> str:
    lines: list[str] = []
    current = ""
    for item in context_actions_payload(menu, language):
        menu_name = str(item["menu"])
        if menu_name != current:
            current = menu_name
            lines.append(f"[{current}]")
        lines.append(f"{int(item['index']):02d} {item['label']} -> {item['ported_to']}")
    if include_opacity:
        lines.append("[sticky-opacity]")
        for choice in legacy_opacity_choices():
            lines.append(f"{choice.index:02d} {choice.label} -> opacity={choice.opacity:g}")
    return "\n".join(lines) if lines else "keine Kontextmenüeinträge"


def context_actions_json(menu: str | None = None, language: str = "de", *, include_opacity: bool = False) -> str:
    payload: dict[str, object] = {"menus": context_actions_payload(menu, language)}
    if include_opacity:
        payload["sticky_opacity"] = sticky_opacity_payload()
    return json.dumps(payload, indent=2, ensure_ascii=False)
