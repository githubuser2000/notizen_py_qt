from __future__ import annotations

from datetime import datetime
from pathlib import Path

from notizen_py_qt.alx_io import (
    BackupEntry,
    backup_directory_for,
    backup_file_pattern,
    create_backup,
    list_backups,
    parse_legacy_backup_timestamp,
    prune_backups,
)


def test_legacy_backup_directory_and_timestamp() -> None:
    path = Path("/tmp/notizen/demo.alx")
    assert backup_directory_for(path) == Path("/tmp/notizen/demo")
    assert backup_file_pattern(path) == "demo-*.alx"
    stamp = parse_legacy_backup_timestamp("/tmp/notizen/demo/demo-2026-05-01-14-03-02-123.alx", path)
    assert stamp == datetime(2026, 5, 1, 14, 3, 2, 123_000)
    assert parse_legacy_backup_timestamp("/tmp/notizen/demo/other-2026-05-01-14-03-02-123.alx", path) is None


def test_create_backup_copies_to_legacy_safety_folder_and_prunes(tmp_path: Path) -> None:
    target = tmp_path / "notes.alx"
    target.write_bytes(b"new content")
    backup_dir = backup_directory_for(target)
    backup_dir.mkdir()

    old_names = [
        "notes-2024-01-01-01-01-01-001.alx",
        "notes-2024-01-02-01-01-01-001.alx",
        "notes-2024-01-03-01-01-01-001.alx",
    ]
    for name in old_names:
        (backup_dir / name).write_bytes(name.encode("ascii"))

    created = create_backup(target, keep=2)

    assert created is not None
    assert created.parent == backup_dir
    assert created.name.startswith("notes-20")
    assert created.suffix == ".alx"
    assert created.read_bytes() == b"new content"

    backups = list_backups(target)
    assert len(backups) == 2
    assert all(isinstance(entry, BackupEntry) for entry in backups)
    assert backups[-1].path == created
    assert not (backup_dir / old_names[0]).exists()
    assert not (backup_dir / old_names[1]).exists()


def test_prune_backups_keep_zero_removes_all(tmp_path: Path) -> None:
    target = tmp_path / "notes.alx"
    target.write_text("x", encoding="utf-8")
    backup_dir = backup_directory_for(target)
    backup_dir.mkdir()
    for day in range(1, 4):
        (backup_dir / f"notes-2024-02-0{day}-00-00-00-000.alx").write_text(str(day), encoding="utf-8")

    removed = prune_backups(target, keep=0)

    assert len(removed) == 3
    assert list_backups(target) == []
