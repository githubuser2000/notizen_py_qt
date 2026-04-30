#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
BUILD_DIR="${2:-$ROOT/build/qt611}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

"$SCRIPT_DIR/verify_qt611_environment.sh"
"$SCRIPT_DIR/check_no_slint.sh" "$ROOT"
"$PYTHON_BIN" "$SCRIPT_DIR/qml_sanity_check.py" "$ROOT"
cmake -S "$ROOT" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" --parallel
