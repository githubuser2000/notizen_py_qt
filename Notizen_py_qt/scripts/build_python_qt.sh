#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 -m pip install -e .
QT_QPA_PLATFORM=offscreen python3 -m notizen_py_qt --smoke-test
