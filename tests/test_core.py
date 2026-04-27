from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from notizen_pypy_slint.des_compat import DES, decrypt_notizen_payload, encrypt_notizen_payload
from notizen_pypy_slint.model import Note, NoteDocument
from notizen_pypy_slint.rtf import rtf_to_text, text_to_rtf
from notizen_pypy_slint.storage import load_document, save_document


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


if __name__ == "__main__":
    unittest.main()
