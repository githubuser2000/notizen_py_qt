# Qt 6.11 / Slint-Removal Migration Kit v2

Dieses Kit stellt ein Slint-basiertes Transpilierungsprojekt auf **Qt 6.11 + Qt Quick/QML** um. Gegenüber v1 ist jetzt ein echter Best-Effort-Transpilierer enthalten: `.slint`-Dateien werden nicht nur archiviert, sondern zuerst nach QML übersetzt.

## Was v2 jetzt macht

- entfernt Slint-Abhängigkeiten aus `Cargo.toml`;
- ersetzt `build.rs`-Slint-Build-Hooks durch CXX-Qt-Buildintegration;
- benennt Cargo-Paketnamen um, wenn darin `slint` vorkommt;
- transpiliert `.slint` nach `qml/*.qml`;
- erzeugt pro `.slint` einen JSON-Report mit Warnungen;
- archiviert oder löscht alte `.slint`-Dateien danach;
- erzeugt einen Qt-6.11-CMake/Qt-Quick-Shell;
- liefert eine Cargo/CXX-Qt-Vorlage mit `cxx-qt 0.8.1`;
- prüft aktiv, ob Slint-Referenzen in Source-/Build-Dateien übrig sind.

## Wichtig

Der Transpilierer ist bewusst konservativ. Er übersetzt häufige Slint-UI-Strukturen direkt und markiert unsichere Stellen als `TODO(slint->qml)`. Das ist besser als ein scheinbar erfolgreicher Blindflug: QML soll danach kompilierbar und reviewbar sein, aber komplexe Slint-Zustände, Animationen, globale Singletons und eigene Datenmodelle brauchen fast immer manuelle Nacharbeit.

## Sofort auf ein echtes Projekt anwenden

Vom Projektwurzelverzeichnis aus:

```bash
python3 /pfad/zum/kit/scripts/migrate_remove_slint_to_qt611.py . --apply --rust-cxx-qt --overwrite-qml
bash /pfad/zum/kit/scripts/check_no_slint.sh .
bash /pfad/zum/kit/scripts/verify_qt611_environment.sh --rust
```

Dann bauen:

```bash
bash /pfad/zum/kit/scripts/build_qt611.sh . build/qt611
```

Wenn Qt 6.11 nicht im Standardsuchpfad liegt:

```bash
export QMAKE="$HOME/Qt/6.11.0/gcc_64/bin/qmake6"
cmake -S . -B build/qt611 \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$HOME/Qt/6.11.0/gcc_64"
cmake --build build/qt611 --parallel
```

Für Cargo/CXX-Qt zusätzlich:

```bash
export QT_VERSION_MAJOR=6
export QMAKE="$HOME/Qt/6.11.0/gcc_64/bin/qmake6"
cargo run
```

## Einzelne `.slint`-Datei direkt transpilieren

```bash
python3 scripts/slint_to_qml.py path/to/MainWindow.slint -o qml --overwrite
```

Das erzeugt z. B.:

- `qml/MainWindow.qml`
- `qml/Main.qml`, falls der Komponentenname nach Hauptfenster aussieht
- `qml/main_window.slint_to_qml.report.json`

## Tests ausführen

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -v
```

In dieser Containerumgebung musste ich `python3 -S` verwenden, weil der globale Python-`site`-Import hängt. Auf normalen Entwicklungsmaschinen sollte `python3` reichen.

## Dateien im Kit

- `scripts/slint_to_qml.py` — Best-Effort-Transpilierer von Slint nach QML.
- `scripts/migrate_remove_slint_to_qt611.py` — Projektmigration: Slint raus, QML rein, Qt-6.11-Shell erzeugen.
- `scripts/check_no_slint.sh` — harter Scanner für aktive Source-/Build-Dateien.
- `scripts/verify_qt611_environment.sh` — prüft Qt-6.11/qmake/CMake/Cargo-Umgebung.
- `scripts/build_qt611.sh` — prüft Umgebung und baut über CMake.
- `template_cpp_qml/` — reines C++/Qt-Quick-Projekt.
- `template_rust_cxx_qt/` — Cargo/CXX-Qt/QML-Projekt mit Rust-Backend.
- `examples/main_window.slint` — Beispielquelle.
- `transpiled_examples/MainWindow.qml` — Ergebnis der Beispieltranspilierung.
- `docs/MAPPING.md` — genaue Mapping-Regeln und Grenzen.
- `TRANSPILE_ATTEMPT.log` — Protokoll der bisherigen Arbeit.
