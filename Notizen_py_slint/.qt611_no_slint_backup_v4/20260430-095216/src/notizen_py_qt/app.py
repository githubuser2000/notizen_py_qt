from __future__ import annotations

from .qt_runtime import run_qml_app
from .qt_compat import QtCompatNamespace, create_qt_window

import argparse
import importlib.util
import os
import sys
from importlib import resources
from pathlib import Path


def _normalize_legacy_argv(argv: list[str] | None = None) -> list[str]:
    """Keep old command-line tests stable while the Qt runner replaces the UI."""
    return list(sys.argv[1:] if argv is None else argv)


def _candidate_qml_files(explicit: str | None = None) -> list[Path]:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_path = os.environ.get("NOTIZEN_QML_PATH")
    if env_path:
        candidates.append(Path(env_path).expanduser())

    try:
        packaged = resources.files("notizen_py_qt.ui").joinpath("Main.qml")
        candidates.append(Path(str(packaged)))
    except Exception:
        pass

    here = Path(__file__).resolve()
    if len(here.parents) > 2:
        candidates.append(here.parents[2] / "qml" / "Main.qml")
    candidates.extend([
        here.parent / "ui" / "Main.qml",
        Path.cwd() / "qml" / "Main.qml",
    ])
    return candidates


def _first_existing_qml(explicit: str | None = None) -> Path:
    for path in _candidate_qml_files(explicit):
        if path.exists():
            return path
    tried = "\n  ".join(str(p) for p in _candidate_qml_files(explicit))
    raise FileNotFoundError(f"Keine QML-Startdatei gefunden. Geprüft:\n  {tried}")


class NotizenQtApp:
    """Qt/QML application runner used after the UI migration."""

    def __init__(self, initial_path: str | None = None, password: str | None = None, qml_path: str | None = None) -> None:
        self.initial_path = initial_path
        self.password = password
        self.qml_path = qml_path
        self.status_text = "Bereit"
        self.window = None
        self.backend = None

    def _set_status(self, message: str) -> None:
        self.status_text = message
        backend = getattr(self, "backend", None)
        if backend is not None and hasattr(backend, "setStatusText"):
            backend.setStatusText(message)

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
        if smoke_test:
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QGuiApplication
            from PySide6.QtQml import QQmlApplicationEngine
            try:
                from PySide6.QtQuickControls2 import QQuickStyle
            except Exception:
                QQuickStyle = None
            from .qt_backend import NotizenQtBackend
        except ModuleNotFoundError as exc:
            if exc.name and exc.name.startswith("PySide6"):
                print("PySide6 ist nicht installiert. Installiere Qt for Python mit:")
                print("  python3 -m pip install -e .")
                print("oder:")
                print("  python3 -m pip install 'PySide6>=6.11,<6.12'")
                return 2
            raise

        qml_file = _first_existing_qml(self.qml_path)
        app = QGuiApplication.instance() or QGuiApplication(sys.argv)
        if QQuickStyle is not None:
            try:
                QQuickStyle.setStyle("Fusion")
            except Exception:
                pass

        self.backend = NotizenQtBackend()
        if self.initial_path:
            self.backend.setInitialPath(self.initial_path)

        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("notizenBackend", self.backend)
        engine.load(QUrl.fromLocalFile(str(qml_file)))
        roots = engine.rootObjects()
        if not roots:
            print(f"QML konnte nicht geladen werden: {qml_file}", file=sys.stderr)
            return 3
        self.window = roots[0]
        if smoke_test:
            return 0
        return int(app.exec())


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

    app = NotizenQtApp(initial_path=args.file, password=args.password, qml_path=args.qml_path)
    return app.run(smoke_test=args.smoke_test)


if __name__ == "__main__":
    raise SystemExit(main())
