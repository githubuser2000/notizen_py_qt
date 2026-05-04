# Importierter Projektkontext aus bisherigen Notizen-Chats

Stand: 2026-05-01

Aus den bisherigen Projekt-Chats wurde für diese Portierungsrunde folgender Arbeitskontext übernommen:

- Das Original ist ein altes VB.NET-WinForms-Projekt auf .NET Framework 2.0.
- Die frühere Portierungsrichtung war zeitweise Rust/Slint und später Python/Qt.
- Eine mechanische 1:1-Transpilierung der WinForms-Oberfläche ist nicht das Ziel. Sinnvoller ist eine semantische Portierung der alten Programmfunktionen in wartbare Python/Qt-Module.
- Gut weiter portierbar sind Baumstruktur/Outliner, Notizenverwaltung, Suche, Autosave, Exportlogik, Bilder und Einstellungen.
- Mittlerer Aufwand liegt bei Mehrsprachigkeit und alten Ressourcen.
- Höherer Aufwand beziehungsweise bewusst vorsichtig zu behandeln sind Desktop-Notizen, RTF-Spezialfälle, FTP und stark WinForms-gebundene Eventlogik.
- Die aktive Richtung dieses Archivs ist Python/Qt mit PySide6/PyQt6-Kompatibilitätslayer. Alte Slint/QML-Zwischenschritte sind Legacy-Material und nicht mehr aktiver Laufzeitpfad.

Konkrete Umsetzung dieser Runde steht in `TRANSPILE_NET_TO_PYQT_REPORT.md`; die aktuelle Archivversion ist 0.10.17.

In dieser Runde zusätzlich übernommen: Die offenen nächsten Schritte aus den vorigen Chats lagen bei Einstellungs-/Autosave-Parität, Autostart, alten Config-Details und RichText-Spezialfällen. Darauf bauten 0.10.0 und diese 0.10.1-Runde gezielt auf.

In 0.10.1 zusätzlich übernommen: Die aktuelle Weiterführung greift die verbliebenen Legacy-Details aus `Datei.vb`, `desknote_kontext_opacy.vb` und `xml_kram.vb` auf: Standardordner/Dateiname, robustes Pfad-Splitting, alte Transparenzsemantik der Desktop-Notizen und normalisierte Fensterzustände.


In 0.10.2 zusätzlich übernommen: Die Nutzer-Rückmeldung zu falschen ZIP-Berechtigungen und zum unter GNOME unsichtbaren Tray-Start wurde direkt verarbeitet. Der Port enthält seitdem einen sicheren GNOME-Tray-Startpfad, neue CLI-Schalter und eine reproduzierbare ZIP-Verpackung mit korrekten Unix-Rechten.

In 0.10.3 zusätzlich übernommen: Die erneute GNOME-Rückmeldung zeigt, dass ein sichtbares Trayicon nicht zuverlässig genug ist. Deshalb startet GNOME jetzt sichtbar-first, selbst wenn eine AppIndicator-Erweiterung erkannt wird. Zusätzlich liegen echte Startdateien im Archiv: `Notizen starten.sh`, `notizen-starten.sh`, `Notizen PyQt.desktop` und ein Installationsskript für den Linux-Anwendungsstarter.

In 0.10.4 zusätzlich übernommen: Der nächste Paritätsschritt lag bei alter RichTextBox-Zusammenführung und Dateizuordnung. RTF-Zusammenfassungen behalten seitdem eingebettete Bilder, und Linux/GNOME bekommt eine echte `*.alx`-MIME-Zuordnung im Starter-Installer.

In 0.10.5 zusätzlich übernommen: Der nächste Paritätsschritt liegt bei `suche.vb` und `suchergebnisse.vb`. Der Suchdialog zeigt jetzt eine alte Ergebnislisten-Entsprechung, und die Ganzwortsuche verwendet die historische Leerzeichen/CR/LF-Tokenregel.

In 0.10.6 zusätzlich übernommen: Der nächste Paritätsschritt greift `Baum.element_loeschen`, `Baum.mach_haft_weg` und `Autosavetimer_Tick` auf. Die Auswahl nach dem Löschen folgt jetzt `PrevVisibleNode`, Desktop-Notizen in betroffenen Teilbäumen werden rekursiv geschlossen, und Autosave erzeugt keine verschwundene `.alx`-Datei still neu.


## Weiterführung 0.10.7

Der importierte Projekt-/Chat-Kontext bleibt maßgeblich: semantische Portierung statt Slint/QML-Rückfall. In dieser Runde wurde eine kleine, aber konkrete WinForms-Abweichung korrigiert: `neu_neben_knoten` hängt neue Geschwister ans Ende der Elternebene. Zusätzlich wurde die erreichbare `get_lightcolor`-Zufallspalette auf die alte `Random.Next(0, 14)`-Reichweite eingeschränkt.


## Weiterführung 0.10.8

Der nächste Paritätsschritt wurde wieder direkt aus dem alten WinForms-Code abgeleitet: `Baum_MouseUp` verschiebt per Drag-and-drop nicht in den Zielknoten hinein, sondern vor den Ziel-Geschwisterknoten. Außerdem wurde `ToolStrip_dot_Click` für den Bullet-Button übernommen und die lokale `.alx`-Existenzprüfung aus `ApplicationEvents.vb` ergänzt.

## Weiterführung 0.10.9

Der nächste Paritätsschritt greift zwei kleine, aber konkrete WinForms-Details auf: `kontext_inhalt.vb` erlaubte BMP-Bilder, die RichTextBox als DIB/Bitmap-RTF speichern kann, und `BaumTyp_NodeMouseDoubleClick` startete direkt die Knoten-Umbenennung. Der Port erhält jetzt alte `\dibitmap`-Bilder über HTML, Zusammenfassung und RTF-Export hinweg und startet die Titelbearbeitung per Baum-Doppelklick.



## Weiterführung 0.10.10

Diese Runde behebt den vom Nutzer gemeldeten GNOME-Start ohne sichtbares Fenster. Der Port wendet die alte `xml_kram.on_load()`-Bedingung genauer an: Der in der Legacy-Standardconfig gespeicherte minimierte Fensterzustand wird nicht mehr als echter Startwunsch behandelt, wenn die alte Position `0/0` ist. Zusätzlich erzwingen die Startdateien `--reset-window`, klemmen alte/offscreen Koordinaten auf den aktuellen Arbeitsbereich und schreiben ein Startprotokoll für Menüstarts.

## Weiterführung 0.10.11

Die neue Nutzerdiagnose zeigte einen wichtigen Unterschied: Der GNOME-Menüstart war sichtbar, aber Terminalstarts waren nicht sichtbar. Das spricht gegen einen reinen Trayfehler und für geerbte Shell-/Qt-Anzeigevariablen. Diese Runde ergänzt deshalb eine frühe, Qt-unabhängige Display-Normalisierung vor dem PySide6/PyQt6-Import und erweitert die Startprotokolle. `python3 -m notizen_py_qt --no-tray --show` und die Startdateien sollen nun denselben sichtbaren GNOME/Wayland-Pfad verwenden wie der Menüstart. Zusätzlich verhindert ein Root-Shim, dass Direktstarts aus dem entpackten Ordner unbemerkt eine alte installierte Paketversion laden.



## Weiterführung 0.10.12

Die aktuelle Nutzerdiagnose präzisiert den GNOME-Startfehler: Der Menüstart funktioniert, aber Shellstarts übernehmen ein kaputtes `DISPLAY=:1` und `GDK_BACKEND=x11`. Die Runde behandelt das nicht mehr als Tray- oder Fensterzustandsfehler, sondern als frühes Display-Backend-Problem vor dem Qt-Import. Zusätzlich wurden Build- und Diagnose-Skripte so korrigiert, dass sie am Ende nicht dauerhaft die GUI starten und dadurch nicht mehr hängen bleiben.

## Weiterführung 0.10.13

Die aktuelle Runde folgt der großen Rest-Transpilierungsuntersuchung und priorisiert zuerst den realen Zielsystemstart. Der Nutzer bestätigte, dass der GNOME-Menüstart sichtbar war, während Shell- und Startdatei-Aufrufe hängen blieben. Daher wird das Startverhalten nicht weiter aggressiv verändert, sondern auf den sichtbar funktionierenden GNOME-Menüpfad zurückgeführt: grafische Sitzungsvariablen werden übernommen, `DISPLAY=:1` wird bei GNOME/Wayland sichtbar auf `DISPLAY=:0` repariert, `QT_QPA_PLATFORM=wayland;xcb` bleibt erhalten und `GDK_BACKEND=x11` wird nur entfernt.

Zusätzlich wurde die ALX-Testbasis datenschutzbewusst erweitert: Die echte alte leere `unbenannt.alx` bleibt als Original-Minimalfixture erhalten, während persönliche große Beispielnotizen nicht ins Paket übernommen werden. Unbekannte Legacy-Config-Zweige und Root-Attribute werden beim Speichern konserviert, die aus `languages.vb` stammende Sprachreihenfolge wurde als testbare Legacy-API offengelegt und die alten `tastendruck`-Shortcuts, Recent-Files-Rotation, Desktop-Notiz-Randlogik und Wecker-Wochentage wurden als testbare Qt-unabhängige Zuordnungen nachgezogen.

## Weiterführung 0.10.13, Restanalyse umgesetzt

Auf Basis der großen Rest-Transpilierungsuntersuchung wurden in dieser Runde mehrere der dort markierten Lücken gezielt geschlossen, ohne den zuletzt sichtbar funktionierenden GNOME-Menüstart wieder zu verändern. Die Startdateien bleiben sichtbar-first, `QT_QPA_PLATFORM=wayland;xcb` bleibt der konservative GNOME/Wayland-Pfad, und die Display-Umgebung wird nur so weit repariert, wie es der Nutzerbefund nötig machte.

Zusätzlich wurden die Spracharrays aus `languages.vb` vollständig positionsgenau übernommen, reale alte `.alx`-Dateien aus dem Originalprojekt als Fixtures eingebaut, die alte Vierer-Recent-Dateiliste testbar gemacht, Desktop-Notiz-Opacity/Rand-/Klickzonenlogik weiter aus `desknote.vb` abgeleitet und der Info-/Hilfe-Text wieder aus dem alten `aboutinfotext` gespeist.


## Weiterführung 0.10.14

Der Nutzerwunsch war ausdrücklich, den sichtbar funktionierenden GNOME-Start nicht wieder umzubauen. Deshalb bleibt der Startpfad aus 0.10.13 erhalten; nur eine syntaktisch ungültige Bash-Bedingung im Starter wurde repariert. Die fachliche Weitertranspilierung greift den Audit-Block „echte alte ALX-Dateien und Roundtrip-Sicherheit“ auf: unbekannte Notizattribute werden konserviert, sparse Desktop-Notizattribute werden nicht künstlich aufgefüllt, ein datenschutzarmer ALX-Validator erlaubt Tests mit echten alten Dateien ohne Rohtextausgabe, und RTF-`\ansicpg`-Codepages werden für alte RichTextBox-Hex-Escapes berücksichtigt.

## Weiterführung 0.10.15

Der Nutzerwunsch war, zuerst Desktop-Notizen näher an WinForms zu bringen und den sichtbar funktionierenden Startpfad nicht wieder zu verändern. Diese Runde konzentriert sich deshalb auf `desknote.vb`, `desknote_kontext.vb` und `desknote_kontext_opacy.vb`: Desktop-Notizen sind nun rahmenlose kompakte Tool-Fenster mit alter `show2`-Geometrie, Hover-Rand, Titelstreifen-Hide/Close-Zonen, Move-/Resize-Hotzones, Read-only-RichText-Fläche, Titel-Farbwechsel, 4000-ms-Collapse-Timer und testbarer Legacy-Geometrie. Der GNOME-Start bleibt sichtbar-first wie in 0.10.13/0.10.14.



## Weiterführung 0.10.16

Die aktuelle Nutzer-Rückmeldung meldete zwei Regressions: Desktop-Notizen zeigten zwar den Verschiebe-Cursor, ließen sich unter GNOME aber nicht tatsächlich verschieben, und der GNOME-Menüstarter zeigte kein Fenster mehr. Deshalb wurde die Desktop-Notiz-Bewegung auf Qt/Wayland-Systemdrag umgestellt, während der manuelle WinForms-Pfad als Fallback bleibt. Der Menüstart wurde konservativ gehärtet: ein gutes von GNOME geliefertes `DISPLAY` wird nicht mehr überschrieben; `NOTIZEN_KEEP_DISPLAY=1` wird in den `.desktop`-Start übernommen. Zusätzlich wurde die im Audit offene Config-Roundtrip-Lücke für unbekannte Attribute an bekannten Config-Elementen geschlossen.

## Weiterführung 0.10.17

Diese Runde folgt weiter der großen Rest-Transpilierungsuntersuchung, ohne den sichtbar funktionierenden GNOME-Startpfad erneut umzubauen. Schwerpunkt ist jetzt die alte RichTextBox-/RTF-Fidelity aus `inhalt.vb`, `kontext_inhalt.vb` und den Zusammenfassungs-/Exportpfaden in `Notizen.vb`: alte Listenmarker aus ignorierbaren RTF-Zielen bleiben sichtbar, Hyperlink-Felder werden über Plaintext/HTML/RTF-Roundtrip erhalten, HTML-Tabellen und Listen werden strukturiert nach RTF übertragen, und OLE-Objekte verschwinden nicht mehr still. Zusätzlich gibt es einen optionalen lokalen venv-Starter für Systeme, auf denen Paketinstallation und System-Python-Umgebung getrennt bleiben sollen.
