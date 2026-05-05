# Validierung 0.10.25

Ausgeführt im Archivstand `Notizen_py_qt`.

```bash
python3 -m compileall -q src notizen_py_qt scripts tests
bash -n notizen-starten.sh "Notizen starten.sh" notizen-starten-venv.sh \
  scripts/install_linux_launcher.sh scripts/uninstall_linux_launcher.sh \
  scripts/build_linux_appdir.sh scripts/continue_qt611_transpile.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q --ignore=tests/test_v6_continue.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 QT611_CONTINUE_STEP_TIMEOUT=60 \
  pytest -q tests/test_v6_continue.py -o faulthandler_timeout=300
```

Ergebnisse:

```text
227 passed, 3 skipped in 9.34s
3 passed in 20.96s
```

Zusätzlich gezielt geprüft:

- generische RTF-Felder zeigen `fldrslt` und bewahren die Rohgruppe,
- RTF-/OLE-Objektgruppen bleiben in HTML-Roundtrip und RTF-Baumexport erhalten,
- unbekannte `.alx`-Kindelemente unter `<Notiz>` werden beim Speichern nicht verworfen.
