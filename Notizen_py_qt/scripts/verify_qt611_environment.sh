#!/usr/bin/env bash
set -euo pipefail

REQUIRE_RUST=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rust) REQUIRE_RUST=1; shift ;;
    *) echo "usage: $0 [--rust]" >&2; exit 2 ;;
  esac
done

fail=0
need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: missing required command: $1" >&2
    fail=1
  fi
}

need cmake

QMAKE_BIN="${QMAKE:-}"
if [[ -z "$QMAKE_BIN" ]]; then
  if command -v qmake6 >/dev/null 2>&1; then
    QMAKE_BIN="$(command -v qmake6)"
  elif command -v qmake >/dev/null 2>&1; then
    QMAKE_BIN="$(command -v qmake)"
  fi
fi

if [[ -z "$QMAKE_BIN" || ! -x "$QMAKE_BIN" ]]; then
  echo "ERROR: qmake6/qmake not found. Set QMAKE=/path/to/Qt/6.11.x/bin/qmake6." >&2
  fail=1
else
  QT_VERSION="$($QMAKE_BIN -query QT_VERSION 2>/dev/null || true)"
  QT_INSTALL_PREFIX="$($QMAKE_BIN -query QT_INSTALL_PREFIX 2>/dev/null || true)"
  echo "Qt qmake: $QMAKE_BIN"
  echo "Qt version: ${QT_VERSION:-unknown}"
  echo "Qt prefix: ${QT_INSTALL_PREFIX:-unknown}"
  IFS=. read -r major minor patch <<<"${QT_VERSION:-0.0.0}"
  major=${major:-0}; minor=${minor:-0}
  if [[ "$major" -ne 6 || "$minor" -lt 11 ]]; then
    echo "ERROR: Qt 6.11 or newer in the Qt 6 line is required; found ${QT_VERSION:-unknown}." >&2
    fail=1
  fi
fi

if [[ "$REQUIRE_RUST" -eq 1 ]]; then
  need cargo
  need rustc
fi

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi

echo "OK: Qt 6.11 environment looks usable."
