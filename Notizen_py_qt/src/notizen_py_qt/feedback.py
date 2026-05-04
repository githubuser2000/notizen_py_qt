from __future__ import annotations

import gzip
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

LEGACY_FEEDBACK_MIN_CHARS = 10
LEGACY_FEEDBACK_DAILY_LIMIT = 30
LEGACY_FEEDBACK_DAILY_INCREMENT = 10
LEGACY_FEEDBACK_EMAIL = "notizen@notiza.de"
LEGACY_FEEDBACK_WEB_URL = "http://www.notiza.de"


@dataclass(frozen=True, slots=True)
class FeedbackDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class FeedbackThrottleState:
    day_ticks: int
    count: int


def dotnet_date_ticks(day: date | None = None) -> int:
    """Return .NET ``DateTime.Today.Ticks`` for ``day``.

    The legacy feedback throttle stored ``DateTime.Today.Ticks`` in config
    attribute ``x.y``.  .NET ticks are 100 ns units since 0001-01-01.
    """

    day = day or date.today()
    return (day.toordinal() - 1) * 24 * 60 * 60 * 10_000_000


def legacy_feedback_text_is_long_enough(text: str) -> bool:
    """Notizen.NET required more than nine characters before sending."""

    return len(text or "") >= LEGACY_FEEDBACK_MIN_CHARS


def legacy_feedback_decision(*, text: str, previous_day_ticks: int, previous_count: int, today_ticks: int | None = None) -> FeedbackDecision:
    """Return whether the old feedback dialog would allow one more send.

    The VB.NET condition was ``when < Today.Ticks`` or ``when == Today.Ticks``
    with ``count < 30``.  The Python port keeps that throttle, but stores a
    local gzip feedback file instead of uploading to the old hard-coded FTP
    endpoint.
    """

    if not legacy_feedback_text_is_long_enough(text):
        return FeedbackDecision(False, "char10minimum")
    today = dotnet_date_ticks() if today_ticks is None else int(today_ticks)
    when = int(previous_day_ticks or 0)
    count = int(previous_count or 0)
    if when < today:
        return FeedbackDecision(True, "new-day")
    if when == today and count < LEGACY_FEEDBACK_DAILY_LIMIT:
        return FeedbackDecision(True, "same-day")
    return FeedbackDecision(False, "no-send")


def legacy_feedback_next_state(*, previous_day_ticks: int, previous_count: int, today_ticks: int | None = None) -> FeedbackThrottleState:
    """Return the next ``x.y``/``x.z`` feedback throttle state.

    The original reset ``z`` on a new day and added ten for each same-day send.
    It then attempted to save ``x.y``; the port does this in the safe order so
    the throttle actually persists.
    """

    today = dotnet_date_ticks() if today_ticks is None else int(today_ticks)
    when = int(previous_day_ticks or 0)
    count = int(previous_count or 0)
    if when < today:
        return FeedbackThrottleState(day_ticks=today, count=0)
    return FeedbackThrottleState(day_ticks=today, count=count + LEGACY_FEEDBACK_DAILY_INCREMENT)


def legacy_feedback_filename(now: datetime | None = None) -> str:
    """Return a filesystem-safe counterpart to the old FTP feedback filename."""

    now = now or datetime.now()
    stamp = now.strftime("%Y-%m-%d-%H-%M-%S")
    return f"feedback.{stamp}.txt.gz"


def write_local_feedback_archive(text: str, directory: str | Path, *, now: datetime | None = None) -> Path:
    """Write feedback as UTF-16 gzip like the old FTP upload payload."""

    target_dir = Path(directory).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / legacy_feedback_filename(now)
    with gzip.open(target, "wb") as stream:
        stream.write((text or "").encode("utf-16-le"))
    return target
