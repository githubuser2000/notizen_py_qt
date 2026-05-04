# Validierung Notizen PyQt 0.10.22

## Ausgeführt

```bash
python3 -m compileall -q src notizen_py_qt scripts tests
bash -n notizen-starten.sh "Notizen starten.sh" notizen-starten-venv.sh scripts/install_linux_launcher.sh scripts/uninstall_linux_launcher.sh scripts/build_linux_appdir.sh
pytest -q --ignore=tests/test_v6_continue.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -vv tests/test_v6_continue.py
```

## Ergebnis

```text
213 passed, 3 skipped in 13.35s
3 passed in 18.56s
```

Der komplette Ein-Prozess-Testlauf erreichte in der Containerumgebung 98 % ohne angezeigte Fehlschläge, lief aber in ein Tool-Timeout. Deshalb ist der reproduzierbare Split-Lauf oben dokumentiert.

## Neue Regressionstests

- `tests/test_rtf_fidelity_1022.py`
  - `\plain` behält Absatzformatierung,
  - `\slmult`, `\cbpat` und Unterstreichungsvarianten,
  - Fonttabellen mit `\*\falt`-Aliasgruppen,
  - Farbtabellen ohne führenden Automatikslot,
  - HTML/CSS→RTF für Caps, Small-Caps, Hidden, RTL/LTR, Letter-Spacing, Margin-Kurzform, Prozent-Zeilenhöhe,
  - semantische HTML-Tags/Attribute wie `body`, `font`, `center`, `blockquote`, `code`, `big`.

## Einschränkung

Eine echte grafische RichTextBox unter Windows und eine echte GNOME-/Window-Manager-Sitzung konnten im Container nicht visuell gegengeprüft werden. Die Änderungen sind über Parser-, Exporter- und Roundtrip-Regressionstests abgesichert.
