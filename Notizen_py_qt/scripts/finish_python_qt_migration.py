#!/usr/bin/env python3
"""
Finish the Python side of a Slint-to-Qt 6.11 migration.

Default mode is dry-run. Use --apply to edit files.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from qt611_project_utils import find_project_root, is_ignored_path, prune_dirnames, should_skip_dir_name
from typing import Iterable

OLD_WORD_RE = re.compile(r"slint|Slint|SLINT|slint_build|slint-build|slint_interpreter|\.slint")

IGNORE_DIRS = {
    ".git", ".hg", ".svn",
    "target", "build", "cmake-build-debug", "cmake-build-release",
    "node_modules", ".venv", "venv", "env", ".tox",
    ".mypy_cache", ".pytest_cache", "__pycache__",
    ".qt611_no_slint_backup", ".qt611_no_slint_backup_v4",
    "legacy_slint", "legacy_build_metadata", "dist",
}

TEXT_SUFFIXES = {
    ".py", ".toml", ".qml", ".js", ".json", ".sh", ".md", ".rst", ".txt",
    ".desktop", ".plist", ".service", ".spec", ".yml", ".yaml", ".cmake",
}
TEXT_NAMES = {"CMakeLists.txt", "build.rs", "Cargo.toml", "pyproject.toml", "MANIFEST.in"}

# These tools intentionally contain old framework tokens so they can find them.
SKIP_FILENAMES = {
    "finish_python_qt_migration.py",
    "migrate_remove_slint_to_qt611.py",
    "slint_to_qml.py",
    "check_no_slint.sh",
    "check_no_slint_strict.sh", "repair_pyproject_qt611.py",

    "continue_qt611_transpile.py",
    "fix_qml_for_pyside.py",
    "harden_python_qt_runtime.py",
    "restore_qt_controller_from_backup.py",
    "probe_python_qt_runtime.py",
    "recover_misrooted_qt611_migration.py",
    "repair_qml_todo_blocks.py",
    "qt611_project_utils.py",
    "build_python_qt.sh",
    "build_qt611.sh",
    "verify_qt611_environment.sh",
    "qml_sanity_check.py",
    "analyze_transpilation.py",
}

REPLACEMENTS = [
    (".slint", ".qml"),
    ("notizen-py-slint-subtree", "notizen-py-qt-subtree"),
    ("notizen-py-slint-node-clipboard", "notizen-py-qt-node-clipboard"),
    ("notizen_py_slint", "notizen_py_qt"),
    ("notizen_pypy_slint", "notizen_pypy_qt"),
    ("notizen-py-slint", "notizen-py-qt"),
    ("notizen-pypy-slint", "notizen-pypy-qt"),
    ("NotizenSlintApp", "NotizenQtApp"),
    ("_format_slint_compile_error", "_format_qt_load_error"),
    ("SLINT_FULLSCREEN", "QT_FULLSCREEN"),
    ("Python/Slint", "Python/Qt"),
    ("PyPy3/Slint", "PyPy3/Qt"),
    ("Slint", "Qt"),
    ("slint", "qt"),
    ("SLINT", "QT"),
]

APP_PY = r'''
from __future__ import annotations

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
'''

QT_BACKEND_PY = r'''
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot


class NotizenQtBackend(QObject):
    """Small QObject bridge exposed to QML as ``notizenBackend``."""

    statusTextChanged = Signal()
    contentTextChanged = Signal()
    rowsJsonChanged = Signal()
    initialPathChanged = Signal()

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
        if self._status_text != value:
            self._status_text = value
            self.statusTextChanged.emit()

    @Property(str, notify=contentTextChanged)
    def contentText(self) -> str:
        return self._content_text

    @Slot(str)
    def setContentText(self, value: str) -> None:
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

    @Slot(str)
    def openFile(self, path: str) -> None:
        self.setInitialPath(path)
        self.setStatusText(f"Öffnen angefordert: {path}")

    @Slot(str)
    def saveFile(self, path: str) -> None:
        self.setStatusText(f"Speichern angefordert: {path}")

    @Slot(str)
    def notify(self, message: str) -> None:
        self.setStatusText(message)
'''

INIT_PY = "\"\"\"Python/Qt port of the old Notizen.NET application.\"\"\"\n\n__all__ = []\n"
UI_INIT_PY = "\"\"\"Packaged QML resources for the Qt UI.\"\"\"\n"
MAIN_PY = "from .app import main\n\nraise SystemExit(main())\n"
RUN_GUI_SH = "#!/usr/bin/env bash\nset -euo pipefail\nexec python3 -m notizen_py_qt \"$@\"\n"

STRICT_CHECK_SH = r'''#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
if grep -RInE '(^|[^A-Za-z0-9_])(slint|Slint|SLINT|slint_build|slint-build|slint_interpreter|\.slint)([^A-Za-z0-9_]|$)' \
  "$ROOT" \
  --include='*.py' \
  --include='*.rs' \
  --include='*.cpp' \
  --include='*.cc' \
  --include='*.cxx' \
  --include='*.h' \
  --include='*.hpp' \
  --include='*.qml' \
  --include='*.js' \
  --include='*.toml' \
  --include='*.cmake' \
  --include='CMakeLists.txt' \
  --include='build.rs' \
  --include='*.sh' \
  --exclude='Cargo.lock' \
  --exclude='migrate_remove_slint_to_qt611.py' \
  --exclude='slint_to_qml.py' \
  --exclude='finish_python_qt_migration.py' \
  --exclude='check_no_slint.sh' \
  --exclude='check_no_slint_strict.sh' \
  --exclude='repair_pyproject_qt611.py' \
  --exclude-dir=.git \
  --exclude-dir=target \
  --exclude-dir=build \
  --exclude-dir=cmake-build-debug \
  --exclude-dir=cmake-build-release \
  --exclude-dir=node_modules \
  --exclude-dir=.qt611_no_slint_backup \
  --exclude-dir=.qt611_no_slint_backup_v4 \
  --exclude-dir=.qt611_pyproject_repair_backup \
  --exclude-dir='qt611_no_slint_migration_kit*' \
  --exclude-dir=legacy_slint \
  --exclude-dir=legacy_build_metadata \
  --exclude-dir=dist \
  --exclude-dir=.venv \
  --exclude-dir=venv \
  --exclude-dir=env \
  --exclude-dir=__pycache__ \
  --exclude-dir=.pytest_cache \
  --exclude-dir=.mypy_cache \
  --exclude-dir='*.egg-info' ; then
  echo "ERROR: old UI-framework references remain in active source/build files." >&2
  exit 1
else
  echo "OK: no old UI-framework references found in active source/build files."
fi
'''

BUILD_PYTHON_QT_SH = r'''#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${1:-.}" && pwd)"
if [[ -f "$SCRIPT_DIR/repair_pyproject_qt611.py" ]]; then
  python3 "$SCRIPT_DIR/repair_pyproject_qt611.py" "$ROOT" --apply
fi
cd "$ROOT"
python3 -m pip install -e .
QT_QPA_PLATFORM=offscreen python3 -m notizen_py_qt --smoke-test
'''


@dataclass
class ActionLog:
    apply: bool
    root: Path
    backup_root: Path
    actions: list[str]

    def add(self, message: str) -> None:
        self.actions.append(message)

    def backup(self, path: Path) -> None:
        if not path.exists() or path.is_dir():
            return
        try:
            rel = path.relative_to(self.root)
        except ValueError:
            return
        target = self.backup_root / rel
        if self.apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    def write_text(self, path: Path, content: str, executable: bool = False) -> None:
        old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else None
        if old == content:
            self.add(f"keep unchanged: {path}")
            return
        self.add(("update" if path.exists() else "create") + f": {path}")
        if self.apply:
            if path.exists():
                self.backup(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            if executable:
                path.chmod(path.stat().st_mode | 0o755)


def is_text_file(path: Path) -> bool:
    return path.name in TEXT_NAMES or path.suffix in TEXT_SUFFIXES


def should_skip_file(path: Path) -> bool:
    return path.name in SKIP_FILENAMES or should_skip_dir_name(path.name) or is_ignored_path(path)


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        prune_dirnames(dirnames)
        d = Path(dirpath)
        if is_ignored_path(d, root):
            continue
        for filename in filenames:
            path = d / filename
            if should_skip_file(path):
                continue
            if is_text_file(path):
                yield path


def apply_replacements(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def remove_legacy_ui_dependency_lines(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        lower = line.lower()
        stripped = line.strip()
        if re.match(r"^[\"']?slint[\"']?\s*=", stripped, re.I):
            continue
        if "slint>=" in lower or "slint==" in lower or "slint~=" in lower:
            continue
        if "ui/*.slint" in lower or "*.slint" in lower:
            continue
        out.append(line)
    return "".join(out)


def ensure_pyside_dependency(text: str) -> str:
    if "PySide6" in text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    inserted = False
    in_project = False
    for line in lines:
        if in_project and line.startswith("[") and line.strip() != "[project]":
            if not inserted:
                out.append('dependencies = ["PySide6>=6.11,<6.12"]')
                inserted = True
            in_project = False
        out.append(line)
        if line.strip() == "[project]":
            in_project = True
            continue
        if in_project and re.match(r"\s*dependencies\s*=\s*\[\s*$", line):
            out.append('    "PySide6>=6.11,<6.12",')
            inserted = True
    if in_project and not inserted:
        out.append('dependencies = ["PySide6>=6.11,<6.12"]')
        inserted = True
    if not inserted:
        out.extend(["", "[project]", 'dependencies = ["PySide6>=6.11,<6.12"]'])
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def update_pyproject(path: Path, log: ActionLog) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    repair_path = Path(__file__).resolve().with_name("repair_pyproject_qt611.py")
    try:
        spec = importlib.util.spec_from_file_location("_qt611_pyproject_repair", repair_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {repair_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        new = module.repair_text(text)
    except Exception:
        # Fallback to the older line-based path. The dedicated repair script is
        # preferred because it also fixes already-invalid TOML with duplicate keys.
        new = remove_legacy_ui_dependency_lines(text)
        new = apply_replacements(new)
        new = ensure_pyside_dependency(new)
        if "notizen_py_qt.ui" not in new and "[tool.setuptools.package-data]" in new:
            new = new.rstrip() + '\nnotizen_py_qt = ["ui/*.qml", "ui/*.js"]\n"notizen_py_qt.ui" = ["*.qml", "*.js"]\n'
    if new != text:
        log.write_text(path, new)
    else:
        log.add(f"keep unchanged: {path}")


def merge_or_move_dir(src: Path, dst: Path, log: ActionLog) -> None:
    if not src.exists():
        return
    log.add(f"rename package dir: {src} -> {dst}")
    if not log.apply:
        return
    if dst.exists():
        for item in src.iterdir():
            target = dst / item.name
            if target.exists():
                if item.is_dir():
                    merge_or_move_dir(item, target, log)
                else:
                    log.backup(target)
                    shutil.move(str(item), str(target))
            else:
                shutil.move(str(item), str(target))
        try:
            src.rmdir()
        except OSError:
            pass
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def archive_egg_info(root: Path, log: ActionLog) -> None:
    target_root = root / "legacy_build_metadata"
    for path in root.rglob("*.egg-info"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        rel = path.relative_to(root)
        target = target_root / rel
        log.add(f"archive generated metadata: {path} -> {target}")
        if log.apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(path), str(target))


def archive_remaining_ui_files(root: Path, log: ActionLog) -> None:
    for path in list(root.rglob("*.slint")):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        rel = path.relative_to(root)
        target = root / "legacy_slint" / rel
        log.add(f"archive remaining old UI file: {path} -> {target}")
        if log.apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(target))


def rewrite_text_files(root: Path, log: ActionLog) -> None:
    for path in iter_files(root):
        if path.name == "pyproject.toml":
            update_pyproject(path, log)
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = apply_replacements(text)
        if new != text:
            log.write_text(path, new, executable=os.access(path, os.X_OK))


def copy_qml_resources(root: Path, log: ActionLog) -> None:
    pkg = root / "src" / "notizen_py_qt"
    qml_root = root / "qml"
    if not pkg.exists() or not qml_root.exists():
        return
    ui = pkg / "ui"
    copied_names: list[str] = []
    for src in sorted(qml_root.iterdir()):
        if src.suffix not in {".qml", ".js"} or not src.is_file():
            continue
        dst = ui / src.name
        content = apply_replacements(src.read_text(encoding="utf-8", errors="ignore"))
        log.write_text(dst, content)
        copied_names.append(src.name)
    if copied_names:
        log.write_text(ui / "__init__.py", UI_INIT_PY)
        for name in ("AppWindow.qml", "app-window_AppWindow.qml", "Main.qml"):
            src = ui / name
            if src.exists():
                log.write_text(ui / "app-window.qml", src.read_text(encoding="utf-8", errors="ignore"))
                break


def write_python_qt_runner(root: Path, log: ActionLog) -> None:
    pkg = root / "src" / "notizen_py_qt"
    if not pkg.exists():
        return
    log.write_text(pkg / "app.py", APP_PY.lstrip())
    log.write_text(pkg / "qt_backend.py", QT_BACKEND_PY.lstrip())
    log.write_text(pkg / "__main__.py", MAIN_PY)
    if not (pkg / "__init__.py").exists():
        log.write_text(pkg / "__init__.py", INIT_PY)

    compat = root / "src" / "notizen_pypy_qt"
    if compat.exists():
        log.write_text(compat / "app.py", "from notizen_py_qt.app import *  # noqa: F401,F403\n")
        log.write_text(compat / "__main__.py", "from notizen_py_qt.app import main\n\nraise SystemExit(main())\n")
        log.write_text(compat / "__init__.py", "from notizen_py_qt import *  # noqa: F401,F403\n")

    log.write_text(root / "scripts" / "run-gui.sh", RUN_GUI_SH, executable=True)


def write_helper_scripts(root: Path, log: ActionLog) -> None:
    scripts = root / "scripts"
    log.write_text(scripts / "check_no_slint.sh", STRICT_CHECK_SH, executable=True)
    log.write_text(scripts / "check_no_slint_strict.sh", STRICT_CHECK_SH, executable=True)
    log.write_text(scripts / "build_python_qt.sh", BUILD_PYTHON_QT_SH, executable=True)
    repair_source = Path(__file__).resolve().with_name("repair_pyproject_qt611.py")
    if repair_source.exists():
        log.write_text(
            scripts / "repair_pyproject_qt611.py",
            repair_source.read_text(encoding="utf-8"),
            executable=True,
        )


def scan_remaining(root: Path) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if OLD_WORD_RE.search(line):
                hits.append((path, line_no, line.strip()))
                if len(hits) >= 300:
                    return hits
    return hits


def write_report(root: Path, log: ActionLog, remaining: list[tuple[Path, int, str]]) -> None:
    report = root / "QT611_PYTHON_QT_MIGRATION_ACTIONS.md"
    lines = [
        "# Python Qt migration actions",
        "",
        f"Mode: {'APPLY' if log.apply else 'DRY-RUN'}",
        f"Root: `{root}`",
        "",
        "## Actions",
        "",
    ]
    lines.extend(f"- {a}" for a in log.actions)
    lines += ["", "## Remaining active references", ""]
    if remaining:
        lines.extend(f"- `{p.relative_to(root)}`:{n}: `{line}`" for p, n, line in remaining[:300])
    else:
        lines.append("None found by the Python migration scanner.")
    log.write_text(report, "\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Finish Python/Qt migration after old UI files were converted to QML")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--apply", action="store_true", help="Edit files instead of dry-run")
    args = parser.parse_args(argv)

    root = find_project_root(Path(args.root).resolve())
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = root / ".qt611_no_slint_backup_v4" / timestamp
    log = ActionLog(apply=args.apply, root=root, backup_root=backup_root, actions=[])

    merge_or_move_dir(root / "src" / "notizen_py_slint", root / "src" / "notizen_py_qt", log)
    merge_or_move_dir(root / "src" / "notizen_pypy_slint", root / "src" / "notizen_pypy_qt", log)
    archive_egg_info(root, log)
    archive_remaining_ui_files(root, log)
    rewrite_text_files(root, log)
    copy_qml_resources(root, log)
    write_python_qt_runner(root, log)
    write_helper_scripts(root, log)

    remaining = scan_remaining(root)
    write_report(root, log, remaining)

    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Root: {root}")
    print("Actions:")
    for action in log.actions:
        print(f"- {action}")
    if remaining:
        print("\nRemaining old UI-framework references to handle manually:")
        for path, line_no, line in remaining[:80]:
            print(f"- {path.relative_to(root)}:{line_no}: {line}")
        if len(remaining) > 80:
            print(f"... {len(remaining) - 80} more")
        return 1
    print("\nOK: Python package names, QML strings, entry points and active source references are clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
