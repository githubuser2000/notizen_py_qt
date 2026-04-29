from __future__ import annotations

import io
import json
import os
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
import unittest

from notizen_py_slint.alarm import AlarmRule, add_months, add_or_replace_alarm, alarm_message, due_alarms, load_alarms, next_alarm, parse_weekdays, remove_alarm
from notizen_py_slint.des_compat import DES, decrypt_notizen_payload, encrypt_notizen_payload
from notizen_py_slint.feedback import feedback_gzip_payload, read_feedback_gzip
from notizen_py_slint.fonts import list_system_fonts
from notizen_py_slint.intellibit import document_to_notes_doc_xml
from notizen_py_slint.opml import document_to_opml, opml_to_note
from notizen_py_slint.paths import default_file_path, default_paths
from notizen_py_slint.passwords import legacy_password_info, normalize_legacy_password
from notizen_py_slint.repair import repair_document
from notizen_py_slint.app import NotizenSlintApp, _normalize_legacy_argv
from notizen_py_slint.cli import main as cli_main
from notizen_py_slint.config import AppConfig
from notizen_py_slint.context_menus import context_actions_payload, format_context_actions, sticky_opacity_payload
from notizen_py_slint.clipboard import clipboard_info, entry_from_clipboard_text, note_to_clipboard_text, read_clipboard_file, write_clipboard_file
from notizen_py_slint.compat import analyze_document, analyze_file
from notizen_py_slint.legacy_colors import argb_to_signed, legacy_color_by_name, legacy_light_color, legacy_palette_table
from notizen_py_slint.legacy_sticky import legacy_opacity_choices, opacity_from_legacy_choice
from notizen_py_slint.legacy_config import load_legacy_config, write_legacy_like_config
from notizen_py_slint.model import Note, NoteDocument, StickyWindow, argb_to_hex, parse_int_or_hex
from notizen_py_slint.notify import notify
from notizen_py_slint.shortcuts import shortcut_manifest
from notizen_py_slint.sticky_runtime import sticky_window_specs
from notizen_py_slint.remote import parse_ftp_url
from notizen_py_slint.translations import LEGACY_KEYS, normalize_language, translate, translation_table
from notizen_py_slint.rtf import append_picture_to_rtf, change_rtf_font_size, detect_rtf_style, extract_pictures, first_rtf_font_size, is_rtf, normalize_text_range, replace_rtf_text_range, restyle_rtf_as_plain, restyle_rtf_with_defaults, rtf_to_html_fragment, rtf_to_text, set_rtf_font_size, style_rtf_text_range, text_to_rtf
from notizen_py_slint.storage import (
    autosize_sticky,
    change_note_font_size,
    combine_subtree_to_new_note,
    export_document_images,
    document_to_xml_bytes,
    export_html,
    export_legacy_text,
    export_alx,
    export_json,
    export_markdown,
    export_opml,
    export_notes_doc,
    export_sticky_html,
    export_unity_rtf,
    load_document,
    load_document_from_bytes,
    save_document,
    save_document_to_bytes,
    import_json_into_document,
    import_opml_into_document,
    insert_image_into_note,
    insert_text_into_note,
    append_bullet_into_note,
    apply_toolbar_style_to_note,
    delete_note_text_range,
    set_note_font_size,
    style_note_text_range,
    list_backups,
    read_raw_xml,
    restore_backup,
    write_raw_xml,
)


FIXTURE = Path(__file__).parent / "fixtures" / "test.alx"


class DesCompatTests(unittest.TestCase):
    def test_standard_des_known_vector(self) -> None:
        key = bytes.fromhex("133457799BBCDFF1")
        plain = bytes.fromhex("0123456789ABCDEF")
        cipher = bytes.fromhex("85E813540F0AB405")
        des = DES(key)
        self.assertEqual(des.encrypt_block(plain), cipher)
        self.assertEqual(des.decrypt_block(cipher), plain)

    def test_notizen_cascade_roundtrip(self) -> None:
        payload = b"\x1f\x8b fake gzip payload in test"
        password = "0123456789abcdefghijklmn"
        encrypted = encrypt_notizen_payload(payload, password)
        self.assertNotEqual(encrypted, payload)
        self.assertEqual(decrypt_notizen_payload(encrypted, password), payload)


class RtfTests(unittest.TestCase):
    def test_plain_text_roundtrip(self) -> None:
        text = "Hallo Welt\nZweite Zeile — Umlaut ä"
        self.assertEqual(rtf_to_text(text_to_rtf(text)), text)

    def test_plain_text_range_helpers(self) -> None:
        text = "Hallo Welt"
        self.assertEqual(normalize_text_range(text, -3, 99).as_dict(), {"start": 0, "end": 10, "length": 10})
        replaced = replace_rtf_text_range(text_to_rtf(text, font_family="Arial", font_size_half_points=20), 6, 4, "Mars")
        self.assertEqual(rtf_to_text(replaced), "Hallo Mars")
        style = detect_rtf_style(replaced)
        self.assertEqual(style.font_family, "Arial")
        self.assertEqual(style.font_size_half_points, 20)

    def test_style_rtf_text_range_formats_selected_text(self) -> None:
        styled = style_rtf_text_range(text_to_rtf("Hallo Welt"), 6, 4, bold=True, font_size_half_points=28)
        self.assertEqual(rtf_to_text(styled), "Hallo Welt")
        self.assertIn(r"\b", styled)
        self.assertIn(r"\fs28", styled)
        self.assertIn("Welt", styled)

    def test_rtf_detection(self) -> None:
        self.assertTrue(is_rtf(text_to_rtf("x")))
        self.assertFalse(is_rtf("normaler Text"))

    def test_unicode_surrogate_roundtrip(self) -> None:
        text = "Emoji 😀 und Musik 𝄞"
        self.assertEqual(rtf_to_text(text_to_rtf(text)), text)

    def test_restyle_whole_note(self) -> None:
        styled = restyle_rtf_as_plain(
            text_to_rtf("Hallo"),
            font_family="Arial",
            font_size_half_points=24,
            bold=True,
            italic=True,
            underline=True,
            fg_color=0xFF112233,
            bg_color=0xFF445566,
        )
        self.assertIn(r"\b", styled)
        self.assertIn(r"\i", styled)
        self.assertIn(r"\ul", styled)
        self.assertIn(r"\cf1", styled)
        self.assertIn(r"\highlight2", styled)
        self.assertEqual(rtf_to_text(styled), "Hallo")

    def test_detect_and_restyle_with_defaults(self) -> None:
        rtf = text_to_rtf("Hallo", font_family="Arial", font_size_half_points=22, bold=True)
        detected = detect_rtf_style(rtf)
        self.assertEqual(detected.font_family, "Arial")
        self.assertEqual(detected.font_size_half_points, 22)
        self.assertTrue(detected.bold)
        changed = restyle_rtf_with_defaults(rtf, italic=True)
        after = detect_rtf_style(changed)
        self.assertTrue(after.bold)
        self.assertTrue(after.italic)
        self.assertEqual(rtf_to_text(changed), "Hallo")

    def test_font_size_change_preserves_rtf(self) -> None:
        rtf = text_to_rtf("Hallo", font_size_half_points=18)
        bigger = change_rtf_font_size(rtf, 2)
        self.assertEqual(first_rtf_font_size(bigger), 20)
        smaller = change_rtf_font_size(bigger, -4)
        self.assertEqual(first_rtf_font_size(smaller), 16)
        direct = set_rtf_font_size("plain", 24)
        self.assertTrue(is_rtf(direct))
        self.assertIn(r"\fs24", direct)
        self.assertEqual(rtf_to_text(direct), "plain")

    def test_extract_rtf_picture(self) -> None:
        sample = r"{\rtf1{\pict\pngblip\picwgoal10\pichgoal20 89504E470D0A1A0A}}"
        pictures = extract_pictures(sample)
        self.assertEqual(len(pictures), 1)
        self.assertEqual(pictures[0].extension, "png")
        self.assertEqual(pictures[0].width_twips, 10)
        self.assertEqual(pictures[0].height_twips, 20)
        self.assertEqual(pictures[0].data, bytes.fromhex("89504E470D0A1A0A"))

    def test_append_picture_to_rtf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "tiny.png"
            image.write_bytes(bytes.fromhex("89504E470D0A1A0A"))
            rtf = append_picture_to_rtf(text_to_rtf("Hallo"), image)
        self.assertEqual(rtf_to_text(rtf), "Hallo")
        pictures = extract_pictures(rtf)
        self.assertEqual(len(pictures), 1)
        self.assertEqual(pictures[0].data, bytes.fromhex("89504E470D0A1A0A"))

    def test_rtf_to_html_fragment_embeds_text_and_images(self) -> None:
        rtf = r"{\rtf1 <&>{\pict\pngblip 89504E470D0A1A0A}}"
        html = rtf_to_html_fragment(rtf)
        self.assertIn("&lt;&amp;&gt;", html)
        self.assertIn("data:image/png;base64,", html)


class StorageTests(unittest.TestCase):
    def test_load_original_sample(self) -> None:
        doc = load_document(FIXTURE)
        self.assertEqual(doc.root.title, "Notes")
        self.assertEqual(sum(1 for _ in doc.iter_notes()), 65)
        self.assertEqual(doc.root.text, "test")

    def test_save_reload_plain(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("Text")), selected_id=None)
        child = doc.root.add_child(Note("Kind", text_to_rtf("Mehr Text")))
        doc.selected_id = child.note_id
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plain.alx"
            save_document(doc, path=path, backup_count=0)
            loaded = load_document(path)
        self.assertEqual(loaded.root.title, "Root")
        self.assertEqual(loaded.root.children[0].title, "Kind")
        self.assertEqual(loaded.root.children[0].text, "Mehr Text")

    def test_backup_list_and_restore(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("Version 1")), selected_id=None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plain.alx"
            save_document(doc, path=path, backup_count=0)
            doc.root.set_text("Version 2")
            save_document(doc, path=path, backup_count=3)
            backups = list_backups(path)
            self.assertEqual(len(backups), 1)
            restored = Path(tmp) / "restored.alx"
            restore_backup(backups[0].path, target=restored, backup_current=False)
            self.assertEqual(load_document(restored).root.text, "Version 1")

    def test_save_reload_encrypted(self) -> None:
        doc = NoteDocument(root=Note("Secret", text_to_rtf("Geheim")), selected_id=None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "secret.alx"
            save_document(doc, path=path, password="abcdefghijklmnopqrstuvwx", backup_count=0)
            loaded = load_document(path, password="abcdefghijklmnopqrstuvwx")
        self.assertEqual(loaded.root.title, "Secret")
        self.assertEqual(loaded.root.text, "Geheim")

    def test_save_load_from_bytes_keeps_metadata(self) -> None:
        root = Note("Root", text_to_rtf("Text"), bg_color=parse_int_or_hex("#FFEEDDCC"), fg_color=-16777216)
        child = root.add_child(Note("Sticky", text_to_rtf("Pin"), sticky=StickyWindow(True, 1, 2, 300, 120, 0.75, -1)))
        doc = NoteDocument(root=root, selected_id=child.note_id)
        payload = save_document_to_bytes(doc)
        loaded = load_document_from_bytes(payload, source="memory")
        self.assertEqual(argb_to_hex(loaded.root.bg_color), "#FFEEDDCC")
        self.assertEqual(loaded.root.children[0].sticky.width, 300)  # type: ignore[union-attr]
        self.assertTrue(loaded.root.children[0].sticky.visible)  # type: ignore[union-attr]

    def test_xml_writes_signed_argb_for_legacy_winforms(self) -> None:
        root = Note("Root", text_to_rtf("Text"), bg_color=0xFFEEDDCC, fg_color=0xFF112233)
        root.sticky = StickyWindow(True, 1, 2, 300, 120, 0.75, 0xFFFF00FF)
        doc = NoteDocument(root=root, selected_id=root.note_id)
        xml = document_to_xml_bytes(doc).decode("utf-16")
        self.assertIn(f'bgcolor="{argb_to_signed(0xFFEEDDCC)}"', xml)
        self.assertIn(f'fgcolor="{argb_to_signed(0xFF112233)}"', xml)
        self.assertIn(f'argb="{argb_to_signed(0xFFFF00FF)}"', xml)
        loaded = load_document_from_bytes(save_document_to_bytes(doc), source="memory")
        self.assertEqual(argb_to_hex(loaded.root.bg_color), "#FFEEDDCC")

    def test_sticky_runtime_specs_normalize_windows(self) -> None:
        root = Note("Root", text_to_rtf("Text"), bg_color=legacy_light_color(4).signed_argb, fg_color=-16777216)
        sticky_note = root.add_child(Note("Pin", text_to_rtf("Pin Text"), sticky=StickyWindow(True, 12, 34, 200, 100, 0.5, None)))
        doc = NoteDocument(root=root, selected_id=sticky_note.note_id)
        specs = sticky_window_specs(doc)
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].title, "Pin")
        self.assertEqual(specs[0].x, 12)
        self.assertIn("Pin Text", specs[0].text)

    def test_toolbar_style_helper_formats_whole_note(self) -> None:
        note = Note("Root", text_to_rtf("Toolbar", font_family="Arial", font_size_half_points=20))
        apply_toolbar_style_to_note(note, "bold")
        style = detect_rtf_style(note.rtf)
        self.assertTrue(style.bold)
        self.assertFalse(style.italic)
        self.assertEqual(style.font_family, "Arial")
        apply_toolbar_style_to_note(note, "regular")
        style = detect_rtf_style(note.rtf)
        self.assertFalse(style.bold)
        self.assertEqual(rtf_to_text(note.rtf), "Toolbar")

    def test_note_range_helpers(self) -> None:
        note = Note("Root", text_to_rtf("Hallo Welt", font_family="Arial", font_size_half_points=20))
        insert_text_into_note(note, "schöne ", 6)
        self.assertEqual(note.text, "Hallo schöne Welt")
        delete_note_text_range(note, 6, 7)
        self.assertEqual(note.text, "Hallo Welt")
        style_note_text_range(note, 6, 4, style="bold", font_size_half_points=24)
        self.assertEqual(note.text, "Hallo Welt")
        self.assertIn(r"\b", note.rtf)
        self.assertIn(r"\fs24", note.rtf)

    def test_saved_xml_has_single_root_note(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("Text")), selected_id=None)
        doc.root.add_child(Note("Kind", text_to_rtf("Mehr")))
        xml = document_to_xml_bytes(doc).decode("utf-16")
        self.assertEqual(xml.count("<Notiz"), 2)
        loaded = load_document_from_bytes(save_document_to_bytes(doc), source="memory")
        self.assertEqual(sum(1 for _ in loaded.iter_notes()), 2)
        self.assertEqual([child.title for child in loaded.root.children], ["Kind"])

    def test_plain_xml_load_and_save(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("XML Text")), selected_id=None)
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "notes.xml"
            save_document(doc, xml_path, backup_count=0)
            self.assertTrue(xml_path.read_bytes().startswith(b"\xff\xfe"))
            loaded = load_document(xml_path)
        self.assertEqual(loaded.root.title, "Root")
        self.assertEqual(loaded.root.text, "XML Text")

    def test_raw_xml_read_write_roundtrip(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("roh")), selected_id=None)
        with tempfile.TemporaryDirectory() as tmp:
            alx = Path(tmp) / "a.alx"
            xml = Path(tmp) / "a.xml"
            packed = Path(tmp) / "packed.alx"
            save_document(doc, alx, backup_count=0)
            raw_xml = read_raw_xml(alx)
            self.assertIn("notizen-alx2", raw_xml)
            xml.write_text(raw_xml, encoding="utf-8")
            write_raw_xml(xml.read_bytes(), packed)
            loaded = load_document(packed)
        self.assertEqual(loaded.root.text, "roh")

    def test_html_export_escapes_text(self) -> None:
        root = Note("Root <tag>", text_to_rtf("Eins & Zwei"))
        doc = NoteDocument(root=root)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.html"
            export_html(doc, path)
            html = path.read_text(encoding="utf-8")
        self.assertIn("Root &lt;tag&gt;", html)
        self.assertIn("Eins &amp; Zwei", html)

    def test_markdown_export_and_combine_subtree(self) -> None:
        root = Note("Root", text_to_rtf("root text"))
        child = root.add_child(Note("Kind", text_to_rtf("kind text")))
        doc = NoteDocument(root=root, selected_id=child.note_id)
        combined = combine_subtree_to_new_note(doc, start=child, title="Einheit")
        self.assertEqual(combined.title, "Einheit")
        self.assertIn("Kind", combined.text)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            export_markdown(doc, path)
            md = path.read_text(encoding="utf-8")
        self.assertIn("# Root", md)
        self.assertIn("## Root", md)
        self.assertIn("### Kind", md)

    def test_json_export_import_subtree(self) -> None:
        root = Note("Root", text_to_rtf("root text"))
        child = root.add_child(Note("Kind", text_to_rtf("kind text"), sticky=StickyWindow(True, 1, 2, 3, 4, 0.5, -1)))
        doc = NoteDocument(root=root, selected_id=child.note_id)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "subtree.json"
            export_json(doc, path, start=child)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["note"]["text"], "kind text")
            target_doc = NoteDocument(root=Note("Target", text_to_rtf("")))
            imported = import_json_into_document(target_doc, path, target=target_doc.root)
            plain_path = Path(tmp) / "plain.json"
            plain_path.write_text(json.dumps({"title": "Plain", "text": "Plain Text", "children": []}), encoding="utf-8")
            plain = import_json_into_document(target_doc, plain_path, target=target_doc.root)
        self.assertEqual(imported.title, "Kind")
        self.assertEqual(imported.text, "kind text")
        self.assertIsNotNone(imported.sticky)
        self.assertEqual(imported.sticky.x, 1)  # type: ignore[union-attr]
        self.assertEqual(plain.text, "Plain Text")

    def test_document_image_export(self) -> None:
        png = "89504E470D0A1A0A"
        root = Note("Root", r"{\rtf1{\pict\pngblip " + png + "}}")
        doc = NoteDocument(root=root)
        with tempfile.TemporaryDirectory() as tmp:
            paths = export_document_images(doc, tmp)
            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].name.endswith(".png"))
            self.assertEqual(paths[0].read_bytes(), bytes.fromhex(png))

    def test_insert_image_and_bullet_into_note(self) -> None:
        note = Note("Root", text_to_rtf("Text"))
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "tiny.png"
            image.write_bytes(bytes.fromhex("89504E470D0A1A0A"))
            insert_image_into_note(note, image)
        append_bullet_into_note(note)
        self.assertEqual(len(extract_pictures(note.rtf)), 1)
        self.assertIn("•", rtf_to_text(note.rtf))

    def test_font_size_helpers_on_note(self) -> None:
        note = Note("Root", text_to_rtf("Text", font_size_half_points=18))
        change_note_font_size(note, 2)
        self.assertIn(r"\fs20", note.rtf)
        set_note_font_size(note, 26)
        self.assertIn(r"\fs26", note.rtf)
        self.assertEqual(note.text, "Text")

    def test_sticky_autosize_and_html_export(self) -> None:
        root = Note("Root", text_to_rtf(""))
        sticky_note = root.add_child(Note("Merkzettel", text_to_rtf("Eine lange Zeile für Autogröße\nZweite Zeile")))
        sticky_note.sticky = StickyWindow(True, 12, 34, None, None, None, parse_int_or_hex("#FFFFFF99"))
        doc = NoteDocument(root=root, selected_id=sticky_note.note_id)
        sticky = autosize_sticky(sticky_note)
        self.assertGreaterEqual(sticky.width or 0, 180)
        self.assertGreaterEqual(sticky.height or 0, 120)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sticky.html"
            export_sticky_html(doc, path)
            html = path.read_text(encoding="utf-8")
        self.assertIn("Merkzettel", html)
        self.assertIn("position:absolute", html)
        self.assertIn("#FFFF99", html)


class ModelOperationTests(unittest.TestCase):
    def _doc(self) -> NoteDocument:
        root = Note("Root", text_to_rtf("root"))
        a = root.add_child(Note("A", text_to_rtf("eins")))
        b = root.add_child(Note("B", text_to_rtf("zwei")))
        a.add_child(Note("A1", text_to_rtf("kind")))
        return NoteDocument(root=root, selected_id=b.note_id)

    def test_move_indent_outdent_duplicate(self) -> None:
        doc = self._doc()
        self.assertTrue(doc.move_selected_up())
        self.assertEqual([child.title for child in doc.root.children], ["B", "A"])
        self.assertTrue(doc.move_selected_down())
        self.assertEqual([child.title for child in doc.root.children], ["A", "B"])
        self.assertTrue(doc.indent_selected())
        self.assertEqual(doc.root.children[0].children[-1].title, "B")
        self.assertTrue(doc.outdent_selected())
        self.assertEqual([child.title for child in doc.root.children], ["A", "B"])
        clone = doc.duplicate_selected()
        self.assertIsNotNone(clone)
        self.assertEqual([child.title for child in doc.root.children], ["A", "B", "B"])

    def test_search_options_and_stats(self) -> None:
        doc = self._doc()
        self.assertEqual(len(doc.find_all("zwei")), 1)
        self.assertEqual(len(doc.find_all("wei", whole_words=True)), 0)
        details = doc.find_detailed("A", context=3)
        self.assertTrue(any(hit.title_matches for hit in details))
        self.assertTrue(any(hit.snippets for hit in details))
        stats = doc.stats()
        self.assertEqual(stats.notes, 4)
        self.assertEqual(stats.max_depth, 2)

    def test_search_occurrences_match_old_selection_start(self) -> None:
        root = Note("Root", text_to_rtf("Alpha Beta Alpha"))
        root.add_child(Note("Alpha Child", text_to_rtf("child alpha")))
        doc = NoteDocument(root=root)
        hits = doc.find_occurrences("Alpha", case_sensitive=False, context=5)
        self.assertEqual(hits[0].field, "text")
        self.assertEqual((hits[0].start, hits[0].end), (0, 5))
        self.assertTrue(any(hit.field == "title" and hit.note.title == "Alpha Child" for hit in hits))
        self.assertEqual(doc.find_occurrences("Alpha", limit=1)[0].as_dict()["length"], 5)

    def test_path_selection_disambiguates_duplicate_titles(self) -> None:
        root = Note("Root", text_to_rtf(""))
        first = root.add_child(Note("Projekt", text_to_rtf("eins")))
        second = root.add_child(Note("Projekt", text_to_rtf("zwei")))
        first_todo = first.add_child(Note("Todo", text_to_rtf("falsch")))
        second_todo = second.add_child(Note("Todo", text_to_rtf("richtig")))
        doc = NoteDocument(root=root, selected_id=root.note_id)
        self.assertIs(doc.first_note_by_title("Todo"), first_todo)
        self.assertIs(doc.first_note_by_path("Root/Projekt/Todo"), first_todo)
        self.assertIs(doc.first_note_by_path("Projekt/Todo"), first_todo)
        self.assertIs(doc.first_note_by_title_or_path("Root/Projekt/Todo"), first_todo)
        self.assertEqual(second_todo.path_string(), "Root / Projekt / Todo")

    def test_color_helpers(self) -> None:
        self.assertEqual(argb_to_hex(-1), "#FFFFFFFF")
        self.assertEqual(parse_int_or_hex("#112233"), 0xFF112233)
        self.assertEqual(parse_int_or_hex("0x01020304"), 0x01020304)


    def test_legacy_light_palette(self) -> None:
        self.assertEqual(legacy_light_color(0).name, "LightCoral")
        self.assertEqual(legacy_color_by_name("light-yellow").hex, "#FFFFFFE0")
        self.assertEqual(argb_to_signed(0xFFFFFFFF), -1)
        self.assertEqual(len(legacy_palette_table()), 15)


class AlarmTests(unittest.TestCase):

    def test_due_alarms_and_message(self) -> None:
        alarm = AlarmRule.create("Review", "2026-04-27 09:00", repeat="daily", message="prüfen", note_title="Todo")
        hits = due_alarms([alarm], now=datetime(2026, 4, 28, 9, 0), grace_seconds=60)
        self.assertEqual(len(hits), 1)
        self.assertIn("Review", alarm_message(*hits[0]))
        self.assertFalse(due_alarms([alarm], now=datetime(2026, 4, 28, 9, 2), grace_seconds=60))

    def test_weekly_and_monthly_alarm_recurrence(self) -> None:
        alarm = AlarmRule.create(
            "Review",
            datetime(2026, 4, 27, 9, 0),
            repeat="weekly",
            weekdays=parse_weekdays(["mo,mi"]),
        )
        self.assertEqual(alarm.next_after(datetime(2026, 4, 27, 10, 0)), datetime(2026, 4, 29, 9, 0))
        self.assertEqual(add_months(datetime(2024, 1, 31, 9, 0), 1), datetime(2024, 2, 29, 9, 0))

    def test_alarm_store_and_next(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alarms.json"
            old = AlarmRule.create("Alt", "2026-04-27 08:00", repeat="none")
            later = AlarmRule.create("Später", "2026-04-27 10:00", repeat="none")
            add_or_replace_alarm(later, path)
            add_or_replace_alarm(old, path)
            alarms = load_alarms(path)
            found = next_alarm(alarms, now=datetime(2026, 4, 27, 8, 30))
            self.assertIsNotNone(found)
            self.assertEqual(found[0].name, "Später")  # type: ignore[index]
            self.assertTrue(remove_alarm("Später", path))
            self.assertEqual([alarm.name for alarm in load_alarms(path)], ["Alt"])


class ConfigMigrationTests(unittest.TestCase):
    def test_legacy_config_read_write(self) -> None:
        xml = """<?xml version="1.0" encoding="utf-16"?>
<notizen-alx>
  <scrolls choice="2"/>
  <saftycopies amount="7"/>
  <autorun if="yes" minimized="yes"/>
  <ftp name="name" pass="secret" host="example.org" path="/x/y.alx"/>
  <files a="/tmp/a.alx" b="/tmp/b.alx" c="" d=""/>
  <language choice="english"/>
  <open file="notes.alx" directory="/tmp"/>
  <main-form x="1" y="2" width="300" height="400" windowstate="maximized"/>
  <minimized-show-in taskbar="yes"/>
  <desknotes show_desknote_borders="no"/>
  <x a="60"/>
</notizen-alx>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "notizen.config.xml"
            path.write_bytes(xml.encode("utf-16"))
            legacy = load_legacy_config(path)
            self.assertEqual(legacy.backup_count, 7)
            self.assertEqual(legacy.autosave_seconds, 60)
            self.assertTrue(legacy.autorun)
            self.assertEqual(legacy.language, "english")
            self.assertEqual(legacy.last_file, "/tmp/notes.alx")
            self.assertEqual(legacy.ftp_password, "secret")
            self.assertEqual(legacy.window_width, 300)
            app_config = legacy.to_app_config(AppConfig())
            self.assertEqual(app_config.language, "en")
            self.assertEqual(app_config.backup_count, 7)
            self.assertEqual(app_config.ftp_host, "example.org")
            self.assertEqual(app_config.ftp_username, "name")
            self.assertEqual(app_config.ftp_password, "secret")
            self.assertEqual(app_config.default_remote_url(), "ftp://name:secret@example.org/x/y.alx")
            out = Path(tmp) / "roundtrip.xml"
            write_legacy_like_config(app_config, out)
            self.assertTrue(out.read_bytes().startswith(b"\xff\xfe"))

    def test_recent_files_keep_remote_uri(self) -> None:
        config = AppConfig()
        config.add_recent("ftp://user:pass@example.org/dir/notizen.alx")
        self.assertEqual(config.last_file, "ftp://user:pass@example.org/dir/notizen.alx")

    def test_cli_recent_reads_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = tmp
            try:
                config = AppConfig()
                config.add_recent("/tmp/a.alx")
                config.add_recent("ftp://example.org/notizen.alx")
                config.save()
                with redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(cli_main(["recent"]), 0)
                self.assertIn("ftp://example.org/notizen.alx", out.getvalue())
            finally:
                if old_home is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = old_home

    def test_default_remote_url_quotes_credentials(self) -> None:
        config = AppConfig(ftp_host="example.org", ftp_username="u ser", ftp_password="p@ss", ftp_path="dir/file.alx", ftp_use_tls=True)
        self.assertEqual(config.default_remote_url(), "ftps://u%20ser:p%40ss@example.org/dir/file.alx")

    def test_cli_config_set_updates_general_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = tmp
            try:
                with redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(
                        cli_main([
                            "config-set",
                            "--backup-count",
                            "9",
                            "--autosave-seconds",
                            "45",
                            "--language",
                            "English",
                            "--autorun",
                            "--autorun-minimized",
                            "--hide-desknote-borders",
                            "--window",
                            "1,2,300,400",
                            "--last-file",
                            "/tmp/notizen.alx",
                            "--json",
                        ]),
                        0,
                    )
                payload = json.loads(out.getvalue())
                self.assertEqual(payload["backup_count"], 9)
                self.assertEqual(payload["autosave_seconds"], 45)
                self.assertEqual(payload["language"], "en")
                self.assertFalse(payload["show_desknote_borders"])
                self.assertEqual(payload["window_width"], 300)
                self.assertIn("/tmp/notizen.alx", payload["recent_files"])
                with redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(cli_main(["config-path"]), 0)
                self.assertTrue(out.getvalue().strip().endswith("config.json"))
            finally:
                if old_home is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = old_home




class LegacyContextMenuTests(unittest.TestCase):
    def test_context_menu_manifest_matches_old_winforms_menus(self) -> None:
        tree = context_actions_payload("tree", "en")
        self.assertEqual(len(tree), 11)
        self.assertIn("rename", {item["action"] for item in tree})
        content_text = format_context_actions("content", "de")
        self.assertIn("Bild", content_text)
        opacity = sticky_opacity_payload()
        self.assertEqual(opacity[0]["label"], "90 %")
        self.assertEqual(opacity[0]["opacity"], 0.1)


class TranslationAndShortcutTests(unittest.TestCase):
    def test_legacy_translation_table_is_available(self) -> None:
        self.assertEqual(len(LEGACY_KEYS), 118)
        self.assertEqual(translate("Strip1_1", "de"), "&Menü")
        self.assertEqual(translate("Strip1_3", "english"), "&Open        CTRL+O")
        self.assertEqual(normalize_language("Russian"), "ru")
        table = translation_table(languages=["de", "en"])
        self.assertEqual(table[0]["key"], "Strip1_1")
        self.assertEqual(table[0]["de"], "&Menü")

    def test_shortcut_manifest_contains_old_global_keys(self) -> None:
        keys = {item["keys"]: item["action"] for item in shortcut_manifest()}
        self.assertEqual(keys["Ctrl+S"], "Datei speichern")
        self.assertEqual(keys["Insert"], "Neuen Unterknoten anlegen")

    def test_cli_language_and_shortcut_commands(self) -> None:
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli_main(["lang-get", "Strip1_1", "--language", "en"]), 0)
        self.assertIn("&Menu", out.getvalue())
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli_main(["lang-list", "--json"]), 0)
        self.assertIn('"ru"', out.getvalue())
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli_main(["shortcuts", "--json"]), 0)
        self.assertIn("Ctrl+S", out.getvalue())
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli_main(["context-menus", "--menu", "tree", "--include-opacity"]), 0)
        self.assertIn("Desktop", out.getvalue())
        self.assertIn("sticky-opacity", out.getvalue())

    def test_about_and_feedback_draft(self) -> None:
        payload = feedback_gzip_payload("Das ist ein längerer Testtext")
        self.assertTrue(payload.startswith(b"\x1f\x8b"))
        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "feedback.txt.gz"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["feedback-draft", str(out_file), "--text", "Das ist ein längerer Testtext"]), 0)
            self.assertEqual(read_feedback_gzip(out_file), "Das ist ein längerer Testtext")
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli_main(["about", "--language", "de"]), 0)
        self.assertIn("Desktop", out.getvalue())


class CliIntegrationTests(unittest.TestCase):
    def test_cli_rename_export_html_and_format(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("Text")))
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.alx"
            renamed = Path(tmp) / "renamed.alx"
            formatted = Path(tmp) / "formatted.alx"
            html = Path(tmp) / "out.html"
            save_document(doc, path=source, backup_count=0)
            self.assertEqual(cli_main(["rename", str(source), str(renamed), "--title", "Root", "--new-title", "Neu"]), 0)
            self.assertEqual(cli_main(["format-note", str(renamed), str(formatted), "--title", "Neu", "--bold", "--fg-color", "#112233"]), 0)
            loaded = load_document(formatted)
            self.assertIn(r"\b", loaded.root.rtf)
            self.assertEqual(cli_main(["export-html", str(formatted), str(html)]), 0)
            self.assertIn("Neu", html.read_text(encoding="utf-8"))
            image = Path(tmp) / "tiny.png"
            image.write_bytes(bytes.fromhex("89504E470D0A1A0A"))
            with_image = Path(tmp) / "with_image.alx"
            self.assertEqual(cli_main(["insert-image", str(formatted), str(with_image), "--title", "Neu", "--image", str(image)]), 0)
            loaded_image = load_document(with_image)
            self.assertEqual(len(extract_pictures(loaded_image.root.rtf)), 1)

    def test_cli_font_size_sticky_and_sticky_html(self) -> None:
        root = Note("Root", text_to_rtf("Text", font_size_half_points=18))
        doc = NoteDocument(root=root)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.alx"
            sized = Path(tmp) / "sized.alx"
            sticky_file = Path(tmp) / "sticky.alx"
            sticky_html = Path(tmp) / "sticky.html"
            save_document(doc, path=source, backup_count=0)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["font-size", str(source), str(sized), "--title", "Root", "--bigger"]), 0)
            self.assertIn(r"\fs20", load_document(sized).root.rtf)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["sticky", str(sized), str(sticky_file), "--title", "Root", "--show", "--autosize", "--x", "10", "--y", "20", "--argb", "#FFFFFF99"]), 0)
            loaded = load_document(sticky_file)
            self.assertIsNotNone(loaded.root.sticky)
            self.assertEqual(loaded.root.sticky.x, 10)  # type: ignore[union-attr]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["export-sticky-html", str(sticky_file), str(sticky_html)]), 0)
            self.assertIn("Root", sticky_html.read_text(encoding="utf-8"))

    def test_cli_style_note_and_alarm_due(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("Text", font_family="Arial", font_size_half_points=18)))
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.alx"
            styled = Path(tmp) / "styled.alx"
            save_document(doc, path=source, backup_count=0)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["style-note", str(source), str(styled), "--title", "Root", "--style", "italic"]), 0)
            style = detect_rtf_style(load_document(styled).root.rtf)
            self.assertTrue(style.italic)

            old_home = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = tmp
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(cli_main(["alarm-add", "--name", "Due", "--at", "2026-04-27 09:00", "--message", "ping"]), 0)
                with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                    self.assertEqual(cli_main(["alarm-due", "--now", "2026-04-27 09:00", "--grace-seconds", "60", "--notify", "--dry-run"]), 0)
                self.assertIn("Due", out.getvalue())
            finally:
                if old_home is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = old_home


    def test_cli_insert_delete_and_style_range(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("Hallo Welt")))
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.alx"
            inserted = Path(tmp) / "inserted.alx"
            deleted = Path(tmp) / "deleted.alx"
            styled = Path(tmp) / "styled.alx"
            save_document(doc, path=source, backup_count=0)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["insert-text", str(source), str(inserted), "--title", "Root", "--at", "6", "--text", "schöne "]), 0)
            self.assertEqual(load_document(inserted).root.text, "Hallo schöne Welt")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["delete-range", str(inserted), str(deleted), "--title", "Root", "--start", "6", "--length", "7"]), 0)
            self.assertEqual(load_document(deleted).root.text, "Hallo Welt")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                self.assertEqual(cli_main(["style-range", str(deleted), str(styled), "--title", "Root", "--start", "6", "--length", "4", "--style", "bold", "--font-size", "24", "--show"]), 0)
            loaded = load_document(styled)
            self.assertEqual(loaded.root.text, "Hallo Welt")
            self.assertIn(r"\b", loaded.root.rtf)
            self.assertIn('"plain_text": "Hallo Welt"', err.getvalue())

    def test_cli_config_show_outputs_json(self) -> None:
        with redirect_stdout(io.StringIO()) as buf:
            code = cli_main(["config-show"])
        self.assertEqual(code, 0)
        self.assertIn("backup_count", buf.getvalue())

    def test_cli_dump_and_pack_xml(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("XML CLI")))
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.alx"
            xml = Path(tmp) / "source.xml"
            packed = Path(tmp) / "packed.alx"
            save_document(doc, path=source, backup_count=0)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["dump-xml", str(source), str(xml)]), 0)
            self.assertIn("notizen-alx2", xml.read_text(encoding="utf-8"))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["pack-xml", str(xml), str(packed)]), 0)
            self.assertEqual(load_document(packed).root.text, "XML CLI")

    def test_cli_search_json_combine_and_backups(self) -> None:
        root = Note("Root", text_to_rtf("Root Text"))
        root.add_child(Note("Kind", text_to_rtf("Kind Text")))
        doc = NoteDocument(root=root)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.alx"
            combined = Path(tmp) / "combined.alx"
            md = Path(tmp) / "out.md"
            save_document(doc, path=source, backup_count=0)
            save_document(doc, path=source, backup_count=2)
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["search", str(source), "Kind", "--json"]), 0)
            self.assertIn('"title": "Kind"', out.getvalue())
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["search", str(source), "Kind", "--occurrences", "--json"]), 0)
            self.assertIn('"start"', out.getvalue())
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["combine-subtree", str(source), str(combined), "--title", "Kind", "--new-title", "Einheit"]), 0)
            self.assertEqual(load_document(combined).root.children[-1].title, "Einheit")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["export-md", str(combined), str(md)]), 0)
            self.assertIn("# Root", md.read_text(encoding="utf-8"))
            subtree_json = Path(tmp) / "kind.json"
            imported_file = Path(tmp) / "imported.alx"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["export-json", str(combined), str(subtree_json), "--title", "Kind"]), 0)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["import-json", str(combined), str(imported_file), "--title", "Root", "--input", str(subtree_json)]), 0)
            self.assertTrue(load_document(imported_file).root.children[-1].title.startswith("Kind"))
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["backup-list", str(source)]), 0)
            self.assertIn("source-", out.getvalue())

    def test_cli_color_note_sticky_list_and_palette(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("Text")))
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.alx"
            colored = Path(tmp) / "colored.alx"
            sticky_file = Path(tmp) / "sticky.alx"
            save_document(doc, path=source, backup_count=0)
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["color-palette", "--json"]), 0)
            self.assertIn("LightCoral", out.getvalue())
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["color-note", str(source), str(colored), "--title", "Root", "--random-bg", "--random-index", "4", "--show"]), 0)
            self.assertIn("#FFFFFFE0", out.getvalue())
            self.assertEqual(load_document(colored).root.bg_color, legacy_light_color(4).signed_argb)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["sticky", str(colored), str(sticky_file), "--title", "Root", "--show", "--autosize"]), 0)
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(cli_main(["sticky-list", str(sticky_file), "--json"]), 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload[0]["title"], "Root")
            self.assertIn("bg_css", payload[0])

    def test_cli_alarm_add_next_remove(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = tmp
            try:
                with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                    self.assertEqual(
                        cli_main([
                            "alarm-add",
                            "--name",
                            "Review",
                            "--at",
                            "2026-04-27 09:00",
                            "--repeat",
                            "weekly",
                            "--weekday",
                            "mo,mi",
                            "--message",
                            "prüfen",
                        ]),
                        0,
                    )
                self.assertIn("Review", out.getvalue())
                with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                    self.assertEqual(cli_main(["alarm-list"]), 0)
                self.assertIn("Review", out.getvalue())
                with redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(cli_main(["alarm-remove", "--name", "Review"]), 0)
                self.assertIn("entfernt", out.getvalue())
            finally:
                if old_home is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = old_home


    def test_clipboard_roundtrip_and_relative_tree_operations(self) -> None:
        root = Note("Root", text_to_rtf("Root Text"))
        a = root.add_child(Note("A", text_to_rtf("Alpha")))
        a.add_child(Note("A1", text_to_rtf("Alpha Kind")))
        b = root.add_child(Note("B", text_to_rtf("Beta")))
        doc = NoteDocument(root=root)

        payload = note_to_clipboard_text(a, source_path="source.alx")
        entry = entry_from_clipboard_text(payload)
        self.assertEqual(entry.note.title, "A")
        self.assertEqual(entry.note.children[0].title, "A1")

        doc.select(a)
        self.assertTrue(doc.move_selected_relative_to(b, where="after"))
        self.assertEqual([child.title for child in doc.root.children], ["B", "A"])
        created = doc.copy_selected_relative_to(b, where="before")
        self.assertIsNotNone(created)
        self.assertEqual([child.title for child in doc.root.children], ["A", "B", "A"])

        with tempfile.TemporaryDirectory() as tmp:
            clip = Path(tmp) / "clip.json"
            write_clipboard_file(a, clip, source_path="source.alx")
            read_back = read_clipboard_file(clip)
            self.assertEqual(read_back.note.title, "A")
            info = clipboard_info(clip)
            self.assertEqual(info["title"], "A")
            self.assertEqual(info["nodes"], 2)

    def test_legacy_exports_and_sticky_opacity_mapping(self) -> None:
        root = Note("Root", text_to_rtf("äöü"))
        root.add_child(Note("Kind", text_to_rtf("zweite Zeile")))
        doc = NoteDocument(root=root)
        choices = legacy_opacity_choices()
        self.assertEqual(choices[0].label, "90 %")
        self.assertAlmostEqual(opacity_from_legacy_choice("90%"), 0.1)
        self.assertAlmostEqual(opacity_from_legacy_choice("0%"), 1.0)
        self.assertAlmostEqual(opacity_from_legacy_choice("9"), 1.0)

        with tempfile.TemporaryDirectory() as tmp:
            txt = Path(tmp) / "legacy.txt"
            rtf = Path(tmp) / "unity.rtf"
            export_legacy_text(doc, txt, numbered=True, encoding="cp1252")
            raw = txt.read_bytes()
            self.assertIn(b"\r\n", raw)
            self.assertIn("äöü".encode("cp1252"), raw)
            export_unity_rtf(doc, rtf, numbered=True)
            unity = rtf.read_text(encoding="utf-8")
            self.assertTrue(is_rtf(unity))
            self.assertIn("Root", rtf_to_text(unity))

    def test_cli_clipboard_relative_exports_and_sticky_opacity(self) -> None:
        root = Note("Root", text_to_rtf("Root Text"))
        root.add_child(Note("A", text_to_rtf("Alpha")))
        root.add_child(Note("B", text_to_rtf("Beta")))
        doc = NoteDocument(root=root)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.alx"
            moved = Path(tmp) / "moved.alx"
            copied = Path(tmp) / "copied.alx"
            pasted = Path(tmp) / "pasted.alx"
            sticky_file = Path(tmp) / "sticky.alx"
            legacy_txt = Path(tmp) / "legacy.txt"
            unity_rtf = Path(tmp) / "unity.rtf"
            clip = Path(tmp) / "clip.json"
            save_document(doc, path=source, backup_count=0)

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["move-relative", str(source), str(moved), "--title", "A", "--target-title", "B", "--where", "after"]), 0)
            self.assertEqual([child.title for child in load_document(moved).root.children], ["B", "A"])

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["copy-node", str(source), "--title", "A", "--clipboard", str(clip)]), 0)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["paste-node", str(source), str(pasted), "--target-title", "B", "--where", "before", "--clipboard", str(clip)]), 0)
            self.assertEqual([child.title for child in load_document(pasted).root.children], ["A", "A", "B"])
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(cli_main(["clipboard-show", "--clipboard", str(clip), "--json"]), 0)
            self.assertIn('"title": "A"', out.getvalue())

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["copy-relative", str(source), str(copied), "--title", "A", "--target-title", "B", "--where", "after"]), 0)
            self.assertEqual([child.title for child in load_document(copied).root.children], ["A", "B", "A"])

            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["export-legacy-txt", str(source), str(legacy_txt)]), 0)
                self.assertEqual(cli_main(["export-unity-rtf", str(source), str(unity_rtf), "--plain"]), 0)
            self.assertIn(b"\r\n", legacy_txt.read_bytes())
            self.assertIn("Root", rtf_to_text(unity_rtf.read_text(encoding="utf-8")))

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["sticky", str(source), str(sticky_file), "--title", "Root", "--show", "--opacity-choice", "90%"]), 0)
            self.assertAlmostEqual(load_document(sticky_file).root.sticky.opacity, 0.1)  # type: ignore[union-attr]
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(cli_main(["sticky-opacity", "--json"]), 0)
            self.assertIn('"label": "90 %"', out.getvalue())



class OpmlAndFontsTests(unittest.TestCase):
    def test_opml_roundtrip_preserves_metadata(self) -> None:
        root = Note("Root", text_to_rtf("Root Text"), bg_color=-256, fg_color=-16777216)
        child = root.add_child(Note("Kind", text_to_rtf("Alpha"), sticky=StickyWindow(True, 10, 20, 250, 160, 0.7, -256)))
        doc = NoteDocument(root=root)
        xml = document_to_opml(doc)
        self.assertIn("<opml", xml)
        self.assertIn("_notizen_rtf_b64", xml)
        imported = opml_to_note(xml)
        self.assertEqual(imported.title, "Root")
        self.assertEqual(imported.text, "Root Text")
        self.assertEqual(imported.children[0].title, "Kind")
        self.assertEqual(imported.children[0].text, "Alpha")
        self.assertIsNotNone(imported.children[0].sticky)
        self.assertAlmostEqual(imported.children[0].sticky.opacity, 0.7)  # type: ignore[union-attr]

    def test_storage_export_import_opml_and_export_alx_subtree(self) -> None:
        root = Note("Root", text_to_rtf("root"))
        a = root.add_child(Note("A", text_to_rtf("alpha")))
        a.add_child(Note("A1", text_to_rtf("alpha child")))
        root.add_child(Note("B", text_to_rtf("beta")))
        doc = NoteDocument(root=root)
        with tempfile.TemporaryDirectory() as tmp:
            opml = Path(tmp) / "a.opml"
            base = Path(tmp) / "base.alx"
            imported_path = Path(tmp) / "imported.alx"
            subtree = Path(tmp) / "subtree.alx"
            export_opml(doc, opml, start=a)
            save_document(doc, path=base, backup_count=0)
            loaded = load_document(base)
            created = import_opml_into_document(loaded, opml, target=loaded.root.children[1], where="after")
            self.assertEqual(created.title, "A")
            save_document(loaded, path=imported_path, backup_count=0)
            self.assertEqual([child.title for child in load_document(imported_path).root.children], ["A", "B", "A"])
            export_alx(doc, subtree, start=a)
            subdoc = load_document(subtree)
            self.assertEqual(subdoc.root.title, "A")
            self.assertEqual(subdoc.root.children[0].title, "A1")

    def test_cli_opml_alx_search_expand_and_font_list(self) -> None:
        root = Note("Root", text_to_rtf("Root Text"))
        a = root.add_child(Note("A", text_to_rtf("Alpha Alpha")))
        a.add_child(Note("A1", text_to_rtf("Kind Alpha")))
        root.add_child(Note("B", text_to_rtf("Beta")))
        doc = NoteDocument(root=root)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.alx"
            opml = Path(tmp) / "a.opml"
            subtree = Path(tmp) / "a.alx"
            imported = Path(tmp) / "imported.alx"
            collapsed = Path(tmp) / "collapsed.alx"
            fonts_dir = Path(tmp) / "fonts"
            fonts_dir.mkdir()
            (fonts_dir / "DemoSans-Regular.ttf").write_bytes(b"not a real font")
            save_document(doc, path=source, backup_count=0)

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["export-opml", str(source), str(opml), "--title", "A"]), 0)
                self.assertEqual(cli_main(["export-alx", str(source), str(subtree), "--title", "A"]), 0)
                self.assertEqual(cli_main(["import-opml", str(source), str(imported), "--title", "B", "--where", "after", "--input", str(opml)]), 0)
                self.assertEqual(cli_main(["expand-state", str(source), str(collapsed), "--all", "--collapsed"]), 0)
            self.assertEqual(load_document(subtree).root.title, "A")
            self.assertFalse(load_document(collapsed).root.children[0].expanded)
            self.assertEqual([child.title for child in load_document(imported).root.children], ["A", "B", "A"])

            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["search-occurrences", str(source), "Alpha", "--json"]), 0)
            payload = json.loads(out.getvalue())
            self.assertGreaterEqual(len(payload), 3)
            self.assertIn("start", payload[0])

            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["font-list", "--path", str(fonts_dir), "--contains", "DemoSans", "--json"]), 0)
            fonts = json.loads(out.getvalue())
            self.assertEqual(fonts[0]["family"], "DemoSans")

    def test_font_scanner_uses_filename_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            font = Path(tmp) / "ExampleFont-Regular.ttf"
            font.write_bytes(b"dummy")
            entries = list_system_fonts(paths=[tmp])
        self.assertEqual(entries[0].family, "ExampleFont")



class NotesDocCompatPathTests(unittest.TestCase):
    def test_notes_doc_export_loads_back_through_legacy_parser(self) -> None:
        root = Note("Root", text_to_rtf("A\nB"))
        child = root.add_child(Note("Kind", text_to_rtf("C")))
        doc = NoteDocument(root=root, selected_id=child.note_id)
        xml = document_to_notes_doc_xml(doc)
        self.assertIn(b"notes_doc", xml)
        self.assertIn(b"leaf_text", xml)
        loaded = load_document_from_bytes(xml)
        self.assertEqual(loaded.root.title, "Root")
        self.assertEqual(loaded.root.text, "A\nB")
        self.assertEqual(loaded.root.children[0].title, "Kind")
        self.assertEqual(loaded.root.children[0].text, "C")
        with tempfile.TemporaryDirectory() as tmp:
            out_xml = Path(tmp) / "legacy-notes-doc.xml"
            export_notes_doc(doc, out_xml)
            reloaded = load_document(out_xml)
        self.assertEqual(reloaded.root.title, "Root")
        self.assertEqual(reloaded.root.children[0].title, "Kind")

    def test_compat_report_flags_metadata_and_counts(self) -> None:
        root = Note("Root", "plain body", bg_color=0x00112233)
        root.sticky = StickyWindow(True, 0, 0, 0, 1, 2.0, 0x00112233)
        root.add_child(Note("", text_to_rtf("Kind")))
        doc = NoteDocument(root=root)
        report = analyze_document(doc, encrypted=False, source="memory.alx")
        codes = {issue.code for issue in report.issues}
        self.assertIn("plain-body", codes)
        self.assertIn("empty-title", codes)
        self.assertIn("transparent-bgcolor", codes)
        self.assertIn("sticky-width", codes)
        self.assertIn("sticky-opacity", codes)
        self.assertEqual(report.summary["notes"], 2)
        self.assertEqual(report.summary["sticky_notes"], 1)

    def test_default_paths_create_documents_notizen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("HOME")
            old_userprofile = os.environ.get("USERPROFILE")
            os.environ["HOME"] = tmp
            os.environ.pop("USERPROFILE", None)
            try:
                paths = default_paths(create=True)
                default_path = default_file_path(create_dir=False)
                self.assertTrue(Path(paths.notes_dir).exists())
                self.assertEqual(Path(paths.notes_dir).name, "Notizen")
                self.assertEqual(default_path.name, "unbenannt.alx")
                self.assertIn("Documents", str(default_path))
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home
                if old_userprofile is None:
                    os.environ.pop("USERPROFILE", None)
                else:
                    os.environ["USERPROFILE"] = old_userprofile

    def test_cli_notes_doc_init_paths_and_compat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "new.alx"
            out_xml = Path(tmp) / "new-notes-doc.xml"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["init-file", str(path), "--title", "Root", "--text", "Hallo", "--overwrite"]), 0)
            self.assertEqual(load_document(path).root.text, "Hallo")
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["compat-report", str(path), "--json"]), 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["summary"]["notes"], 1)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["export-notes-doc", str(path), str(out_xml)]), 0)
            self.assertEqual(load_document(out_xml).root.title, "Root")
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["default-paths", "--json"]), 0)
            self.assertIn("default_file", json.loads(out.getvalue()))

    def test_analyze_file_detects_plain_xml_notes_doc(self) -> None:
        doc = NoteDocument(root=Note("Root", text_to_rtf("Text")))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.xml"
            export_notes_doc(doc, path)
            report = analyze_file(path)
        self.assertEqual(report.format_name, "notes_doc")
        self.assertFalse(report.encrypted)
        self.assertEqual(report.summary["notes"], 1)



class PasswordRepairAndConfigTests(unittest.TestCase):
    def test_legacy_password_info_matches_old_dialog_segments(self) -> None:
        info = legacy_password_info("abcdefghijklmnopqrstuvwx")
        self.assertEqual(info.normalized_length, 24)
        self.assertEqual(info.key1, "abcdefgh")
        self.assertEqual(info.key2, "hijklmno")
        self.assertEqual(info.key3, "pqrstuvw")
        self.assertEqual(info.unused_char, "x")
        self.assertFalse(info.padded)
        self.assertFalse(info.truncated)
        self.assertEqual(normalize_legacy_password("abc"), "abc" + " " * 21)
        self.assertTrue(legacy_password_info("" ).blank)
        self.assertTrue(legacy_password_info("x" * 30).truncated)
        self.assertFalse(legacy_password_info("ä").ascii_only)

    def test_repair_document_normalizes_migration_edge_cases(self) -> None:
        root = Note("", "plain body", bg_color=0x00112233, fg_color=0xFF112233)
        root.sticky = StickyWindow(True, 0, 0, 10, 2, 2.0, 0x00112233)
        doc = NoteDocument(root=root, selected_id=root.note_id)
        report = repair_document(doc)
        self.assertGreaterEqual(report.total_changes, 6)
        self.assertEqual(root.title, "...")
        self.assertTrue(is_rtf(root.rtf))
        self.assertIsNone(root.bg_color)
        self.assertEqual(root.sticky.width, 80)  # type: ignore[union-attr]
        self.assertEqual(root.sticky.height, 60)  # type: ignore[union-attr]
        self.assertEqual(root.sticky.opacity, 1.0)  # type: ignore[union-attr]
        self.assertIsNone(root.sticky.argb)  # type: ignore[union-attr]

    def test_legacy_config_toolstrip_positions_roundtrip(self) -> None:
        config = AppConfig()
        config.set_toolstrip_position("haupt", 11, 22)
        config.set_toolstrip_position("font", 33, 44)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "notizen.config.xml"
            write_legacy_like_config(config, path)
            legacy = load_legacy_config(path)
        self.assertEqual(legacy.toolstrip_positions["haupt"], [11, 22])
        self.assertEqual(legacy.toolstrip_positions["font"], [33, 44])
        migrated = legacy.to_app_config(AppConfig())
        self.assertEqual(migrated.toolstrip_position("haupt"), (11, 22))

    def test_cli_password_repair_and_toolstrips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg_home = Path(tmp) / "cfg"
            old_xdg = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = str(cfg_home)
            try:
                with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                    self.assertEqual(cli_main(["password-info", "abcdefghijklmnopqrstuvwx", "--json", "--reveal"]), 0)
                self.assertEqual(json.loads(out.getvalue())["key2"], "hijklmno")
                with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                    self.assertEqual(cli_main(["toolstrips", "--set", "haupt", "5", "6", "--json"]), 0)
                self.assertEqual(json.loads(out.getvalue())["haupt"], [5, 6])
                source = Path(tmp) / "broken.alx"
                output = Path(tmp) / "fixed.alx"
                doc = NoteDocument(root=Note("", "plain", bg_color=0x00112233), selected_id=None)
                save_document(doc, path=source, backup_count=0)
                with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                    self.assertEqual(cli_main(["repair", str(source), str(output), "--json"]), 0)
                self.assertGreater(json.loads(out.getvalue())["total_changes"], 0)
                self.assertEqual(load_document(output).root.title, "...")
            finally:
                if old_xdg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = old_xdg


class AppCompatTests(unittest.TestCase):
    def test_about_and_shortcut_ui_hooks(self) -> None:
        class DummyWindow:
            meta_text = ""
            status_text = ""

        app = object.__new__(NotizenSlintApp)
        app.config = AppConfig(language="en")
        app.window = DummyWindow()
        app._current_password = "abcdefghijklmnopqrstuvwx"
        app.document = NoteDocument(root=Note("Root", text_to_rtf("Text")))
        NotizenSlintApp.show_about(app)
        self.assertIn("Info", app.window.status_text)
        self.assertIn("desknote", app.window.meta_text)
        NotizenSlintApp.show_shortcuts(app)
        self.assertIn("Tastenkürzel", app.window.status_text)
        self.assertIn("Ctrl+S", app.window.meta_text)
        NotizenSlintApp.show_context_menus(app)
        self.assertIn("Kontext", app.window.status_text)
        self.assertIn("content", app.window.meta_text)
        NotizenSlintApp.show_password_info(app)
        self.assertIn("Passwort", app.window.status_text)
        NotizenSlintApp.show_toolstrips(app)
        self.assertIn("ToolStrip", app.window.status_text)

    def test_legacy_argv_normalization(self) -> None:
        self.assertEqual(_normalize_legacy_argv(["/min", "datei.alx"]), ["--minimized", "datei.alx"])
        self.assertEqual(_normalize_legacy_argv(["-min"]), ["--minimized"])
        self.assertEqual(_normalize_legacy_argv(["/h"]), ["--help"])
        self.assertEqual(_normalize_legacy_argv(["/?"]), ["--help"])

    def test_compat_and_default_path_ui_hooks(self) -> None:
        class DummyWindow:
            meta_text = ""
            status_text = ""

        app = object.__new__(NotizenSlintApp)
        app.window = DummyWindow()
        app.document = NoteDocument(root=Note("Root", text_to_rtf("Text")))
        app._current_password = None
        NotizenSlintApp.show_compat_report(app)
        self.assertIn("Kompatibilität", app.window.status_text)
        self.assertIn("Notizen", app.window.meta_text)
        NotizenSlintApp.show_default_paths(app)
        self.assertIn("Standardpfade", app.window.status_text)
        self.assertIn("unbenannt.alx", app.window.meta_text)

class NotificationTests(unittest.TestCase):
    def test_notify_dry_run_is_dependency_free(self) -> None:
        result = notify("Titel", "Text", dry_run=True)
        self.assertTrue(result.delivered)
        self.assertEqual(result.backend, "dry-run")
        self.assertIn("Titel", result.message)


class RemoteTests(unittest.TestCase):
    def test_parse_ftp_url(self) -> None:
        loc = parse_ftp_url("ftps://u:p@example.org:2121/dir/file.alx")
        self.assertEqual(loc.host, "example.org")
        self.assertEqual(loc.port, 2121)
        self.assertEqual(loc.username, "u")
        self.assertEqual(loc.password, "p")
        self.assertEqual(loc.path, "/dir/file.alx")
        self.assertTrue(loc.use_tls)


if __name__ == "__main__":
    unittest.main()
