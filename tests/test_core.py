from __future__ import annotations

import io
from importlib import resources
import os
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
import unittest

from notizen_py_slint.alarm import AlarmRule, add_months, add_or_replace_alarm, load_alarms, next_alarm, parse_weekdays, remove_alarm
from notizen_py_slint.des_compat import DES, decrypt_notizen_payload, encrypt_notizen_payload
from notizen_py_slint.cli import main as cli_main
from notizen_py_slint.app import _format_slint_compile_error
from notizen_py_slint.config import AppConfig, load_config
from notizen_py_slint.legacy_config import load_legacy_config, write_legacy_like_config
from notizen_py_slint.model import Note, NoteDocument, StickyWindow, argb_to_hex, parse_int_or_hex
from notizen_py_slint.remote import parse_ftp_url
from notizen_py_slint.rtf import append_picture_to_rtf, extract_pictures, is_rtf, restyle_rtf_as_plain, rtf_to_text, text_to_rtf
from notizen_py_slint.storage import (
    export_document_images,
    export_html,
    load_document,
    load_document_from_bytes,
    save_document,
    save_document_to_bytes,
    insert_image_into_note,
    append_bullet_into_note,
    read_raw_xml,
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
        self.assertEqual(loaded.root.bg_color, 0xFFEEDDCC)
        self.assertEqual(loaded.root.children[0].sticky.width, 300)  # type: ignore[union-attr]
        self.assertTrue(loaded.root.children[0].sticky.visible)  # type: ignore[union-attr]

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
        stats = doc.stats()
        self.assertEqual(stats.notes, 4)
        self.assertEqual(stats.max_depth, 2)

    def test_color_helpers(self) -> None:
        self.assertEqual(argb_to_hex(-1), "#FFFFFFFF")
        self.assertEqual(parse_int_or_hex("#112233"), 0xFF112233)
        self.assertEqual(parse_int_or_hex("0x01020304"), 0x01020304)


class AlarmTests(unittest.TestCase):
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

    def test_default_remote_url_quotes_credentials(self) -> None:
        config = AppConfig(ftp_host="example.org", ftp_username="u ser", ftp_password="p@ss", ftp_path="dir/file.alx", ftp_use_tls=True)
        self.assertEqual(config.default_remote_url(), "ftps://u%20ser:p%40ss@example.org/dir/file.alx")


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


class RemoteTests(unittest.TestCase):
    def test_parse_ftp_url(self) -> None:
        loc = parse_ftp_url("ftps://u:p@example.org:2121/dir/file.alx")
        self.assertEqual(loc.host, "example.org")
        self.assertEqual(loc.port, 2121)
        self.assertEqual(loc.username, "u")
        self.assertEqual(loc.password, "p")
        self.assertEqual(loc.path, "/dir/file.alx")
        self.assertTrue(loc.use_tls)


class PythonProjectCompatibilityTests(unittest.TestCase):
    def test_legacy_import_path_still_forwards(self) -> None:
        from notizen_pypy_slint.storage import load_document as old_load_document

        self.assertIs(old_load_document, load_document)

    def test_load_config_falls_back_to_old_config_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = tmp
            try:
                legacy = Path(tmp) / "notizen-pypy-slint"
                legacy.mkdir()
                (legacy / "config.json").write_text('{"backup_count": 11, "language": "en"}', encoding="utf-8")
                loaded = load_config()
            finally:
                if old_home is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = old_home
        self.assertEqual(loaded.backup_count, 11)
        self.assertEqual(loaded.language, "en")


    def test_packaged_slint_file_compiles_when_slint_is_installed(self) -> None:
        try:
            import slint
        except ModuleNotFoundError:
            self.skipTest("slint is not installed")
        ui_path = resources.files("notizen_py_slint.ui").joinpath("app-window.slint")
        components = slint.load_file(str(ui_path))
        self.assertTrue(hasattr(components, "AppWindow"))

    def test_slint_compile_error_formatter_shows_diagnostics(self) -> None:
        class FakeDiagnostic:
            def message(self) -> str:
                return "expected callback syntax"

            def level(self) -> str:
                return "Error"

            def source_file(self) -> str:
                return "app-window.slint"

            def line_column(self) -> tuple[int, int]:
                return (218, 25)

        exc = RuntimeError("compile failed", [FakeDiagnostic()])
        text = _format_slint_compile_error(exc, Path("app-window.slint"))
        self.assertIn("218", text)
        self.assertIn("expected callback syntax", text)


if __name__ == "__main__":
    unittest.main()
