# Validation v8

Performed in the build workspace:

- `python3 -S -m py_compile scripts/repair_qml_engine_errors.py scripts/continue_qt611_transpile.py`: OK
- `bash -n scripts/build_python_qt.sh`: OK
- Manual unit checks for parsing Qt engine errors and patching `padding: 12` to `property real padding: 12`: OK

PySide6 runtime smoke tests must run on the real repository because the user's project tree and installed Qt/PySide environment are local to that machine.
