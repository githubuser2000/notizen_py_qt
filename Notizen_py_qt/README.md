# Qt 6.11 / Slint-Removal Migration Kit

This kit is for moving a Slint-based transpilation/GUI project to the current Qt 6 line, pinned to **Qt 6.11**.

What it does:

- removes Slint references from build files where it can do so safely;
- archives or deletes `.slint` files;
- creates a Qt Quick / QML starter shell using Qt 6.11;
- provides a CXX-Qt Rust bridge template for Rust projects that still need Rust backend logic;
- provides a Slint detector so active source/build files can be checked after migration.

What it cannot do automatically without your real source tree:

- faithfully translate custom Slint components, callbacks, stores, and layouts into QML;
- infer project-specific Rust/C++ backend APIs;
- run a successful build where Qt/Cargo/Rust are not installed.

## Recommended target architecture

Use one of these two shapes:

1. **C++/Qt Quick only**: best when the transpiler can be in C++ or already has a C++ core.
2. **Qt Quick + CXX-Qt Rust backend**: best when the transpiler core stays in Rust and only the UI moves from Slint to Qt/QML.

For the user's existing Rust+Slint direction, option 2 is the safer default.

## Apply to a real project

From the root of the real project:

```bash
python3 /path/to/qt611_no_slint_migration_kit/scripts/migrate_remove_slint_to_qt611.py . --apply --rust-cxx-qt
bash /path/to/qt611_no_slint_migration_kit/scripts/check_no_slint.sh .
```

Then build the generated Qt shell:

```bash
cmake -S . -B build/qt611 -DCMAKE_BUILD_TYPE=Release
cmake --build build/qt611 --parallel
```

If multiple Qt versions are installed, point CMake at Qt 6.11 explicitly, for example:

```bash
cmake -S . -B build/qt611 \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$HOME/Qt/6.11.0/gcc_64"
```

For Cargo/CXX-Qt builds with multiple Qt versions, set:

```bash
export QT_VERSION_MAJOR=6
export QMAKE="$HOME/Qt/6.11.0/gcc_64/bin/qmake6"
```

## Files in this kit

- `scripts/migrate_remove_slint_to_qt611.py` — migration assistant.
- `scripts/check_no_slint.sh` — hard check for leftover Slint references.
- `scripts/build_qt611.sh` — generic Qt 6.11 CMake build command.
- `template_cpp_qml/` — minimal pure C++/Qt Quick project.
- `template_rust_cxx_qt/` — minimal Rust+CXX-Qt+QML project skeleton.
- `cmake/Qt611QuickApp.CMakeLists.txt` — CMake fragment you can merge into an existing project.
- `TRANSPILE_ATTEMPT.log` — what was checked in this session.
