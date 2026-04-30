#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
INPUT_ROOT="${1:-.}"
PROJECT_ROOT="$($PYTHON - "$INPUT_ROOT" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1]).expanduser().resolve()
if root.name == 'pyproject.toml' and root.is_file():
    root = root.parent
while root.parent != root:
    if (root / 'pyproject.toml').is_file() and (root / 'src' / 'notizen_py_qt').is_dir():
        break
    root = root.parent
print(root)
PY
)"
echo "Detected project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"
"$PYTHON" -m pip install -e ".[crypto]"
"$PYTHON" "$SCRIPT_DIR/probe_python_qt_runtime.py" "$PROJECT_ROOT" --skip-smoke
QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}" NOTIZEN_QT_SMOKE_TEST=1 "$PYTHON" -m notizen_py_qt --smoke-test
