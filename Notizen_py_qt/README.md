# Notizen Python/Qt Port

Dies ist die Weitertranspilierung des alten VB.NET/WinForms-Projekts **Notizen.NET** nach Python/Qt.

## Start

```bash
python -m pip install -e ".[crypto]"
notizen-py-qt /pfad/zur/datei.alx
```

PySide6 ist die bevorzugte Qt-Bindung. PyQt6 wird vom Kompatibilitätslayer ebenfalls akzeptiert, falls PySide6 nicht installiert ist.

## Enthalten

- ALX-Dateiformat mit GZip, UTF-16-XML und Legacy-DES-Passwortmodus.
- Baumansicht, Editor, Knotenoperationen, Suche, Export, Backups.
- Desktop-Notizen, System-Tray, Grundeinstellungen und zuletzt geöffnete Dateien.
- FTP-Öffnen/Speichern wie im alten `ftpkram.vb`.
- Einfacher Weckerdialog per `Ctrl+Space`.
- Importiertes Notizen-Icon als Paketressource plus `.qrc`.

Details stehen in [`TRANSPILE_NET_TO_PYQT_REPORT.md`](TRANSPILE_NET_TO_PYQT_REPORT.md). Validierung steht in [`VALIDATION_NET_PORT.md`](VALIDATION_NET_PORT.md).

---

# Qt 6.11 / no-Slint migration kit v8

v8 continues after a successful PySide6 install and clean static QML syntax check.
It repairs first-order QML engine errors reported by `QQmlApplicationEngine`, especially generated assignments such as `padding: 8` on `Item` or `Rectangle`, which Qt rejects because those types do not own a `padding` property.

## Recommended command

```bash
python3 scripts/repair_qml_engine_errors.py /path/to/Notizen_Py_Slint --apply --run-smoke --max-rounds 12 --static-padding-pass
bash scripts/build_python_qt.sh /path/to/Notizen_Py_Slint
```

`build_python_qt.sh` in v8 automatically runs the engine repair once if the first runtime probe fails.

## What gets changed

A line such as:

```qml
padding: 8
```

is preserved as a custom property when Qt says the target object has no such built-in property:

```qml
property real padding: 8
```

This is a pragmatic transpilation continuation step: the component loads again, and the numeric value remains available for later layout refinement.

Backups are written under `.qt611_qml_engine_repair_backup/<timestamp>/`.
A report is written to `QT611_QML_ENGINE_REPAIR.md`.
