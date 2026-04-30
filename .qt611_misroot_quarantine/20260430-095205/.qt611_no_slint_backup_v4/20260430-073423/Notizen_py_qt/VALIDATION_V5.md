# Validation v5

- Added `scripts/repair_pyproject_qt611.py`.
- Fixed the v4 duplicate `dependencies` insertion path.
- `build_python_qt.sh` now repairs `pyproject.toml` before `pip install -e .`.
- `finish_python_qt_migration.py` now uses the structural pyproject repair routine.
- `check_no_slint.sh` excludes the repair/migration tools and repair backups.

Local validation in this workspace:

```text
python -m py_compile scripts/*.py: OK
bash -n scripts/*.sh: OK
pytest tests: 5 passed
synthetic duplicate-key pyproject repair: OK
```

The real Notizen project was not present in this workspace, so the full application
build still needs to be run on the user's checkout.
