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
