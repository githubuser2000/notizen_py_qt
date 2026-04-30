from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StartupOptions:
    """Command-line options compatible with the legacy Notizen.NET launcher."""

    file: str | None = None
    minimized: bool = False
    help_requested: bool = False
    cleaned_args: tuple[str, ...] = ()


_LEGACY_MIN_FLAGS = {"/min", "-min", "min"}
_LEGACY_HELP_FLAGS = {"/h", "-h", "h", "/?", "-?", "?"}


def _looks_like_notizen_file(token: str) -> bool:
    lower = token.casefold()
    return lower.endswith(".alx") or lower.startswith("ftp://")


def parse_legacy_startup_args(argv: list[str] | tuple[str, ...]) -> StartupOptions:
    """Strip old WinForms flags while preserving modern argparse flags.

    Notizen.NET accepted ``/min``, ``-min`` and ``min`` for minimized startup,
    plus ``/h``/``/?`` variants for help. It also accepted local ``.alx`` files
    and ``ftp://`` URLs as positional startup targets.
    """
    file: str | None = None
    minimized = False
    help_requested = False
    cleaned: list[str] = []

    skip_next = False
    for raw in argv:
        if skip_next:
            cleaned.append(raw)
            skip_next = False
            continue

        token = str(raw)
        lower = token.casefold()
        if lower in _LEGACY_MIN_FLAGS:
            minimized = True
            continue
        if lower in _LEGACY_HELP_FLAGS:
            help_requested = True
            continue
        if _looks_like_notizen_file(token):
            file = token
            continue

        cleaned.append(token)
        if token in {"--password"}:
            skip_next = True

    return StartupOptions(file=file, minimized=minimized, help_requested=help_requested, cleaned_args=tuple(cleaned))
