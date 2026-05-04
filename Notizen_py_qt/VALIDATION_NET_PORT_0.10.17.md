# Validierung Notizen Python/Qt Port 0.10.17

## Ergebnis

Der Stand 0.10.17 wurde im Arbeitsbaum und anschließend im frisch entpackten ZIP validiert. Die echte GNOME-/Qt-Oberfläche konnte in dieser Umgebung nicht visuell gestartet werden, weil keine echte GNOME-Sitzung mit Qt-Oberfläche verfügbar ist. Der Startpfad wurde in dieser Runde bewusst nicht erneut verändert.

## Durchgeführte Prüfungen

```text
pytest: 165 passed, 3 skipped
compileall: OK
bash -n scripts/*.sh *.sh: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt-Import: OK
API probe: OK, Version 0.10.17
ZIP permission check: OK
package recheck via unzip: OK
```

## Neue Tests in 0.10.17

`tests/test_rtf_fidelity_1017.py` prüft:

- sichtbare Listenmarker aus `\*\pntext`,
- sichtbare Nummernpräfixe aus `\*\listtext`,
- HTML-Tabellen-Roundtrip mit Tabs und Zeilenumbrüchen,
- geordnete HTML-Listen mit Nummernpräfixen,
- RTF-`HYPERLINK`-Felder in Plaintext, HTML und Content-Parts,
- HTML-Hyperlinks zurück nach RTF-`HYPERLINK`,
- kombinierten RTF-Export mit Hyperlink-Feldern,
- sichtbare `[Objekt]`-Platzhalter für alte RTF-OLE-Gruppen.

`tests/test_launchers_1017.py` prüft:

- der optionale venv-Starter ist ausführbar,
- seine Shell-Syntax ist gültig,
- er delegiert an den bestehenden sichtbaren Starter,
- der Linux-Starter-Installer kann per `--venv` den venv-Starter auswählen.

## Einschränkung

Die RTF-Brücke ist weiterhin kein vollständiger Microsoft-RTF-Renderer. 0.10.17 verbessert gezielt alte RichTextBox-Fälle, die in Notizen.NET relevant sind: Listenmarker, Hyperlinks, Tabellen-/Listen-Textstruktur und eingebettete Objektgruppen. Komplexe OLE-Objekte werden sichtbar markiert, aber nicht als echte OLE-Einbettung wiederhergestellt.
