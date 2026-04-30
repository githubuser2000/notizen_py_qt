# Validation v6

Executed in the build container:

```text
python3 -m py_compile scripts/*.py: OK
bash -n scripts/*.sh: OK
pytest -q tests: 8 passed
synthetic continue_qt611_transpile.py --apply --no-restore-controller: OK
synthetic continue_qt611_transpile.py --apply with controller restore: OK
check_no_slint.sh on synthetic migrated projects: OK
```

Not executed here:

```text
pip install -e . on the user's real checkout
PySide6/Qt runtime smoke test on the user's real checkout
```

Reason: the real repository and local PySide6/Qt runtime are available on the user's machine, not in this workspace.
