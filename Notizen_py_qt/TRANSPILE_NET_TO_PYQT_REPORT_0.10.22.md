# Notizen PyQt 0.10.22 Transpilationsbericht

Diese Runde setzt auf 0.10.21 auf und konzentriert sich auf weitere WinForms-`RichTextBox`-/RTF-Parität. Der verfügbare Projektkontext enthielt keine zusätzlichen konkreten offenen Punkte aus anderen Chats; die bekannten Restbereiche bleiben daher RichTextBox/OLE-Vollsemantik, pixelgenaue Desktop-Haftnotiz-Paintdetails, alte FTP-Dialog-UI-Details und historische Windows-/ClickOnce-Installationsdetails.

## Weiter portierte RTF-Funktionen

- `\plain` behandelt jetzt nur Zeichenformatierung als Reset. Absatzformatierungen wie `\qc`, `\li`, `\ri`, `\fi`, `\sb`, `\sa`, `\sl` und `\slmult` bleiben im laufenden Absatz erhalten.
- RTF-Parser und HTML-Brücke kennen zusätzliche RichTextBox-/RTF-Steuerwörter:
  - `\slmult` für mehrfache Zeilenhöhe,
  - `\cbpat` und `\chcbpat` als Hintergrundfarbe,
  - weitere Unterstreichungsvarianten wie `\ulwave`, `\uldash`, `\ulth...`,
  - `\striked`/`\strikedl`,
  - `\caps`, `\scaps`, `\v`,
  - `\rtlpar`/`\rtlch` und `\ltrpar`/`\ltrch`,
  - `\expnd`/`\expndtw` für Zeichenabstand.
- Versteckter RTF-Text (`\v`) wird aus der Plaintext-Suche/-Statistik herausgehalten, bleibt aber in der HTML-/Segmentbrücke mit `display:none` nachvollziehbar.
- RTF-Fonttabellen werden robuster gelesen, auch wenn Word/WordPad Aliasgruppen wie `{\*\falt ...;}` in der Fontdefinition einbettet.
- RTF-Farbtabellen ohne führenden Automatik-Farbslot werden kompatibel indiziert, damit `\cf1` nicht versehentlich auf den Defaultslot zeigt.

## Weiter portierte HTML/CSS→RTF-Funktionen

- CSS-Farben: CSS-Farbnamen, `#rgb`, `#rrggbb`, Qt-ähnliche 8-stellige Hexwerte und `rgb(...)`/`rgba(...)`, auch mit Prozentwerten.
- Absatz-/Blockformatierung: `margin`-Kurzform, einzelne Margin-Seiten, `padding-left`, Qt-Blockeinzüge, `text-align`, `text-indent`, Prozent-/Faktor-`line-height` mit `\slmult`.
- Zeichenformatierung: `font-variant: small-caps`, `text-transform: uppercase`, `letter-spacing`, `direction`, `display:none`, `visibility:hidden`.
- Semantische HTML-Tags/Attribute: `body text/bgcolor`, `font face/size/color`, `center`, `blockquote`, `code`/`kbd`/`samp`/`pre`, `small`, `big`, sowie vorhandene Überschriften und Links.
- Kombinierte Teilbaum-/Gesamtbaum-RTF-Exporte übernehmen die neuen `RtfTextStyle`-Felder ebenfalls.

## Weiterhin offen

- Vollständige Microsoft-RichTextBox-/OLE-Semantik, vor allem echte eingebettete OLE-Objekte jenseits der aktuellen Platzhalter/Bildbrücke.
- Pixelgenaue WinForms-Paintdetails der Desktop-Haftnotiz-Ränder/Ecken.
- Alte FTP-Dialogoberfläche in allen WinForms-Details.
- Historische Windows-/ClickOnce-Installationsdetails.

## Kompatibilitätsnotiz

Der Port speichert weiterhin das kanonische `notizen-alx2`-Format. Roh-RTF bleibt erhalten, solange eine Notiz nicht bearbeitet wird. Nach Bearbeitung entscheidet die jetzt erweiterte HTML→RTF-Brücke, welche Formatfelder aktiv zurückgeschrieben werden können.
