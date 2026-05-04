from __future__ import annotations

import gzip
from datetime import date, datetime
from xml.etree import ElementTree as ET

from notizen_py_qt.feedback import (
    LEGACY_FEEDBACK_DAILY_INCREMENT,
    dotnet_date_ticks,
    legacy_feedback_decision,
    legacy_feedback_filename,
    legacy_feedback_next_state,
    write_local_feedback_archive,
)
from notizen_py_qt.settings import AppSettings


def test_dotnet_today_ticks_matches_known_epoch_day() -> None:
    assert dotnet_date_ticks(date(1, 1, 1)) == 0
    assert dotnet_date_ticks(date(1, 1, 2)) == 24 * 60 * 60 * 10_000_000


def test_legacy_feedback_throttle_rules() -> None:
    today = dotnet_date_ticks(date(2026, 5, 4))
    assert not legacy_feedback_decision(text="kurz", previous_day_ticks=0, previous_count=0, today_ticks=today).allowed
    assert legacy_feedback_decision(text="lange genug", previous_day_ticks=0, previous_count=99, today_ticks=today).allowed
    assert legacy_feedback_decision(text="lange genug", previous_day_ticks=today, previous_count=20, today_ticks=today).allowed
    blocked = legacy_feedback_decision(text="lange genug", previous_day_ticks=today, previous_count=30, today_ticks=today)
    assert not blocked.allowed
    assert blocked.reason == "no-send"


def test_legacy_feedback_next_state() -> None:
    today = dotnet_date_ticks(date(2026, 5, 4))
    assert legacy_feedback_next_state(previous_day_ticks=0, previous_count=30, today_ticks=today).count == 0
    same_day = legacy_feedback_next_state(previous_day_ticks=today, previous_count=10, today_ticks=today)
    assert same_day.day_ticks == today
    assert same_day.count == 10 + LEGACY_FEEDBACK_DAILY_INCREMENT


def test_local_feedback_archive_is_utf16_gzip(tmp_path) -> None:
    target = write_local_feedback_archive("Hallo Feedback", tmp_path, now=datetime(2026, 5, 4, 9, 30, 5))
    assert target.name == legacy_feedback_filename(datetime(2026, 5, 4, 9, 30, 5))
    with gzip.open(target, "rb") as stream:
        assert stream.read().decode("utf-16-le") == "Hallo Feedback"


def test_settings_preserve_feedback_x_y_z(tmp_path) -> None:
    settings = AppSettings(config_dir=tmp_path)
    xml = '''<?xml version="1.0" encoding="utf-16"?>
<notizen-alx>
  <x y="123456" z="20" a="60" extra="keep" />
</notizen-alx>
'''
    path = tmp_path / "notizen.config.xml"
    path.write_text(xml, encoding="utf-16")
    settings.apply_from_file(path)
    assert settings.feedback_day_ticks == 123456
    assert settings.feedback_count == 20
    settings.feedback_day_ticks = 789
    settings.feedback_count = 30
    settings.save()
    root = ET.parse(settings.path).getroot()
    x = root.find("x")
    assert x is not None
    assert x.get("y") == "789"
    assert x.get("z") == "30"
    assert x.get("a") == "60"
    assert x.get("extra") == "keep"
