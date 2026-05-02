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

Konkrete Umsetzung dieser Runde steht in `TRANSPILE_NET_TO_PYQT_REPORT.md`; die aktuelle Archivversion ist 0.10.1.

In dieser Runde zusätzlich übernommen: Die offenen nächsten Schritte aus den vorigen Chats lagen bei Einstellungs-/Autosave-Parität, Autostart, alten Config-Details und RichText-Spezialfällen. Darauf bauten 0.10.0 und diese 0.10.1-Runde gezielt auf.

In 0.10.1 zusätzlich übernommen: Die aktuelle Weiterführung greift die verbliebenen Legacy-Details aus `Datei.vb`, `desknote_kontext_opacy.vb` und `xml_kram.vb` auf: Standardordner/Dateiname, robustes Pfad-Splitting, alte Transparenzsemantik der Desktop-Notizen und normalisierte Fensterzustände.
