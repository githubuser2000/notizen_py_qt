from __future__ import annotations

from datetime import datetime

from notizen_py_qt.alarms import (
    AlarmSpec,
    LEGACY_WECKER_WEEKDAY_CHECKBOXES,
    describe_recurrence,
    legacy_wecker_interval_unit,
    legacy_wecker_weekday_for_checkbox,
    legacy_wecker_weekday_labels,
    next_occurrence,
)


def test_wecker_vb_weekday_checkboxes_keep_legacy_control_order() -> None:
    # From wecker.Designer.vb: Monday was CheckBox15 and Sunday CheckBox13.
    assert LEGACY_WECKER_WEEKDAY_CHECKBOXES[0] == ("CheckBox15", 0, "Montag")
    assert LEGACY_WECKER_WEEKDAY_CHECKBOXES[-1] == ("CheckBox13", 6, "Sonntag")
    assert legacy_wecker_weekday_for_checkbox("CheckBox15") == 0
    assert legacy_wecker_weekday_for_checkbox("checkbox12") == 1
    assert legacy_wecker_weekday_for_checkbox("CheckBox13") == 6
    assert legacy_wecker_weekday_for_checkbox("CheckBox999") is None
    assert legacy_wecker_weekday_labels() == (
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    )


def test_wecker_interval_units_and_disabled_state() -> None:
    assert legacy_wecker_interval_unit("daily") == "Tage"
    assert legacy_wecker_interval_unit("weekly") == "Wochen"
    assert legacy_wecker_interval_unit("monthly") == "Monate"
    assert legacy_wecker_interval_unit("yearly") == "Jahre"
    assert legacy_wecker_interval_unit("none") == ""

    disabled = AlarmSpec(datetime(2026, 5, 3, 9, 0), recurrence="daily", enabled=False)
    assert next_occurrence(disabled, datetime(2026, 5, 3, 8, 0)) is None
    assert describe_recurrence(disabled) == "deaktiviert"
    assert disabled.normalized().enabled is False
