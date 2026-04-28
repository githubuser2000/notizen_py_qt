from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import time

from .autostart import autostart_status, sync_autostart
from .alarm import AlarmRule, add_or_replace_alarm, alarm_message, due_alarms, load_alarms, next_alarm, parse_alarm_datetime, parse_weekdays, remove_alarm
from . import __version__
from .config import AppConfig, config_dir
from .legacy_colors import argb_to_signed, legacy_color_by_name, legacy_light_color, legacy_palette_table, readable_color_lines
from .feedback import FeedbackError, write_feedback_gzip
from .fonts import format_font_list, list_system_fonts
from .legacy_config import import_legacy_config, load_legacy_config, write_legacy_like_config
from .model import Note, NoteDocument, StickyWindow, argb_to_hex, parse_int_or_hex
from .remote import load_uri, save_uri
from .notify import notify
from .shortcuts import format_shortcuts, shortcut_manifest
from .sticky_runtime import run_tk_sticky_windows, sticky_window_specs
from .translations import LANGUAGE_NAMES, LEGACY_KEYS, iter_translations, normalize_language, translate, translation_table
from .rtf import detect_rtf_style, restyle_rtf_as_plain, restyle_rtf_with_defaults, text_to_rtf
from .storage import (
    NotizenFileError,
    append_bullet_into_note,
    apply_font_family_to_note,
    apply_toolbar_style_to_note,
    append_current_date_into_note,
    autosize_sticky,
    change_note_font_size,
    export_document_images,
    combine_subtree_to_new_note,
    export_alx,
    export_html,
    export_json,
    export_markdown,
    export_opml,
    export_note_images,
    export_note_rtf,
    export_rtf,
    export_sticky_html,
    export_text,
    list_backups,
    import_document_root_into_document,
    import_json_into_document,
    import_opml_into_document,
    import_rtf_into_note,
    import_text_into_note,
    insert_image_into_note,
    document_to_xml_bytes,
    load_document_from_bytes,
    restore_backup,
    set_note_font_size,
    subtree_document,
)


def _select_by_title(doc: NoteDocument, title: str | None) -> None:
    if not title:
        return
    note = doc.first_note_by_title_or_path(title)
    if note is None:
        raise NotizenFileError(f"Keine Notiz mit Titel/Pfad gefunden: {title}")
    doc.select(note)


def _note_by_title(doc: NoteDocument, title: str) -> Note:
    note = doc.first_note_by_title_or_path(title)
    if note is None:
        raise NotizenFileError(f"Keine Notiz mit Titel/Pfad gefunden: {title}")
    return note


def _save_after_edit(doc: NoteDocument, output: str, password: str | None, new_password: str | None) -> None:
    save_uri(doc, output, password=new_password if new_password is not None else password)
    print(output)


def _print_tree(file: str, password: str | None, include_collapsed: bool) -> None:
    doc = load_uri(file, password=password)
    for i, row in enumerate(doc.flatten(include_collapsed=include_collapsed)):
        print(f"{i:04d} {row.label}")


def _export_txt(file: str, output: str, password: str | None, title: str | None, numbered: bool) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    export_text(doc, output, start=doc.selected_note if title else None, numbered=numbered)
    print(output)


def _export_rtf(file: str, output: str, password: str | None, title: str | None, numbered: bool) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    export_rtf(doc, output, start=doc.selected_note if title else None, numbered=numbered)
    print(output)


def _export_html(file: str, output: str, password: str | None, title: str | None) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    export_html(doc, output, start=doc.selected_note if title else None)
    print(output)


def _export_md(file: str, output: str, password: str | None, title: str | None) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    export_markdown(doc, output, start=doc.selected_note if title else None)
    print(output)


def _export_json(file: str, output: str, password: str | None, title: str | None) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    export_json(doc, output, start=doc.selected_note if title else None)
    print(output)


def _export_alx(file: str, output: str, password: str | None, title: str | None, new_password: str | None, keep_password: bool) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    exported = subtree_document(doc, start=doc.selected_note if title else None, keep_password=keep_password)
    effective_password = new_password if new_password is not None else exported.password
    save_uri(exported, output, password=effective_password, backup_count=0)
    print(output)


def _export_opml(file: str, output: str, password: str | None, title: str | None, plain: bool) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    export_opml(doc, output, start=doc.selected_note if title else None, include_rtf=not plain)
    print(output)


def _export_note_rtf(file: str, output: str, password: str | None, title: str) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    export_note_rtf(doc.selected_note, output)
    print(output)


def _extract_images(file: str, output_dir: str, password: str | None, title: str | None) -> None:
    doc = load_uri(file, password=password)
    if title:
        _select_by_title(doc, title)
        paths = export_note_images(doc.selected_note, output_dir)
    else:
        paths = export_document_images(doc, output_dir)
    for path in paths:
        print(path)
    print(f"{len(paths)} Bilddatei(en)", file=sys.stderr)


def _export_sticky_html(file: str, output: str, password: str | None, include_hidden: bool) -> None:
    doc = load_uri(file, password=password)
    export_sticky_html(doc, output, visible_only=not include_hidden)
    print(output)


def _sticky(
    file: str,
    output: str,
    title: str,
    password: str | None,
    new_password: str | None,
    show: bool,
    hide: bool,
    clear: bool,
    autosize: bool,
    x: int | None,
    y: int | None,
    width: int | None,
    height: int | None,
    opacity: float | None,
    argb: str | None,
) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    if clear:
        note.sticky = None
    else:
        sticky = note.sticky or StickyWindow(visible=True, x=100, y=100, width=260, height=180, opacity=0.85, argb=note.bg_color)
        if show:
            sticky.visible = True
        if hide:
            sticky.visible = False
        if x is not None:
            sticky.x = x
        if y is not None:
            sticky.y = y
        if width is not None:
            sticky.width = width
        if height is not None:
            sticky.height = height
        if opacity is not None:
            sticky.opacity = max(0.05, min(1.0, opacity))
        if argb is not None:
            sticky.argb = parse_int_or_hex(argb)
        note.sticky = sticky
        if autosize:
            autosize_sticky(note)
    doc.select(note)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)
    print(note.sticky.summary() if note.sticky else "Sticky-Metadaten gelöscht", file=sys.stderr)


def _change_password(file: str, output: str, old_password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=old_password)
    save_uri(doc, output, password=new_password or None)
    print(output)


def _dump_xml(file: str, output: str | None, password: str | None) -> None:
    doc = load_uri(file, password=password)
    xml_text = document_to_xml_bytes(doc).decode("utf-16")
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(xml_text, encoding="utf-8")
        print(output)
    else:
        print(xml_text)


def _pack_xml(xml_file: str, output: str, password: str | None) -> None:
    doc = load_document_from_bytes(Path(xml_file).read_bytes(), source=xml_file)
    save_uri(doc, output, password=password)
    print(output)


def _stats(file: str, password: str | None) -> None:
    doc = load_uri(file, password=password)
    stats = doc.stats()
    print(f"Notizen: {stats.notes}")
    print(f"Blätter: {stats.leaves}")
    print(f"Maximale Tiefe: {stats.max_depth}")
    print(f"Sticky-Metadaten: {stats.sticky_notes}")
    print(f"Textzeichen: {stats.characters}")


def _search(
    file: str,
    needle: str,
    password: str | None,
    case_sensitive: bool,
    whole_words: bool,
    details: bool = False,
    as_json: bool = False,
    context: int = 40,
    title: str | None = None,
) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    start = doc.selected_note if title else None
    if details or as_json:
        hits = doc.find_detailed(needle, case_sensitive=case_sensitive, whole_words=whole_words, context=context, start=start)
        if as_json:
            payload = [
                {
                    "path": hit.note.path_titles(),
                    "title": hit.note.title,
                    "title_matches": hit.title_matches,
                    "text_matches": hit.text_matches,
                    "total_matches": hit.total_matches,
                    "snippets": hit.snippets,
                }
                for hit in hits
            ]
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            for hit in hits:
                print(f"{hit.note.path_string()} [{hit.total_matches} Treffer; Titel {hit.title_matches}, Text {hit.text_matches}]")
                for snippet in hit.snippets:
                    print(f"  {snippet}")
        print(f"{len(hits)} Notiz(en) mit Treffern", file=sys.stderr)
        return

    hits = doc.find_all(needle, case_sensitive=case_sensitive, whole_words=whole_words, start=start)
    for hit in hits:
        where = []
        if hit.title_match:
            where.append("Titel")
        if hit.text_match:
            where.append("Text")
        print(f"{hit.note.path_string()} [{', '.join(where)}]")
    print(f"{len(hits)} Treffer", file=sys.stderr)


def _insert_image(
    file: str,
    output: str,
    title: str,
    image: str,
    password: str | None,
    new_password: str | None,
    width_twips: int | None,
    height_twips: int | None,
) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    insert_image_into_note(note, image, width_twips=width_twips, height_twips=height_twips)
    doc.select(note)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)


def _append_date(file: str, output: str, title: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    append_current_date_into_note(note)
    doc.select(note)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)


def _append_bullet(file: str, output: str, title: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    append_bullet_into_note(note)
    doc.select(note)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)

def _set_note(file: str, output: str, title: str, input_file: str, password: str | None, new_password: str | None, as_rtf: bool) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    if as_rtf:
        import_rtf_into_note(doc.selected_note, input_file)
    else:
        import_text_into_note(doc.selected_note, input_file)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)


def _import_json(file: str, output: str, title: str, input_file: str, where: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    target = _note_by_title(doc, title)
    created = import_json_into_document(doc, input_file, target=target, where=where)
    _save_after_edit(doc, output, password, new_password)
    print(f"importiert: {created.title}", file=sys.stderr)


def _import_opml(file: str, output: str, title: str | None, input_path: str, where: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    target = _note_by_title(doc, title) if title else doc.selected_note
    created = import_opml_into_document(doc, input_path, target=target, where=where)
    _save_after_edit(doc, output, password, new_password)
    print(f"OPML importiert: {created.title}", file=sys.stderr)


def _import_file(
    file: str,
    output: str,
    title: str,
    input_file: str,
    where: str,
    password: str | None,
    input_password: str | None,
    new_password: str | None,
) -> None:
    doc = load_uri(file, password=password)
    imported = load_uri(input_file, password=input_password)
    target = _note_by_title(doc, title)
    created = import_document_root_into_document(doc, imported, target=target, where=where)
    _save_after_edit(doc, output, password, new_password)
    print(f"importiert: {created.title}", file=sys.stderr)


def _search_occurrences(
    file: str,
    needle: str,
    password: str | None,
    case_sensitive: bool,
    whole_words: bool,
    title: str | None,
    context: int,
    max_hits: int | None,
    as_json: bool,
) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    start = doc.selected_note if title else None
    hits = doc.find_occurrences(needle, case_sensitive=case_sensitive, whole_words=whole_words, context=context, start=start, max_hits=max_hits)
    if as_json:
        payload = [
            {
                "path": hit.note.path_titles(),
                "path_string": hit.note.path_string(),
                "title": hit.note.title,
                "field": hit.field,
                "start": hit.start,
                "end": hit.end,
                "length": hit.length,
                "occurrence_index": hit.occurrence_index,
                "snippet": hit.snippet,
            }
            for hit in hits
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    for index, hit in enumerate(hits, start=1):
        print(f"{index:04d} {hit.note.path_string()} [{hit.field}:{hit.start}-{hit.end}] {hit.snippet}")
    print(f"{len(hits)} Treffer", file=sys.stderr)


def _replace(
    file: str,
    output: str,
    needle: str,
    replacement: str,
    password: str | None,
    new_password: str | None,
    case_sensitive: bool,
    whole_words: bool,
    title: str | None,
    titles_only: bool,
    text_only: bool,
) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    start = doc.selected_note if title else None
    report = doc.replace_all(
        needle,
        replacement,
        case_sensitive=case_sensitive,
        whole_words=whole_words,
        start=start,
        include_titles=not text_only,
        include_text=not titles_only,
    )
    _save_after_edit(doc, output, password, new_password)
    if report.total_replacements == 0:
        print("keine Ersetzung", file=sys.stderr)
    else:
        print(
            f"{report.total_replacements} Ersetzung(en) in {report.notes_changed} Notiz(en); "
            f"Titel {report.title_replacements}, Text {report.text_replacements}",
            file=sys.stderr,
        )


def _validate(file: str, password: str | None, as_json: bool) -> None:
    doc = load_uri(file, password=password)
    stats = doc.stats()
    payload = {
        "ok": True,
        "path": doc.path,
        "password_protected": bool(doc.password),
        "notes": stats.notes,
        "leaves": stats.leaves,
        "max_depth": stats.max_depth,
        "sticky_notes": stats.sticky_notes,
        "characters": stats.characters,
    }
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("OK")
        print(f"Pfad: {doc.path}")
        print(f"Passwortgeschützt: {'ja' if doc.password else 'nein'}")
        print(f"Notizen: {stats.notes}; Blätter: {stats.leaves}; Tiefe: {stats.max_depth}; Zeichen: {stats.characters}")


def _recent(as_json: bool) -> None:
    config = AppConfig.load()
    if as_json:
        print(json.dumps(config.recent_files, indent=2, ensure_ascii=False))
        return
    if not config.recent_files:
        print("keine zuletzt geöffneten Dateien")
        return
    for index, path in enumerate(config.recent_files, start=1):
        marker = "*" if path == config.last_file else " "
        print(f"{index}. {marker} {path}")


def _color_palette(as_json: bool) -> None:
    payload = legacy_palette_table()
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(readable_color_lines())


def _resolve_color(value: str | None, name: str | None, randomize: bool, random_index: int | None) -> int | None:
    if value:
        return argb_to_signed(parse_int_or_hex(value))
    if name:
        return legacy_color_by_name(name).signed_argb
    if randomize:
        return legacy_light_color(random_index).signed_argb
    return None


def _color_note(
    file: str,
    output: str,
    title: str,
    password: str | None,
    new_password: str | None,
    bg_color: str | None,
    fg_color: str | None,
    bg_name: str | None,
    fg_name: str | None,
    random_bg: bool,
    random_fg: bool,
    random_index: int | None,
    clear: bool,
    clear_bg: bool,
    clear_fg: bool,
    show: bool,
) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    changed = False
    if clear or clear_bg:
        note.bg_color = None
        changed = True
    if clear or clear_fg:
        note.fg_color = None
        changed = True
    bg = _resolve_color(bg_color, bg_name, random_bg, random_index)
    fg = _resolve_color(fg_color, fg_name, random_fg, random_index)
    if bg is not None:
        note.bg_color = bg
        if note.sticky is not None and note.sticky.argb is None:
            note.sticky.argb = bg
        changed = True
    if fg is not None:
        note.fg_color = fg
        changed = True
    if show:
        print(json.dumps({
            "path": note.path_titles(),
            "title": note.title,
            "bg_color": argb_to_hex(note.bg_color) if note.bg_color is not None else None,
            "fg_color": argb_to_hex(note.fg_color) if note.fg_color is not None else None,
            "bg_int": note.bg_color,
            "fg_int": note.fg_color,
        }, indent=2, ensure_ascii=False))
    if not changed:
        if show:
            return
        raise NotizenFileError("Bitte Farbe, Namen, --random-bg/--random-fg oder --clear angeben.")
    doc.select(note)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)


def _sticky_list(file: str, password: str | None, include_hidden: bool, as_json: bool) -> None:
    doc = load_uri(file, password=password)
    specs = sticky_window_specs(doc, include_hidden=include_hidden)
    if as_json:
        print(json.dumps([spec.as_dict() for spec in specs], indent=2, ensure_ascii=False))
        return
    if not specs:
        print("keine Sticky-Notizen")
        return
    for spec in specs:
        print(f"{spec.index:02d} {spec.title} [{spec.path}] {spec.width}x{spec.height}+{spec.x}+{spec.y} opacity={spec.opacity:g} bg={spec.bg_css}")


def _sticky_run(file: str, password: str | None, output: str | None, new_password: str | None, include_hidden: bool, readonly: bool) -> None:
    doc = load_uri(file, password=password)
    run_tk_sticky_windows(doc, include_hidden=include_hidden, readonly=readonly)
    if doc.modified and not readonly:
        target = output or file
        saved = save_uri(doc, target, password=new_password if new_password is not None else password)
        print(saved)


def _format_note(
    file: str,
    output: str,
    title: str,
    password: str | None,
    new_password: str | None,
    font_family: str,
    font_size: int,
    bold: bool,
    italic: bool,
    underline: bool,
    strike: bool,
    fg_color: str | None,
    bg_color: str | None,
) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    note.rtf = restyle_rtf_as_plain(
        note.rtf,
        font_family=font_family,
        font_size_half_points=font_size,
        bold=bold,
        italic=italic,
        underline=underline,
        strike=strike,
        fg_color=parse_int_or_hex(fg_color),
        bg_color=parse_int_or_hex(bg_color),
    )
    doc.select(note)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)



def _toolbar_style(
    file: str,
    output: str,
    title: str,
    password: str | None,
    new_password: str | None,
    style: str | None,
    font_family: str | None,
    font_size: int | None,
    fg_color: str | None,
    bg_color: str | None,
    show: bool,
) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    if show:
        current = detect_rtf_style(note.rtf)
        print(json.dumps({
            "font_family": current.font_family,
            "font_size_half_points": current.font_size_half_points,
            "bold": current.bold,
            "italic": current.italic,
            "underline": current.underline,
            "strike": current.strike,
            "bg_color": argb_to_hex(note.bg_color) if note.bg_color is not None else None,
            "fg_color": argb_to_hex(note.fg_color) if note.fg_color is not None else None,
        }, indent=2, ensure_ascii=False))
    if style is None and font_family is None and font_size is None and fg_color is None and bg_color is None:
        if show:
            return
        raise NotizenFileError("Bitte --style, --font-family, --font-size, --fg-color, --bg-color oder --show angeben.")
    if style is not None:
        apply_toolbar_style_to_note(
            note,
            style,
            font_family=font_family,
            font_size_half_points=font_size,
            fg_color=parse_int_or_hex(fg_color) if fg_color else None,
            bg_color=parse_int_or_hex(bg_color) if bg_color else None,
        )
    else:
        note.rtf = restyle_rtf_with_defaults(
            note.rtf,
            font_family=font_family,
            font_size_half_points=font_size,
            fg_color=parse_int_or_hex(fg_color) if fg_color else None,
            bg_color=parse_int_or_hex(bg_color) if bg_color else None,
        )
    doc.select(note)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)

def _font_size(
    file: str,
    output: str,
    title: str,
    password: str | None,
    new_password: str | None,
    bigger: bool,
    smaller: bool,
    set_size: int | None,
    step: int,
) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    if set_size is not None:
        set_note_font_size(note, set_size)
    else:
        if not bigger and not smaller:
            raise NotizenFileError("Bitte --bigger, --smaller oder --set angeben.")
        delta = abs(step or 2) * (1 if bigger else -1)
        change_note_font_size(note, delta)
    doc.select(note)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)


def _rename(file: str, output: str, title: str, new_title: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    note.title = new_title.strip() or "..."
    doc.select(note)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)


def _add_note(file: str, output: str, title: str, new_title: str, text: str, where: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    doc.select(_note_by_title(doc, title))
    note = Note(new_title.strip() or "...", text_to_rtf(text or ""))
    if where == "child":
        created = doc.selected_note.add_child(note)
        doc.selected_note.expanded = True
    elif where == "before":
        created = doc.selected_note.insert_before(note)
    else:
        created = doc.selected_note.insert_after(note)
    doc.select(created)
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)


def _delete_note(file: str, output: str, title: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    doc.select(_note_by_title(doc, title))
    doc.delete_selected()
    _save_after_edit(doc, output, password, new_password)


def _move(file: str, output: str, title: str, action: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    if action == "up":
        ok = doc.move_selected_up()
    elif action == "down":
        ok = doc.move_selected_down()
    elif action == "indent":
        ok = doc.indent_selected()
    elif action == "outdent":
        ok = doc.outdent_selected()
    else:  # pragma: no cover
        raise NotizenFileError(f"Unbekannte Bewegung: {action}")
    if not ok:
        raise NotizenFileError(f"Aktion nicht möglich: {action}")
    _save_after_edit(doc, output, password, new_password)


def _move_under(file: str, output: str, title: str, target_title: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    note = _note_by_title(doc, title)
    target = _note_by_title(doc, target_title)
    doc.select(note)
    if not doc.move_selected_under(target):
        raise NotizenFileError("Notiz kann nicht unter das Ziel verschoben werden.")
    _save_after_edit(doc, output, password, new_password)


def _duplicate(file: str, output: str, title: str, password: str | None, new_password: str | None) -> None:
    doc = load_uri(file, password=password)
    _select_by_title(doc, title)
    clone = doc.duplicate_selected()
    if clone is None:
        raise NotizenFileError("Wurzel kann nicht dupliziert werden.")
    _save_after_edit(doc, output, password, new_password)


def _combine_subtree(
    file: str,
    output: str,
    title: str | None,
    new_title: str | None,
    password: str | None,
    new_password: str | None,
    numbered: bool,
    attach_to_selected: bool,
) -> None:
    doc = load_uri(file, password=password)
    if title:
        _select_by_title(doc, title)
    created = combine_subtree_to_new_note(
        doc,
        start=doc.selected_note,
        title=new_title,
        numbered=numbered,
        attach_to_root=not attach_to_selected,
    )
    _save_after_edit(doc, output, password, new_password)
    print(f"zusammengefasst: {created.title}", file=sys.stderr)


def _expand_state(
    file: str,
    output: str,
    password: str | None,
    new_password: str | None,
    title: str | None,
    state: str,
    all_notes: bool,
) -> None:
    doc = load_uri(file, password=password)
    notes: list[Note]
    if all_notes:
        notes = list(doc.iter_notes())
    else:
        if not title:
            raise NotizenFileError("Bitte --title oder --all angeben.")
        notes = [_note_by_title(doc, title)]
    for note in notes:
        if state == "expanded":
            note.expanded = True
        elif state == "collapsed":
            note.expanded = False
        elif state == "toggle":
            note.expanded = not note.expanded
        else:  # pragma: no cover
            raise NotizenFileError(f"Unbekannter Zustand: {state}")
    if doc.root in notes and state == "collapsed":
        doc.root.expanded = True
    doc.modified = True
    _save_after_edit(doc, output, password, new_password)
    print(f"{len(notes)} Knoten aktualisiert", file=sys.stderr)


def _font_list(as_json: bool, contains: str | None, limit: int | None) -> None:
    fonts = list_system_fonts(contains=contains, limit=limit)
    if as_json:
        print(json.dumps([font.as_dict() for font in fonts], indent=2, ensure_ascii=False))
    else:
        print(format_font_list(fonts))
    print(f"{len(fonts)} Schrift(en)", file=sys.stderr)


def _backup_list(file: str, as_json: bool) -> None:
    backups = list_backups(file)
    if as_json:
        print(json.dumps([info.as_dict() for info in backups], indent=2, ensure_ascii=False))
    else:
        for info in backups:
            print(f"{info.path}	{int(info.created)}	{info.size}")
    print(f"{len(backups)} Backup(s)", file=sys.stderr)


def _backup_restore(backup: str, target: str | None, no_backup_current: bool) -> None:
    restored = restore_backup(backup, target=target, backup_current=not no_backup_current)
    print(restored)


def _config_show() -> None:
    config = AppConfig.load()
    print(json.dumps(config.__dict__ if hasattr(config, "__dict__") else _slots_dict(config), indent=2, ensure_ascii=False))


def _config_path() -> None:
    print(config_dir() / "config.json")


def _config_set(
    *,
    backup_count: int | None,
    autosave_seconds: int | None,
    language: str | None,
    autorun: bool | None,
    autorun_minimized: bool | None,
    show_in_taskbar: bool | None,
    show_desknote_borders: bool | None,
    scrollbars_choice: int | None,
    last_file: str | None,
    add_recent: list[str] | None,
    clear_recent: bool,
    window: str | None,
    window_state: str | None,
    as_json: bool,
) -> None:
    config = AppConfig.load()
    if backup_count is not None:
        config.backup_count = max(0, int(backup_count))
    if autosave_seconds is not None:
        config.autosave_seconds = max(0, int(autosave_seconds))
    if language is not None:
        config.language = normalize_language(language)
    if autorun is not None:
        config.autorun = autorun
    if autorun_minimized is not None:
        config.autorun_minimized = autorun_minimized
    if show_in_taskbar is not None:
        config.show_in_taskbar = show_in_taskbar
    if show_desknote_borders is not None:
        config.show_desknote_borders = show_desknote_borders
    if scrollbars_choice is not None:
        config.scrollbars_choice = max(0, min(3, int(scrollbars_choice)))
    if clear_recent:
        config.recent_files = []
        config.last_file = None
    if last_file:
        config.add_recent(last_file)
    for recent in add_recent or []:
        config.add_recent(recent)
    if window:
        parts = [part.strip() for part in window.replace("x", ",").replace("+", ",").split(",") if part.strip()]
        if len(parts) != 4:
            raise ValueError("--window erwartet vier Werte: x,y,width,height")
        x, y, width, height = (int(part) for part in parts)
        config.window_x = x
        config.window_y = y
        config.window_width = max(1, width)
        config.window_height = max(1, height)
    if window_state is not None:
        state = window_state.strip().lower()
        aliases = {"normal": "normal", "max": "maximized", "maximized": "maximized", "min": "minimized", "minimized": "minimized"}
        if state not in aliases:
            raise ValueError("--window-state muss normal, maximized oder minimized sein")
        config.window_state = aliases[state]
    config.save()
    if as_json:
        print(json.dumps(_slots_dict(config), indent=2, ensure_ascii=False))
    else:
        print(config_dir() / "config.json")


def _lang_list(as_json: bool) -> None:
    payload = {code: {"name": name, "keys": len(LEGACY_KEYS)} for code, name in LANGUAGE_NAMES.items()}
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    for code, info in payload.items():
        print(f"{code:>2}  {info['name']}  ({info['keys']} Texte)")


def _lang_get(key: str, language: str, all_languages: bool, as_json: bool) -> None:
    if all_languages:
        rows = translation_table(languages=list(LANGUAGE_NAMES))
        # Reuse translate's validation/key matching by filtering through key_index indirectly.
        wanted = translate(key, language)
        matches = [row for row in rows if row["key"].casefold() == key.casefold() or str(row["index"]) == key]
        if not matches:
            raise ValueError(f"Unbekannter Sprachschlüssel: {key}")
        payload = matches[0]
        if as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"{payload['index']} {payload['key']}")
            for code in LANGUAGE_NAMES:
                print(f"{code}: {payload[code]}")
        return
    code = normalize_language(language)
    text = translate(key, code)
    if as_json:
        entry = next(item for item in iter_translations(code) if item.key.casefold() == key.casefold() or str(item.index) == key)
        print(json.dumps(entry.as_dict(), indent=2, ensure_ascii=False))
    else:
        print(text)


def _lang_dump(language: str, all_languages: bool, as_json: bool) -> None:
    if all_languages:
        payload = translation_table(languages=list(LANGUAGE_NAMES))
        if as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return
        for row in payload:
            texts = " | ".join(f"{code}: {row[code]}" for code in LANGUAGE_NAMES)
            print(f"{row['index']:03d} {row['key']}: {texts}")
        return
    code = normalize_language(language)
    entries = iter_translations(code)
    if as_json:
        print(json.dumps([entry.as_dict() for entry in entries], indent=2, ensure_ascii=False))
        return
    for entry in entries:
        print(f"{entry.index:03d} {entry.key}: {entry.text}")


def _shortcuts(as_json: bool) -> None:
    if as_json:
        print(json.dumps(shortcut_manifest(), indent=2, ensure_ascii=False))
    else:
        print(format_shortcuts())


def _about(language: str, as_json: bool) -> None:
    code = normalize_language(language)
    payload = {
        "product": "Notizen Py Slint",
        "version": __version__,
        "legacy_product": "Notizen.NET",
        "legacy_website": "http://www.notiza.de",
        "language": code,
        "help_text": translate("aboutinfotext", code),
        "feedback_label": translate("feedback", code),
    }
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(f"{payload['product']} {payload['version']}")
    print(f"Port von {payload['legacy_product']}")
    print()
    print(payload["help_text"])


def _feedback_draft(output: str, text_value: str | None, input_file: str | None) -> None:
    if text_value is None and input_file is None:
        raise FeedbackError("Bitte --text oder --input angeben.")
    if text_value is not None and input_file is not None:
        raise FeedbackError("Bitte nur --text oder nur --input angeben.")
    body = text_value if text_value is not None else Path(input_file or "").read_text(encoding="utf-8")
    target = write_feedback_gzip(body, output)
    print(target)


def _config_import_legacy(path: str | None) -> None:
    config = import_legacy_config(path)
    print(json.dumps(_slots_dict(config), indent=2, ensure_ascii=False))


def _config_read_legacy(path: str) -> None:
    legacy = load_legacy_config(path)
    print(json.dumps(legacy.as_dict(), indent=2, ensure_ascii=False))


def _config_export_legacy(output: str) -> None:
    path = write_legacy_like_config(AppConfig.load(), output)
    print(path)


def _config_set_ftp(host: str | None, username: str | None, password: str | None, path_value: str | None, use_tls: bool | None) -> None:
    config = AppConfig.load()
    if host is not None:
        config.ftp_host = host
    if username is not None:
        config.ftp_username = username
    if password is not None:
        config.ftp_password = password
    if path_value is not None:
        config.ftp_path = path_value
    if use_tls is not None:
        config.ftp_use_tls = use_tls
    config.save()
    print(config.default_remote_url())


def _autostart(enable: bool | None) -> None:
    config = AppConfig.load()
    if enable is not None:
        config.autorun = enable
        config.save()
        status = sync_autostart(config)
    else:
        status = autostart_status()
    print(f"unterstützt: {'ja' if status.supported else 'nein'}")
    print(f"installiert: {'ja' if status.installed else 'nein'}")
    if status.path:
        print(f"pfad: {status.path}")
    if status.message:
        print(f"hinweis: {status.message}")


def _alarm_add(
    name: str,
    at: str,
    repeat: str,
    interval: int,
    weekdays: list[str] | None,
    message: str,
    note_title: str,
    inactive: bool,
) -> None:
    alarm = AlarmRule.create(
        name,
        at,
        active=not inactive,
        repeat=repeat,
        interval=interval,
        weekdays=parse_weekdays(weekdays),
        message=message or "",
        note_title=note_title or "",
    )
    add_or_replace_alarm(alarm)
    print(alarm.summary())


def _alarm_list() -> None:
    alarms = load_alarms()
    for alarm in alarms:
        print(alarm.summary())
    print(f"{len(alarms)} Wecker", file=sys.stderr)


def _alarm_next() -> None:
    found = next_alarm(load_alarms())
    if found is None:
        print("kein aktiver Wecker")
        return
    alarm, when = found
    note = f" [{alarm.note_title}]" if alarm.note_title else ""
    message = f" - {alarm.message}" if alarm.message else ""
    print(f"{when:%Y-%m-%d %H:%M} {alarm.name}{note}{message}")


def _alarm_remove(name: str) -> None:
    removed = remove_alarm(name)
    print("entfernt" if removed else "nicht gefunden")



def _parse_optional_now(value: str | None) -> datetime | None:
    if not value:
        return None
    return parse_alarm_datetime(value)


def _alarm_due(now_text: str | None, grace_seconds: int, notify_desktop: bool, dry_run: bool) -> None:
    now = _parse_optional_now(now_text)
    hits = due_alarms(load_alarms(), now=now, grace_seconds=grace_seconds)
    for alarm, when in hits:
        line = alarm_message(alarm, when)
        print(line)
        if notify_desktop:
            result = notify(alarm.name, alarm.message or line, dry_run=dry_run)
            print(f"notify: {result.backend} {'ok' if result.delivered else 'fehlgeschlagen'} {result.message}".rstrip(), file=sys.stderr)
    print(f"{len(hits)} fällige Wecker", file=sys.stderr)


def _alarm_watch(poll_seconds: float, grace_seconds: int, once: bool, notify_desktop: bool, dry_run: bool) -> None:
    poll = max(1.0, float(poll_seconds or 30))
    grace = max(1, int(grace_seconds or poll))
    fired: set[tuple[str, str]] = set()
    while True:
        now = datetime.now()
        hits = due_alarms(load_alarms(), now=now, grace_seconds=grace)
        for alarm, when in hits:
            key = (alarm.name, when.strftime("%Y-%m-%d %H:%M"))
            if key in fired:
                continue
            fired.add(key)
            line = alarm_message(alarm, when)
            print(line, flush=True)
            if notify_desktop:
                result = notify(alarm.name, alarm.message or line, dry_run=dry_run)
                print(f"notify: {result.backend} {'ok' if result.delivered else 'fehlgeschlagen'} {result.message}".rstrip(), file=sys.stderr, flush=True)
        if once:
            return
        time.sleep(poll)

def _slots_dict(obj: object) -> dict[str, object]:
    result: dict[str, object] = {}
    for cls in type(obj).mro():
        for name in getattr(cls, "__slots__", ()):  # dataclass(slots=True)
            if name.startswith("_"):
                continue
            result[name] = getattr(obj, name)
    return result


def _add_password_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--password")


def _add_new_password_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--new-password")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kommandozeilenwerkzeug für Notizen.NET-.alx-Dateien")
    sub = parser.add_subparsers(dest="cmd", required=True)

    tree = sub.add_parser("tree", help="Notizbaum ausgeben")
    tree.add_argument("file")
    tree.add_argument("--visible-only", action="store_true", help="eingeklappte Unterknoten ausblenden")
    _add_password_arg(tree)

    txt = sub.add_parser("export-txt", help="Nach TXT exportieren")
    txt.add_argument("file")
    txt.add_argument("output")
    txt.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel exportieren")
    txt.add_argument("--numbered", action="store_true")
    _add_password_arg(txt)

    rtf = sub.add_parser("export-rtf", help="Nach RTF exportieren")
    rtf.add_argument("file")
    rtf.add_argument("output")
    rtf.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel exportieren")
    rtf.add_argument("--numbered", action="store_true")
    _add_password_arg(rtf)

    html = sub.add_parser("export-html", help="Nach HTML exportieren")
    html.add_argument("file")
    html.add_argument("output")
    html.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel exportieren")
    _add_password_arg(html)

    md = sub.add_parser("export-md", help="Nach Markdown exportieren")
    md.add_argument("file")
    md.add_argument("output")
    md.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel exportieren")
    _add_password_arg(md)

    json_exp = sub.add_parser("export-json", help="Dokument oder Teilbaum als JSON exportieren")
    json_exp.add_argument("file")
    json_exp.add_argument("output")
    json_exp.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel exportieren")
    _add_password_arg(json_exp)

    alx_exp = sub.add_parser("export-alx", help="Dokument oder Teilbaum als eigenständige .alx/.xml/FTP-Datei exportieren")
    alx_exp.add_argument("file")
    alx_exp.add_argument("output")
    alx_exp.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel exportieren")
    alx_exp.add_argument("--new-password", help="Export verschlüsseln; leer/fehlend speichert unverschlüsselt")
    alx_exp.add_argument("--keep-password", action="store_true", help="Quellpasswort für den Export übernehmen, wenn kein --new-password gesetzt ist")
    _add_password_arg(alx_exp)

    opml_exp = sub.add_parser("export-opml", help="Dokument oder Teilbaum als OPML-Outline exportieren")
    opml_exp.add_argument("file")
    opml_exp.add_argument("output")
    opml_exp.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel exportieren")
    opml_exp.add_argument("--plain", action="store_true", help="nur OPML/Plain-Text schreiben, kein base64-RTF-Metadatum")
    _add_password_arg(opml_exp)

    note_rtf = sub.add_parser("export-note-rtf", help="Roh-RTF einer einzelnen Notiz exportieren")
    note_rtf.add_argument("file")
    note_rtf.add_argument("output")
    note_rtf.add_argument("--title", required=True)
    _add_password_arg(note_rtf)

    images = sub.add_parser("extract-images", help="eingebettete RTF-Bilder extrahieren")
    images.add_argument("file")
    images.add_argument("output_dir")
    images.add_argument("--title", help="nur eine Notiz untersuchen")
    _add_password_arg(images)

    sticky_html = sub.add_parser("export-sticky-html", help="sichtbare Sticky-Notizen als HTML-Board exportieren")
    sticky_html.add_argument("file")
    sticky_html.add_argument("output")
    sticky_html.add_argument("--all", action="store_true", help="auch ausgeblendete Sticky-Metadaten exportieren")
    _add_password_arg(sticky_html)

    password = sub.add_parser("change-password", help="Datei neu speichern und Passwort ändern/entfernen")
    password.add_argument("file")
    password.add_argument("output")
    password.add_argument("--old-password")
    password.add_argument("--new-password", help="Leer/fehlend speichert unverschlüsselt")

    dump_xml = sub.add_parser("dump-xml", help=".alx/.xml/FTP-Datei als lesbares XML ausgeben")
    dump_xml.add_argument("file")
    dump_xml.add_argument("output", nargs="?")
    _add_password_arg(dump_xml)

    pack_xml = sub.add_parser("pack-xml", help="XML wieder als .alx/.xml oder FTP-Ziel speichern")
    pack_xml.add_argument("xml_file")
    pack_xml.add_argument("output")
    pack_xml.add_argument("--password")

    stats = sub.add_parser("stats", help="Baumstatistik ausgeben")
    stats.add_argument("file")
    _add_password_arg(stats)

    search = sub.add_parser("search", help="Titel und Text durchsuchen")
    search.add_argument("file")
    search.add_argument("needle")
    search.add_argument("--case-sensitive", action="store_true")
    search.add_argument("--whole-words", action="store_true")
    search.add_argument("--details", action="store_true", help="Treffer zählen und Snippets ausgeben")
    search.add_argument("--json", action="store_true", help="detaillierte Treffer als JSON ausgeben")
    search.add_argument("--context", type=int, default=40, help="Snippet-Kontextzeichen")
    search.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel durchsuchen")
    _add_password_arg(search)

    search_occ = sub.add_parser("search-occurrences", help="einzelne Suchtreffer mit Position wie alte suchergebnisse ausgeben")
    search_occ.add_argument("file")
    search_occ.add_argument("needle")
    search_occ.add_argument("--case-sensitive", action="store_true")
    search_occ.add_argument("--whole-words", action="store_true")
    search_occ.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel durchsuchen")
    search_occ.add_argument("--context", type=int, default=40, help="Snippet-Kontextzeichen")
    search_occ.add_argument("--max", dest="max_hits", type=int, help="maximale Trefferzahl")
    search_occ.add_argument("--json", action="store_true")
    _add_password_arg(search_occ)

    replace = sub.add_parser("replace", help="Text in Titeln und/oder Notiztext ersetzen")
    replace.add_argument("file")
    replace.add_argument("output")
    replace.add_argument("needle")
    replace.add_argument("replacement")
    replace.add_argument("--title", help="nur Teilbaum ab erstem passenden Titel ändern")
    replace.add_argument("--case-sensitive", action="store_true")
    replace.add_argument("--whole-words", action="store_true")
    group_replace = replace.add_mutually_exclusive_group()
    group_replace.add_argument("--titles-only", action="store_true")
    group_replace.add_argument("--text-only", action="store_true")
    _add_new_password_arg(replace)
    _add_password_arg(replace)

    validate = sub.add_parser("validate", help="Datei laden und Kompatibilitäts-/Statistikcheck ausgeben")
    validate.add_argument("file")
    validate.add_argument("--json", action="store_true")
    _add_password_arg(validate)

    sub_recent = sub.add_parser("recent", help="zuletzt geöffnete Dateien aus der Port-Konfiguration anzeigen")
    sub_recent.add_argument("--json", action="store_true")

    palette = sub.add_parser("color-palette", help="alte helle Notizen.NET-Farbpalette anzeigen")
    palette.add_argument("--json", action="store_true")

    color_note = sub.add_parser("color-note", help="Knotenfarben bgcolor/fgcolor setzen, löschen oder anzeigen")
    color_note.add_argument("file")
    color_note.add_argument("output")
    color_note.add_argument("--title", required=True)
    color_note.add_argument("--bg-color")
    color_note.add_argument("--fg-color")
    color_note.add_argument("--bg-name", help="Name aus color-palette, z.B. LightYellow")
    color_note.add_argument("--fg-name", help="Name aus color-palette")
    color_note.add_argument("--random-bg", action="store_true", help="alte zufällige helle Hintergrundfarbe setzen")
    color_note.add_argument("--random-fg", action="store_true", help="alte zufällige helle Vordergrundfarbe setzen")
    color_note.add_argument("--random-index", type=int, help="deterministischer Palette-Index für --random-bg/--random-fg")
    color_note.add_argument("--clear", action="store_true", help="bgcolor und fgcolor löschen")
    color_note.add_argument("--clear-bg", action="store_true")
    color_note.add_argument("--clear-fg", action="store_true")
    color_note.add_argument("--show", action="store_true", help="Farben nach der Änderung als JSON ausgeben")
    _add_new_password_arg(color_note)
    _add_password_arg(color_note)

    sticky_list = sub.add_parser("sticky-list", help="Sticky-Fenster-Metadaten normalisiert anzeigen")
    sticky_list.add_argument("file")
    sticky_list.add_argument("--all", action="store_true", help="auch ausgeblendete Sticky-Metadaten anzeigen")
    sticky_list.add_argument("--json", action="store_true")
    _add_password_arg(sticky_list)

    sticky_run = sub.add_parser("sticky-run", help="sichtbare Sticky-Notizen als kleine Python/Tk-Fenster öffnen")
    sticky_run.add_argument("file")
    sticky_run.add_argument("--all", action="store_true", help="auch ausgeblendete Sticky-Metadaten öffnen")
    sticky_run.add_argument("--readonly", action="store_true", help="Sticky-Fenster nicht editierbar machen")
    sticky_run.add_argument("--output", help="Zieldatei für Änderungen; ohne Angabe wird die Eingabedatei überschrieben")
    _add_new_password_arg(sticky_run)
    _add_password_arg(sticky_run)

    set_note = sub.add_parser("set-note", help="Text/RTF einer Notiz ersetzen und speichern")
    set_note.add_argument("file")
    set_note.add_argument("output")
    set_note.add_argument("--title", required=True)
    set_note.add_argument("--input", required=True)
    set_note.add_argument("--rtf", action="store_true")
    _add_new_password_arg(set_note)
    _add_password_arg(set_note)

    json_imp = sub.add_parser("import-json", help="JSON-Teilbaum in eine Datei importieren")
    json_imp.add_argument("file")
    json_imp.add_argument("output")
    json_imp.add_argument("--title", required=True, help="Ziel-/Bezugsknoten")
    json_imp.add_argument("--input", required=True)
    json_imp.add_argument("--where", choices=["child", "before", "after"], default="child")
    _add_new_password_arg(json_imp)
    _add_password_arg(json_imp)

    opml_imp = sub.add_parser("import-opml", help="OPML-Outline als Notiz-Teilbaum importieren")
    opml_imp.add_argument("file")
    opml_imp.add_argument("output")
    opml_imp.add_argument("--title", required=True, help="Ziel-/Bezugsknoten")
    opml_imp.add_argument("--input", required=True)
    opml_imp.add_argument("--where", choices=["child", "before", "after"], default="child")
    _add_new_password_arg(opml_imp)
    _add_password_arg(opml_imp)

    file_imp = sub.add_parser("import-file", help="Root-Teilbaum einer anderen .alx/.xml/FTP-Datei importieren")
    file_imp.add_argument("file")
    file_imp.add_argument("output")
    file_imp.add_argument("--title", required=True, help="Ziel-/Bezugsknoten")
    file_imp.add_argument("--input", required=True, help="zu importierende .alx/.xml/FTP-Datei")
    file_imp.add_argument("--where", choices=["child", "before", "after"], default="child")
    file_imp.add_argument("--input-password")
    _add_new_password_arg(file_imp)
    _add_password_arg(file_imp)

    img = sub.add_parser("insert-image", help="PNG/JPEG/BMP als RTF-Bild an eine Notiz anhängen")
    img.add_argument("file")
    img.add_argument("output")
    img.add_argument("--title", required=True)
    img.add_argument("--image", required=True)
    img.add_argument("--width-twips", type=int)
    img.add_argument("--height-twips", type=int)
    _add_new_password_arg(img)
    _add_password_arg(img)

    date = sub.add_parser("append-date", help="aktuelles Datum/Uhrzeit an eine Notiz anhängen")
    date.add_argument("file")
    date.add_argument("output")
    date.add_argument("--title", required=True)
    _add_new_password_arg(date)
    _add_password_arg(date)

    bullet = sub.add_parser("append-bullet", help="Aufzählungszeichen an eine Notiz anhängen")
    bullet.add_argument("file")
    bullet.add_argument("output")
    bullet.add_argument("--title", required=True)
    _add_new_password_arg(bullet)
    _add_password_arg(bullet)

    fmt = sub.add_parser("format-note", help="eine Notiz als schlichtes, formatiertes RTF neu schreiben")
    fmt.add_argument("file")
    fmt.add_argument("output")
    fmt.add_argument("--title", required=True)
    fmt.add_argument("--font-family", default="Sans Serif")
    fmt.add_argument("--font-size", type=int, default=18, help="RTF-Halbpunkte, 18 = 9pt")
    fmt.add_argument("--bold", action="store_true")
    fmt.add_argument("--italic", action="store_true")
    fmt.add_argument("--underline", action="store_true")
    fmt.add_argument("--strike", action="store_true")
    fmt.add_argument("--fg-color")
    fmt.add_argument("--bg-color")
    _add_new_password_arg(fmt)
    _add_password_arg(fmt)

    style = sub.add_parser("style-note", help="alte RichTextBox-Toolbar-Stile auf eine ganze Notiz anwenden")
    style.add_argument("file")
    style.add_argument("output")
    style.add_argument("--title", required=True)
    style.add_argument("--style", choices=["bold", "italic", "underline", "strike", "regular"], help="Toolbar-Stil wie im Original")
    style.add_argument("--font-family", help="Schriftfamilie setzen")
    style.add_argument("--font-size", type=int, help="RTF-Halbpunkte setzen, 18 = 9pt")
    style.add_argument("--fg-color")
    style.add_argument("--bg-color")
    style.add_argument("--show", action="store_true", help="erkannte globale Formatwerte anzeigen")
    _add_new_password_arg(style)
    _add_password_arg(style)

    font_list = sub.add_parser("font-list", help="installierte Schriften wie alte ToolStrip-Schriftliste anzeigen")
    font_list.add_argument("--json", action="store_true")
    font_list.add_argument("--contains", help="nach Name oder Pfad filtern")
    font_list.add_argument("--limit", type=int, help="maximale Trefferzahl")

    font_size = sub.add_parser("font-size", help="Textgröße einer Notiz wie Ctrl+Plus/Ctrl+Minus ändern")
    font_size.add_argument("file")
    font_size.add_argument("output")
    font_size.add_argument("--title", required=True)
    size_group = font_size.add_mutually_exclusive_group(required=True)
    size_group.add_argument("--bigger", action="store_true")
    size_group.add_argument("--smaller", action="store_true")
    size_group.add_argument("--set", dest="set_size", type=int, help="RTF-Halbpunkte direkt setzen, z.B. 22")
    font_size.add_argument("--step", type=int, default=2, help="Halbpunkte pro Schritt; Standard 2 = 1pt")
    _add_new_password_arg(font_size)
    _add_password_arg(font_size)

    sticky = sub.add_parser("sticky", help="Sticky-Metadaten einer Notiz anzeigen/ändern")
    sticky.add_argument("file")
    sticky.add_argument("output")
    sticky.add_argument("--title", required=True)
    state_group = sticky.add_mutually_exclusive_group()
    state_group.add_argument("--show", action="store_true")
    state_group.add_argument("--hide", action="store_true")
    sticky.add_argument("--clear", action="store_true", help="Sticky-Metadaten entfernen")
    sticky.add_argument("--autosize", action="store_true", help="Breite/Höhe aus Textlänge schätzen")
    sticky.add_argument("--x", type=int)
    sticky.add_argument("--y", type=int)
    sticky.add_argument("--width", type=int)
    sticky.add_argument("--height", type=int)
    sticky.add_argument("--opacity", type=float)
    sticky.add_argument("--argb", help="ARGB/Farbe dezimal oder hex, z.B. 0xFFFFFF99")
    _add_new_password_arg(sticky)
    _add_password_arg(sticky)

    expand_state = sub.add_parser("expand-state", help="gespeicherten Auf-/Zu-Zustand von Knoten setzen")
    expand_state.add_argument("file")
    expand_state.add_argument("output")
    expand_state.add_argument("--title", help="einzelnen Knoten per Titel/Pfad ändern")
    expand_state.add_argument("--all", action="store_true", help="alle Knoten ändern")
    expand_group = expand_state.add_mutually_exclusive_group(required=True)
    expand_group.add_argument("--expanded", action="store_true")
    expand_group.add_argument("--collapsed", action="store_true")
    expand_group.add_argument("--toggle", action="store_true")
    _add_new_password_arg(expand_state)
    _add_password_arg(expand_state)

    rename = sub.add_parser("rename", help="Notiz umbenennen")
    rename.add_argument("file")
    rename.add_argument("output")
    rename.add_argument("--title", required=True)
    rename.add_argument("--new-title", required=True)
    _add_new_password_arg(rename)
    _add_password_arg(rename)

    add = sub.add_parser("add-note", help="neue Notiz einfügen")
    add.add_argument("file")
    add.add_argument("output")
    add.add_argument("--title", required=True, help="Bezugsknoten")
    add.add_argument("--new-title", required=True)
    add.add_argument("--text", default="")
    add.add_argument("--where", choices=["child", "before", "after"], default="child")
    _add_new_password_arg(add)
    _add_password_arg(add)

    delete = sub.add_parser("delete-note", help="Notiz löschen")
    delete.add_argument("file")
    delete.add_argument("output")
    delete.add_argument("--title", required=True)
    _add_new_password_arg(delete)
    _add_password_arg(delete)

    move = sub.add_parser("move", help="Notiz verschieben und speichern")
    move.add_argument("file")
    move.add_argument("output")
    move.add_argument("--title", required=True)
    move.add_argument("--action", choices=["up", "down", "indent", "outdent"], required=True)
    _add_new_password_arg(move)
    _add_password_arg(move)

    move_under = sub.add_parser("move-under", help="Notiz unter einen Zielknoten verschieben")
    move_under.add_argument("file")
    move_under.add_argument("output")
    move_under.add_argument("--title", required=True)
    move_under.add_argument("--target-title", required=True)
    _add_new_password_arg(move_under)
    _add_password_arg(move_under)

    duplicate = sub.add_parser("duplicate", help="Notiz duplizieren und speichern")
    duplicate.add_argument("file")
    duplicate.add_argument("output")
    duplicate.add_argument("--title", required=True)
    _add_new_password_arg(duplicate)
    _add_password_arg(duplicate)

    combine = sub.add_parser("combine-subtree", help="Teilbaum wie die alte Einheit/Zusammenfassen-Funktion als neue Notiz einfügen")
    combine.add_argument("file")
    combine.add_argument("output")
    combine.add_argument("--title", help="Teilbaum ab erstem passenden Titel; ohne Angabe die Wurzel")
    combine.add_argument("--new-title")
    combine.add_argument("--numbered", action="store_true", default=True)
    combine.add_argument("--plain", action="store_true", help="ohne Nummerierung zusammenfassen")
    combine.add_argument("--attach-to-selected", action="store_true", help="neue Zusammenfassung als Kind des ausgewählten Knotens statt unter der Wurzel")
    _add_new_password_arg(combine)
    _add_password_arg(combine)

    backup_list = sub.add_parser("backup-list", help="lokale Sicherheitskopien einer Datei anzeigen")
    backup_list.add_argument("file")
    backup_list.add_argument("--json", action="store_true")

    backup_restore = sub.add_parser("backup-restore", help="eine Sicherheitskopie zurückspielen")
    backup_restore.add_argument("backup")
    backup_restore.add_argument("--target", help="Zieldatei; ohne Angabe aus Backup-Ordner abgeleitet")
    backup_restore.add_argument("--no-backup-current", action="store_true", help="aktuelle Zieldatei vor dem Überschreiben nicht sichern")

    cfg_show = sub.add_parser("config-show", help="Port-Konfiguration anzeigen")

    sub.add_parser("config-path", help="Pfad zur neuen JSON-Konfiguration ausgeben")

    cfg_set = sub.add_parser("config-set", help="allgemeine Einstellungen aus dem alten Einstellungen-Dialog setzen")
    cfg_set.add_argument("--backup-count", type=int)
    cfg_set.add_argument("--autosave-seconds", type=int)
    cfg_set.add_argument("--language", help="de/en/zh/fr/es/ru oder alter Name wie Deutsch/English")
    autorun_group = cfg_set.add_mutually_exclusive_group()
    autorun_group.add_argument("--autorun", action="store_true")
    autorun_group.add_argument("--no-autorun", action="store_true")
    autorun_min_group = cfg_set.add_mutually_exclusive_group()
    autorun_min_group.add_argument("--autorun-minimized", action="store_true")
    autorun_min_group.add_argument("--no-autorun-minimized", action="store_true")
    taskbar_group = cfg_set.add_mutually_exclusive_group()
    taskbar_group.add_argument("--show-in-taskbar", action="store_true")
    taskbar_group.add_argument("--hide-in-taskbar", action="store_true")
    border_group = cfg_set.add_mutually_exclusive_group()
    border_group.add_argument("--show-desknote-borders", action="store_true")
    border_group.add_argument("--hide-desknote-borders", action="store_true")
    cfg_set.add_argument("--scrollbars-choice", type=int, choices=[0, 1, 2, 3])
    cfg_set.add_argument("--last-file")
    cfg_set.add_argument("--add-recent", action="append")
    cfg_set.add_argument("--clear-recent", action="store_true")
    cfg_set.add_argument("--window", help="Fenstergeometrie x,y,width,height")
    cfg_set.add_argument("--window-state", choices=["normal", "max", "maximized", "min", "minimized"])
    cfg_set.add_argument("--json", action="store_true")

    lang_list = sub.add_parser("lang-list", help="portierte alte UI-Sprachen anzeigen")
    lang_list.add_argument("--json", action="store_true")

    lang_get = sub.add_parser("lang-get", help="alten lang_keys-Text übersetzen")
    lang_get.add_argument("key", help="Name wie Strip1_1 oder numerischer Index")
    lang_get.add_argument("--language", default="de")
    lang_get.add_argument("--all", action="store_true", help="alle Sprachen für diesen Schlüssel anzeigen")
    lang_get.add_argument("--json", action="store_true")

    lang_dump = sub.add_parser("lang-dump", help="portierte alte Sprachtexte ausgeben")
    lang_dump.add_argument("--language", default="de")
    lang_dump.add_argument("--all", action="store_true", help="alle Sprachen tabellarisch ausgeben")
    lang_dump.add_argument("--json", action="store_true")

    shortcuts = sub.add_parser("shortcuts", help="alte Notizen.NET-Tastenkürzel anzeigen")
    shortcuts.add_argument("--json", action="store_true")

    about = sub.add_parser("about", help="portierten alten Hilfe-/Info-Text anzeigen")
    about.add_argument("--language", default="de")
    about.add_argument("--json", action="store_true")

    feedback = sub.add_parser("feedback-draft", help="Feedback wie im alten Dialog als gzip/UTF-16-Datei vorbereiten, ohne es hochzuladen")
    feedback.add_argument("output")
    source_group = feedback.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--text")
    source_group.add_argument("--input")

    cfg_read_legacy = sub.add_parser("config-read-legacy", help="alte notizen.config.xml lesen und ausgeben")
    cfg_read_legacy.add_argument("path")

    cfg_import = sub.add_parser("config-import-legacy", help="alte notizen.config.xml in die neue JSON-Konfiguration übernehmen")
    cfg_import.add_argument("path", nargs="?")

    cfg_export = sub.add_parser("config-export-legacy", help="neue Konfiguration als alte XML-Struktur schreiben")
    cfg_export.add_argument("output")

    cfg_ftp = sub.add_parser("config-set-ftp", help="FTP/FTPS-Standardziel in der Port-Konfiguration setzen")
    cfg_ftp.add_argument("--host")
    cfg_ftp.add_argument("--user")
    cfg_ftp.add_argument("--password")
    cfg_ftp.add_argument("--path")
    tls_group = cfg_ftp.add_mutually_exclusive_group()
    tls_group.add_argument("--tls", action="store_true")
    tls_group.add_argument("--no-tls", action="store_true")

    auto = sub.add_parser("autostart", help="Autostart-Eintrag anzeigen/setzen")
    group = auto.add_mutually_exclusive_group()
    group.add_argument("--enable", action="store_true")
    group.add_argument("--disable", action="store_true")

    alarm_add = sub.add_parser("alarm-add", help="Wecker/Erinnerung anlegen oder ersetzen")
    alarm_add.add_argument("--name", required=True)
    alarm_add.add_argument("--at", required=True, help="z.B. 2026-04-27 09:30 oder 27.04.2026 09:30")
    alarm_add.add_argument("--repeat", default="none", help="none/daily/weekly/monthly/yearly oder deutsch: einmal/tage/wochen/monate/jahre")
    alarm_add.add_argument("--interval", type=int, default=1)
    alarm_add.add_argument("--weekday", action="append", help="für weekly: mo,di,mi,do,fr,sa,so; mehrfach oder kommagetrennt")
    alarm_add.add_argument("--message", default="")
    alarm_add.add_argument("--note-title", default="")
    alarm_add.add_argument("--inactive", action="store_true")

    sub.add_parser("alarm-list", help="gespeicherte Wecker anzeigen")
    sub.add_parser("alarm-next", help="nächsten aktiven Wecker anzeigen")
    alarm_remove = sub.add_parser("alarm-remove", help="Wecker entfernen")
    alarm_remove.add_argument("--name", required=True)

    alarm_due = sub.add_parser("alarm-due", help="fällige Wecker im aktuellen Zeitfenster prüfen")
    alarm_due.add_argument("--now", help="Test-/Vergleichszeit, z.B. 2026-04-27 09:30")
    alarm_due.add_argument("--grace-seconds", type=int, default=60, help="Rückblickfenster für fällige Termine")
    alarm_due.add_argument("--notify", action="store_true", help="Desktop-Benachrichtigung auslösen")
    alarm_due.add_argument("--dry-run", action="store_true", help="Benachrichtigung nur simulieren")

    alarm_watch = sub.add_parser("alarm-watch", help="Wecker-Schleife starten und bei Fälligkeit melden")
    alarm_watch.add_argument("--poll-seconds", type=float, default=30)
    alarm_watch.add_argument("--grace-seconds", type=int, default=60)
    alarm_watch.add_argument("--once", action="store_true", help="nur einmal prüfen und beenden")
    alarm_watch.add_argument("--no-notify", action="store_true", help="nur in stdout ausgeben")
    alarm_watch.add_argument("--dry-run", action="store_true", help="Benachrichtigung nur simulieren")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "tree":
            _print_tree(args.file, args.password, include_collapsed=not args.visible_only)
        elif args.cmd == "export-txt":
            _export_txt(args.file, args.output, args.password, args.title, args.numbered)
        elif args.cmd == "export-rtf":
            _export_rtf(args.file, args.output, args.password, args.title, args.numbered)
        elif args.cmd == "export-html":
            _export_html(args.file, args.output, args.password, args.title)
        elif args.cmd == "export-md":
            _export_md(args.file, args.output, args.password, args.title)
        elif args.cmd == "export-json":
            _export_json(args.file, args.output, args.password, args.title)
        elif args.cmd == "export-alx":
            _export_alx(args.file, args.output, args.password, args.title, args.new_password, args.keep_password)
        elif args.cmd == "export-opml":
            _export_opml(args.file, args.output, args.password, args.title, args.plain)
        elif args.cmd == "export-note-rtf":
            _export_note_rtf(args.file, args.output, args.password, args.title)
        elif args.cmd == "extract-images":
            _extract_images(args.file, args.output_dir, args.password, args.title)
        elif args.cmd == "export-sticky-html":
            _export_sticky_html(args.file, args.output, args.password, args.all)
        elif args.cmd == "change-password":
            _change_password(args.file, args.output, args.old_password, args.new_password)
        elif args.cmd == "dump-xml":
            _dump_xml(args.file, args.output, args.password)
        elif args.cmd == "pack-xml":
            _pack_xml(args.xml_file, args.output, args.password)
        elif args.cmd == "stats":
            _stats(args.file, args.password)
        elif args.cmd == "search":
            _search(args.file, args.needle, args.password, args.case_sensitive, args.whole_words, args.details, args.json, args.context, args.title)
        elif args.cmd == "search-occurrences":
            _search_occurrences(args.file, args.needle, args.password, args.case_sensitive, args.whole_words, args.title, args.context, args.max_hits, args.json)
        elif args.cmd == "replace":
            _replace(args.file, args.output, args.needle, args.replacement, args.password, args.new_password, args.case_sensitive, args.whole_words, args.title, args.titles_only, args.text_only)
        elif args.cmd == "validate":
            _validate(args.file, args.password, args.json)
        elif args.cmd == "recent":
            _recent(args.json)
        elif args.cmd == "color-palette":
            _color_palette(args.json)
        elif args.cmd == "color-note":
            _color_note(args.file, args.output, args.title, args.password, args.new_password, args.bg_color, args.fg_color, args.bg_name, args.fg_name, args.random_bg, args.random_fg, args.random_index, args.clear, args.clear_bg, args.clear_fg, args.show)
        elif args.cmd == "sticky-list":
            _sticky_list(args.file, args.password, args.all, args.json)
        elif args.cmd == "sticky-run":
            _sticky_run(args.file, args.password, args.output, args.new_password, args.all, args.readonly)
        elif args.cmd == "set-note":
            _set_note(args.file, args.output, args.title, args.input, args.password, args.new_password, args.rtf)
        elif args.cmd == "import-json":
            _import_json(args.file, args.output, args.title, args.input, args.where, args.password, args.new_password)
        elif args.cmd == "import-opml":
            _import_opml(args.file, args.output, args.title, args.input, args.where, args.password, args.new_password)
        elif args.cmd == "import-file":
            _import_file(args.file, args.output, args.title, args.input, args.where, args.password, args.input_password, args.new_password)
        elif args.cmd == "insert-image":
            _insert_image(args.file, args.output, args.title, args.image, args.password, args.new_password, args.width_twips, args.height_twips)
        elif args.cmd == "append-date":
            _append_date(args.file, args.output, args.title, args.password, args.new_password)
        elif args.cmd == "append-bullet":
            _append_bullet(args.file, args.output, args.title, args.password, args.new_password)
        elif args.cmd == "format-note":
            _format_note(
                args.file,
                args.output,
                args.title,
                args.password,
                args.new_password,
                args.font_family,
                args.font_size,
                args.bold,
                args.italic,
                args.underline,
                args.strike,
                args.fg_color,
                args.bg_color,
            )
        elif args.cmd == "style-note":
            _toolbar_style(args.file, args.output, args.title, args.password, args.new_password, args.style, args.font_family, args.font_size, args.fg_color, args.bg_color, args.show)
        elif args.cmd == "font-list":
            _font_list(args.json, args.contains, args.limit)
        elif args.cmd == "font-size":
            _font_size(args.file, args.output, args.title, args.password, args.new_password, args.bigger, args.smaller, args.set_size, args.step)
        elif args.cmd == "sticky":
            _sticky(args.file, args.output, args.title, args.password, args.new_password, args.show, args.hide, args.clear, args.autosize, args.x, args.y, args.width, args.height, args.opacity, args.argb)
        elif args.cmd == "expand-state":
            state = "expanded" if args.expanded else "collapsed" if args.collapsed else "toggle"
            _expand_state(args.file, args.output, args.password, args.new_password, args.title, state, args.all)
        elif args.cmd == "rename":
            _rename(args.file, args.output, args.title, args.new_title, args.password, args.new_password)
        elif args.cmd == "add-note":
            _add_note(args.file, args.output, args.title, args.new_title, args.text, args.where, args.password, args.new_password)
        elif args.cmd == "delete-note":
            _delete_note(args.file, args.output, args.title, args.password, args.new_password)
        elif args.cmd == "move":
            _move(args.file, args.output, args.title, args.action, args.password, args.new_password)
        elif args.cmd == "move-under":
            _move_under(args.file, args.output, args.title, args.target_title, args.password, args.new_password)
        elif args.cmd == "duplicate":
            _duplicate(args.file, args.output, args.title, args.password, args.new_password)
        elif args.cmd == "combine-subtree":
            _combine_subtree(args.file, args.output, args.title, args.new_title, args.password, args.new_password, not args.plain, args.attach_to_selected)
        elif args.cmd == "backup-list":
            _backup_list(args.file, args.json)
        elif args.cmd == "backup-restore":
            _backup_restore(args.backup, args.target, args.no_backup_current)
        elif args.cmd == "config-show":
            _config_show()
        elif args.cmd == "config-path":
            _config_path()
        elif args.cmd == "config-set":
            _config_set(
                backup_count=args.backup_count,
                autosave_seconds=args.autosave_seconds,
                language=args.language,
                autorun=True if args.autorun else False if args.no_autorun else None,
                autorun_minimized=True if args.autorun_minimized else False if args.no_autorun_minimized else None,
                show_in_taskbar=True if args.show_in_taskbar else False if args.hide_in_taskbar else None,
                show_desknote_borders=True if args.show_desknote_borders else False if args.hide_desknote_borders else None,
                scrollbars_choice=args.scrollbars_choice,
                last_file=args.last_file,
                add_recent=args.add_recent,
                clear_recent=args.clear_recent,
                window=args.window,
                window_state=args.window_state,
                as_json=args.json,
            )
        elif args.cmd == "lang-list":
            _lang_list(args.json)
        elif args.cmd == "lang-get":
            _lang_get(args.key, args.language, args.all, args.json)
        elif args.cmd == "lang-dump":
            _lang_dump(args.language, args.all, args.json)
        elif args.cmd == "shortcuts":
            _shortcuts(args.json)
        elif args.cmd == "about":
            _about(args.language, args.json)
        elif args.cmd == "feedback-draft":
            _feedback_draft(args.output, args.text, args.input)
        elif args.cmd == "config-read-legacy":
            _config_read_legacy(args.path)
        elif args.cmd == "config-import-legacy":
            _config_import_legacy(args.path)
        elif args.cmd == "config-export-legacy":
            _config_export_legacy(args.output)
        elif args.cmd == "config-set-ftp":
            _config_set_ftp(args.host, args.user, args.password, args.path, True if args.tls else False if args.no_tls else None)
        elif args.cmd == "autostart":
            _autostart(True if args.enable else False if args.disable else None)
        elif args.cmd == "alarm-add":
            _alarm_add(args.name, args.at, args.repeat, args.interval, args.weekday, args.message, args.note_title, args.inactive)
        elif args.cmd == "alarm-list":
            _alarm_list()
        elif args.cmd == "alarm-next":
            _alarm_next()
        elif args.cmd == "alarm-due":
            _alarm_due(args.now, args.grace_seconds, args.notify, args.dry_run)
        elif args.cmd == "alarm-watch":
            _alarm_watch(args.poll_seconds, args.grace_seconds, args.once, not args.no_notify, args.dry_run)
        elif args.cmd == "alarm-remove":
            _alarm_remove(args.name)
        else:  # pragma: no cover
            parser.error(f"unbekannter Befehl: {args.cmd}")
    except (NotizenFileError, ValueError, RuntimeError, KeyError, FeedbackError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
