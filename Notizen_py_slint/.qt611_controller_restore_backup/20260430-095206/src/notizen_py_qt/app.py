from __future__ import annotations

import argparse
import os
import sys

from .qt_backend import NotizenQtBackend
from .qt_runtime import run_qml_app


def _normalize_legacy_argv(argv: list[str] | None = None) -> list[str]:
    return list(sys.argv[1:] if argv is None else argv)


class NotizenQtApp:
    """Qt/QML runner for the migrated Notizen UI."""

    def __init__(self, initial_path: str | None = None, password: str | None = None, qml_path: str | None = None) -> None:
        self.initial_path = initial_path
        self.password = password
        self.qml_path = qml_path
        self.backend = NotizenQtBackend()
        if initial_path:
            self.backend.setInitialPath(initial_path)

    def _set_status(self, message: str) -> None:
        self.backend.setStatusText(message)

    def show_about(self) -> None:
        self._set_status("Notizen Qt")

    def show_shortcuts(self) -> None:
        self._set_status("Tastenkürzel sind im Qt-Menü verfügbar.")

    def show_context_menus(self) -> None:
        self._set_status("Kontextmenüs werden über Qt Quick Controls bereitgestellt.")

    def show_password_info(self) -> None:
        self._set_status("Passwortkompatibilität bleibt im Python-Kern.")

    def show_toolstrips(self) -> None:
        self._set_status("Werkzeugleisten werden durch Qt ToolBar/Action ersetzt.")

    def show_compat_report(self) -> None:
        self._set_status("Qt-Migrationsbericht liegt in QT611_MIGRATION_STATUS.md.")

    def show_default_paths(self) -> None:
        self._set_status("Standardpfade werden vom bestehenden Python-Kern verwaltet.")

    def rename_row(self, index: int) -> None:
        self._set_status(f"Umbenennen angefordert: Zeile {index}")

    def run(self, smoke_test: bool = False) -> int:
        return run_qml_app(backend=self.backend, qml_path=self.qml_path, smoke_test=smoke_test)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Notizen.NET-Port für Python mit Qt/QML")
    parser.add_argument("file", nargs="?", help="ALX/Notizen-Datei zum Öffnen")
    parser.add_argument("--password", help="Passwort für geschützte Dateien")
    parser.add_argument("--qml", dest="qml_path", help="Explizite QML-Startdatei")
    parser.add_argument("--fullscreen", action="store_true", help="Qt-Fenster im Vollbild starten")
    parser.add_argument("--smoke-test", action="store_true", help="QML laden und ohne Eventloop beenden")
    args = parser.parse_args(_normalize_legacy_argv(argv))
    if args.fullscreen:
        os.environ.setdefault("QT_FULLSCREEN", "1")
    return NotizenQtApp(initial_path=args.file, password=args.password, qml_path=args.qml_path).run(smoke_test=args.smoke_test)


if __name__ == "__main__":
    raise SystemExit(main())
