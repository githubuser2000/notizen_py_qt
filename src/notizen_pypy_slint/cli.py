from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .storage import NotizenFileError, export_rtf, export_text, load_document, save_document


def _print_tree(file: str, password: str | None) -> None:
    doc = load_document(file, password=password)
    for row in doc.flatten(include_collapsed=True):
        print(row.label)


def _export_txt(file: str, output: str, password: str | None) -> None:
    doc = load_document(file, password=password)
    export_text(doc, output)
    print(output)


def _export_rtf(file: str, output: str, password: str | None) -> None:
    doc = load_document(file, password=password)
    export_rtf(doc, output)
    print(output)


def _change_password(file: str, output: str, old_password: str | None, new_password: str | None) -> None:
    doc = load_document(file, password=old_password)
    save_document(doc, path=output, password=new_password or None)
    print(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kommandozeilenwerkzeug für Notizen.NET-.alx-Dateien")
    sub = parser.add_subparsers(dest="cmd", required=True)

    tree = sub.add_parser("tree", help="Notizbaum ausgeben")
    tree.add_argument("file")
    tree.add_argument("--password")

    txt = sub.add_parser("export-txt", help="Nach TXT exportieren")
    txt.add_argument("file")
    txt.add_argument("output")
    txt.add_argument("--password")

    rtf = sub.add_parser("export-rtf", help="Nach RTF exportieren")
    rtf.add_argument("file")
    rtf.add_argument("output")
    rtf.add_argument("--password")

    password = sub.add_parser("change-password", help="Datei neu speichern und Passwort ändern/entfernen")
    password.add_argument("file")
    password.add_argument("output")
    password.add_argument("--old-password")
    password.add_argument("--new-password", help="Leer/fehlend speichert unverschlüsselt")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "tree":
            _print_tree(args.file, args.password)
        elif args.cmd == "export-txt":
            _export_txt(args.file, args.output, args.password)
        elif args.cmd == "export-rtf":
            _export_rtf(args.file, args.output, args.password)
        elif args.cmd == "change-password":
            _change_password(args.file, args.output, args.old_password, args.new_password)
        else:  # pragma: no cover
            parser.error(f"unbekannter Befehl: {args.cmd}")
    except NotizenFileError as exc:
        print(f"Dateifehler: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
