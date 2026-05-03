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

Konkrete Umsetzung dieser Runde steht in `TRANSPILE_NET_TO_PYQT_REPORT.md`; die aktuelle Archivversion ist 0.10.11.

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

