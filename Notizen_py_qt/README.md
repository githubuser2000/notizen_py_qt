# Qt 6.11 / No-Qt Migration Kit v3

Dieses Kit migriert ein Rust/C++ UI-Projekt von Qt auf Qt 6.11 mit Qt Quick/QML.
Es arbeitet bewusst konservativ: alles, was mechanisch übersetzbar ist, wird nach
QML übertragen; alles Unsichere wird als Warnung im JSON-/Markdown-Report abgelegt
und, falls nötig, als `TODO(qt611-port)` in generiertem QML markiert.

## Wichtigste Neuerungen in v3

- echte Qt→QML-Transpilierung für Komponenten, Widgets, Layouts und Bindings
- `export global ...` → QML Singleton (`pragma Singleton`, `QtObject`)
- `enum`/`struct` → `Qt611Types.js` Hilfsbibliothek
- `<=>`-Bindings → QML-Binding plus Rückwärts-Handler, wo mechanisch sicher
- `animate property { ... }` → `Behavior on property { NumberAnimation { ... } }`
- automatische Entfernung offensichtlicher Rust-Qt-Hooks, z. B. `qt::include_modules!()` und `use qt::...`
- generierte Singleton-CMake-Datei für `QT_QML_SINGLETON_TYPE`
- `qml_sanity_check.py` für schnelle QML/JS-Klammerprüfung
- `analyze_transpilation.py` erzeugt `QT611_MIGRATION_STATUS.md`
- `check_no_qt.sh` prüft aktive Source-/Build-Dateien hart auf verbliebene Qt-Referenzen

## Empfohlene Ausführung auf dem echten Projekt

```bash
python3 qt611_no_qt_migration_kit_v3/scripts/migrate_remove_qt_to_qt611.py . \
  --apply \
  --rust-cxx-qt \
  --overwrite-qml

bash qt611_no_qt_migration_kit_v3/scripts/check_no_qt.sh .
python3 qt611_no_qt_migration_kit_v3/scripts/qml_sanity_check.py .
python3 qt611_no_qt_migration_kit_v3/scripts/analyze_transpilation.py . --write
bash qt611_no_qt_migration_kit_v3/scripts/verify_qt611_environment.sh --rust
bash qt611_no_qt_migration_kit_v3/scripts/build_qt611.sh . build/qt611
```

Wenn Qt 6.11 nicht im Standardpfad liegt:

```bash
export QMAKE="$HOME/Qt/6.11.0/gcc_64/bin/qmake6"
export CMAKE_PREFIX_PATH="$HOME/Qt/6.11.0/gcc_64"
```

## Was verändert wird

- `.qml`-Dateien werden zuerst nach `qml/*.qml` transpiliert.
- Danach werden `.qml`-Dateien nach `legacy_qt/` verschoben oder mit `--delete-qt` gelöscht.
- `Cargo.toml` verliert Qt-Dependencies und erhält optional CXX-Qt-Dependencies.
- `build.rs` wird auf CXX-Qt/QML-Buildintegration umgestellt, wenn `--rust-cxx-qt` gesetzt ist.
- offensichtliche Rust-Hooks des alten UI-Frameworks werden entfernt; die Originale liegen in `.qt611_no_qt_backup/<timestamp>/`.
- falls noch kein Qt-CMake-Einstieg existiert, wird ein Qt-6.11-Quick-Projektgerüst erzeugt.

## Dateien im Kit

```text
scripts/qt_to_qml.py                 Qt→QML-Transpilierer
scripts/migrate_remove_qt_to_qt611.py Projektmigration mit Backups
scripts/check_no_qt.sh               harte Restreferenzprüfung
scripts/qml_sanity_check.py             QML/JS-Sanity-Check
scripts/analyze_transpilation.py        Markdown-Statusreport
scripts/verify_qt611_environment.sh     Qt/CMake/Rust-Umgebungscheck
scripts/build_qt611.sh                  Prüfung + CMake-Build
cmake/Qt611QuickApp.CMakeLists.txt      Qt-6.11-CMake-Vorlage
template_cpp_qml/                       reine C++/QML-Vorlage
template_rust_cxx_qt/                   Rust+CXX-Qt+QML-Vorlage
examples/                               Qt-Beispiele
transpiled_examples/                    generierte QML/JS-Beispiele
```

## Validierung, die in dieser Umgebung lief

```text
Unit-Tests: 3/3 OK
QML/JS-Sanity-Check auf generierten Beispielen: OK
check_no_qt.sh auf dem Kit: OK
Sample-Projektmigration mit Cargo.toml/build.rs/Rust/.qml: OK
```

Der echte Qt-Build wurde hier nicht ausgeführt, weil in dieser Umgebung kein Qt 6.11,
kein qmake6 und kein nutzbarer Rust/Cargo-Projektquellbaum deines Projekts vorhanden
sind. Das Kit ist dafür vorbereitet, den Build auf deiner Maschine oder im CI auszuführen.
## v4: Python-Paket nach Qt for Python fertig migrieren

Wenn nach der `.qml`→QML-Konvertierung noch Treffer wie `notizen_py_qt`, alte Entry-Points, Python-Kommentare oder QML-Titel mit dem alten UI-Framework übrig sind, führe zusätzlich aus:

```bash
python3 scripts/finish_python_qt_migration.py .. --apply
bash scripts/check_no_qt.sh ..
```

Der Schritt macht bewusst mehr als eine Textkosmetik:

- benennt `src/notizen_py_qt` nach `src/notizen_py_qt` um,
- benennt `src/notizen_pypy_qt` nach `src/notizen_pypy_qt` um,
- aktualisiert `pyproject.toml`, Entry-Points, Tests und Shell-Skripte,
- entfernt die alte optionale UI-Abhängigkeit,
- fügt `PySide6>=6.11,<6.12` als Qt-for-Python-Laufzeit hinzu,
- kopiert generierte QML/JS-Dateien aus `qml/` nach `src/notizen_py_qt/ui/`,
- ersetzt den alten Python-UI-Controller durch einen Qt/QML-Runner mit `QQmlApplicationEngine`,
- erzeugt `src/notizen_py_qt/qt_backend.py` als QObject-Brücke für QML,
- archiviert alte `.egg-info`-Metadaten nach `legacy_build_metadata/`.

Danach kann die Python-Qt-Variante mit einem Smoke-Test geprüft werden:

```bash
bash scripts/build_python_qt.sh ..
```

Der alte Controller wird vor dem Überschreiben unter `.qt611_no_qt_backup_v4/<timestamp>/` gesichert.
