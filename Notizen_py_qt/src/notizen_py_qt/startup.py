from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True, slots=True)
class StartupOptions:
    """Command-line options compatible with the legacy Notizen.NET launcher."""

    file: str | None = None
    minimized: bool = False
    help_requested: bool = False
    cleaned_args: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StartupTargetValidation:
    """Validated legacy startup target and a possible missing local file."""

    options: StartupOptions
    missing_file: str | None = None


@dataclass(frozen=True, slots=True)
class AutostartResult:
    """Result of applying the legacy autorun preference."""

    changed: bool
    path: Path | None
    command: str
    message: str


_LEGACY_MIN_FLAGS = {"/min", "-min", "min"}
_LEGACY_HELP_FLAGS = {"/h", "-h", "h", "/?", "-?", "?"}
_AUTOSTART_SCRIPT_NAME = "Notizen PyQt.cmd"


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


def validate_legacy_startup_target(
    options: StartupOptions,
    *,
    exists: Callable[[str], bool] | None = None,
) -> StartupTargetValidation:
    """Mirror the old startup guard for missing local ``.alx`` files.

    ``ApplicationEvents.vb`` accepted a local ``.alx`` path but cleared it again
    when the file did not exist.  FTP targets were exempt because they cannot be
    checked through the local filesystem.
    """

    if not options.file:
        return StartupTargetValidation(options=options)
    if options.file.casefold().startswith("ftp://"):
        return StartupTargetValidation(options=options)

    exists_func = exists or (lambda path: Path(path).exists())
    if exists_func(options.file):
        return StartupTargetValidation(options=options)
    return StartupTargetValidation(options=replace(options, file=None), missing_file=options.file)


def legacy_autostart_target_file(recent_files: list[str] | tuple[str, ...]) -> str:
    """Return the file that ``xml_kram.setshortcut`` would put into autorun.

    The old config stored four recent files as ``a``..``d`` and preferred
    ``d`` first, then ``c``, ``b`` and ``a``.  ``AppSettings.recent_files``
    stores the same order as a list, so the newest usable entry is the last one.
    """

    for candidate in reversed([str(item) for item in recent_files if str(item).strip()]):
        if "\\" in candidate or "/" in candidate or candidate.lower().startswith("ftp://"):
            return candidate
    return ""


def legacy_autostart_arguments(
    *,
    enabled: bool,
    minimized: bool,
    recent_files: list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    """Build the legacy command-line tail for autorun.

    This mirrors ``xml_kram.setshortcut``: when a recent file exists it is
    appended, and ``-min`` is prepended if minimized autorun is selected.
    """

    if not enabled:
        return ()
    target = legacy_autostart_target_file(recent_files)
    args: list[str] = []
    if minimized:
        args.append("-min")
    if target:
        args.append(target)
    return tuple(args)


def build_autostart_command(
    *,
    python_executable: str | Path | None = None,
    module: str = "notizen_py_qt",
    arguments: tuple[str, ...] = (),
) -> str:
    """Return a Windows-safe command for starting this port via ``python -m``.

    ``subprocess.list2cmdline`` is used intentionally because the legacy code
    mostly cared about Windows shortcut arguments and quoted file paths.
    """

    executable = str(python_executable or sys.executable)
    return subprocess.list2cmdline([executable, "-m", module, *arguments])


def windows_startup_folder(appdata: str | Path | None = None) -> Path:
    """Return the per-user Windows Startup folder used by the legacy app."""

    base = Path(appdata or os.environ.get("APPDATA", ""))
    if not str(base):
        return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return base / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def autostart_script_path(startup_dir: str | Path | None = None) -> Path:
    return Path(startup_dir) / _AUTOSTART_SCRIPT_NAME if startup_dir is not None else windows_startup_folder() / _AUTOSTART_SCRIPT_NAME


def apply_windows_autostart_script(
    *,
    enabled: bool,
    minimized: bool,
    recent_files: list[str] | tuple[str, ...],
    python_executable: str | Path | None = None,
    startup_dir: str | Path | None = None,
) -> AutostartResult:
    """Create or remove the Windows Startup script for the autorun setting.

    The original VB.NET code created a ``.lnk`` file through Windows shell
    automation.  The Python/Qt port keeps the behavior dependency-free by
    writing a small ``.cmd`` launcher in the same Startup folder.  On non-Windows
    systems the helper is a no-op unless ``startup_dir`` is passed by tests or
    by a future platform adapter.
    """

    path = autostart_script_path(startup_dir)
    if os.name != "nt" and startup_dir is None:
        return AutostartResult(
            changed=False,
            path=None,
            command="",
            message="Autostart wird auf diesem System nicht automatisch eingerichtet.",
        )

    if not enabled:
        if path.exists():
            path.unlink()
            return AutostartResult(True, path, "", "Autostart entfernt.")
        return AutostartResult(False, path, "", "Autostart war nicht eingerichtet.")

    args = legacy_autostart_arguments(enabled=True, minimized=minimized, recent_files=recent_files)
    command = build_autostart_command(python_executable=python_executable, arguments=args)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"@echo off\r\nstart \"\" {command}\r\n", encoding="utf-8")
    return AutostartResult(True, path, command, "Autostart eingerichtet.")
