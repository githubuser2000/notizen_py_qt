from __future__ import annotations

import gzip
import subprocess
import sys
from pathlib import Path

from notizen_py_qt.legacy_validation import summarize_alx_file, validate_alx_roundtrip_bytes, validate_alx_roundtrip_file
from notizen_py_qt.rtf_utils import plain_text_to_rtf

FIXTURES = Path(__file__).parent / "fixtures"


def test_legacy_validation_summarizes_fixture_without_raw_text() -> None:
    summary = summarize_alx_file(FIXTURES / "legacy_sanitized_desktop.alx")
    assert summary.node_count == 4
    assert summary.max_depth == 2
    assert summary.desktop_note_count == 2
    assert len(summary.tree_shape_hash) == 64
    assert len(summary.content_hash) == 64


def test_legacy_validation_roundtrip_ok_for_sparse_legacy_desknote() -> None:
    xml = (
        '<?xml version="1.0" encoding="utf-16"?>'
        '<notizen-alx2><Notiz name="root"><Notiz name="desk" visible="True" x="1" y="2" width="3" height="4">'
        + plain_text_to_rtf("text")
        + '</Notiz></Notiz></notizen-alx2>'
    )
    payload = gzip.compress(xml.encode("utf-16"), mtime=0)
    result = validate_alx_roundtrip_bytes(payload)
    assert result.ok is True
    assert result.before == result.after


def test_validate_legacy_alx_script_reports_roundtrip_ok() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/validate_legacy_alx.py", str(FIXTURES / "legacy_unbenannt.alx")],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    assert "roundtrip=OK" in proc.stdout
    assert "nodes=1" in proc.stdout
