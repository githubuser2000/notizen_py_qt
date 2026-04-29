#!/usr/bin/env python3
"""
Qt 6.11 / Slint migration assistant.

Default mode is dry-run. Use --apply to edit files.
The script is intentionally conservative: it removes obvious Slint dependency
lines and archives .slint files, but it does not pretend to semantically
translate arbitrary Slint UI logic into QML.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable

try:
    from slint_to_qml import transpile_file, transpile_text
except Exception:  # pragma: no cover - allows partial use if the helper is missing
    transpile_file = None
    transpile_text = None

IGNORE_DIRS = {".git", "target", "build", "node_modules", ".qt611_no_slint_backup", "legacy_slint", "dist", ".venv"}
SLINT_DEP_RE = re.compile(
    r"^\s*(slint|slint-build|slint_build|slint-interpreter|slint_interpreter|i-slint-[A-Za-z0-9_-]+)\s*=.*$"
)
SLINT_TEXT_RE = re.compile(r"slint|Slint|SLINT|slint_build|slint-build|slint_interpreter|\.slint")

CPP_MAIN = r'''#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQuickStyle>
#include <QUrl>
#include <QObject>

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("Fusion"));

    QQmlApplicationEngine engine;
    const QUrl url(QStringLiteral("qrc:/qt/qml/Notizen/Main.qml"));

    QObject::connect(
        &engine,
        &QQmlApplicationEngine::objectCreated,
        &app,
        [url](QObject *obj, const QUrl &objUrl) {
            if (!obj && url == objUrl) {
                QCoreApplication::exit(-1);
            }
        },
        Qt::QueuedConnection);

    engine.load(url);
    return app.exec();
}
'''

QML_MAIN = r'''import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1100
    height: 720
    visible: true
    title: qsTr("Notizen / Transpiler")

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            ToolButton { text: qsTr("Öffnen") }
            ToolButton { text: qsTr("Transpilieren") }
            ToolButton { text: qsTr("Export") }
            Item { Layout.fillWidth: true }
            Label { text: qsTr("Qt 6.11") }
        }
    }

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        TextArea {
            id: sourceEditor
            SplitView.preferredWidth: root.width * 0.5
            placeholderText: qsTr("Quelle hier einfügen …")
            wrapMode: TextArea.NoWrap
            selectByMouse: true
        }

        TextArea {
            id: outputEditor
            readOnly: true
            placeholderText: qsTr("Transpilierte Ausgabe erscheint hier …")
            wrapMode: TextArea.NoWrap
            selectByMouse: true
        }
    }
}
'''

CMAKE = r'''cmake_minimum_required(VERSION 3.25)

project(NotizenQt611 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 6.11 REQUIRED COMPONENTS Core Gui Qml Quick QuickControls2)
qt_standard_project_setup(REQUIRES 6.11)

qt_add_executable(notizen_qt611
    cpp/main.cpp
)

file(GLOB_RECURSE NOTIZEN_QML_FILES CONFIGURE_DEPENDS
    qml/*.qml
)

file(GLOB_RECURSE NOTIZEN_QML_JS_FILES CONFIGURE_DEPENDS
    qml/*.js
)

include(${CMAKE_CURRENT_SOURCE_DIR}/qml/GeneratedQmlSingletons.cmake OPTIONAL)

qt_add_qml_module(notizen_qt611
    URI Notizen
    VERSION 1.0
    QML_FILES
        ${NOTIZEN_QML_FILES}
    RESOURCES
        ${NOTIZEN_QML_JS_FILES}
)

target_link_libraries(notizen_qt611
    PRIVATE
        Qt6::Core
        Qt6::Gui
        Qt6::Qml
        Qt6::Quick
        Qt6::QuickControls2
)
'''

RUST_CARGO_SNIPPET = r'''
# Qt/QML bridge replacing previous UI integration
cxx = "1"
cxx-qt = "0.8.1"
cxx-qt-lib = { version = "0.8.1", features = ["qt_full"] }
'''

RUST_BUILD_DEP_SNIPPET = r'''
# Qt/QML bridge build integration
cxx-qt-build = { version = "0.8.1", features = ["link_qt_object_files"] }
'''

RUST_BUILD_RS = r'''use cxx_qt_build::{CxxQtBuilder, QmlModule};

fn main() {
    CxxQtBuilder::new_qml_module(QmlModule::new("org.notizen.transpiler").qml_file("qml/Main.qml"))
        .files(["src/backend.rs"])
        .qt_module("Network")
        .qt_module("Quick")
        .qt_module("QuickControls2")
        .build();
}
'''

RUST_BACKEND = r'''#[cxx_qt::bridge]
pub mod qobject {
    unsafe extern "C++" {
        include!("cxx-qt-lib/qstring.h");
        type QString = cxx_qt_lib::QString;
    }

    extern "RustQt" {
        #[qobject]
        #[qml_element]
        #[qproperty(QString, source)]
        #[qproperty(QString, output)]
        type TranspilerBackend = super::TranspilerBackendRust;

        #[qinvokable]
        fn transpile(self: Pin<&mut Self>);
    }
}

use core::pin::Pin;
use cxx_qt_lib::QString;

#[derive(Default)]
pub struct TranspilerBackendRust {
    source: QString,
    output: QString,
}

impl qobject::TranspilerBackend {
    pub fn transpile(self: Pin<&mut Self>) {
        let source = self.as_ref().source().to_string();
        let translated = format!("// TODO: plug real transpiler core here\n{}", source);
        self.set_output(QString::from(translated));
    }
}
'''

def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for filename in filenames:
            yield Path(dirpath) / filename


def backup_file(path: Path, backup_root: Path, root: Path) -> None:
    rel = path.relative_to(root)
    target = backup_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def write_if_missing(path: Path, content: str, apply: bool, actions: list[str]) -> None:
    if path.exists():
        actions.append(f"keep existing: {path}")
        return
    actions.append(f"create: {path}")
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def remove_slint_dependency_lines(text: str) -> tuple[str, int]:
    removed = 0
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        if SLINT_DEP_RE.match(line):
            removed += 1
            continue
        out.append(line)
    return "".join(out), removed


def rename_slint_package_metadata(text: str) -> tuple[str, int]:
    changed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        value = re.sub("slint", "qt611", match.group("value"), flags=re.IGNORECASE)
        return f'{match.group("prefix")}{value}{match.group("quote")}'

    updated = re.sub(
        r'(?m)^(?P<prefix>\s*name\s*=\s*(?P<quote>["\']))(?P<value>[^"\']*slint[^"\']*)(?P=quote)',
        repl,
        text,
        flags=re.IGNORECASE,
    )
    return updated, changed


def ensure_toml_section(text: str, section: str, snippet: str) -> tuple[str, bool]:
    if snippet.strip().splitlines()[-1].split("=")[0].strip() in text:
        return text, False
    pattern = re.compile(rf"^\[{re.escape(section)}\]\s*$", re.MULTILINE)
    if pattern.search(text):
        # append directly after the section header
        return pattern.sub(f"[{section}]\n{snippet.strip()}\n", text, count=1), True
    else:
        return text.rstrip() + f"\n\n[{section}]\n{snippet.strip()}\n", True


def migrate_cargo(path: Path, backup_root: Path, root: Path, apply: bool, rust_cxx_qt: bool, actions: list[str]) -> None:
    original = path.read_text(encoding="utf-8")
    updated, removed = remove_slint_dependency_lines(original)
    updated, renamed = rename_slint_package_metadata(updated)
    changed = removed > 0 or renamed > 0
    if rust_cxx_qt:
        updated, added_dep = ensure_toml_section(updated, "dependencies", RUST_CARGO_SNIPPET)
        updated, added_build = ensure_toml_section(updated, "build-dependencies", RUST_BUILD_DEP_SNIPPET)
        changed = changed or added_dep or added_build
    if changed:
        actions.append(f"edit Cargo.toml: {path} (removed {removed} Slint dependency lines; renamed {renamed} package metadata values; rust_cxx_qt={rust_cxx_qt})")
        if apply:
            backup_file(path, backup_root, root)
            path.write_text(updated, encoding="utf-8")


def migrate_build_rs(path: Path, backup_root: Path, root: Path, apply: bool, rust_cxx_qt: bool, actions: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    removed = 0
    for line in lines:
        if "slint_build" in line or ".slint" in line:
            removed += 1
            continue
        kept.append(line)
    updated = "".join(kept)
    if rust_cxx_qt:
        updated = RUST_BUILD_RS
        removed = max(removed, 1)
    if updated != text:
        actions.append(f"edit build.rs: {path} (removed/replaced Slint build hooks)")
        if apply:
            backup_file(path, backup_root, root)
            path.write_text(updated, encoding="utf-8")


def migrate_rust_source(path: Path, backup_root: Path, root: Path, apply: bool, actions: list[str]) -> None:
    """Remove obvious old UI-framework Rust hooks.

    This is intentionally blunt for namespaced old-UI lines: those calls normally
    reference generated UI objects that no longer exist after the QML migration.
    Backups and the action report keep the original code recoverable.
    """
    original = path.read_text(encoding="utf-8")
    if not SLINT_TEXT_RE.search(original):
        return
    kept: list[str] = []
    removed = 0
    replaced = 0
    removed_sharedstring_import = False
    for line in original.splitlines(keepends=True):
        stripped = line.strip()
        if (
            "slint::include_modules!" in line
            or stripped.startswith("use slint::")
            or stripped.startswith("use slint {")
            or stripped.startswith("use slint::{")
            or stripped.startswith("extern crate slint")
        ):
            if "SharedString" in line:
                removed_sharedstring_import = True
            removed += 1
            continue
        updated = line.replace("slint::SharedString", "String")
        if updated != line:
            replaced += 1
        if SLINT_TEXT_RE.search(updated):
            removed += 1
            continue
        kept.append(updated)
    updated_text = "".join(kept)
    if removed_sharedstring_import:
        new_text = re.sub(r"\bSharedString\b", "String", updated_text)
        if new_text != updated_text:
            replaced += len(re.findall(r"\bSharedString\b", updated_text))
            updated_text = new_text
    if updated_text != original:
        actions.append(f"edit Rust source: {path.relative_to(root)} (removed {removed} old UI lines; replaced {replaced} SharedString references)")
        if apply:
            backup_file(path, backup_root, root)
            path.write_text(updated_text, encoding="utf-8")


def transpile_slint_to_qml(path: Path, root: Path, apply: bool, overwrite_qml: bool, actions: list[str]) -> None:
    out_dir = root / "qml"
    if transpile_file is None or transpile_text is None:
        actions.append(f"cannot transpile .slint because slint_to_qml.py is unavailable: {path.relative_to(root)}")
        return

    if apply:
        result = transpile_file(path, out_dir, overwrite=overwrite_qml, main_alias=True)
        names = ", ".join(sorted(result.outputs))
        actions.append(f"transpile .slint -> QML: {path.relative_to(root)} -> qml/ ({names}; warnings={len(result.warnings)})")
    else:
        result = transpile_text(path.read_text(encoding="utf-8"), str(path))
        names = ", ".join(sorted(result.outputs))
        actions.append(f"would transpile .slint -> QML: {path.relative_to(root)} -> qml/ ({names}; warnings={len(result.warnings)})")


def archive_or_delete_slint(path: Path, backup_root: Path, root: Path, apply: bool, delete: bool, actions: list[str]) -> None:
    rel = path.relative_to(root)
    if delete:
        actions.append(f"delete .slint: {rel}")
        if apply:
            backup_file(path, backup_root, root)
            path.unlink()
    else:
        dest = root / "legacy_slint" / rel
        actions.append(f"archive .slint: {rel} -> {dest.relative_to(root)}")
        if apply:
            backup_file(path, backup_root, root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dest))


def scan_remaining(root: Path) -> list[str]:
    hits: list[str] = []
    for path in iter_files(root):
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".json", ".md", ".log", ".txt", ".out"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if SLINT_TEXT_RE.search(line):
                hits.append(f"{path.relative_to(root)}:{i}: {line.strip()[:160]}")
    return hits


def write_action_report(root: Path, actions: list[str], remaining: list[str], apply: bool) -> None:
    if not apply:
        return
    lines = [
        "# Qt 6.11 Migration Actions",
        "",
        "## Actions",
        "",
    ]
    if actions:
        lines.extend(f"- {action}" for action in actions)
    else:
        lines.append("- No changes required.")
    lines.extend(["", "## Remaining active references", ""])
    if remaining:
        lines.extend(f"- `{hit}`" for hit in remaining[:500])
        if len(remaining) > 500:
            lines.append(f"- ... {len(remaining) - 500} more")
    else:
        lines.append("- None detected by scanner.")
    (root / "QT611_MIGRATION_ACTIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true", help="actually modify files")
    parser.add_argument("--delete-slint", action="store_true", help="delete .slint files instead of archiving them")
    parser.add_argument("--no-transpile-slint", action="store_true", help="archive/delete .slint files without generating QML first")
    parser.add_argument("--overwrite-qml", action="store_true", help="overwrite generated QML files if they already exist")
    parser.add_argument("--rust-cxx-qt", action="store_true", help="add CXX-Qt dependencies and build.rs for Rust backend")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 2

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / ".qt611_no_slint_backup" / stamp
    actions: list[str] = []

    cargo_files: list[Path] = []
    build_rs_files: list[Path] = []
    slint_files: list[Path] = []
    rust_files: list[Path] = []
    cmake_files: list[Path] = []

    for path in iter_files(root):
        if path.name == "Cargo.toml":
            cargo_files.append(path)
        elif path.name == "build.rs":
            build_rs_files.append(path)
        elif path.name == "CMakeLists.txt":
            cmake_files.append(path)
        elif path.suffix == ".slint":
            slint_files.append(path)
        elif path.suffix == ".rs":
            rust_files.append(path)

    for path in cargo_files:
        migrate_cargo(path, backup_root, root, args.apply, args.rust_cxx_qt, actions)
    for path in build_rs_files:
        migrate_build_rs(path, backup_root, root, args.apply, args.rust_cxx_qt, actions)
    for path in rust_files:
        migrate_rust_source(path, backup_root, root, args.apply, actions)
    if not args.no_transpile_slint:
        for path in slint_files:
            transpile_slint_to_qml(path, root, args.apply, args.overwrite_qml, actions)
    for path in slint_files:
        archive_or_delete_slint(path, backup_root, root, args.apply, args.delete_slint, actions)

    # Always add a Qt Quick shell if the project doesn't already have one.
    write_if_missing(root / "cpp" / "main.cpp", CPP_MAIN, args.apply, actions)
    write_if_missing(root / "qml" / "Main.qml", QML_MAIN, args.apply, actions)
    if not (root / "CMakeLists.txt").exists():
        write_if_missing(root / "CMakeLists.txt", CMAKE, args.apply, actions)
    else:
        write_if_missing(root / "CMakeLists.qt611.generated.txt", CMAKE, args.apply, actions)

    if args.rust_cxx_qt:
        write_if_missing(root / "src" / "backend.rs", RUST_BACKEND, args.apply, actions)
        if not build_rs_files:
            write_if_missing(root / "build.rs", RUST_BUILD_RS, args.apply, actions)

    print("Mode:", "APPLY" if args.apply else "DRY-RUN")
    print("Root:", root)
    print(f"Found: {len(cargo_files)} Cargo.toml, {len(build_rs_files)} build.rs, {len(cmake_files)} CMakeLists.txt, {len(slint_files)} .slint files, {len(rust_files)} Rust source files")
    print("\nActions:")
    if actions:
        for action in actions:
            print("-", action)
    else:
        print("- No changes required.")

    remaining = scan_remaining(root)
    write_action_report(root, actions, remaining, args.apply)
    if args.apply:
        print(f"\nWrote migration action report: {root / 'QT611_MIGRATION_ACTIONS.md'}")
    if remaining:
        print("\nRemaining Slint references to handle manually:")
        for hit in remaining[:200]:
            print("-", hit)
        if len(remaining) > 200:
            print(f"... {len(remaining) - 200} more")
        return 1 if args.apply else 0

    print("\nNo remaining Slint references detected by scanner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
