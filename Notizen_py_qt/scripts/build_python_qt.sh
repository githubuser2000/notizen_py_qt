#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
WITH_SMOKE=0
INPUT_ROOT="."
for arg in "$@"; do
    case "$arg" in
        --with-smoke)
            WITH_SMOKE=1
            ;;
        --no-smoke)
            WITH_SMOKE=0
            ;;
        *)
            INPUT_ROOT="$arg"
            ;;
    esac
done
PROJECT_ROOT="$($PYTHON - "$INPUT_ROOT" <<'PYROOT'
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
PYROOT
)"
echo "Detected project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"
"$PYTHON" -m pip install -e ".[crypto]"
"$PYTHON" "$SCRIPT_DIR/probe_python_qt_runtime.py" "$PROJECT_ROOT" --skip-smoke

if [[ "$WITH_SMOKE" == 1 ]]; then
    echo "Running optional bounded headless smoke test (--with-smoke)."
    smoke_cmd=(env
        -u DISPLAY
        -u WAYLAND_DISPLAY
        -u GDK_BACKEND
        -u QT_QPA_PLATFORMTHEME
        PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
        QT_QPA_PLATFORM=offscreen
        QT_STYLE_OVERRIDE=Fusion
        NOTIZEN_QT_SMOKE_TEST=1
        NOTIZEN_NO_GUI_ERROR=1
        "$PYTHON" -m notizen_py_qt --smoke-test)
    if command -v timeout >/dev/null 2>&1; then
        timeout -k 2s 10s "${smoke_cmd[@]}"
    else
        "${smoke_cmd[@]}"
    fi
else
    echo "Skipping GUI smoke test by default. Use --with-smoke for a bounded headless smoke test."
fi

echo "RESULT: Python/Qt build validation passed."
