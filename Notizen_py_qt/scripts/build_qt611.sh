#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
BUILD_DIR="${2:-$ROOT/build/qt611}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/verify_qt611_environment.sh"
cmake -S "$ROOT" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" --parallel
