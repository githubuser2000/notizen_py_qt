# Weitertranspilierung Notizen.NET → Python/Qt 0.10.9

## Ausgangspunkt

Dieser Stand baut auf 0.10.8 auf. Der aktive Laufzeitpfad bleibt Python/Qt; alte Slint-/QML-/Rust-Zwischenschritte bleiben ausschließlich archiviertes Migrationsmaterial.

Für diese Runde wurden erneut konkrete WinForms-Stellen aus dem alten Notizen.NET-Code herangezogen:

- `kontext_inhalt.vb`: Bildauswahl akzeptiert neben JPG/TIF/GIF ausdrücklich auch `*.bmp`.
- `inhalt.vb`: Der Editor ist eine WinForms-`RichTextBox`, die gepastete oder eingefügte Bitmapbilder in RTF häufig als DIB/Bitmap-Payload schreibt.
- `Baum.vb`: `BaumTyp_NodeMouseDoubleClick` startet bei Doppelklick direkt `BeginEdit()` auf dem Baumknoten.

## Umgesetzte Änderungen in 0.10.9

### Legacy-Bitmapbilder in RTF erhalten

Die RTF-Brücke konnte seit 0.10.4 PNG- und JPEG-`\pict`-Gruppen erhalten. Alte RichTextBox-Bitmapbilder wurden aber noch nicht zuverlässig als Bild übernommen, weil WinForms sie oft als `\pict\dibitmap...` ohne BMP-Dateikopf speichert.

Neu in `rtf_utils.py`:

- `dib_to_bmp_bytes(...)`: erzeugt aus einem RTF-DIB-Payload eine normale BMP-Datei mit `BM`-Header.
- `bmp_to_dib_bytes(...)`: entfernt den BMP-Dateikopf wieder für RTF-`\dibitmap0`.
- `_parse_pict_group(...)` erkennt jetzt `\dibitmap` und `\wbitmap` zusätzlich zu PNG/JPEG.
- `rtf_to_html(...)` gibt alte DIB-Bilder als `data:image/bmp;base64,...` aus.
- `html_to_rtf(...)` akzeptiert `image/bmp`-Data-URIs und lokale `.bmp`-Dateien.

Neu in `exporters.py`:

- `RtfImage(mime_type="image/bmp", ...)` wird beim kombinierten RTF-Export als `\pict\dibitmap0` geschrieben.
- „Teilbaum zusammenfassen“, „Ganzen Baum zusammenfassen“ und der kombinierte RTF-Export behalten dadurch alte Bitmapbilder statt sie durch `[Bild]` zu ersetzen.

### Baum-Doppelklick wie `BaumTyp_NodeMouseDoubleClick`

Die alte WinForms-Baumansicht rief bei Doppelklick auf einen Knoten `BeginEdit()` auf. Der PyQt-Port verbindet jetzt `itemDoubleClicked` mit `edit_tree_item(...)`; `rename_node(...)` nutzt denselben Pfad.

Damit sind Menü-Aktion, Tastenkürzel und Doppelklick konsistent und näher am alten TreeView-Verhalten.

### Öffentliche API ergänzt

Die neuen RTF-Bitmap-Helfer werden aus `notizen_py_qt.__init__` exportiert:

- `dib_to_bmp_bytes(...)`
- `bmp_to_dib_bytes(...)`

## Dateien mit relevanten Änderungen

- `src/notizen_py_qt/rtf_utils.py`
- `src/notizen_py_qt/exporters.py`
- `src/notizen_py_qt/app.py`
- `src/notizen_py_qt/__init__.py`
- `tests/test_rtf_bmp_legacy_109.py`
- `tests/test_legacy_ui_source_109.py`
- `README.md`
- `docs/MAPPING.md`
- `docs/PROJECT_CONTEXT_IMPORTED.md`
- `pyproject.toml`
- `TRANSPILE_NET_TO_PYQT_REPORT.md`
- `VALIDATION_NET_PORT.md`

Zusätzlich wurden die 0.10.8-Berichte archiviert:

- `TRANSPILE_NET_TO_PYQT_REPORT_0.10.8.md`
- `VALIDATION_NET_PORT_0.10.8.md`

## Bewusst nicht geändert

Die RTF-Brücke bleibt ein pragmatischer Notizen.NET-Kompatibilitätsadapter und kein vollständiger Microsoft-RTF-Renderer. Exotische binäre `\bin`-Bildpayloads, WMF/EMF-Objekte und komplexe OLE-Inhalte bleiben weiterhin zurückgestellt. Die GNOME-sicheren Startdateien bleiben sichtbar-first mit `--show --no-tray`.
