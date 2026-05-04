# Weitertranspilierung Notizen.NET → Python/Qt 0.10.15

## Schwerpunkt

Diese Runde setzt die große Rest-Transpilierungsuntersuchung fort, aber priorisiert ausdrücklich zuerst die Desktop-Notizen. Der sichtbare GNOME-Startpfad aus 0.10.13/0.10.14 wurde bewusst nicht erneut umgebaut: Startdateien bleiben sichtbar-first mit `--show --reset-window --no-tray`, `QT_QPA_PLATFORM=wayland;xcb` bleibt erhalten und `DISPLAY` wird nicht pauschal gelöscht.

## Aus Notizen.NET weiter portiert

### `desknote.vb`

Die alte WinForms-Desktop-Notiz war kein normales Editorfenster. Sie war ein rahmenloses Tool-Fenster mit einer kompakten RichTextBox-Fläche und einem nur bei Hover/Fokus sichtbaren Rand-/Titelbereich. 0.10.15 portiert diese Regeln deutlich genauer:

- `FormBorderStyle.None` → rahmenloses Qt-Tool-Fenster.
- `ShowInTaskbar=False`-Entsprechung über Tool-Fenster-Flags.
- Alte `show2`-Startgeometrie: gespeicherte Vollgeometrie wird beim Anzeigen zu `x+12`, `y+32`, `width-26`, `height-48` kontrahiert.
- Alte Hover-Geometrie: aktive Notiz expandiert um `x-12`, `y-32`, `width+26`, `height+48`.
- Alte RichTextBox-Positionen: im Ruhezustand `(0,0,width,height)`, im aktiven Zustand `(12,32,width-26,height-48)`.
- Desktop-Editor ist read-only und nutzt keine normalen Textinteraktionen; Doppelklick oder Tastendruck öffnet die Notiz im Hauptfenster.
- Titelstreifen-Zonen: links ausblenden, rechts Desktop-Notiz entfernen, Mitte verschieben.
- Untere rechte Hotzone skaliert die Notiz wie im alten `desknote_MouseMove`.
- Titelklick toggelt die alte helle/dunkle Titelfarbe.
- MouseLeave-/Collapse-Verhalten nutzt die alte 4000-ms-Timer-Idee und 3-Pixel-Toleranz.
- Neue Notizen werden weiter mit alter Standardgröße, alter Opacity-Logik und alter Zufallsfarbe erzeugt.

### `desknote_kontext.vb` und `desknote_kontext_opacy.vb`

Das Kontextmenü bleibt funktional, aber näher an den alten Begriffen: Hintergrundfarbe, Transparenz, Ausblenden und Desktop-Notiz schließen. Die alte Transparenzsemantik bleibt erhalten: alte Menüwerte sind Transparenzwerte, intern wird daraus Qt-Opacity.

## Neue Legacy-API

`desktop_note_legacy.py` enthält jetzt Qt-unabhängige Helfer für die alten WinForms-Regeln:

- `LegacyDeskNoteMouseAction`
- `LegacyDeskNoteCursor`
- `legacy_desknote_show2_geometry(...)`
- `legacy_desknote_editor_rect(...)`
- `legacy_desknote_label_geometry(...)`
- `legacy_desknote_mouse_down_action(...)`
- `legacy_desknote_mouse_move_action(...)`
- `legacy_desknote_cursor_for_move_action(...)`
- `legacy_desknote_move_geometry(...)`
- `legacy_desknote_resize_geometry(...)`
- `legacy_desknote_clamp_to_work_area(...)`
- `legacy_desknote_point_outside(...)`

Diese Funktionen sind aus `notizen_py_qt.__init__` exportiert und werden direkt getestet.

## Bewusst nicht geändert

Der GNOME-/Shell-Startpfad wurde nicht erneut experimentell verändert. Die Nutzer-Rückmeldung war, dass das Fenster zwischendurch sichtbar startete. 0.10.15 lässt diese sichtbare Startstrategie daher stehen und fokussiert auf Fachportierung.

## Noch offen

Die Desktop-Notizen sind deutlich näher am WinForms-Original, aber nicht jedes Pixel der alten GDI-/RichTextBox-Darstellung ist identisch. Offen bleiben vor allem:

- visuelle Prüfung unter echter GNOME-/Qt-Sitzung,
- vollständige Nachbildung der alten `set_clientsizes`-/Scrollbar-Autosize-Schleife,
- pixelgenaue Paint-Optik des alten Titelstreifens,
- eventuelle Sonderfälle alter RichTextBox-Scrollbars.

## Validierung

Die Validierung steht in `VALIDATION_NET_PORT.md`.
