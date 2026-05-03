# Transpilationsbericht Notizen.NET → Python/Qt 0.10.8

## Ausgangspunkt

Diese Runde baut auf dem geprüften Stand 0.10.7 auf. Der aktive Pfad bleibt Python/Qt; alte Slint-/QML-Migrationsdaten bleiben nur archivierte Metadaten. Nach der 0.10.7-Korrektur für `neu_neben_knoten` und `get_lightcolor()` lag der nächste sinnvolle Block bei weiteren kleinen, aber konkreten WinForms-Verhaltensregeln aus `Baum.vb`, `Notizen.vb` und `ApplicationEvents.vb`.

## Umgesetzte Änderungen in 0.10.8

### Drag-and-drop wie `Baum_MouseUp`

Das alte TreeView-Drag-and-drop verschob einen Knoten nicht als Kind des Zielknotens. `Baum_MouseUp` fügte den gezogenen Teilbaum als Geschwister direkt vor dem anvisierten Zielknoten ein und entfernte danach den ursprünglichen Knoten. Drops auf die Wurzel, auf den Quellknoten selbst oder in einen eigenen Nachfahren wurden verhindert.

Neu in `models.py`:

- `legacy_can_move_before_target(...)`,
- `legacy_move_before_target(...)`.

Neu in `app.py`:

- `LegacyTreeWidget`, eine `QTreeWidget`-Ableitung mit genau dieser Drop-Regel.

Der Port bewegt im Modell das bestehende `NoteNode`-Objekt statt Clone+Remove zu verwenden. Sichtbare Reihenfolge und Blockierregeln entsprechen dem alten Programm, während Referenzen für Desktop-Notizen und Tests stabil bleiben.

### Bullet-Button wie `ToolStrip_dot_Click`

Der bisherige Port fügte `•   ` nur bedingt mit führendem Zeilenumbruch ein. Das alte `ToolStrip_dot_Click` kopierte dagegen immer `Chr(13) + ChrW(8226) + "   "` in die Zwischenablage und paste-te diesen Text in die RichTextBox.

Neu in `editor_legacy.py`:

- `legacy_clipboard_bullet_text(...)`,
- `qt_bullet_insert_text(...)`.

`MainWindow.insert_bullet(...)` nutzt diese Qt-normalisierte Legacy-Sequenz jetzt immer und speichert den sichtbaren Editorinhalt danach sofort zurück ins Modell.

### Startdateien aus `ApplicationEvents.vb` abgesichert

Die alte Anwendung akzeptierte `.alx`-Startargumente, verwarf lokale Dateien aber wieder, wenn sie nicht existierten. FTP-Ziele waren davon ausgenommen.

Neu in `startup.py`:

- `StartupTargetValidation`,
- `validate_legacy_startup_target(...)`.

`main(...)` prüft die alten Startargumente jetzt vor dem Öffnen. Fehlende lokale `.alx`-Ziele erzeugen keinen verwirrenden Ladeversuch mehr; `ftp://...alx` bleibt zulässig.

### Öffentliche API ergänzt

Die neuen Baum-, Bullet- und Startup-Helfer werden aus `notizen_py_qt.__init__` exportiert, damit sie Qt-unabhängig testbar und für Folgewerkzeuge nutzbar sind.

## Dateien mit relevanten Änderungen

- `src/notizen_py_qt/models.py`
- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/startup.py`
- `src/notizen_py_qt/editor_legacy.py`
- `src/notizen_py_qt/__init__.py`
- `tests/test_legacy_drag_startup_bullet_108.py`
- `README.md`
- `docs/MAPPING.md`
- `docs/PROJECT_CONTEXT_IMPORTED.md`
- `pyproject.toml`
- `TRANSPILE_NET_TO_PYQT_REPORT.md`
- `VALIDATION_NET_PORT.md`

Zusätzlich wurden die 0.10.7-Berichte archiviert:

- `TRANSPILE_NET_TO_PYQT_REPORT_0.10.7.md`
- `VALIDATION_NET_PORT_0.10.7.md`

## Bewusst nicht geändert

Die GNOME-sicheren Startdateien bleiben sichtbar-first mit `--show --no-tray`. Die Autostart-Voreinstellungen werden weiterhin nicht aggressiver gemacht, damit der Port keine unerwarteten Autostart-Einträge erzeugt.
