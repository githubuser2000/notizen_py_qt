# Qt 6.11 Migration Status

Root: `/mnt/data/qt611_no_slint_migration_kit_v3`

## Summary

- Reports: 2
- Components generated: 2
- Global singletons generated: 1
- Enums converted to JS helpers: 1
- Structs converted to JS helpers: 1
- Converter warnings: 4
- Generated TODO markers: 0
- Active old-UI references: 0

## Generated outputs

- `AppState.qml`
- `GeneratedQmlSingletons.cmake`
- `Main.qml`
- `MainWindow.qml`
- `Qt611Types.js`

## Converter warnings

### /mnt/data/qt611_no_slint_migration_kit_v3/examples/main_window.slint

- line 13: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `text <=> root.title-text`

### /mnt/data/qt611_no_slint_migration_kit_v3/examples/advanced_app.slint

- line 23: Two-way binding converted to QML binding plus reverse change handler; check for binding loops — `text <=> root.title-text`
- line 27: Slint for-loop converted to Repeater; check model roles and delegate sizing — `for row in rows: CheckBox`
- line 28: Slint animate block converted to QML Behavior/NumberAnimation; easing may need review — `animate opacity`

## v4 continuation

The previous run showed that UI files had been converted, but Python packaging and controller code still contained old UI-framework references. v4 adds `scripts/finish_python_qt_migration.py` to finish that layer.

Recommended sequence on the real repository:

```bash
python3 scripts/finish_python_qt_migration.py .. --apply
bash scripts/check_no_slint.sh ..
python3 scripts/qml_sanity_check.py ..
python3 scripts/analyze_transpilation.py .. --write
bash scripts/build_python_qt.sh ..
```

The script writes `QT611_PYTHON_QT_MIGRATION_ACTIONS.md` and backs up overwritten files under `.qt611_no_slint_backup_v4/<timestamp>/`.
