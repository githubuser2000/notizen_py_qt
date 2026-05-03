#!/usr/bin/env bash
set -euo pipefail
PYTHON="${PYTHON:-python3}"
"$PYTHON" - <<'PY'
import importlib.util
import sys
print('Python:', sys.version.split()[0])
found = []
for name in ('PySide6', 'PyQt6'):
    if importlib.util.find_spec(name):
        found.append(name)
if not found:
    raise SystemExit('ERROR: neither PySide6 nor PyQt6 is importable. Install with: python -m pip install -e ".[crypto]"')
print('Qt binding(s):', ', '.join(found))
PY
echo "OK: Python/Qt environment looks usable."
