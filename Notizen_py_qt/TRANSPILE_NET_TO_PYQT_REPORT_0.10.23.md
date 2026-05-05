# Notizen.NET -> Python/Qt Transpilation Report 0.10.23

## Fokus dieser Runde

Diese Runde setzt direkt an den gemeldeten sichtbaren Abweichungen an:

1. Desktop-Haftnotizen: Transparenz, Zeilenabstände, oberer Textabstand und Ausblenden/Minimieren.
2. Hauptfenster: WinForms-nahe Anordnung der gelben Felder `txt1`/`txt2` ohne zusätzliches sichtbares „Baum“-Label.
3. RTF-Bedienung: sichtbare Formatierungsbuttons oben wie im alten `ToolStrip_fontstyle`.
4. Drucken: robuster PySide/PyQt-kompatibler Druckpfad.
5. RTF-Brücke: weichere RichTextBox-Zeilenumbrüche und keine HTML-Standardabsatzränder.

## Desktop-Haftnotizen

Die alte `desknote.vb`-Form war ein eigenständiges Fenster. Die PyQt-Portierung hatte die Haftnotiz bisher als vom Hauptfenster abhängiges Tool-Fenster angelegt; das ist unter GNOME und anderen Window-Managern ungünstig für Taskleiste, Minimieren und Fenster-Opacity.

Geändert:

- `DesktopNoteWindow` wird jetzt als unabhängiges Top-Level-Fenster erzeugt (`WINDOW | FRAMELESS`, kein Parent, kein `Qt.Tool`).
- `WA_TranslucentBackground` bleibt aktiv.
- Das Top-Level-Fenster wird nicht mehr per `setAutoFillBackground(True)` opak gefüllt.
- Die Notizfarbe wird im `QTextEdit` als CSS-`rgba(...)` gesetzt, sodass ALX-ARGB-Farben Alpha behalten.
- Die im Kontextmenü gewählte Transparenz wird dauerhaft auf das Fenster angewendet und beim Hover/Fokus nicht mehr auf 100 % zurückgesetzt.
- „Ausblenden / minimieren“ speichert die Desktop-Notiz weiterhin als sichtbar im Modell und ruft `showMinimized()` auf. Damit bleibt sie für Window-Manager/Taskleiste erreichbar, sofern die Umgebung minimierte Fenster dort anzeigt.

## RTF und Zeilenabstände in Haftnotizen

Die alte WinForms-`RichTextBox` behandelt `\line` nicht wie einen neuen Absatz. Qt-HTML hatte vorher aus praktischen Gründen alle RTF-Zeilenwechsel zu `<p>`-Absätzen gemacht; dadurch entstanden zusätzliche Leerzeilen und ein zu großer Abstand vor der ersten Zeile.

Geändert:

- RTF `\line` wird intern als weicher Zeilenumbruch geführt und in HTML als `<br/>` ausgegeben.
- RTF `\par` bleibt ein echter Absatz.
- HTML `<br>` wird wieder als RTF `\line` geschrieben.
- `rtf_to_html()` setzt am `<body>` `margin:0`.
- Standard-`<p>`-Ausgabe erhält `margin-top:0; margin-bottom:0`, solange die RTF-Quelle keine expliziten `\sb`/`\sa`-Abstände vorgibt.
- Das Haftnotiz-`QTextDocument` nutzt `setDocumentMargin(0)`, keine QTextEdit-Rahmen und keine zusätzlichen Viewport-Ränder.

Dadurch liegen einfache Zeilenumbrüche näher am alten RichTextBox-Verhalten, ohne echte RTF-Absatzabstände zu verlieren.

## RTF-Formatierungsbuttons oben

Aus `Notizen.Designer.vb` war relevant, dass `ToolStrip_fontstyle` oben unter anderem diese Controls hatte:

- `ToolStrip_regular`
- `ToolStrip_bold`
- `ToolStrip_italic`
- `ToolStrip_underline`
- `ToolStrip_strikeout`
- `ToolStrip_bigger`
- `ToolStrip_smaller`
- `ToolStrip_fontsizenumber`
- `ToolStrip_fonts`
- `ToolStrip_dot`
- `ToolStrip_whatscroll`
- `ToolStrip_colormenue` beziehungsweise Farbmenüeinträge für Vorder-/Hintergrundfarbe

Die PyQt-Version hat jetzt eine sichtbare obere `RTF-Formatierung`-Toolbar mit Text-Buttons und den alten ObjectNames für die wichtigsten ToolStrip-Elemente. Die Funktionen binden an die vorhandenen QTextEdit-Formatpfade: Fett, Kursiv, Unterstrichen, Durchgestrichen, Normal, Schriftgröße größer/kleiner, Schriftart, Schriftgröße, Textfarbe, Texthintergrund, Aufzählungspunkt und Scrollleisten-Wechsel.

## Drucken

Der Druckpfad wurde gehärtet:

- `QtPrintSupport` wird erst beim Drucken geladen und bei Bedarf für PySide6/PyQt6 erneut gesucht.
- `QPrinter.HighResolution` wird über den Kompatibilitäts-Enum geholt.
- `QTextDocument.print_` wird bevorzugt; falls eine Bindung nur `print` anbietet, wird diese Methode verwendet.
- Aktuelle Notiz, aktueller Teilbaum und gesamter Baum verwenden denselben Druckpfad.

## Hauptlayout

Notizen.NET zeigte kein zusätzliches Wort „Baum“ über dem Baum. Links oben war das gelbe `txt1`, rechts oben das gelbe `txt2`, direkt nebeneinander in den Split-Panels.

Geändert:

- Der Qt-Baum-Header ist versteckt.
- Das sichtbare Label „Baum“ wurde aus dem Layout entfernt.
- Das sichtbare Label „Titel:“ und der zusätzliche Modus-/Apply-Bereich über dem Editor wurden aus dem Layout entfernt beziehungsweise versteckt.
- `txt1` und `txt2` bleiben als gelbe Felder oben in ihren Split-Panels.

## Weiter offene Bereiche

Weiterhin nicht vollständig 1:1 nachgebildet sind:

- vollständige Microsoft-RichTextBox-/OLE-Semantik jenseits der vorhandenen Bild-, Link-, Objektplatzhalter- und Formatbrücke,
- pixelgenaue WinForms-Paint-Details der Desktop-Haftnotiz-Ränder/Ecken,
- alte FTP-Dialog-UI in allen WinForms-Details,
- historische Windows-/ClickOnce-Installationsdetails.
