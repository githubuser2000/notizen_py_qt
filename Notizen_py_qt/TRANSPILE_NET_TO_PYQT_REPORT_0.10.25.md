# Notizen.NET → PyQt Weitertranspilierung 0.10.25

## Schwerpunkt

Diese Runde konzentriert sich auf weitere RichTextBox-/RTF-Kompatibilität und eine noch offen dokumentierte ALX-Roundtrip-Lücke.

## Umgesetzt

### RTF-Felder

- Nicht-Hyperlink-Felder wie `PAGE`, `DATE`, `REF` und ähnliche `\field`-Gruppen werden nicht mehr als interne `fldinst`-Anweisung sichtbar.
- Für Plaintext, Suche, Statistik, Textsegmente und HTML wird das sichtbare `\fldrslt`-Ergebnis verwendet.
- Die originale `\field`-Rohgruppe wird als `RtfField` erhalten.
- `rtf_to_html()` schreibt die Rohgruppe als `data-notizen-rtf-field` in die HTML-Brücke.
- `html_to_rtf()` liest diese Brücke zurück und schreibt wieder die originale Feldgruppe.
- Der Teilbaum-/Gesamtbaum-RTF-Export erhält solche Rohfelder ebenfalls.

### RTF-/OLE-Objekte

- Legacy-`\object`-Gruppen werden als `RtfObject` modelliert.
- Plaintext/Suche zeigen weiterhin den sichtbaren Platzhalter `[Objekt]`.
- Die Rohgruppe bleibt in `rtf_to_content_parts()` und im kombinierten RTF-Export erhalten.
- `rtf_to_html()` schreibt OLE-Gruppen als `data-notizen-rtf-object`; `html_to_rtf()` kann sie daraus zurückschreiben.
- Der Objektklassenname aus `\objclass`, zum Beispiel `Package`, wird für HTML-Titel extrahiert.

### ALX-Roundtrip

- `NoteNode` enthält jetzt `extra_child_xml`.
- Unbekannte zusätzliche XML-Kindelemente unter `<Notiz>` werden beim Laden gespeichert und beim Speichern wieder angehängt.
- Bekannte Notiz-Kinder bleiben weiter echte Baumknoten.
- Bekannte alte Attribute, `isexpanded`, Desktop-Haftnotizdaten, Farben und RTF-Inhalt bleiben unverändert behandelt.

### Migrationsskript-Robustheit

- `scripts/continue_qt611_transpile.py` hat jetzt pro Subprozess einen konfigurierbaren Timeout über `QT611_CONTINUE_STEP_TIMEOUT`.
- Dadurch kann ein externer Hilfsschritt die Weitertranspilierung nicht mehr unbegrenzt blockieren.

## Weiter offen

- Vollständige Microsoft-RichTextBox-/OLE-Aktivierung und echtes Bearbeiten eingebetteter OLE-Objekte ist weiterhin nicht 1:1 portiert.
- RTF-Tabellen werden aktuell lesbar über Zell-/Zeilen-Trenner behandelt; pixelgenaue Tabellenlayout-Rekonstruktion bleibt offen.
- Pixelgenaue WinForms-Paintdetails der Desktop-Haftnotizen bleiben offen.
- Die alte FTP-Dialogoberfläche ist noch nicht in allen WinForms-Details nachgebaut.
- Historische Windows-/ClickOnce-Installationsdetails bleiben außerhalb des PyQt-Linux-Fokus.
