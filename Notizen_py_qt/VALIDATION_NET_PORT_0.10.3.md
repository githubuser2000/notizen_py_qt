# Validierungsbericht Notizen.NET → Python/Qt 0.10.3

## Zusammenfassung

Der Stand 0.10.3 wurde funktional, syntaktisch, strukturell und mit Blick auf die neuen Startdateien geprüft. Die GUI konnte in dieser Umgebung nicht visuell gestartet werden, weil weder PySide6 noch PyQt6 installiert ist. Der Direktstarter erkennt diesen Zustand und meldet ihn verständlich.

## Prüfumgebung

- Python: aus der bereitgestellten Ausführungsumgebung
- Projekt: entpacktes Archiv `notizenPyQt_0.10.2.zip`, weitergeführt zu 0.10.3
- Qt-Bindung: nicht installiert
- Tests: reine Modell-, Datei-, Einstellungs-, Tray-, Launcher- und Portierungslogik

## Durchgeführte Prüfungen

### Pytest

```text
62 passed, 2 skipped
```

### Compileall

```text
python -m compileall -q src tests scripts
OK
```

### Shell-Syntax

```text
bash -n scripts/*.sh
bash -n *.sh
OK
```

Geprüfte neue Startdateien:

- `notizen-starten.sh`
- `Notizen starten.sh`
- `scripts/install_linux_launcher.sh`

### Slint-/QML-Aktivpfadprüfung

```text
scripts/check_no_slint_strict.sh
OK: no old UI-framework references found in active source/build files
```

### API-Probe ohne installierte Qt-Bindung

```text
PYTHONPATH=src python - <<'PY'
import notizen_py_qt
print(notizen_py_qt.__version__)
PY
```

Ergebnis:

```text
0.10.3
```

### GNOME-Tray-Entscheidung

Geprüft wurde, dass GNOME auch mit erkannter AppIndicator-Erweiterung nicht mehr automatisch verborgen ins Tray startet:

```text
hide_to_tray = False
```

Erzwungener Tray-Start bleibt per `--force-tray-start` möglich und ist in den Tests abgedeckt.

### Direktstarter ohne Qt

```bash
./notizen-starten.sh --smoke-test
```

Erwartetes Ergebnis in dieser Umgebung:

```text
Exit-Code: 2
Qt für Python fehlt. Installiere es mit:

python -m pip install --user 'PySide6>=6.6,<7'
```

Das ist korrekt, weil die Umgebung keine Qt-Bindung enthält. Wichtig ist: Der Starter endet nicht still und nicht unsichtbar.

## Neue Tests in 0.10.3

`tests/test_launchers_103.py` prüft:

- `notizen-starten.sh` ist ausführbar.
- Der Starter setzt `PYTHONPATH`.
- Der Starter ruft `-m notizen_py_qt` auf.
- Der Starter hängt standardmäßig `--show` und `--no-tray` an.
- `Notizen starten.sh` delegiert an `notizen-starten.sh`.
- `Notizen PyQt.desktop` verweist auf den relativen Startpfad.
- `scripts/install_linux_launcher.sh` erzeugt einen sichtbaren No-Tray-Starter.
- Shell-Syntax der neuen Startdateien ist gültig.

`tests/test_tray_permissions_102.py` wurde angepasst:

- GNOME bleibt auch mit erkannter AppIndicator-Erweiterung sichtbar.
- Versteckter Tray-Start funktioniert nur bei explizitem Force-Flag.
- `.desktop`-Dateien werden in der ZIP-Rechte-Policy als ausführbare Starter behandelt.

## ZIP-Rechteprüfung

Nach dem Paketieren muss gelten:

```text
755 Notizen_py_qt/
755 Notizen_py_qt/notizen-starten.sh
755 Notizen_py_qt/Notizen starten.sh
755 Notizen_py_qt/Notizen PyQt.desktop
755 Notizen_py_qt/scripts/install_linux_launcher.sh
755 Notizen_py_qt/scripts/package_zip.py
644 Notizen_py_qt/src/notizen_py_qt/app.py
```

## Nicht visuell geprüft

Nicht geprüft wurde:

- tatsächliches Öffnen des Hauptfensters in GNOME,
- Darstellung des `.desktop`-Starters im GNOME-Menü,
- visuelle Funktion der PySide6-/PyQt6-Oberfläche.

Dafür ist lokal eine Qt-Bindung nötig:

```bash
python3 -m pip install --user "PySide6>=6.6,<7"
./Notizen\ starten.sh
```

## Bewertung

0.10.3 ist gegenüber 0.10.2 deutlich sicherer für GNOME: Der Standardpfad startet sichtbar ohne Tray und kann direkt aus dem Archiv geklickt oder über ein installiertes Desktop-Menü gestartet werden. Die alte Tray-Logik ist nicht entfernt, aber sie muss jetzt bewusst erzwungen werden.
