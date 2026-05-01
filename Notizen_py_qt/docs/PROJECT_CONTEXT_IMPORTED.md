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

Konkrete Umsetzung dieser Runde steht in `TRANSPILE_NET_TO_PYQT_REPORT_0.9.8.md`.
