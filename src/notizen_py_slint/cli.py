from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .autostart import autostart_status, sync_autostart
from .alarm import AlarmRule, add_or_replace_alarm, load_alarms, next_alarm, parse_weekdays, remove_alarm
from .config import AppConfig
from .legacy_config import import_legacy_config, load_legacy_config, write_legacy_like_config
from .model import Note, NoteDocument, parse_int_or_hex
from .remote import load_uri, save_uri
from .rtf import restyle_rtf_as_plain, text_to_rtf
from .storage import (
    NotizenFileError,
    append_bullet_into_note,
    append_current_date_into_note,
    export_document_images,
    export_html,
    export_note_images,
    export_note_rtf,
    export_rtf,
    export_text,
    import_rtf_into_note,
    import_text_into_note,
    insert_image_into_note,
    document_to_xml_bytes,
    load_document_from_bytes,
)


def _select_by_title(doc: NoteDocument, title: str | None) -> None:
    if not title:
        return
    note = doc.first_note_by_title(title)
    if note is None:
        raise NotizenFileError(f"Keine Notiz mit Titel gefunden: {title}")
    doc.select(note)


def _note_by_title(doc: NoteDocument, title: str) -> Note:
    note = doc.first_note_by_title(title)
    if note is None:
        raise NotizenFileError(f"Keine Notiz mit Titel gefunden: {title}")
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


def _search(file: str, needle: str, password: str | None, case_sensitive: bool, whole_words: bool) -> None:
    doc = load_uri(file, password=password)
    hits = doc.find_all(needle, case_sensitive=case_sensitive, whole_words=whole_words)
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


def _config_show() -> None:
    config = AppConfig.load()
    print(json.dumps(config.__dict__ if hasattr(config, "__dict__") else _slots_dict(config), indent=2, ensure_ascii=False))


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
    _add_password_arg(search)

    set_note = sub.add_parser("set-note", help="Text/RTF einer Notiz ersetzen und speichern")
    set_note.add_argument("file")
    set_note.add_argument("output")
    set_note.add_argument("--title", required=True)
    set_note.add_argument("--input", required=True)
    set_note.add_argument("--rtf", action="store_true")
    _add_new_password_arg(set_note)
    _add_password_arg(set_note)

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

    cfg_show = sub.add_parser("config-show", help="Port-Konfiguration anzeigen")

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
        elif args.cmd == "export-note-rtf":
            _export_note_rtf(args.file, args.output, args.password, args.title)
        elif args.cmd == "extract-images":
            _extract_images(args.file, args.output_dir, args.password, args.title)
        elif args.cmd == "change-password":
            _change_password(args.file, args.output, args.old_password, args.new_password)
        elif args.cmd == "dump-xml":
            _dump_xml(args.file, args.output, args.password)
        elif args.cmd == "pack-xml":
            _pack_xml(args.xml_file, args.output, args.password)
        elif args.cmd == "stats":
            _stats(args.file, args.password)
        elif args.cmd == "search":
            _search(args.file, args.needle, args.password, args.case_sensitive, args.whole_words)
        elif args.cmd == "set-note":
            _set_note(args.file, args.output, args.title, args.input, args.password, args.new_password, args.rtf)
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
        elif args.cmd == "config-show":
            _config_show()
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
        elif args.cmd == "alarm-remove":
            _alarm_remove(args.name)
        else:  # pragma: no cover
            parser.error(f"unbekannter Befehl: {args.cmd}")
    except (NotizenFileError, ValueError, RuntimeError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
