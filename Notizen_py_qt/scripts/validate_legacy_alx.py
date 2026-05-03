#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from notizen_py_qt.alx_io import AlxError  # noqa: E402
from notizen_py_qt.legacy_validation import validate_alx_roundtrip_file  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prüft alte Notizen.NET-ALX-Dateien per load/dump/load-Roundtrip. "
            "Der Bericht enthält nur Zahlen und Hashes, keine Notiztexte."
        )
    )
    parser.add_argument("files", nargs="+", help="ALX-Dateien, die geprüft werden sollen")
    parser.add_argument(
        "--password-env",
        default="",
        metavar="NAME",
        help="Name einer Umgebungsvariable mit dem ALX-Passwort; kein Passwort wird ausgegeben",
    )
    args = parser.parse_args(argv)
    password = os.environ.get(args.password_env) if args.password_env else None
    exit_code = 0

    for raw in args.files:
        path = Path(raw)
        print(f"== {path} ==")
        try:
            result = validate_alx_roundtrip_file(path, password=password)
        except AlxError as exc:
            exit_code = 2
            print(f"ERROR: {exc}")
            continue
        except OSError as exc:
            exit_code = 2
            print(f"ERROR: {exc}")
            continue
        before = result.before
        print(f"nodes={before.node_count} max_depth={before.max_depth}")
        print(
            "desktop_notes=%s visible_desktop_notes=%s images=%s"
            % (before.desktop_note_count, before.visible_desktop_note_count, before.embedded_image_count)
        )
        print(
            "rtf_chars=%s plain_chars=%s"
            % (before.rtf_character_count, before.plain_text_character_count)
        )
        print(f"tree_shape_hash={before.tree_shape_hash}")
        print(f"content_hash={before.content_hash}")
        if result.ok:
            print("roundtrip=OK")
        else:
            exit_code = 1
            print("roundtrip=DIFFERENT")
            for diff in result.differences:
                print(f"  {diff}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
