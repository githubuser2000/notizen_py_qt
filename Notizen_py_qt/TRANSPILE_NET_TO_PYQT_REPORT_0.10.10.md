# Weitertranspilierung Notizen.NET → Python/Qt 0.10.10

## Ausgangspunkt

Weitergeführt wurde der Stand 0.10.9. Der konkrete Nutzerfehler war: Unter GNOME erscheint nach dem Start weiterhin kein sichtbares Hauptfenster. Die bisherige Tray-Abschaltung allein reicht dafür nicht, weil auch gespeicherte Legacy-Fensterzustände und Offscreen-Koordinaten ein Fenster faktisch unsichtbar machen können.

## Umgesetzte Änderungen in 0.10.10

### Sichtbarer GNOME-Start

- Die Startdatei `notizen-starten.sh` erzwingt jetzt neben `--show` und `--no-tray` auch `--reset-window`.
- `Notizen starten.sh`, `Notizen PyQt.desktop` und der installierte Linux-Starter nutzen denselben sichtbaren Startpfad.
- Beim Start aus einem Menü ohne Terminal schreibt `notizen-starten.sh` ein Protokoll nach `~/.local/state/notizen-py-qt/startup.log`.
- Neu: `notizen-diagnose.sh` erzeugt zusätzlich `~/.local/state/notizen-py-qt/diagnose.log` mit Umgebung, Python-Version und Startausgabe.

### Legacy-Fensterzustand genauer portiert

Das alte `xml_kram.on_load()` setzte `Location`, `Size` und `WindowState` nur, wenn sowohl X als auch Y ungleich 0 waren. Die alte Standardconfig schreibt jedoch `x="0"`, `y="0"` und `windowstate="minimized"`. Der PyQt-Port behandelte diesen minimierten Zustand bisher zu stark. 0.10.10 übernimmt die alte Bedingung:

- `legacy_window_state_is_restorable(...)` entscheidet, ob gespeicherter Fensterzustand angewendet werden darf.
- `should_start_minimized(...)` ignoriert gespeichertes `Minimized`, wenn die Legacy-Position nicht restorable ist.
- Explizite Startwünsche wie `--minimized` oder altes `-min` bleiben erhalten.

### Fensterpositionen auf aktuellen Arbeitsbereich klemmen

- Neu: `sanitize_legacy_window_geometry(...)`.
- Negative Koordinaten, ehemalige Zweitmonitor-Positionen und zu große Fenstergrößen werden sichtbar in den aktuellen Arbeitsbereich zurückgeholt.
- `--reset-window` verwirft alte Position/Größe bewusst und setzt eine normale sichtbare Startgeometrie.
- `MainWindow.ensure_main_window_visible(...)` zeigt das Fenster normal an, hebt es an und wiederholt die Sichtbarkeitsaktion kurz nach dem Start über Qt-Timer.

### API / Paket

- Version auf `0.10.10` gesetzt.
- Neues Modul: `src/notizen_py_qt/window_visibility.py`.
- Neue Exports aus `notizen_py_qt.__init__`:
  - `VisibleWindowGeometry`
  - `sanitize_legacy_window_geometry`
  - `legacy_window_state_is_restorable`
  - `should_start_minimized`
  - `env_requests_window_reset`

## Neue Tests

- `tests/test_gnome_visible_start_1010.py`

Die Tests prüfen die Legacy-0/0-Minimized-Regel, die Geometrie-Klemmung, die neuen Starterargumente, Diagnoseprotokolle und die Shell-Syntax.

## Weiterhin offen

Eine echte visuelle GNOME-Prüfung ist in dieser Umgebung nicht möglich, weil keine Qt-Bindung und keine GNOME-Sitzung verfügbar sind. Der Codepfad ist aber so geändert, dass der normale Starter nicht mehr vom alten minimierten Configzustand oder Offscreen-Koordinaten abhängig ist.
