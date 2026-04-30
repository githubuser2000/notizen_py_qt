# Qt 6.11 / no-Slint migration kit v7

v7 fixes the parent-folder mis-run seen in the real Notizen repository.

Key changes:

- auto-detects the real Python project root via `pyproject.toml`
- quarantines accidental artifacts generated in the parent folder
- ignores `.qt611*` backups during scans and QML hardening
- prevents the migration tools from rewriting themselves into `check_no_qt.sh`
- repairs generated QML TODO callback blocks that left unmatched `}` braces
- runs the Python/Qt runtime hardening in the detected project root

Recommended command from the freshly extracted v7 kit directory:

```bash
python3 scripts/continue_qt611_transpile.py /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint --apply --probe
```

Then:

```bash
bash scripts/check_no_slint.sh /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint
bash scripts/build_python_qt.sh /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint
```

If you know the real project root, passing it directly is also fine:

```bash
python3 scripts/continue_qt611_transpile.py /home/alex/Eigene-Dateien/myRepos/Notizen_Py_Slint/Notizen_py_slint --apply --probe
```
