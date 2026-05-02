# Transpilationsbericht Notizen.NET → Python/Qt 0.10.3

## Ausgangslage

Der Stand 0.10.2 hatte bereits korrekte ZIP-Rechte und einen ersten Schutz gegen den unsichtbaren GNOME-Tray-Start. Die neue Rückmeldung zeigt aber, dass das in GNOME praktisch noch nicht robust genug ist: Selbst mit Tray-Erkennung kann die Anwendung für den Nutzer unerreichbar bleiben. Zusätzlich soll die Anwendung aus dem entpackten Archiv direkt per Startdatei ausführbar sein und nicht nur über `python -m` oder ein installiertes Konsolenskript.

Der aktive Port bleibt Python/Qt mit PySide6/PyQt6-Kompatibilität. Frühere Slint-/QML-/Rust-Zwischenschritte bleiben archiviert und sind weiterhin nicht Teil des aktiven Laufzeitpfads.

## Umgesetzte Änderungen in 0.10.3

### 1. Direkt startbare Dateien im Archiv

Neu im Wurzelordner:

- `Notizen starten.sh`
- `notizen-starten.sh`
- `Notizen PyQt.desktop`

`Notizen starten.sh` ist die menschenlesbare Startdatei und delegiert an `notizen-starten.sh`. Der technische Starter ermittelt seinen eigenen Projektordner, setzt automatisch `PYTHONPATH=<Projekt>/src` und startet dann das Paketmodul. Dadurch kann der entpackte Quellstand ohne vorheriges `python -m notizen_py_qt` gestartet werden.

Der Starter bevorzugt:

1. die Umgebungsvariable `PYTHON`, falls gesetzt,
2. `.venv/bin/python` im Projektordner,
3. `python3`,
4. `python`.

Wenn weder PySide6 noch PyQt6 installiert ist, erscheint eine klare Fehlermeldung mit Installationsbefehl statt eines stillen Fehlstarts.

### 2. GNOME sichtbar-first statt Tray-first

Der GNOME-Schutz wurde bewusst verschärft. Ab 0.10.3 versteckt sich die Anwendung unter GNOME beim Start nicht mehr automatisch ins Tray, auch dann nicht, wenn eine bekannte AppIndicator/KStatusNotifier-Erweiterung erkannt wird. Der Grund ist die konkrete Nutzererfahrung: Eine erkannte Erweiterung bedeutet nicht zuverlässig, dass das Icon in der jeweiligen GNOME-Sitzung sichtbar und erreichbar ist.

Das alte versteckte Tray-Verhalten bleibt nur noch über explizite Absicht erreichbar:

```bash
./notizen-starten.sh --allow-tray --force-tray-start --minimized
```

Die neue Startdatei hängt standardmäßig an:

```text
--show --no-tray
```

Damit werden gespeicherte `Minimized`-Fensterzustände und alte `/min`-/`-min`-Startzustände für den Direktstart übersteuert. Das Hauptfenster wird sichtbar geöffnet und das Trayicon deaktiviert.

### 3. Neuer CLI-Schalter `--show` / `--visible`

`app.py` akzeptiert jetzt:

```bash
notizen-py-qt --show
notizen-py-qt --visible
```

Dieser Schalter erzwingt einen sichtbaren Start. Er hat Vorrang vor:

- altem `/min`, `-min`, `min`,
- `--minimized`, wenn über die Startdatei nicht zusätzlich verwendet,
- gespeichertem Fensterzustand `Minimized` aus der Config.

Das ist wichtig für GNOME, aber auch allgemein nützlich, wenn eine alte Config das Programm immer wieder minimiert starten ließ.

### 4. Linux-/GNOME-Anwendungsstarter

Neu:

```bash
scripts/install_linux_launcher.sh
```

Das Skript installiert einen Starter unter:

```text
$XDG_DATA_HOME/applications/notizen-py-qt.desktop
```

beziehungsweise standardmäßig unter:

```text
~/.local/share/applications/notizen-py-qt.desktop
```

Zusätzlich wird das Icon aus `src/notizen_py_qt/resources/notizen.png` nach:

```text
~/.local/share/icons/hicolor/256x256/apps/notizen-py-qt.png
```

kopiert. Der erzeugte Menüeintrag nutzt eine absolute `Exec=`-Zeile und startet ebenfalls sichtbar ohne Tray:

```text
--show --no-tray
```

Mit:

```bash
scripts/install_linux_launcher.sh --desktop
```

wird zusätzlich eine anklickbare Desktop-/Schreibtisch-Datei erstellt und, soweit über `gio` möglich, als vertrauenswürdig markiert.

### 5. ZIP-Rechte für Desktop-Starter erweitert

Die Verpackungshilfe `scripts/package_zip.py` speichert jetzt auch `.desktop`-Dateien als ausführbare Startdateien mit `755`. Die bestehende Rechte-Policy bleibt erhalten:

- Verzeichnisse: `755`
- Shell-Skripte: `755`
- Python-Skripte unter `scripts/`: `755`
- Desktop-Starter: `755`
- normale Dateien: `644`

### 6. Dokumentation und Tests

Aktualisiert:

- `README.md`
- `docs/MAPPING.md`
- `docs/PROJECT_CONTEXT_IMPORTED.md`
- `TRANSPILE_NET_TO_PYQT_REPORT.md`
- `VALIDATION_NET_PORT.md`

Archiviert:

- `TRANSPILE_NET_TO_PYQT_REPORT_0.10.2.md`
- `VALIDATION_NET_PORT_0.10.2.md`

Neue beziehungsweise angepasste Tests:

- `tests/test_launchers_103.py`
- `tests/test_tray_permissions_102.py`

## Ergebnis

0.10.3 behebt die praktische GNOME-Aussperrung robuster als 0.10.2: Der sichere Standard ist jetzt ein sichtbarer Fensterstart ohne Tray. Gleichzeitig kann die Anwendung aus dem entpackten Archiv über eine echte Startdatei gestartet werden. Wer das alte Tray-Verhalten bewusst nutzen will, kann es weiterhin explizit erzwingen.

## Weiter offene Punkte

- Die echte visuelle Qt-Prüfung muss lokal mit installierter PySide6- oder PyQt6-Bindung erfolgen.
- Ein vollständiges Linux-Paketformat wie `.deb`, `.rpm`, AppImage oder Flatpak ist noch nicht erzeugt. Für diese Runde wurde bewusst zuerst der robuste Direktstarter aus dem Quellarchiv umgesetzt.
