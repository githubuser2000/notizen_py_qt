"""Compatibility wrapper for the old package name.

The project was renamed to :mod:`notizen_py_qt`. Keep this package so
existing commands such as ``python3 -m notizen_pypy_qt`` keep working.
"""

from notizen_py_qt import *  # noqa: F401,F403
