# Qt 6.11 no-legacy-UI migration kit v5

v5 fixes the `pyproject.toml` duplicate-key problem seen during `pip install -e .`:

```text
tomllib.TOMLDecodeError: Cannot overwrite a value
```

Run this repair first on a project that was already migrated with v4:

```bash
python3 scripts/repair_pyproject_qt611.py .. --apply
bash scripts/build_python_qt.sh ..
```

For a fresh run, use:

```bash
python3 scripts/migrate_remove_slint_to_qt611.py .. --apply --rust-cxx-qt --overwrite-qml
python3 scripts/finish_python_qt_migration.py .. --apply
python3 scripts/repair_pyproject_qt611.py .. --apply
bash scripts/check_no_slint.sh ..
bash scripts/build_python_qt.sh ..
```

`build_python_qt.sh` now calls the pyproject repair step before `pip install -e .`, so re-running it is safe.

---

# Qt 6.11 / No-Slint Migration Kit v3

Dieses Kit migriert ein Rust/C++ UI-Projekt von Slint auf Qt 6.11 mit Qt Quick/QML.
Es arbeitet bewusst konservativ: alles, was mechanisch übersetzbar ist, wird nach
QML übertragen; alles Unsichere wird als Warnung im JSON-/Markdown-Report abgelegt
und, falls nötig, als `TODO(qt611-port)` in generiertem QML markiert.

## Wichtigste Neuerungen in v3

- echte Slint→QML-Transpilierung für Komponenten, Widgets, Layouts und Bindings
- `export global ...` → QML Singleton (`pragma Singleton`, `QtObject`)
- `enum`/`struct` → `Qt611Types.js` Hilfsbibliothek
- `<=>`-Bindings → QML-Binding plus Rückwärts-Handler, wo mechanisch sicher
- `animate property { ... }` → `Behavior on property { NumberAnimation { ... } }`
- automatische Entfernung offensichtlicher Rust-Slint-Hooks, z. B. `slint::include_modules!()` und `use slint::...`
- generierte Singleton-CMake-Datei für `QT_QML_SINGLETON_TYPE`
- `qml_sanity_check.py` für schnelle QML/JS-Klammerprüfung
- `analyze_transpilation.py` erzeugt `QT611_MIGRATION_STATUS.md`
- `check_no_slint.sh` prüft aktive Source-/Build-Dateien hart auf verbliebene Slint-Referenzen

## Empfohlene Ausführung auf dem echten Projekt

```bash
python3 qt611_no_slint_migration_kit_v3/scripts/migrate_remove_slint_to_qt611.py . \
  --apply \
  --rust-cxx-qt \
  --overwrite-qml

bash qt611_no_slint_migration_kit_v3/scripts/check_no_slint.sh .
python3 qt611_no_slint_migration_kit_v3/scripts/qml_sanity_check.py .
python3 qt611_no_slint_migration_kit_v3/scripts/analyze_transpilation.py . --write
bash qt611_no_slint_migration_kit_v3/scripts/verify_qt611_environment.sh --rust
bash qt611_no_slint_migration_kit_v3/scripts/build_qt611.sh . build/qt611
```

Wenn Qt 6.11 nicht im Standardpfad liegt:

```bash
export QMAKE="$HOME/Qt/6.11.0/gcc_64/bin/qmake6"
export CMAKE_PREFIX_PATH="$HOME/Qt/6.11.0/gcc_64"
```

## Was verändert wird

- `.slint`-Dateien werden zuerst nach `qml/*.qml` transpiliert.
- Danach werden `.slint`-Dateien nach `legacy_slint/` verschoben oder mit `--delete-slint` gelöscht.
- `Cargo.toml` verliert Slint-Dependencies und erhält optional CXX-Qt-Dependencies.
- `build.rs` wird auf CXX-Qt/QML-Buildintegration umgestellt, wenn `--rust-cxx-qt` gesetzt ist.
- offensichtliche Rust-Hooks des alten UI-Frameworks werden entfernt; die Originale liegen in `.qt611_no_slint_backup/<timestamp>/`.
- falls noch kein Qt-CMake-Einstieg existiert, wird ein Qt-6.11-Quick-Projektgerüst erzeugt.

## Dateien im Kit

```text
scripts/slint_to_qml.py                 Slint→QML-Transpilierer
scripts/migrate_remove_slint_to_qt611.py Projektmigration mit Backups
scripts/check_no_slint.sh               harte Restreferenzprüfung
scripts/qml_sanity_check.py             QML/JS-Sanity-Check
scripts/analyze_transpilation.py        Markdown-Statusreport
scripts/verify_qt611_environment.sh     Qt/CMake/Rust-Umgebungscheck
scripts/build_qt611.sh                  Prüfung + CMake-Build
cmake/Qt611QuickApp.CMakeLists.txt      Qt-6.11-CMake-Vorlage
template_cpp_qml/                       reine C++/QML-Vorlage
template_rust_cxx_qt/                   Rust+CXX-Qt+QML-Vorlage
examples/                               Slint-Beispiele
transpiled_examples/                    generierte QML/JS-Beispiele
```

## Validierung, die in dieser Umgebung lief

```text
Unit-Tests: 3/3 OK
QML/JS-Sanity-Check auf generierten Beispielen: OK
check_no_slint.sh auf dem Kit: OK
Sample-Projektmigration mit Cargo.toml/build.rs/Rust/.slint: OK
```

Der echte Qt-Build wurde hier nicht ausgeführt, weil in dieser Umgebung kein Qt 6.11,
kein qmake6 und kein nutzbarer Rust/Cargo-Projektquellbaum deines Projekts vorhanden
sind. Das Kit ist dafür vorbereitet, den Build auf deiner Maschine oder im CI auszuführen.
## v4: Python-Paket nach Qt for Python fertig migrieren

Wenn nach der `.slint`→QML-Konvertierung noch Treffer wie `notizen_py_slint`, alte Entry-Points, Python-Kommentare oder QML-Titel mit dem alten UI-Framework übrig sind, führe zusätzlich aus:

```bash
python3 scripts/finish_python_qt_migration.py .. --apply
bash scripts/check_no_slint.sh ..
```

Der Schritt macht bewusst mehr als eine Textkosmetik:

- benennt `src/notizen_py_slint` nach `src/notizen_py_qt` um,
- benennt `src/notizen_pypy_slint` nach `src/notizen_pypy_qt` um,
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

Der alte Controller wird vor dem Überschreiben unter `.qt611_no_slint_backup_v4/<timestamp>/` gesichert.
