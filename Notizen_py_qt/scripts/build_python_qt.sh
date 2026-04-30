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
echo "Detected project root: $PROJECT_ROOT"
"$PYTHON" "$SCRIPT_DIR/repair_pyproject_qt611.py" "$PROJECT_ROOT" --apply
cd "$PROJECT_ROOT"
"$PYTHON" -m pip install -e .

run_probe() {
  QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}" \
  QT_QUICK_BACKEND="${QT_QUICK_BACKEND:-software}" \
  QSG_RHI_BACKEND="${QSG_RHI_BACKEND:-software}" \
  NOTIZEN_QT_SMOKE_TEST=1 \
  "$PYTHON" "$SCRIPT_DIR/probe_python_qt_runtime.py" "$PROJECT_ROOT"
}

if run_probe; then
  exit 0
fi

echo "Initial Qt/QML probe failed; attempting automatic QML engine-error repair..."
"$PYTHON" "$SCRIPT_DIR/repair_qml_engine_errors.py" "$PROJECT_ROOT" --apply --run-smoke --max-rounds 12 --static-padding-pass --python "$PYTHON" || true

echo "Re-running Qt/QML probe after repair..."
run_probe
