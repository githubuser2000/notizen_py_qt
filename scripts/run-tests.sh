#!/usr/bin/env sh
set -eu
PYTHONPATH=src exec python3 -m unittest discover -s tests -v
