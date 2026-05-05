# Validation 0.10.23

## Ausgeführt

```bash
python3 -m compileall -q src notizen_py_qt scripts tests
bash -n notizen-starten.sh "Notizen starten.sh" notizen-starten-venv.sh scripts/install_linux_launcher.sh scripts/uninstall_linux_launcher.sh scripts/build_linux_appdir.sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src pytest -q --ignore=tests/test_v6_continue.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src pytest -q tests/test_v6_continue.py
```

Ergebnis:

```text
219 passed, 3 skipped in 12.46s
3 passed in 27.69s
```

Die Suite wurde in zwei Läufen ausgeführt, weil der komplette Ein-Prozess-Lauf in der Containerumgebung am Ende erneut in ein Tool-Timeout lief, nachdem keine Fehlschläge angezeigt wurden. Der Split-Lauf ist reproduzierbar und deckt die regulären Tests plus die alten Qt611-Hilfsskript-Tests ab.

## Neue/erweiterte Regressionstests

- `tests/test_desktop_rtf_print_layout_1023.py`: RTF-`\line` als weicher Zeilenumbruch, HTML-Absatzränder ohne Extra-Abstand, Haftnotiz-Transparenz/Minimieren, QTextEdit-Ränder, WinForms-nahes Hauptlayout, ToolStrip-RTF-Toolbar und PySide/PyQt-kompatibler Druckpfad.

## Einschränkung

Ein echter visueller GNOME-/Wayland-/X11-Klick, tatsächliche Taskleistenanzeige minimierter Haftnotizen und ein realer Druckdialog konnten im Container nicht interaktiv geprüft werden. Geprüft wurden Source, Kompatibilitätspfade, Shell-Syntax und automatisierte Regressionstests.
