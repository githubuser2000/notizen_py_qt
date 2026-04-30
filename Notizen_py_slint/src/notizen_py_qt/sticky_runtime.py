from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .legacy_colors import css_color
from .model import Note, NoteDocument, StickyWindow
from .rtf import text_to_rtf
from .storage import autosize_sticky


@dataclass(slots=True)
class StickyWindowSpec:
    index: int
    note_id: int
    title: str
    path: str
    text: str
    x: int
    y: int
    width: int
    height: int
    opacity: float
    bg_color: int | None
    fg_color: int | None
    visible: bool

    @property
    def bg_css(self) -> str:
        return css_color(self.bg_color, "#FFF8B5")

    @property
    def fg_css(self) -> str:
        return css_color(self.fg_color, "#111111")

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["bg_css"] = self.bg_css
        payload["fg_css"] = self.fg_css
        return payload


def sticky_window_specs(document: NoteDocument, *, include_hidden: bool = False, autosize_missing: bool = True) -> list[StickyWindowSpec]:
    """Return normalized sticky-window geometry for the document.

    The old application stored desktop-note state directly on tree nodes and
    recreated borderless WinForms windows from these attributes.  This helper is
    the shared Python equivalent used by HTML export, CLI inspection and the
    optional Tk sticky runtime.
    """

    specs: list[StickyWindowSpec] = []
    for note in document.iter_notes():
        sticky = note.sticky
        if sticky is None:
            continue
        if not include_hidden and not sticky.visible:
            continue
        if autosize_missing and any(getattr(sticky, attr) is None for attr in ("width", "height")):
            sticky = autosize_sticky(note)
        specs.append(_spec_from_note(len(specs), note, sticky))
    return specs


def _spec_from_note(index: int, note: Note, sticky: StickyWindow) -> StickyWindowSpec:
    return StickyWindowSpec(
        index=index,
        note_id=note.note_id,
        title=note.title or "...",
        path=note.path_string(),
        text=note.text,
        x=int(sticky.x if sticky.x is not None else 100 + index * 24),
        y=int(sticky.y if sticky.y is not None else 100 + index * 24),
        width=max(120, int(sticky.width if sticky.width is not None else 260)),
        height=max(80, int(sticky.height if sticky.height is not None else 180)),
        opacity=max(0.05, min(1.0, float(sticky.opacity if sticky.opacity is not None else 0.85))),
        bg_color=sticky.argb if sticky.argb is not None else note.bg_color,
        fg_color=note.fg_color,
        visible=bool(sticky.visible),
    )


def run_tk_sticky_windows(
    document: NoteDocument,
    *,
    include_hidden: bool = False,
    readonly: bool = False,
    on_dirty: Callable[[NoteDocument], None] | None = None,
) -> None:
    """Show visible sticky notes in small Tk windows.

    This is intentionally optional and dependency-free.  Qt is still the main
    UI; Tk is used here only because Python ships it on many desktop systems and
    it can recreate the old independent sticky-note windows more closely than a
    single Qt main window.  In headless environments this raises a readable
    RuntimeError instead of crashing during import.
    """

    try:
        import tkinter as tk
    except Exception as exc:  # pragma: no cover - depends on runtime image
        raise RuntimeError("Tkinter ist nicht verfügbar; Sticky-Fenster können nicht geöffnet werden.") from exc

    specs = sticky_window_specs(document, include_hidden=include_hidden)
    if not specs:
        raise RuntimeError("Keine Sticky-Metadaten gefunden.")

    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:  # pragma: no cover - depends on desktop/display
        raise RuntimeError(f"Tk konnte kein Fenster öffnen: {exc}") from exc

    dirty = {"changed": False}

    def save_note(spec: StickyWindowSpec, text_widget: object) -> None:
        note = document.note_by_id(spec.note_id)
        if note is None:
            return
        try:
            value = text_widget.get("1.0", "end-1c")  # type: ignore[attr-defined]
        except Exception:
            return
        if value != note.text:
            note.rtf = text_to_rtf(value)
            document.modified = True
            dirty["changed"] = True
            if on_dirty is not None:
                on_dirty(document)

    for spec in specs:
        win = tk.Toplevel(root)
        win.title(spec.title)
        win.geometry(f"{spec.width}x{spec.height}+{spec.x}+{spec.y}")
        try:
            win.attributes("-alpha", spec.opacity)
        except Exception:
            pass
        frame = tk.Frame(win, bg=spec.bg_css)
        frame.pack(fill="both", expand=True)
        title = tk.Label(frame, text=spec.title, bg=spec.bg_css, fg=spec.fg_css, anchor="w")
        title.pack(fill="x", padx=6, pady=(4, 0))
        text = tk.Text(frame, wrap="word", bg=spec.bg_css, fg=spec.fg_css, relief="flat", borderwidth=0)
        text.insert("1.0", spec.text)
        text.pack(fill="both", expand=True, padx=6, pady=6)
        if readonly:
            text.configure(state="disabled")
        else:
            text.bind("<Control-s>", lambda _event, s=spec, t=text: (save_note(s, t), "break"))
        win.protocol("WM_DELETE_WINDOW", lambda w=win, s=spec, t=text: (None if readonly else save_note(s, t), w.destroy()))

    def on_root_close() -> None:
        root.quit()

    root.protocol("WM_DELETE_WINDOW", on_root_close)
    try:
        root.mainloop()
    finally:
        root.destroy()
