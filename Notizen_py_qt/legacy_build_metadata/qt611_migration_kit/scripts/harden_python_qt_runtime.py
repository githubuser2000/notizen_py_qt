#!/usr/bin/env python3
"""Install a robust Python/Qt runtime layer for the migrated Notizen package."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from qt611_project_utils import find_project_root

QT_RUNTIME = r'''
from __future__ import annotations

import os
import sys
from importlib import resources
from pathlib import Path
from typing import Iterable


def candidate_qml_files(explicit: str | None = None, package: str = "notizen_py_qt.ui") -> list[Path]:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_path = os.environ.get("NOTIZEN_QML_PATH")
    if env_path:
        candidates.append(Path(env_path).expanduser())
    for name in ("Main.qml", "AppWindow.qml", "app-window_AppWindow.qml", "main.qml", "app-window.qml"):
        try:
            candidates.append(Path(str(resources.files(package).joinpath(name))))
        except Exception:
            pass
    here = Path(__file__).resolve()
    roots: list[Path] = [here.parent / "ui"]
    if len(here.parents) > 2:
        roots.append(here.parents[2] / "qml")
    roots.extend([Path.cwd() / "qml", Path.cwd() / "src" / "notizen_py_qt" / "ui"])
    for root in roots:
        for name in ("Main.qml", "AppWindow.qml", "app-window_AppWindow.qml", "main.qml", "app-window.qml"):
            candidates.append(root / name)
    # Preserve order but remove duplicates.
    out: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def first_existing_qml(explicit: str | None = None) -> Path:
    for path in candidate_qml_files(explicit):
        if path.exists():
            return path
    tried = "\n  ".join(str(p) for p in candidate_qml_files(explicit))
    raise FileNotFoundError(f"Keine QML-Startdatei gefunden. Geprüft:\n  {tried}")


def prepare_qt_environment(smoke_test: bool = False) -> None:
    if smoke_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.setdefault("QSG_RHI_BACKEND", "software")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")


def run_qml_app(backend: object | None = None, qml_path: str | None = None, smoke_test: bool = False, argv: list[str] | None = None) -> int:
    prepare_qt_environment(smoke_test=smoke_test)
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtQml import QQmlApplicationEngine
        try:
            from PySide6.QtQuickControls2 import QQuickStyle
        except Exception:  # pragma: no cover - module availability varies by wheel split
            QQuickStyle = None
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PySide6"):
            print("PySide6 ist nicht installiert oder passt nicht zu dieser Python-Version.", file=sys.stderr)
            print("Installiere Qt for Python im Projekt-Interpreter:", file=sys.stderr)
            print("  python3 -m pip install -e .", file=sys.stderr)
            print("oder direkt:", file=sys.stderr)
            print("  python3 -m pip install 'PySide6>=6.11,<6.12'", file=sys.stderr)
            return 2
        raise

    qml_file = first_existing_qml(qml_path)
    app = QGuiApplication.instance() or QGuiApplication(sys.argv if argv is None else argv)
    if QQuickStyle is not None:
        try:
            QQuickStyle.setStyle(os.environ.get("NOTIZEN_QT_STYLE", "Fusion"))
        except Exception:
            pass

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_file.parent))
    engine.addImportPath(str(Path.cwd() / "qml"))
    if backend is not None:
        engine.rootContext().setContextProperty("notizenBackend", backend)
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    roots = engine.rootObjects()
    if not roots:
        print(f"QML konnte nicht geladen werden: {qml_file}", file=sys.stderr)
        return 3
    root = roots[0]
    if os.environ.get("QT_FULLSCREEN") == "1" and hasattr(root, "showFullScreen"):
        try:
            root.showFullScreen()
        except Exception:
            pass
    if smoke_test:
        return 0
    return int(app.exec())
'''

QT_BACKEND = r'''
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot


class NotizenQtBackend(QObject):
    """QObject bridge exposed to QML as ``notizenBackend``."""

    statusTextChanged = Signal()
    contentTextChanged = Signal()
    rowsJsonChanged = Signal()
    initialPathChanged = Signal()
    actionRequested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._status_text = "Bereit"
        self._content_text = ""
        self._rows_json = "[]"
        self._initial_path = ""

    @Property(str, notify=statusTextChanged)
    def statusText(self) -> str:
        return self._status_text

    @Slot(str)
    def setStatusText(self, value: str) -> None:
        value = str(value)
        if self._status_text != value:
            self._status_text = value
            self.statusTextChanged.emit()

    @Property(str, notify=contentTextChanged)
    def contentText(self) -> str:
        return self._content_text

    @Slot(str)
    def setContentText(self, value: str) -> None:
        value = str(value)
        if self._content_text != value:
            self._content_text = value
            self.contentTextChanged.emit()

    @Property(str, notify=rowsJsonChanged)
    def rowsJson(self) -> str:
        return self._rows_json

    @Slot(str)
    def setRowsJson(self, value: str) -> None:
        try:
            json.loads(value or "[]")
        except Exception:
            value = "[]"
        if self._rows_json != value:
            self._rows_json = value
            self.rowsJsonChanged.emit()

    @Property(str, notify=initialPathChanged)
    def initialPath(self) -> str:
        return self._initial_path

    @Slot(str)
    def setInitialPath(self, value: str) -> None:
        value = str(Path(value).expanduser()) if value else ""
        if self._initial_path != value:
            self._initial_path = value
            self.initialPathChanged.emit()
            self.setStatusText(f"Startdatei: {value}" if value else "Bereit")

    @Slot(str, result=str)
    def echo(self, value: str) -> str:
        return value

    @Slot(str, str)
    def trigger(self, action: str, payload: str = "") -> None:
        self.actionRequested.emit(str(action), str(payload))
        self.setStatusText(f"Aktion: {action}")

    @Slot(str)
    def openFile(self, path: str) -> None:
        self.setInitialPath(path)
        self.trigger("open-file", path)

    @Slot(str)
    def saveFile(self, path: str) -> None:
        self.trigger("save-file", path)

    @Slot(str)
    def notify(self, message: str) -> None:
        self.setStatusText(message)
'''

QT_COMPAT = r'''
from __future__ import annotations

import json
import os
from collections.abc import Iterable
from typing import Any, Callable


class QtListModel(list):
    """Small replacement for the former UI toolkit's Python ListModel."""

    def __init__(self, values: Iterable[Any] | None = None) -> None:
        super().__init__(values or [])

    def set_array(self, values: Iterable[Any]) -> None:
        self[:] = list(values)


class QtCompatNamespace:
    ListModel = QtListModel


class QtCompatWindow:
    """Dynamic window proxy used by the controller during the Qt migration.

    It stores properties such as ``rows`` and ``window_title`` and records old
    ``on_name(callback)`` callback registrations. When PySide6 is available,
    ``run()`` opens the generated QML through ``qt_runtime.run_qml_app``.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "_props", {})
        object.__setattr__(self, "_callbacks", {})
        object.__setattr__(self, "_backend", None)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("on_"):
            event = name[3:]
            def bind(callback: Callable[..., Any] | None = None) -> None:
                self._callbacks[event] = callback
            return bind
        if name in self._props:
            return self._props[name]
        # Compatibility: many tests probe optional UI properties before the QML
        # object exists. Returning None is closer to a missing Qt property than
        # raising AttributeError during the migration window.
        return None

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self._props[name] = value
            backend = self._backend
            if backend is not None:
                try:
                    if name in {"status", "status_text", "statusText"}:
                        backend.setStatusText(str(value))
                    elif name in {"content", "content_text", "contentText"}:
                        backend.setContentText(str(value))
                    elif name == "rows":
                        backend.setRowsJson(json.dumps(value, ensure_ascii=False, default=str))
                except Exception:
                    pass

    def emit(self, event: str, *args: Any, **kwargs: Any) -> Any:
        callback = self._callbacks.get(event)
        if callback is not None:
            return callback(*args, **kwargs)
        return None

    def show(self) -> None:
        return None

    def hide(self) -> None:
        return None

    def run(self) -> int:
        try:
            from .qt_backend import NotizenQtBackend
            from .qt_runtime import run_qml_app
        except Exception as exc:
            print(f"Qt-Laufzeit nicht verfügbar: {exc}")
            return 2
        backend = NotizenQtBackend()
        object.__setattr__(self, "_backend", backend)
        if "status" in self._props:
            backend.setStatusText(str(self._props["status"]))
        if "rows" in self._props:
            try:
                backend.setRowsJson(json.dumps(self._props["rows"], ensure_ascii=False, default=str))
            except Exception:
                pass
        return run_qml_app(backend=backend, smoke_test=os.environ.get("NOTIZEN_QT_SMOKE_TEST") == "1")


def create_qt_window() -> QtCompatWindow:
    return QtCompatWindow()
'''

APP = r'''
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
'''

MAIN = "from .app import main\n\nraise SystemExit(main())\n"
INIT = '"""Python/Qt port of the old Notizen.NET application."""\n\n__all__: list[str] = []\n'


@dataclass
class Log:
    root: Path
    apply: bool
    backup_root: Path
    actions: list[str]

    def add(self, text: str) -> None:
        self.actions.append(text)

    def backup(self, path: Path) -> None:
        if not self.apply or not path.exists() or not path.is_file():
            return
        try:
            rel = path.relative_to(self.root)
        except ValueError:
            return
        dst = self.backup_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)

    def write(self, path: Path, text: str) -> None:
        old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else None
        if old == text:
            self.add(f"keep unchanged: {path}")
            return
        self.add(("update" if path.exists() else "create") + f": {path}")
        if self.apply:
            self.backup(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


def looks_like_generated_stub(path: Path) -> bool:
    if not path.exists():
        return True
    text = path.read_text(encoding="utf-8", errors="ignore")
    markers = [
        "Qt/QML application runner used after the UI migration",
        "Qt/QML runner for the migrated Notizen UI",
        "class NotizenQtApp",
    ]
    return any(marker in text for marker in markers) and len(text.splitlines()) < 260


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install hardened Python/Qt runtime files")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--force-app", action="store_true", help="replace app.py even if it no longer looks like the generated stub")
    args = parser.parse_args(argv)
    root = find_project_root(Path(args.root).resolve())
    pkg = root / "src" / "notizen_py_qt"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log = Log(root=root, apply=args.apply, backup_root=root / ".qt611_runtime_backup" / timestamp, actions=[])
    if not pkg.exists():
        log.add(f"package not found, skipped: {pkg}")
    else:
        log.write(pkg / "qt_runtime.py", QT_RUNTIME.lstrip())
        log.write(pkg / "qt_backend.py", QT_BACKEND.lstrip())
        log.write(pkg / "qt_compat.py", QT_COMPAT.lstrip())
        log.write(pkg / "__main__.py", MAIN)
        if not (pkg / "__init__.py").exists():
            log.write(pkg / "__init__.py", INIT)
        app_path = pkg / "app.py"
        if args.force_app or looks_like_generated_stub(app_path):
            log.write(app_path, APP.lstrip())
        else:
            log.add(f"preserve existing app controller: {app_path}")
    report = root / "QT611_RUNTIME_HARDENING.md"
    lines = ["# Python/Qt runtime hardening", "", f"Mode: {'APPLY' if log.apply else 'DRY-RUN'}", f"Root: `{root}`", "", "## Actions", ""]
    lines.extend(f"- {a}" for a in log.actions)
    log.write(report, "\n".join(lines) + "\n")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Root: {root}")
    for action in log.actions:
        print(f"- {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
