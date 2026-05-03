# Notizen.NET → Python/Qt Mapping

Aktiver Portierungsstand: **0.10.13**. Diese Datei beschreibt die aktuelle semantische Zuordnung vom alten VB.NET/WinForms-Projekt zu den Python/Qt-Modulen. Die früheren Qt/QML-Zwischenschritte sind archiviert unter `legacy_build_metadata/` und nicht mehr Teil des aktiven Laufzeitpfads.

## Kernstruktur

| Notizen.NET-Quelle | Python/Qt-Ziel | Stand |
|---|---|---|
| `Notizen.vb`, `Notizen.Designer.vb` | `src/notizen_py_qt/app.py` | Hauptfenster, Menüs, Toolbar, Baum, Editor, Dialoge und Legacy-Aktionen sind semantisch portiert. |
| `Baum.vb`, `Baum_Kontext_.vb` | `app.py`, `models.py`, `node_clipboard.py` | Baumoperationen, Einfügen/Ausschneiden/Kopieren, Drag-and-drop-nahe Modellpflege, Doppelklick-Umbenennung, Knotenfarben, Auf-/Zu-Funktionen, `PrevVisibleNode`-Löschauswahl, alte `neu_neben_knoten`-Einfügeposition und Teilbaum-Zusammenfassung sind portiert. |
| `inhalt.vb`, `kontext_inhalt.vb`, `fontsize.vb` | `app.py`, `rtf_utils.py` | RichText-Bearbeitung, Formatierungen, Datum, Bild-Einfügen inklusive BMP/DIB-RTF-Brücke, Fokus-abhängige Zwischenablage und RTF/HTML-Brücke sind portiert. |
| `Datei.vb`, `xml_kram.vb`, `Autosavetimer_Tick` | `alx_io.py`, `settings.py`, `legacy_paths.py`, `app.py` | ALX-Laden/Speichern, UTF-16-XML, GZip, `saftycopies`-Backupordner, Backup-Rotation, Passwortmodus, alte Config-Dateien, Standardordner `Documents/Notizen`, Legacy-Dateipfad-Splitting und die alte Autosave-Schutzbedingung sind portiert. |
| `suche.vb`, `suchergebnisse.vb` | `search_logic.py`, `search_results.py`, `SearchDialog`, Schnell-Suchleiste in `app.py` | Suche in aktuellem Knoten oder Gesamtbaum ist portiert; 0.10.5 ergänzt die sichtbare Ergebnisliste und die alte Ganzwort-Tokenregel. |
| `desknote.vb`, `desknote_kontext.vb`, `desknote_kontext_opacy.vb` | `DesktopNoteWindow`, `DesktopNoteState`, `legacy_colors.py`, `desktop_note_legacy.py` | Desktop-Notizen, Farben inklusive exakt erreichbarer `get_lightcolor`-Zufallspalette, altes Transparenzmenü, Kontextmenü, Rücksprung ins Hauptfenster und WinForms-nahe Startgeometrie sind portiert. |
| `einstellungen.vb` | `settings.py`, Settings-Dialog in `app.py` | Backups, Autosave, Sprache, Scrollleisten, Desktop-Notiz-Ränder, Autostart-Felder und zuletzt geöffnete Dateien sind portiert. |
| `ftpkram.vb` | `ftp_sync.py`, FTP-Dialog in `app.py` | FTP-Öffnen/Speichern der ALX-Datei ist portiert. |
| `wecker.vb`, `wecker.Designer.vb` | `alarms.py`, Alarm-Dialog in `app.py` | Einmalige und wiederholende Wecker sind portiert; 0.10.13 ergänzt die alte Aktiviert-Checkbox, Wochentags-Checkbox-Zuordnung und Intervall-Einheiten. |
| `languages.vb`, `.resx`-Sprachdaten | `i18n.py`, dynamische Aktionsbeschriftungen in `app.py` | Die sechs alten Spracharrays sind positionsgenau aus `languages.vb`/`lang_keys` übernommen; 118 semantische Legacy-Schlüssel sind testbar und umschaltbar. |
| `ApplicationEvents.vb` | `startup.py`, `app.py` | Legacy-Startargumente wie minimierter Start und direkte Datei-/FTP-Ziele sind portiert. |
| `passwort_dialog*.vb`, `wanna_save.vb`, `wanna_restart.vb`, `AboutBox1.vb` | Qt-Dialoge in `app.py` | Passwort-, Speicher-, Einstellungs- und Info-Dialoge sind in Qt nachgebildet. |
| `Notizen.ico`, `Notizen.png` | `src/notizen_py_qt/resources/` | Programm-Icon und Ressource sind importiert. |



## In 0.10.13 weitergeführt

- Der GNOME-Startpfad wurde auf das vom Nutzer bestätigte sichtbare Verhalten zurückgestellt: `display_env.py` baut jetzt die grafische Sitzungsumgebung beziehungsweise den GNOME-Menüstart nach, statt `DISPLAY` für sichtbare Starts zu löschen.
- `apply_graphical_session_environment(...)` übernimmt `XDG_RUNTIME_DIR`, `WAYLAND_DISPLAY`, `XDG_CURRENT_DESKTOP`, `XDG_SESSION_DESKTOP` und `DISPLAY` aus der grafischen Sitzung. Falls die Shell weiterhin `DISPLAY=:1` liefert und keine Sitzungskopie verfügbar ist, wird für sichtbaren GNOME/Wayland-Start auf den sichtbar funktionierenden Menüwert `DISPLAY=:0` gewechselt.
- `notizen-starten.sh` und der direkte Modulstart verwenden wieder `QT_QPA_PLATFORM=wayland;xcb`; ein geerbtes `GDK_BACKEND=x11` wird entfernt, ohne die gesamte Anzeigeumgebung hart auf Pure-Wayland zu zwingen. Startlogs enthalten jetzt Paketversion, Paketdatei und Python-Executable.
- Die ALX-Testbasis wurde datenschutzbewusst erweitert: Eine echte alte leere `unbenannt.alx` prüft den originalen Minimalfall, während eine sanitisierte Legacy-Desktop-Notiz-Fixture Baumstruktur und Desktop-Notiz-Attribute ohne persönliche Altinhalte testet.
- `settings.py` konserviert unbekannte alte Config-XML-Zweige als `legacy_passthrough_elements`, damit noch nicht vollständig semantisch portierte Einstellungen beim Speichern nicht verschwinden.
- Die alte Vierer-Recent-Liste aus `xml_kram.vb` ist als `LEGACY_RECENT_FILE_SLOTS`, `legacy_recent_files_from_slots(...)`, `legacy_recent_slots_from_files(...)`, `legacy_remember_recent_file(...)` und `legacy_activate_recent_file(...)` testbar.
- `desktop_note_legacy.py` ergänzt die alte Desktop-Notiz-Randgeometrie, Titelstreifen-Klickzonen sowie aktive/inaktive Opacity-Regeln. Die Qt-Fenster speichern nicht mehr versehentlich die temporäre Vollsichtbarkeit als dauerhafte Transparenz.
- `i18n.py` legt die aus `languages.vb` übernommene positionsgenaue Reihenfolge über `LEGACY_LANGUAGE_KEY_ORDER` offen und stellt testbare Legacy-Übersetzungshelfer bereit. Der Info-/Hilfe-Dialog nutzt wieder `aboutinfotext`.
- `alarms.py` bildet die alten Wecker-Wochentagscheckboxen (`CheckBox15` bis `CheckBox13`) und den Aktiviert/Deaktiviert-Zustand aus `wecker.Designer.vb` ab. Der Dialog verwendet diese Legacy-Daten und plant deaktivierte Alarme nicht.

- `keyboard_legacy.py` bildet die alten `Notizen.vb/tastendruck`-Shortcuts Qt-unabhängig ab; `app.py` verwendet diese Zuordnung für globale Ctrl-Aktionen und baumbezogene Insert/Delete/Enter-Regeln.

## In 0.10.12 weitergeführt

- Die Nutzerdiagnose zeigte, dass der GNOME-Menüstart sichtbar war, während Terminalstarts mit `DISPLAY=:1`, `GDK_BACKEND=x11` und vorhandener `WAYLAND_DISPLAY=wayland-0` hängen oder unsichtbar bleiben konnten. 0.10.12 behandelte diesen Fall zunächst als harte Wayland-Bereinigung.
- `build_python_qt.sh` und `notizen-diagnose.sh` wurden entkoppelt vom dauerhaften GUI-Start: Build validiert standardmäßig ohne Smoke-GUI, Diagnose startet nur bounded/offscreen und eine sichtbare GUI nur explizit per `--launch`.

## In 0.10.11 weitergeführt

- Die Nutzerdiagnose zeigte: Der GNOME-Menüstarter öffnete sichtbar, aber Shell-Starts mit `python3 -m notizen_py_qt --no-tray --show` und den Startdateien blieben unsichtbar beziehungsweise meldeten `Gtk-WARNING: cannot open display: :1`. Das wurde als Startumgebungsproblem statt als reine Trayfrage behandelt.
- `display_env.py` normalisiert Qt-Displayvariablen vor dem Import von PySide6/PyQt6: sichtbarer GNOME/Wayland-Start bevorzugt `wayland;xcb`, entfernt unsichtbare/offscreen Backends und entfernt problematische GTK-Platform-Themes.
- `notizen-starten.sh` und `notizen-diagnose.sh` protokollieren jetzt `DISPLAY`, `WAYLAND_DISPLAY`, `QT_QPA_PLATFORM`, `QT_QPA_PLATFORMTHEME`, `PYTHONPATH` und die tatsächlich übergebenen Argumente.
- Die Startdateien erzwingen den sichtbaren Fenstermodus weiterhin, bereinigen aber doppelte Flags und lassen absichtliches Beibehalten der Shell-Qt-Umgebung über `NOTIZEN_KEEP_QT_ENV=1` zu.
- Ein Root-Shim unter `notizen_py_qt/` erlaubt `python3 -m notizen_py_qt` direkt aus dem entpackten Ordner und verhindert, dass versehentlich eine ältere installierte Version statt des lokalen `src`-Ports startet.

## In 0.10.10 weitergeführt

- `xml_kram.on_load()` / Hauptfenster-Wiederherstellung: Der PyQt-Port übernimmt jetzt die alte Bedingung, dass `windowstate` nur aus der Config angewendet wird, wenn X und Y ungleich 0 sind. Dadurch erzeugt die alte Standardconfig kein unsichtbar minimiertes GNOME-Fenster mehr.
- `Notizen.Designer.vb` / gespeicherte Fensterdaten: Position und Größe werden mit `sanitize_legacy_window_geometry(...)` auf den aktuellen Arbeitsbereich geklemmt, inklusive negativer/offscreen Koordinaten nach Monitorwechseln.
- Linux-/GNOME-Starter: `notizen-starten.sh` startet sichtbar mit `--show --reset-window --no-tray` und schreibt bei Menüstarts ein Diagnoseprotokoll. `notizen-diagnose.sh` wurde ergänzt.

## In 0.10.9 weitergeführt

- `kontext_inhalt.vb` akzeptierte Bilddateien inklusive `*.bmp`; WinForms-RichTextBox speichert solche eingefügten oder gepasteten Bitmapbilder häufig als RTF-`\pict\dibitmap`. `rtf_utils.py` erkennt diese DIB-Payloads jetzt, erzeugt daraus BMP-Dateien für HTML/Qt und schreibt sie beim Export wieder als `\dibitmap0`.
- Kombinierte RTF-Exporte, „Teilbaum zusammenfassen“ und „Ganzen Baum zusammenfassen“ behalten damit neben PNG/JPEG nun auch alte RichTextBox-Bitmapbilder. Neue reine Helfer sind `dib_to_bmp_bytes(...)` und `bmp_to_dib_bytes(...)`.
- `Baum.vb` / `BaumTyp_NodeMouseDoubleClick` ist in der Oberfläche nachgezogen: Ein Doppelklick auf einen `QTreeWidgetItem` ruft `edit_tree_item(...)` auf und startet die Titelbearbeitung wie im alten TreeView.

## In 0.10.8 weitergeführt

- `Baum.vb` / `Baum_MouseUp`: Drag-and-drop verschiebt einen Nicht-Wurzelknoten als Geschwister **vor** den anvisierten Zielknoten. Drops auf die Wurzel, auf den Quellknoten selbst oder in einen Nachfahren werden blockiert. Die reine Modellregel liegt in `legacy_can_move_before_target(...)` und `legacy_move_before_target(...)`; die Oberfläche verwendet dafür `LegacyTreeWidget`.
- `Notizen.vb` / `ToolStrip_dot_Click`: Der Bullet-Button fügt wie früher `Chr(13) + ChrW(8226) + "   "` ein. Für Qt wird der Zeilenumbruch auf `\n` normalisiert; der Editor wird danach ins Modell gespeichert.
- `ApplicationEvents.vb`: Alte Startargumente behalten lokale `.alx`-Dateien nur, wenn sie existieren. Fehlende lokale Ziele werden verworfen, `ftp://`-Ziele bleiben erlaubt.

## In 0.10.7 weitergeführt

- `Notizen.vb`/`neu_neben_knoten` ist genauer abgebildet: „Neu daneben“/Enter hängt den neuen Geschwisterknoten wie im alten Programm ans Ende der Elternebene, statt ihn direkt nach dem aktuell markierten Knoten einzufügen. Die Qt-unabhängigen Helfer heißen `legacy_new_next_parent(...)` und `legacy_new_next_node(...)`.
- `get_lightcolor()` ist präzisiert: Das alte `Random.Next(0, 14)` konnte nur die Fälle 0 bis 13 auswählen. Die im VB-Code vorhandenen Fälle `14`/`Else` bleiben dokumentiert, werden aber bei automatisch erzeugten Desktop-Notiz-Farben nicht mehr zufällig gewählt.

## In 0.10.6 weitergeführt

- `Baum.element_loeschen` ist genauer abgebildet: Nach dem Löschen eines Nicht-Wurzelknotens wird wie im alten WinForms-TreeView der vorher sichtbare Knoten ausgewählt. Dafür stellt `models.py` die Qt-unabhängigen Helfer `legacy_visible_walk`, `legacy_previous_visible_node` und `legacy_delete_fallback_node` bereit.
- `Baum.mach_haft_weg`/`loesche_haftnotiz_aus_baum` ist auf Teilbäume übertragen: Beim Löschen und beim Ausschneiden/Verschieben werden Desktop-Notizfenster im gesamten betroffenen Teilbaum geschlossen, nicht nur am obersten Knoten.
- `Autosavetimer_Tick` ist als reine Schutzfunktion `legacy_autosave_should_save` portiert. Autosave speichert nur noch, wenn ein Baum existiert, Änderungen vorliegen, eine Datei zugeordnet ist und diese Datei noch existiert.

## In 0.10.5 weitergeführt

- `suche.vb` und `suchergebnisse.vb` sind genauer abgebildet: Der Suchdialog besitzt jetzt eine sichtbare Ergebnisliste `Suchliste`, behält weiterhin das alte „Suchen / Weiter“-Durchschalten und kann Treffer per Doppelklick/Enter direkt anspringen.
- Die Suchtreffer werden wie im alten Hilfsobjekt aus Knotenreferenz plus `SelectionStart` geführt; `search_results.py` ergänzt daraus Pfad, Vorschautext und Listenbeschriftung ohne Qt-Abhängigkeit.
- Die Option „ganze Wörter“ folgt jetzt der historischen Token-Regel aus `suche.vb`: Nur Leerzeichen und CR/LF trennen Wörter. Satzzeichen und Tabs bleiben absichtlich Teil des Such-Tokens, damit alte Suchfälle reproduzierbar bleiben.
- Neue testbare Kernhilfen sind `SearchHitView`, `node_path`, `legacy_search_snippet`, `legacy_search_result_label` und `build_search_hit_views`.

## In 0.10.4 weitergeführt

- Das alte `fasse_zusammen`-Prinzip wurde für eingebettete Bilder präzisiert: kombinierte RTF-Exporte und neue Zusammenfassungsnotizen laufen nun über geordnete RTF-Inhaltsteile und behalten PNG-/JPEG-`\pict`-Gruppen statt nur Textsegmente zu übernehmen.
- `rtf_utils.py` stellt dafür `rtf_to_content_parts` bereit; `exporters.py` schreibt Bilder wieder als RTF-`\pict\pngblip` beziehungsweise `\pict\jpegblip`.
- Der Linux-Starter-Installer richtet zusätzlich eine XDG-MIME-Zuordnung für `*.alx` ein und setzt `notizen-py-qt.desktop` als Standard-App für `application/x-notizen-alx`. Damit ist die alte Windows-Dateizuordnungs-Idee plattformgerecht auf GNOME/Linux übertragen.

## In 0.10.3 weitergeführt

- Linux/GNOME-Direktstart ergänzt: `Notizen starten.sh` und `notizen-starten.sh` starten aus dem entpackten Ordner ohne vorheriges `python -m` und setzen automatisch `PYTHONPATH` auf `src/`.
- Die Direktstarter hängen standardmäßig `--show --reset-window --no-tray` an. Damit werden gespeicherte minimierte Fensterzustände ignoriert und das unter GNOME problematische Trayicon deaktiviert.
- Ein Menü-/Desktop-Starter kann jetzt mit `scripts/install_linux_launcher.sh` installiert werden; mit `--desktop` wird zusätzlich eine anklickbare Desktop-/Schreibtisch-Datei erstellt und, soweit möglich, als vertrauenswürdig markiert.
- `app.py` akzeptiert neu `--show`/`--visible`, damit sichtbarer Start Vorrang vor alter `/min`-/`-min`-Logik und gespeicherten `Minimized`-Fensterzuständen bekommt.
- Die GNOME-Tray-Regel wurde verschärft: GNOME versteckt beim Start nicht mehr automatisch ins Tray, auch dann nicht, wenn eine bekannte AppIndicator/KStatusNotifier-Erweiterung erkannt wird. Ein versteckter Tray-Start bleibt nur per `--force-tray-start` beziehungsweise `NOTIZEN_FORCE_TRAY_START=1` möglich.
- `scripts/package_zip.py` behandelt `.desktop`-Dateien wie ausführbare Startdateien und speichert sie im ZIP mit `755`; Verzeichnisse bleiben `755`, normale Dateien `644`.

## In 0.10.1 weitergeführt

- `Datei.vb` ist genauer abgebildet: Der alte Standard-Dateiname `unbenannt.alx` und der Standardordner `MyDocuments\Notizen` entsprechen im Port `Documents/Notizen`.
- `split_legacy_file_location` trennt Windows-Backslash-Pfade, POSIX-Pfade und leere Dateiwerte stabil in Verzeichnis/Dateiname. Damit werden alte Configs mit `C:\...\demo.alx` auf Linux/macOS nicht mehr als ein einziger Dateiname interpretiert.
- Das Desktop-Notiz-Untermenü aus `desknote_kontext_opacy.vb` nutzt wieder die alte Transparenz-Bedeutung: `90 %` Transparenz wird zu 10 % Deckkraft, `0 %` zu 100 % Deckkraft.
- Fensterzustände aus `xml_kram.vb` werden normalisiert. `minimized` und `maximized` werden in der Startlogik berücksichtigt; offensichtlich außerhalb des Arbeitsbereichs liegende Hauptfensterpositionen werden beim Wiederherstellen abgefangen.
- Neue Kernhilfen sind ohne Qt testbar und aus dem Paket exportiert: `LEGACY_DEFAULT_FILENAME`, `legacy_documents_notizen_dir`, `split_legacy_file_location`, `legacy_transparency_menu_options`, `legacy_opacity_percent_for_transparency_percent` und `normalize_window_state`.

## In 0.10.0 weitergeführt

- `xml_kram.vb`/`Notizen.Designer.vb`-Configdetails sind genauer übernommen: `open/once-opened` und `tool-stripes` werden gelesen, gespeichert und bleiben nach einem Import erhalten.
- Die Autosave-Regel aus `einstellungen.vb` ist als `normalize_autosave_seconds` portiert: `0` deaktiviert, aktivierte Werte unter fünf Sekunden werden auf fünf Sekunden gehoben, neue Standard-Config startet mit 60 Sekunden.
- `xml_kram.setshortcut` ist als testbarer Autostart-Adapter in `startup.py` abgebildet. Der Port wählt die jüngste Recent-Datei, setzt optional `-min` davor und schreibt unter Windows einen kleinen Startup-Launcher.
- Die RTF-Brücke behandelt RichTextBox-Tabellensteuerwörter `\cell`, `\nestcell` und `\row` nun als Tabulator-/Zeilen-Grenzen, damit alte Tabelleninhalte in Suche, Statistik und Exporten lesbar bleiben.

## In 0.9.9 weitergeführt

- Die alte `saftycopies`-Sicherungslogik wurde aus `Notizen.vb`/`xml_kram.vb` präzisiert: Backup-Verzeichnis ohne `.alx`-Suffix, Dateinamen nach `Name-YYYY-MM-DD-HH-MM-SS-ms.alx`, Auflistung, Rotation und explizite UI-Aktionen.
- Im Menü und in der Werkzeugleiste gibt es jetzt **Jetzt Sicherung erstellen** und **Sicherung öffnen**. Sicherungen werden aus dem ermittelten Legacy-Ordner geöffnet und durchlaufen vorher denselben Speichern-Abbrechen-Pfad wie normales Öffnen.
- Neue Desktop-Notizen übernehmen die Startwerte des alten Baum-Kontextmenüs: Mausposition, 200×200 Pixel, 85 % Deckkraft und helle Legacy-Farbe.
- Die Backup-Hilfsfunktionen sind als eigenständige API (`backup_directory_for`, `list_backups`, `create_backup`, `prune_backups`) testbar und aus dem Paket exportiert.

## In 0.9.8 weitergeführt

- `einheit_node_MenuItem_Click` bleibt als **Teilbaum zusammenfassen** erhalten.
- `einheit_start_MenuItem_Click` ist jetzt zusätzlich als **Ganzen Baum zusammenfassen** portiert. Die neue Notiz wird wie im alten Programm als Kind des ausgewählten Wurzel-/Quellknotens angelegt und anschließend ausgewählt.
- Suche, Schnell-Suche und Exporte schreiben den gerade sichtbaren Editorinhalt vor der Modellauswertung zurück, damit nicht mehr versehentlich ältere Knotendaten exportiert oder durchsucht werden.
- Das Menü **Zuletzt geöffnet** nutzt nun denselben Speichern-Verwerfen-Abbrechen-Pfad wie normales Öffnen und warnt bei fehlenden Dateien.
- Alte Migrationshilfen aus früheren UI-Zwischenschritten wurden aus dem aktiven Pfad entfernt und im Legacy-Bereich aufbewahrt.

## Noch offene beziehungsweise bewusst zurückgestellte Punkte

- Die RTF-Brücke deckt die üblichen alten Notizen-Fälle ab, ist aber kein vollständiger Microsoft-RTF-Renderer.
- FTP bleibt absichtlich eine Legacy-Kompatibilitätsfunktion; für vertrauliche Daten sollte mindestens die ALX-Datei selbst verschlüsselt werden.
- Visuelle Qt-Prüfung benötigt lokal PySide6 oder PyQt6. In dieser Ausführungsumgebung war keine Qt-Bindung installiert.
