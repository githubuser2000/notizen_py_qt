from __future__ import annotations


def load_qt():
    """Load a Qt binding.

    PySide6 is preferred because the existing migration kit already targeted Qt
    for Python. PyQt6 is accepted as a fallback for users who already have it.
    """
    try:
        from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore

        return "PySide6", QtCore, QtGui, QtWidgets
    except ModuleNotFoundError as first_exc:
        try:
            from PyQt6 import QtCore, QtGui, QtWidgets  # type: ignore

            return "PyQt6", QtCore, QtGui, QtWidgets
        except ModuleNotFoundError as second_exc:
            raise ModuleNotFoundError(
                "No Qt binding is installed. Install one of:\n"
                "  python -m pip install 'PySide6>=6.6,<7'\n"
                "  python -m pip install 'PyQt6>=6.6,<7'"
            ) from second_exc
