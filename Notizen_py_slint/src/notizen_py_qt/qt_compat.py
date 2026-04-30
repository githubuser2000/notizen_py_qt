from __future__ import annotations

import json
import os
from collections.abc import Iterable
from typing import Any, Callable


class QtListModel(list):
    """Small replacement for the former UI toolkit's Python ListModel."""

    def __init__(self, values: Iterable[Any] | None = None) -> None:
        super().__init__(values or [])

    def set_array(self, values: Iterable[Any]) -> None:
        self[:] = list(values)


class QtCompatNamespace:
    ListModel = QtListModel


class QtCompatWindow:
    """Dynamic window proxy used by the controller during the Qt migration.

    It stores properties such as ``rows`` and ``window_title`` and records old
    ``on_name(callback)`` callback registrations. When PySide6 is available,
    ``run()`` opens the generated QML through ``qt_runtime.run_qml_app``.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "_props", {})
        object.__setattr__(self, "_callbacks", {})
        object.__setattr__(self, "_backend", None)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("on_"):
            event = name[3:]
            def bind(callback: Callable[..., Any] | None = None) -> None:
                self._callbacks[event] = callback
            return bind
        if name in self._props:
            return self._props[name]
        # Compatibility: many tests probe optional UI properties before the QML
        # object exists. Returning None is closer to a missing Qt property than
        # raising AttributeError during the migration window.
        return None

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self._props[name] = value
            backend = self._backend
            if backend is not None:
                try:
                    if name in {"status", "status_text", "statusText"}:
                        backend.setStatusText(str(value))
                    elif name in {"content", "content_text", "contentText"}:
                        backend.setContentText(str(value))
                    elif name == "rows":
                        backend.setRowsJson(json.dumps(value, ensure_ascii=False, default=str))
                except Exception:
                    pass

    def emit(self, event: str, *args: Any, **kwargs: Any) -> Any:
        callback = self._callbacks.get(event)
        if callback is not None:
            return callback(*args, **kwargs)
        return None

    def show(self) -> None:
        return None

    def hide(self) -> None:
        return None

    def run(self) -> int:
        try:
            from .qt_backend import NotizenQtBackend
            from .qt_runtime import run_qml_app
        except Exception as exc:
            print(f"Qt-Laufzeit nicht verfügbar: {exc}")
            return 2
        backend = NotizenQtBackend()
        object.__setattr__(self, "_backend", backend)
        if "status" in self._props:
            backend.setStatusText(str(self._props["status"]))
        if "rows" in self._props:
            try:
                backend.setRowsJson(json.dumps(self._props["rows"], ensure_ascii=False, default=str))
            except Exception:
                pass
        return run_qml_app(backend=backend, smoke_test=os.environ.get("NOTIZEN_QT_SMOKE_TEST") == "1")


def create_qt_window() -> QtCompatWindow:
    return QtCompatWindow()
