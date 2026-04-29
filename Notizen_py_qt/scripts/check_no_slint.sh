#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
if grep -RInE '(^|[^A-Za-z0-9_])(slint|Slint|SLINT|slint_build|slint-build|slint_interpreter|\.slint)([^A-Za-z0-9_]|$)' \
  "$ROOT" \
  --include='*.rs' \
  --include='*.cpp' \
  --include='*.cc' \
  --include='*.cxx' \
  --include='*.h' \
  --include='*.hpp' \
  --include='*.qml' \
  --include='*.toml' \
  --include='*.cmake' \
  --include='CMakeLists.txt' \
  --include='build.rs' \
  --exclude-dir=.git \
  --exclude-dir=target \
  --exclude-dir=build \
  --exclude-dir=node_modules \
  --exclude-dir=.qt611_no_slint_backup \
  --exclude-dir=legacy_slint \
  --exclude='Cargo.lock' ; then
  echo "ERROR: Slint references remain in active source/build files." >&2
  exit 1
else
  echo "OK: no Slint references found in active source/build files."
fi
