# Transpilationsbericht Notizen.NET → Python/Qt 0.10.7

## Ausgangspunkt

Diese Runde baut auf dem geprüften Stand 0.10.6 auf. Der Projekt-/Chat-Kontext wurde weitergeführt: Ziel bleibt eine semantische Portierung des alten VB.NET/WinForms-Projekts nach Python/Qt, ohne Rückfall auf die früheren Slint-/QML-Zwischenstände. Nach der Lösch-/Autosave-Parität aus 0.10.6 lag der nächste sinnvolle Block bei kleinen, aber gut belegbaren WinForms-Verhaltensdetails aus `Notizen.vb`.

## Umgesetzte Änderungen in 0.10.7

### „Neu daneben“ wie `neu_neben_knoten`

Im bisherigen Qt-Port wurde **Neu daneben** als modernes „nach dem aktuell markierten Knoten einfügen“ umgesetzt. Das alte Notizen.NET verhielt sich anders: `neu_neben_knoten` wählte bei Nicht-Wurzelknoten zuerst den Elternknoten aus und rief danach `Baum.element_dazu` auf. Da `element_dazu` immer ein Kind am Ende des ausgewählten Knotens anhängt, landet der neue Geschwisterknoten im Original am Ende der Elternebene.

Neu in `models.py`:

- `legacy_new_next_parent(...)`,
- `legacy_new_next_node(...)`.

`MainWindow.add_sibling_node(...)` nutzt diese Helfer jetzt. Enter beziehungsweise **Neu daneben** hängt damit wie im alten WinForms-Programm ans Ende der aktuellen Geschwisterebene. Ist die Wurzel markiert, wird der neue Knoten wie früher als letztes Kind der Wurzel angelegt.

### Zufallsfarbe neuer Desktop-Notizen präzisiert

`get_lightcolor()` im VB-Code enthält Fälle für `0` bis `14` sowie einen `Else`-Fallback. Die Zufallszahl wird jedoch mit `Random.Next(0, 14)` erzeugt; in .NET bedeutet das Werte `0` bis `13`. Dadurch waren `Case 14` und `Else` für automatisch erzeugte Desktop-Notizen praktisch nicht erreichbar.

`legacy_colors.py` dokumentiert jetzt weiterhin die vollständige alte Fallliste, nutzt für automatische Zufallsfarben aber nur die tatsächlich erreichbaren 14 Farben:

- `LEGACY_RANDOM_LIGHT_COLOR_COUNT`,
- `LEGACY_RANDOM_LIGHT_COLOR_ARGB`,
- aktualisiertes `legacy_light_color_argb(...)`.

Damit werden neue Desktop-Notiz-Hintergründe nicht mehr zufällig Magenta oder LightGray, wenn das alte Programm diese Fälle über seine Zufallslogik nicht erreichen konnte.


### ZIP-Rechte für aktive Starter und Legacy-Metadaten geschärft

Die Verpackungslogik bleibt auf Unix-Rechte ausgerichtet, unterscheidet jetzt aber präziser zwischen aktiven Start-/Hilfsskripten und historisch archivierten Migrationsskripten. Direkt unter `scripts/` liegende aktive Python-Helfer bleiben ausführbar; alte `legacy_build_metadata/.../scripts/*.py`-Dateien werden als normale Archivdaten mit `644` gepackt. Dadurch bleiben die Startdateien nutzbar, ohne alten Metadaten unnötige Ausführungsrechte zu geben.

### Öffentliche API ergänzt

Die neuen Baum-Helfer werden aus `notizen_py_qt.__init__` exportiert, damit die Legacy-Einfügeposition ohne Qt testbar bleibt und für spätere Werkzeuge nutzbar ist.

## Dateien mit relevanten Änderungen

- `src/notizen_py_qt/models.py`
- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/legacy_colors.py`
- `src/notizen_py_qt/__init__.py`
- `tests/test_legacy_new_next_colors_107.py`
- `tests/test_tray_permissions_102.py`
- `scripts/package_zip.py`
- `README.md`
- `docs/MAPPING.md`
- `docs/PROJECT_CONTEXT_IMPORTED.md`
- `pyproject.toml`
- `TRANSPILE_NET_TO_PYQT_REPORT.md`
- `VALIDATION_NET_PORT.md`

Zusätzlich wurden die 0.10.6-Berichte archiviert:

- `TRANSPILE_NET_TO_PYQT_REPORT_0.10.6.md`
- `VALIDATION_NET_PORT_0.10.6.md`

## Bewusst nicht geändert

Die GNOME-sicheren Startdateien und der sichtbare Start ohne Tray bleiben unverändert. Die Änderung betrifft Baum-Einfügeparität und Desktop-Notiz-Farblogik. Das alte Drag-and-drop-Verhalten aus `Baum_MouseUp` bleibt ein separater Folgeblock, weil Qt-Drag-and-drop visuell geprüft werden sollte.
