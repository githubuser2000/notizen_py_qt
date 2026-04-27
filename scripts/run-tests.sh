#!/usr/bin/env sh
set -eu
PYTHONPATH=src exec pypy3 -m unittest discover -s tests -v
