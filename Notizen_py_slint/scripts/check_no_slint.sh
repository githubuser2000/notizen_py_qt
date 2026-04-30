#!/usr/bin/env bash
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
