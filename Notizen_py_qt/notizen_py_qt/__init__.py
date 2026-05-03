"""Source-tree launcher shim for ``python -m notizen_py_qt``.

The real package lives in ``src/notizen_py_qt``.  When this archive is unpacked
but not installed, Python would otherwise import an older installed package or
fail to find the module.  This shim extends the package search path to the local
``src`` package and executes its ``__init__`` in this package namespace.
"""
from __future__ import annotations

from pathlib import Path

_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "notizen_py_qt"
if _SRC_PACKAGE.is_dir():
    src_path = str(_SRC_PACKAGE)
    if src_path not in __path__:
        __path__.insert(0, src_path)  # type: ignore[name-defined]
    _INIT = _SRC_PACKAGE / "__init__.py"
    exec(compile(_INIT.read_text(encoding="utf-8"), str(_INIT), "exec"), globals(), globals())
else:  # pragma: no cover - only relevant when the archive layout is broken
    raise ModuleNotFoundError("src/notizen_py_qt was not found next to the launcher shim")
