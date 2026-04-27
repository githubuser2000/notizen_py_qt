#!/usr/bin/env sh
set -eu
exec pypy3 -m notizen_pypy_slint "$@"
