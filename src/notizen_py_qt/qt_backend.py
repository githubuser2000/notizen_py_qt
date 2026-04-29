from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot


class NotizenQtBackend(QObject):
    """Small QObject bridge exposed to QML as ``notizenBackend``."""

    statusTextChanged = Signal()
    contentTextChanged = Signal()
    rowsJsonChanged = Signal()
    initialPathChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._status_text = "Bereit"
        self._content_text = ""
        self._rows_json = "[]"
        self._initial_path = ""

    @Property(str, notify=statusTextChanged)
    def statusText(self) -> str:
        return self._status_text

    @Slot(str)
    def setStatusText(self, value: str) -> None:
        if self._status_text != value:
            self._status_text = value
            self.statusTextChanged.emit()

    @Property(str, notify=contentTextChanged)
    def contentText(self) -> str:
        return self._content_text

    @Slot(str)
    def setContentText(self, value: str) -> None:
        if self._content_text != value:
            self._content_text = value
            self.contentTextChanged.emit()

    @Property(str, notify=rowsJsonChanged)
    def rowsJson(self) -> str:
        return self._rows_json

    @Slot(str)
    def setRowsJson(self, value: str) -> None:
        try:
            json.loads(value or "[]")
        except Exception:
            value = "[]"
        if self._rows_json != value:
            self._rows_json = value
            self.rowsJsonChanged.emit()

    @Property(str, notify=initialPathChanged)
    def initialPath(self) -> str:
        return self._initial_path

    @Slot(str)
    def setInitialPath(self, value: str) -> None:
        value = str(Path(value).expanduser()) if value else ""
        if self._initial_path != value:
            self._initial_path = value
            self.initialPathChanged.emit()
            self.setStatusText(f"Startdatei: {value}" if value else "Bereit")

    @Slot(str, result=str)
    def echo(self, value: str) -> str:
        return value

    @Slot(str)
    def openFile(self, path: str) -> None:
        self.setInitialPath(path)
        self.setStatusText(f"Öffnen angefordert: {path}")

    @Slot(str)
    def saveFile(self, path: str) -> None:
        self.setStatusText(f"Speichern angefordert: {path}")

    @Slot(str)
    def notify(self, message: str) -> None:
        self.setStatusText(message)
