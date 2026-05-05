# Notizen .NET → PyQt Weitertranspilierung 0.10.26

Diese Version setzt die Toolbar-Anpassung aus Notizen.NET weiter um.

## Änderungen

- Die Werkzeugleisten zwischen Menüleiste und Baum/RTF-Editor sind deutlich höher und kräftiger gestaltet.
- Die sichtbaren Toolbar-Buttons verwenden Icon-only-Darstellung statt Textkürzeln.
- RTF-Formatierungsaktionen wurden von sichtbaren Kürzeln (`N`, `B`, `K`, `U`, `D`, `+`, `-`) auf beschreibende Action-Namen und bildhafte Symbole umgestellt.
- Tooltips bleiben erhalten, damit die Bedeutung erst bei Mouse-Hover sichtbar wird.
- Schriftart- und Schriftgrößenfelder in der RTF-Leiste wurden an die größere Toolbar-Höhe angepasst.
- Viele Toolbar-Aktionen erhalten konsistente selbst gezeichnete Piktogramme; übrige Aktionen nutzen Qt-Standardicons als Fallback.

## Validierung

- `python3 -m compileall -q src notizen_py_qt scripts`
