# Notizen Python/Qt Port

Dies ist die Weitertranspilierung des alten VB.NET/WinForms-Projekts **Notizen.NET** nach Python/Qt.

Aktueller Stand dieses Archivs: **0.10.11**.

## Start

Direkt aus dem entpackten Ordner, ohne `python -m`:

```bash
./Notizen\ starten.sh
```

oder technisch gleichwertig:

```bash
./notizen-starten.sh
```

Diese Startdatei setzt den Quellordner automatisch in `PYTHONPATH`, startet standardmäßig mit `--show --reset-window --no-tray` und bereinigt problematische Qt-Anzeigevariablen aus der Shell. Damit GNOME dich weder durch ein unsichtbares Trayicon, alte Offscreen-/Minimized-Fensterpositionen noch durch ein Terminal-`QT_QPA_PLATFORM=xcb/offscreen/minimal` aussperrt. Eine `.alx`-Datei kann als Argument übergeben werden:

```bash
./Notizen\ starten.sh /pfad/zur/datei.alx
```

Für einen GNOME-/Linux-Anwendungsstarter im Menü:

```bash
./scripts/install_linux_launcher.sh
```

Für einen zusätzlichen Desktop-/Schreibtisch-Starter:

```bash
./scripts/install_linux_launcher.sh --desktop
```

PySide6 ist die bevorzugte Qt-Bindung. PyQt6 wird vom Kompatibilitätslayer ebenfalls akzeptiert, falls PyQt6 installiert oder lokal bevorzugt wird. Falls Qt für Python fehlt:

```bash
python3 -m pip install --user "PySide6>=6.6,<7"
```

Optional für alte verschlüsselte ALX-Dateien:

```bash
python3 -m pip install --user pycryptodome
```

Direkter Modulstart aus dem entpackten Projektordner funktioniert jetzt ebenfalls ohne Installation, weil ein kleiner Root-Shim auf `src/notizen_py_qt` verweist:

```bash
python3 -m notizen_py_qt --no-tray --show --reset-window
```

Eine Installation als Python-Paket funktioniert weiterhin:

```bash
python -m pip install -e ".[crypto]"
notizen-py-qt /pfad/zur/datei.alx
```

## Änderungen in 0.10.11

- Der GNOME-Startunterschied zwischen Menü und Shell wurde gezielt behoben: Vor dem Import von PySide6/PyQt6 normalisiert der Port jetzt die Qt-Anzeigeumgebung. Bei sichtbarem Start unter GNOME/Wayland wird ein aus der Shell geerbtes `QT_QPA_PLATFORM=xcb`, `offscreen`, `minimal` usw. auf `wayland;xcb` gesetzt.
- Ein aus der Shell geerbtes `QT_QPA_PLATFORMTHEME=gtk2/gtk3` wird für den sichtbaren GNOME/Wayland-Start entfernt, damit die bekannten `Gtk-WARNING: cannot open display: :1`-Fehler nicht mehr den Startpfad blockieren.
- Die Startdateien setzen jetzt zusätzlich `NOTIZEN_FORCE_VISIBLE=1`, `NOTIZEN_RESET_WINDOW=1` und `NOTIZEN_STARTUP_LOG`, schreiben bei jedem Start die relevante Display-Umgebung in `~/.local/state/notizen-py-qt/startup.log` und duplizieren `--show --reset-window --no-tray` nicht mehr in den Argumenten.
- Direkter Modulstart `python3 -m notizen_py_qt --no-tray --show` aus dem entpackten Projektordner nutzt jetzt ebenfalls die lokale `src`-Version und dieselbe frühe Display-Normalisierung wie die Startdateien. Wer die Shell-Qt-Variablen absichtlich behalten will, kann `NOTIZEN_KEEP_QT_ENV=1` setzen.
- Neuer testbarer Kern: `display_env.py` mit `normalize_qt_display_environment(...)`, `visible_start_requested(...)` und `DisplayEnvironmentDecision`.

## Änderungen in 0.10.10

- GNOME-Sichtbarkeitsfix verschärft: Die Startdateien erzwingen jetzt zusätzlich `--reset-window`. Gespeicherte Fensterpositionen/-größen werden beim Direktstart verworfen und auf den aktuellen Arbeitsbereich gesetzt.
- Die alte Notizen.NET-Config-Regel aus `xml_kram.on_load()` wurde genauer portiert: Ein gespeicherter `windowstate="Minimized"` wird nur berücksichtigt, wenn die alte Hauptfensterposition überhaupt restorable ist. Die alte Standardconfig `x=0`, `y=0`, `windowstate=minimized` startet dadurch nicht mehr unsichtbar.
- Alte/offscreen Fensterkoordinaten werden jetzt vollständig geklemmt: negative X/Y-Werte, ehemalige Zweitmonitor-Positionen und zu große Fenstergrößen landen wieder sichtbar im aktuellen Screen.
- Beim GNOME-/Menüstart schreibt der Starter ein Diagnoseprotokoll nach `~/.local/state/notizen-py-qt/startup.log`, wenn kein Terminal vorhanden ist. Zusätzlich gibt es `./notizen-diagnose.sh`.
- Neue Qt-unabhängige Sichtbarkeitshelfer: `sanitize_legacy_window_geometry(...)`, `legacy_window_state_is_restorable(...)`, `should_start_minimized(...)` und `env_requests_window_reset(...)`.

## Änderungen in 0.10.9

- Alte WinForms-RichTextBox-Bitmapbilder werden besser erhalten: RTF-`\pict\dibitmap`/`\pict\wbitmap`-Gruppen werden als BMP-Daten erkannt, in HTML-`img`-Data-URIs übernommen und beim kombinierten RTF-Export wieder als `\dibitmap0` geschrieben.
- Damit gehen BMP-/DIB-Bilder aus alten Notizen.NET-Dateien bei „Teilbaum zusammenfassen“, „Ganzen Baum zusammenfassen“ und HTML-/RTF-Brücken nicht mehr als `[Bild]` oder leere Stelle verloren.
- HTML-`img`-Quellen mit `image/bmp` sowie lokale `.bmp`-Dateien können jetzt wieder in RTF übernommen werden.
- Baum-Doppelklick folgt jetzt `BaumTyp_NodeMouseDoubleClick`: Ein Doppelklick auf einen Knoten startet direkt die Titelbearbeitung, wie im alten WinForms-TreeView.
- Neue Qt-unabhängige RTF-Helfer: `dib_to_bmp_bytes(...)` und `bmp_to_dib_bytes(...)`.

## Änderungen in 0.10.8

- Baum-Drag-and-drop folgt jetzt dem alten `Baum_MouseUp`-Prinzip: Ein gezogener Nicht-Wurzelknoten wird als Geschwister **vor** dem Zielknoten eingefügt, nicht als Kind darunter. Drops auf die Wurzel, auf sich selbst oder in eigene Nachfahren werden wie im WinForms-Original blockiert.
- Neue Qt-unabhängige Helfer: `legacy_can_move_before_target(...)` und `legacy_move_before_target(...)`. Die sichtbare `QTreeWidget`-Oberfläche nutzt diese Regel jetzt über `LegacyTreeWidget`.
- Der Bullet-Button folgt `ToolStrip_dot_Click`: Es wird immer ein neuer Absatz mit `•   ` eingefügt. Der Editorinhalt wird danach sofort zurück ins Modell synchronisiert.
- Alte Startargumente prüfen lokale `.alx`-Ziele jetzt wie `ApplicationEvents.vb`: Fehlende lokale Dateien werden verworfen und gemeldet, `ftp://`-Ziele bleiben unverändert zulässig.
- Neue Helfer: `legacy_clipboard_bullet_text(...)`, `qt_bullet_insert_text(...)` und `validate_legacy_startup_target(...)`.

## Änderungen in 0.10.7

- „Neu daneben“/Enter folgt jetzt genauer `Notizen.vb`/`neu_neben_knoten`: Bei einem Nicht-Wurzelknoten wird der neue Geschwisterknoten ans Ende der Elternebene angehängt, statt direkt hinter dem markierten Knoten eingefügt zu werden.
- Neue Qt-unabhängige Helfer: `legacy_new_next_parent(...)` und `legacy_new_next_node(...)`.
- Die Zufallsfarbe neuer Desktop-Notizen folgt jetzt exakt der alten `get_lightcolor()`-Reichweite: `Random.Next(0, 14)` wählte nur die Farben 0 bis 13; Magenta und der LightGray-Fallback bleiben dokumentiert, werden aber nicht automatisch zufällig gewählt.

## Änderungen in 0.10.6

- Die Löschlogik des Baums wurde näher an `Baum.element_loeschen` portiert: Nach dem Löschen wird nicht pauschal der Elternknoten markiert, sondern wie im alten WinForms-TreeView der vorher sichtbare Knoten (`PrevVisibleNode`).
- Desktop-Notizen im gelöschten oder ausgeschnittenen Teilbaum werden jetzt rekursiv geschlossen wie in `Baum.mach_haft_weg`, statt nur die Desktop-Notiz des obersten Knotens zu entfernen.
- Autosave folgt jetzt genauer `Autosavetimer_Tick`: Es wird nur automatisch gespeichert, wenn ein Baum existiert, Änderungen vorliegen, eine Datei zugeordnet ist und diese Datei auf dem Datenträger noch existiert.
- Neue Qt-unabhängige Helfer: `legacy_visible_walk`, `legacy_previous_visible_node`, `legacy_delete_fallback_node` und `legacy_autosave_should_save`.

## Änderungen in 0.10.5

- Der Suchdialog wurde näher an `suche.vb`/`suchergebnisse.vb` gebracht: Neben „Suchen / Weiter“ gibt es jetzt eine sichtbare Ergebnisliste mit Knotenpfad, Trefferposition und kurzem Kontext.
- Treffer können über die Liste direkt geöffnet werden; „Zurück“ und „Suchen / Weiter“ schalten zyklisch durch dieselbe Trefferliste wie das alte WinForms-Fenster.
- „Ganze Wörter“ nutzt jetzt die alte Notizen.NET-Regel: Nur Leerzeichen sowie CR/LF trennen Wörter. Satzzeichen und Tabs bleiben Teil des Wort-Tokens, statt wie moderne Regex-Wortgrenzen behandelt zu werden.
- Die neue Qt-unabhängige Suchansicht liegt in `search_results.py` und ist mit Regressionstests abgesichert.

## Enthalten

- ALX-Dateiformat mit GZip, UTF-16-XML und Legacy-DES-Passwortmodus.
- Baumansicht, Editor, Knotenoperationen, WinForms-nahe Drag-and-drop-Regel, Suche, Export und Notizen.NET-kompatible Sicherheitskopien.
- WinForms-nahe Hauptansicht mit sichtbarem Baumfeld `txt1` über dem Baum, Titel-Textfeld `txt2` über dem Editor und dauerhaft sichtbarem RichText-Editor `Inhalt`.
- RTF-zu-HTML-Bridge für den Qt-Editor mit Fett/Kursiv/Unterstrichen/Durchgestrichen, Schriftgröße, Schriftfamilie, Textfarbe, Markierung und Unicode.
- RTF-Bild-Roundtrip für übliche WinForms/Qt-`\pict`-Bilder mit PNG/JPEG-Hexdaten und alte RichTextBox-Bitmapbilder (`\dibitmap`/BMP) sowie HTML-`img`-Data-URIs; kombinierte Teilbaum-/Gesamtbaum-RTF-Exporte und Zusammenfassungsnotizen behalten eingebettete Bilder jetzt ebenfalls.
- Editor-Kontextfunktionen aus Notizen.NET: Text löschen, Bild einfügen, Datum einfügen, Suche und Zwischenablageaktionen.
- Teilbaum-Export nach RTF/TXT mit alter Notizen.NET-Nummerierung sowie „Teilbaum zusammenfassen“ und „Ganzen Baum zusammenfassen“ als neue Notiz.
- Fokusabhängiges Ausschneiden/Kopieren/Einfügen/Löschen wie im alten WinForms-Programm.
- Desktop-Notizen mit Kontextmenü, Hintergrundfarbe, Transparenz, Ausblenden/Schließen und Doppelklick zurück zum Hauptfenster; neue Desktop-Notizen starten wie im WinForms-Kontextmenü an der Mausposition mit 200×200 px und 85 % Deckkraft.
- Das Desktop-Notiz-Transparenzmenü nutzt jetzt die alte WinForms-Semantik aus `desknote_kontext_opacy.vb`: „90 %“ bedeutet 90 % Transparenz und wird intern zu 10 % Qt-Deckkraft.
- System-Tray, Wecker per `Ctrl+Space`, Grundeinstellungen und zuletzt geöffnete Dateien; Recent-Einträge prüfen fehlende Dateien und fragen bei ungespeicherten Änderungen nach.
- FTP-Öffnen/Speichern wie im alten `ftpkram.vb`.
- Importiertes Notizen-Icon als Paketressource plus `.qrc`.
- Importierte Sprachdateien aus `languages.vb` für Deutsch, English, Chinese, français, spanish und russian; Menü-/Aktionsbeschriftungen werden zur Laufzeit umgeschaltet.
- Legacy-Startparameter aus `ApplicationEvents.vb`: `/min`, `-min`, `min`, Hilfe-Flags, lokale `.alx`-Dateien mit Existenzprüfung und direkte `ftp://...alx`-Startziele.
- WinForms-nahe Knoten-Einfügelogik: Kopierte/ausgeschnittene Teilbäume werden wie in `paste_anything(False)` vor dem markierten Geschwisterknoten bzw. als erster Root-Unterknoten eingefügt; „Neu daneben“/Enter hängt wie `neu_neben_knoten` ans Ende der Elternebene; Drag-and-drop verschiebt wie `Baum_MouseUp` vor den Ziel-Geschwisterknoten; Baum-Doppelklick startet wie `BaumTyp_NodeMouseDoubleClick` die Titelbearbeitung.
- Erweiterte Export-Parität: aktueller Teilbaum oder ganzer Baum als RTF, UTF-8-TXT, ANSI-TXT oder Unicode-TXT sowie Roh-RTF des aktuellen Knotens.
- Desktop-Notizen synchronisieren laufende Editoränderungen jetzt live und erhalten bei fehlender Alt-Farbe eine zufällige helle Legacy-Farbe aus der tatsächlich erreichbaren `get_lightcolor()`-Palette.
- Knoten-Kopieren/Ausschneiden nutzt zusätzlich zur internen Ablage ein eigenes systemweites XML-MIME-Format, damit Teilbäume zwischen zwei laufenden Programmfenstern eingefügt werden können.
- Der Wecker aus `wecker.vb` unterstützt jetzt einmalige, tägliche, wöchentliche, monatliche und jährliche Wiederholungen mit Intervall und Wochentagen.
- Drucken über QtPrintSupport für aktuelle Notiz, aktuellen Teilbaum oder ganzen Baum ist angebunden.
- Legacy-Tastaturvarianten `Shift+Insert` und `Shift+Delete` sind ergänzt.
- TXT- und RTF-Import in die aktuelle Notiz sind angebunden.
- HTML-Export für aktuellen Teilbaum und ganzen Baum erzeugt eine eigenständige UTF-8-HTML-Datei mit Nummerierung und eingebetteten Bildern.
- Statistikdialog zählt Knoten, Blätter, Tiefe, Desktop-Notizen, Textmengen und eingebettete Bilder für aktuellen Teilbaum und Gesamtbaum.
- Knoten können per Aktion nach oben/unten verschoben werden; Auf-/Zu, Alle auf und Alle zu sind wieder als sichtbare Befehle vorhanden.
- Alte `notizen.config.xml`-Dateien können aus der Oberfläche importiert werden; Scrollleisten können wie im WinForms-Menü zyklisch umgeschaltet werden.
- Suche, Schnell-Suche und alle Exportpfade synchronisieren den sichtbaren Editorinhalt vor der Auswertung zurück ins Modell.
- Der Suchdialog zeigt Treffer jetzt als alte `suchergebnisse`-nahe Liste mit Knotenpfad, Vorschautext, Zurück/Weiter und direkter Trefferaktivierung.
- Baum-Löschen folgt jetzt der alten `PrevVisibleNode`-Auswahl aus `Baum.element_loeschen`; Desktop-Notizen unter gelöschten oder verschobenen Teilbäumen werden rekursiv geschlossen.
- Autosave folgt der alten `Autosavetimer_Tick`-Schutzbedingung und erzeugt keine fehlende Datei still neu, wenn die gespeicherte `.alx` zwischenzeitlich entfernt wurde.
- Sicherheitskopien folgen der alten `saftycopies`-Logik aus Notizen.NET: Backup-Ordner neben der `.alx`-Datei, Dateinamen `Name-YYYY-MM-DD-HH-MM-SS-ms.alx`, konfigurierbare Rotation und neue Aktionen „Jetzt Sicherung erstellen“/„Sicherung öffnen“.
- Legacy-Config-Parität weitergeführt: `open/once-opened`, alte `tool-stripes`-Positionen und der WinForms-Autosave-Schutz aus `einstellungen.vb` werden übernommen und beim Speichern erhalten; frische Configs starten wie Notizen.NET mit 60 Sekunden Autosave.
- Die alte Datei-Startlogik aus `Datei.vb` ist präzisiert: Standardname `unbenannt.alx`, Standardordner `Documents/Notizen` und Windows-Backslash-Pfade aus alten Configs werden auch auf Linux/macOS korrekt in Verzeichnis und Dateiname getrennt.
- Autostart-Einstellung aus `xml_kram.setshortcut` ist als Windows-Startup-`.cmd`-Adapter portiert: jüngste zuletzt geöffnete Datei wird bevorzugt, `-min` wird bei minimiertem Autostart vorangestellt.
- Fensterzustände aus `xml_kram.vb` werden robuster normalisiert; gespeicherte `minimized`-/`maximized`-Werte werden beim Start ausgewertet, und offensichtlich außerhalb des Arbeitsbereichs liegende Hauptfensterpositionen werden abgefangen.
- RTF-Tabellenzellen aus alten RichTextBox-Inhalten werden in Suche, Statistik und Exporten nicht mehr zusammengeschoben, sondern als Tabulatoren und Zeilenumbrüche erhalten.
- ZIP-Verzeichnisrechte und Skript-Ausführungsrechte werden beim Paketieren korrekt gesetzt: Verzeichnisse `755`, Shell-/Python-Build-Skripte `755`, Desktop-Starter `755`, normale Dateien `644`.
- Neue Startdateien für Linux/GNOME: `Notizen starten.sh`, `notizen-starten.sh`, `notizen-diagnose.sh`, `Notizen PyQt.desktop` und `scripts/install_linux_launcher.sh`. Die Direktstarter setzen automatisch `PYTHONPATH`, setzen die Fensterposition zurück und starten sichtbar ohne Tray; das Installationsskript registriert zusätzlich `*.alx` als `application/x-notizen-alx` und setzt den Notizen-Starter als Standard-App für diesen Dateityp.
- GNOME-Tray-Schutz verschärft: GNOME startet standardmäßig sichtbar, auch wenn eine Tray-/AppIndicator-Erweiterung erkannt wird. Ein versteckter Tray-Start ist nur noch bewusst per `--force-tray-start` beziehungsweise mit `--allow-tray` im Startskript sinnvoll. `--no-tray` deaktiviert das Trayicon vollständig.

## GNOME und Trayicons

GNOME zeigt klassische Trayicons/AppIndicators nicht zuverlässig. Dieser Port startet deshalb unter GNOME ab 0.10.3 grundsätzlich mit sichtbarem Hauptfenster, solange der Tray-Start nicht ausdrücklich erzwungen wird. Das gilt auch dann, wenn eine AppIndicator-Erweiterung erkannt wird.

Sicherster GNOME-Start aus dem entpackten Ordner:

```bash
./Notizen\ starten.sh
```

Der Starter hängt automatisch `--show --reset-window --no-tray` an. Dadurch wird ein gespeicherter minimierter Fensterzustand ignoriert und das Trayicon deaktiviert. Wer das Tray bewusst wieder nutzen will:

```bash
./notizen-starten.sh --allow-tray --force-tray-start --minimized
```

Für sichtbare Trayicons unter GNOME installiere und aktiviere eine AppIndicator/KStatusNotifier-Erweiterung, zum Beispiel `appindicatorsupport@rgcjonas.gmail.com`. Trotzdem bleibt der Standard dieses Ports sichtbar-first, weil die reale Tray-Erreichbarkeit je nach GNOME-Sitzung und Erweiterung variieren kann.

Historische Qt-/QML-Migrationsskripte aus früheren Zwischenschritten liegen nicht mehr im aktiven Projektpfad, sondern unter `legacy_build_metadata/`.

Details stehen in [`TRANSPILE_NET_TO_PYQT_REPORT.md`](TRANSPILE_NET_TO_PYQT_REPORT.md). Validierung steht in [`VALIDATION_NET_PORT.md`](VALIDATION_NET_PORT.md).
