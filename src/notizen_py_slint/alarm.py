from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

from .config import config_dir

_REPEAT_VALUES = {"none", "daily", "weekly", "monthly", "yearly"}
_WEEKDAY_NAMES = {
    "mo": 0,
    "mon": 0,
    "monday": 0,
    "montag": 0,
    "di": 1,
    "tue": 1,
    "tuesday": 1,
    "dienstag": 1,
    "mi": 2,
    "wed": 2,
    "wednesday": 2,
    "mittwoch": 2,
    "do": 3,
    "thu": 3,
    "thursday": 3,
    "donnerstag": 3,
    "fr": 4,
    "fri": 4,
    "friday": 4,
    "freitag": 4,
    "sa": 5,
    "sat": 5,
    "saturday": 5,
    "samstag": 5,
    "so": 6,
    "sun": 6,
    "sunday": 6,
    "sonntag": 6,
}
_WEEKDAY_LABELS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


@dataclass(slots=True)
class AlarmRule:
    """Port of the old Wecker dialog as serializable recurrence logic."""

    name: str
    at: str
    active: bool = True
    repeat: str = "none"
    interval: int = 1
    weekdays: list[int] = field(default_factory=list)
    message: str = ""
    note_title: str = ""

    @classmethod
    def create(
        cls,
        name: str,
        at: str | datetime,
        *,
        active: bool = True,
        repeat: str = "none",
        interval: int = 1,
        weekdays: list[int] | None = None,
        message: str = "",
        note_title: str = "",
    ) -> "AlarmRule":
        moment = at if isinstance(at, datetime) else parse_alarm_datetime(at)
        repeat = normalize_repeat(repeat)
        return cls(
            name=name.strip() or "Wecker",
            at=moment.strftime("%Y-%m-%d %H:%M"),
            active=active,
            repeat=repeat,
            interval=max(1, int(interval or 1)),
            weekdays=sorted(set(weekdays or [])),
            message=message,
            note_title=note_title,
        )

    @property
    def start(self) -> datetime:
        return parse_alarm_datetime(self.at)

    def next_after(self, after: datetime | None = None) -> datetime | None:
        if not self.active:
            return None
        after = after or datetime.now()
        start = self.start
        if self.repeat == "none":
            return start if start >= after else None
        if start >= after:
            return start
        if self.repeat == "daily":
            delta_days = max(0, (after.date() - start.date()).days)
            jumps = delta_days // self.interval
            candidate = start + timedelta(days=jumps * self.interval)
            while candidate < after:
                candidate += timedelta(days=self.interval)
            return candidate
        if self.repeat == "weekly":
            return self._next_weekly(after)
        if self.repeat == "monthly":
            candidate = start
            while candidate < after:
                candidate = add_months(candidate, self.interval)
            return candidate
        if self.repeat == "yearly":
            candidate = start
            while candidate < after:
                candidate = add_years(candidate, self.interval)
            return candidate
        return None

    def _next_weekly(self, after: datetime) -> datetime | None:
        start = self.start
        weekdays = self.weekdays or [start.weekday()]
        week0 = start.date() - timedelta(days=start.weekday())
        cursor = after.date()
        for _ in range(3660):
            week = cursor - timedelta(days=cursor.weekday())
            week_delta = (week - week0).days // 7
            if week_delta >= 0 and week_delta % self.interval == 0 and cursor.weekday() in weekdays:
                candidate = datetime.combine(cursor, start.time())
                if candidate >= start and candidate >= after:
                    return candidate
            cursor += timedelta(days=1)
        return None

    def summary(self, *, now: datetime | None = None) -> str:
        next_at = self.next_after(now)
        repeat = self.repeat
        if self.repeat == "weekly" and self.weekdays:
            repeat += " " + "/".join(_WEEKDAY_LABELS[d] for d in self.weekdays if 0 <= d <= 6)
        next_text = next_at.strftime("%Y-%m-%d %H:%M") if next_at else "kein nächster Termin"
        return f"{self.name}: {next_text} ({'aktiv' if self.active else 'aus'}, {repeat})"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AlarmRule":
        return cls.create(
            str(data.get("name") or "Wecker"),
            str(data.get("at") or datetime.now().strftime("%Y-%m-%d %H:%M")),
            active=bool(data.get("active", True)),
            repeat=str(data.get("repeat") or "none"),
            interval=int(data.get("interval") or 1),
            weekdays=[int(x) for x in data.get("weekdays", []) or []],
            message=str(data.get("message") or ""),
            note_title=str(data.get("note_title") or ""),
        )


def parse_alarm_datetime(value: str) -> datetime:
    text = value.strip()
    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%d.%m.%Y %H:%M", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError("Datum/Zeit erwartet, z.B. 2026-04-27 09:30 oder 27.04.2026 09:30")


def normalize_repeat(value: str) -> str:
    text = (value or "none").strip().lower()
    aliases = {
        "no": "none",
        "none": "none",
        "einmal": "none",
        "once": "none",
        "tag": "daily",
        "tage": "daily",
        "daily": "daily",
        "day": "daily",
        "woche": "weekly",
        "wochen": "weekly",
        "weekly": "weekly",
        "week": "weekly",
        "monat": "monthly",
        "monate": "monthly",
        "monthly": "monthly",
        "month": "monthly",
        "jahr": "yearly",
        "jahre": "yearly",
        "yearly": "yearly",
        "year": "yearly",
    }
    result = aliases.get(text, text)
    if result not in _REPEAT_VALUES:
        raise ValueError(f"Unbekannte Wiederholung: {value}")
    return result


def parse_weekdays(values: list[str] | None) -> list[int]:
    days: list[int] = []
    for value in values or []:
        for part in str(value).replace(",", " ").split():
            key = part.strip().lower()
            if not key:
                continue
            if key.isdigit():
                day = int(key)
                if 0 <= day <= 6:
                    days.append(day)
                    continue
            if key not in _WEEKDAY_NAMES:
                raise ValueError(f"Unbekannter Wochentag: {part}")
            days.append(_WEEKDAY_NAMES[key])
    return sorted(set(days))


def add_months(value: datetime, months: int) -> datetime:
    month0 = value.month - 1 + months
    year = value.year + month0 // 12
    month = month0 % 12 + 1
    day = min(value.day, _days_in_month(year, month))
    return value.replace(year=year, month=month, day=day)


def add_years(value: datetime, years: int) -> datetime:
    year = value.year + years
    day = min(value.day, _days_in_month(year, value.month))
    return value.replace(year=year, day=day)


def load_alarms(path: str | Path | None = None) -> list[AlarmRule]:
    path = Path(path) if path is not None else alarm_store_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [AlarmRule.from_dict(item) for item in data]


def save_alarms(alarms: list[AlarmRule], path: str | Path | None = None) -> Path:
    path = Path(path) if path is not None else alarm_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([alarm.to_dict() for alarm in alarms], indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def alarm_store_path() -> Path:
    return config_dir() / "alarms.json"


def add_or_replace_alarm(alarm: AlarmRule, path: str | Path | None = None) -> list[AlarmRule]:
    alarms = [item for item in load_alarms(path) if item.name != alarm.name]
    alarms.append(alarm)
    alarms.sort(key=lambda item: item.next_after() or datetime.max)
    save_alarms(alarms, path)
    return alarms


def remove_alarm(name: str, path: str | Path | None = None) -> bool:
    alarms = load_alarms(path)
    kept = [item for item in alarms if item.name != name]
    save_alarms(kept, path)
    return len(kept) != len(alarms)


def next_alarm(alarms: list[AlarmRule], *, now: datetime | None = None) -> tuple[AlarmRule, datetime] | None:
    now = now or datetime.now()
    candidates = [(alarm, alarm.next_after(now)) for alarm in alarms]
    valid = [(alarm, when) for alarm, when in candidates if when is not None]
    if not valid:
        return None
    alarm, when = min(valid, key=lambda item: item[1])
    return alarm, when  # type: ignore[return-value]


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day
