#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${1:-.}" && pwd)"
if [[ -f "$SCRIPT_DIR/repair_pyproject_qt611.py" ]]; then
  python3 "$SCRIPT_DIR/repair_pyproject_qt611.py" "$ROOT" --apply
fi
cd "$ROOT"
python3 -m pip install -e .
QT_QPA_PLATFORM=offscreen python3 -m notizen_py_qt --smoke-test
