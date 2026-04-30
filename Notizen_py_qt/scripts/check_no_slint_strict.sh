#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
INPUT_ROOT="${1:-.}"
PROJECT_ROOT="$("$PYTHON" - "$SCRIPT_DIR" "$INPUT_ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from qt611_project_utils import find_project_root
print(find_project_root(Path(sys.argv[2]).resolve()))
PY
)"
PATTERN='(^|[^A-Za-z0-9_])(slint|Slint|SLINT|slint_build|slint-build|slint_interpreter|\.slint)([^A-Za-z0-9_]|$)'
MATCHES="$(
  find "$PROJECT_ROOT" \
    \( -type d \( \
      -name '.git' -o -name '.hg' -o -name '.svn' -o \
      -name 'target' -o -name 'build' -o -name 'cmake-build-debug' -o -name 'cmake-build-release' -o \
      -name 'node_modules' -o -name '.venv' -o -name 'venv' -o -name 'env' -o -name '.tox' -o \
      -name '__pycache__' -o -name '.pytest_cache' -o -name '.mypy_cache' -o \
      -name '.qt611*' -o -name 'qt611_no_slint_migration_kit*' -o \
      -name 'legacy_slint' -o -name 'legacy_build_metadata' -o -name 'dist' -o -name '*.egg-info' \
    \) -prune \) -o \
    \( -type f \( \
      -name '*.py' -o -name '*.rs' -o -name '*.cpp' -o -name '*.cc' -o -name '*.cxx' -o \
      -name '*.h' -o -name '*.hpp' -o -name '*.qml' -o -name '*.js' -o -name '*.toml' -o \
      -name '*.cmake' -o -name 'CMakeLists.txt' -o -name 'build.rs' -o -name '*.sh' \
    \) \
      ! -name 'Cargo.lock' \
      ! -name 'migrate_remove_slint_to_qt611.py' \
      ! -name 'slint_to_qml.py' \
      ! -name 'finish_python_qt_migration.py' \
      ! -name 'check_no_slint.sh' \
      ! -name 'check_no_slint_strict.sh' \
      ! -name 'repair_pyproject_qt611.py' \
      ! -name 'continue_qt611_transpile.py' \
      ! -name 'probe_python_qt_runtime.py' \
      ! -name 'restore_qt_controller_from_backup.py' \
      ! -name 'harden_python_qt_runtime.py' \
      ! -name 'fix_qml_for_pyside.py' \
      ! -name 'recover_misrooted_qt611_migration.py' \
      ! -name 'repair_qml_todo_blocks.py' \
      ! -name 'qt611_project_utils.py' \
      -print0 \) | xargs -0 --no-run-if-empty grep -HnIE "$PATTERN" || true
)"
if [[ -n "$MATCHES" ]]; then
  printf '%s\n' "$MATCHES"
  echo "ERROR: old UI-framework references remain in active source/build files under $PROJECT_ROOT." >&2
  exit 1
fi
echo "OK: no old UI-framework references found in active source/build files under $PROJECT_ROOT."
