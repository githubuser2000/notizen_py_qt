from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

RecurrenceKind = Literal["none", "daily", "weekly", "monthly", "yearly"]


@dataclass(frozen=True, slots=True)
class AlarmSpec:
    """Portable alarm description used by the Qt dialog and unit tests.

    Weekdays follow Python's convention: Monday is 0 and Sunday is 6. The legacy
    ``wecker.vb`` dialog exposed one-shot, daily, weekly, monthly and yearly
    modes; this class keeps those choices independent from Qt so scheduling is
    testable without a GUI binding.
    """

    start: datetime
    message: str = "Notizen-Wecker"
    recurrence: RecurrenceKind = "none"
    interval: int = 1
    weekdays: tuple[int, ...] = ()

    def normalized(self) -> "AlarmSpec":
        interval = max(1, int(self.interval or 1))
        weekdays = tuple(sorted({int(day) for day in self.weekdays if 0 <= int(day) <= 6}))
        recurrence: RecurrenceKind
        recurrence = self.recurrence if self.recurrence in {"none", "daily", "weekly", "monthly", "yearly"} else "none"
        return AlarmSpec(
            start=self.start.replace(microsecond=0),
            message=self.message or "Notizen-Wecker",
            recurrence=recurrence,
            interval=interval,
            weekdays=weekdays,
        )


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return value.replace(year=year, month=month, day=min(value.day, last_day))


def _add_years(value: datetime, years: int) -> datetime:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        # February 29th repeats on February 28th in non-leap years, matching the
        # practical behavior users expect from yearly reminder UIs.
        return value.replace(year=value.year + years, day=28)


def next_occurrence(spec: AlarmSpec, after: datetime | None = None) -> datetime | None:
    """Return the next due time strictly after ``after``.

    ``None`` means a one-shot reminder is already expired. Repeating reminders
    keep the original start date as their anchor so intervals stay stable even if
    the application was closed for a while.
    """

    normalized = spec.normalized()
    after = (after or datetime.now()).replace(microsecond=0)
    start = normalized.start
    if normalized.recurrence == "none":
        return start if start > after else None

    if normalized.recurrence == "daily":
        if start > after:
            return start
        elapsed_days = max(0, (after.date() - start.date()).days)
        steps = elapsed_days // normalized.interval
        candidate = start + timedelta(days=steps * normalized.interval)
        while candidate <= after:
            candidate += timedelta(days=normalized.interval)
        return candidate

    if normalized.recurrence == "weekly":
        weekdays = normalized.weekdays or (start.weekday(),)
        anchor_monday = start.date() - timedelta(days=start.weekday())
        cursor_date = after.date()
        if datetime.combine(cursor_date, start.time()) <= after:
            cursor_date += timedelta(days=1)
        # Search several years ahead; this keeps odd interval/weekday settings
        # deterministic while avoiding a brittle closed-form implementation.
        horizon = max(3700, normalized.interval * 7 * 32)
        for offset in range(horizon):
            date = cursor_date + timedelta(days=offset)
            if date.weekday() not in weekdays:
                continue
            weeks_since_anchor = (date - anchor_monday).days // 7
            if weeks_since_anchor < 0 or weeks_since_anchor % normalized.interval != 0:
                continue
            candidate = datetime.combine(date, start.time())
            if candidate > after and candidate >= start:
                return candidate
        return None

    if normalized.recurrence == "monthly":
        if start > after:
            return start
        elapsed_months = max(0, (after.year - start.year) * 12 + (after.month - start.month))
        steps = elapsed_months // normalized.interval
        candidate = _add_months(start, steps * normalized.interval)
        while candidate <= after:
            steps += 1
            candidate = _add_months(start, steps * normalized.interval)
        return candidate

    if normalized.recurrence == "yearly":
        if start > after:
            return start
        elapsed_years = max(0, after.year - start.year)
        steps = elapsed_years // normalized.interval
        candidate = _add_years(start, steps * normalized.interval)
        while candidate <= after:
            steps += 1
            candidate = _add_years(start, steps * normalized.interval)
        return candidate

    return None


def describe_recurrence(spec: AlarmSpec) -> str:
    normalized = spec.normalized()
    if normalized.recurrence == "none":
        return "einmalig"
    label = {
        "daily": "täglich",
        "weekly": "wöchentlich",
        "monthly": "monatlich",
        "yearly": "jährlich",
    }[normalized.recurrence]
    if normalized.interval > 1:
        label += f" alle {normalized.interval}"
    if normalized.recurrence == "weekly" and normalized.weekdays:
        names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        label += " (" + ", ".join(names[d] for d in normalized.weekdays) + ")"
    return label
