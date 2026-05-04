# Validierung Notizen Python/Qt Port 0.10.15

## Ergebnis

Der Stand 0.10.15 wurde im Arbeitsbaum validiert. Die Qt-Oberfläche selbst konnte in dieser Umgebung nicht visuell gestartet werden, weil keine Qt-Bindung installiert ist. Die reine Portierungslogik, Python-Module, Shell-Skripte und neue Desktop-Notiz-Helfer wurden geprüft.

## Durchgeführte Prüfungen

```text
pytest: 149 passed, 3 skipped
compileall: OK
runtime probe ohne Qt-Smoke/Qt-Import: OK
```

Zusätzlich werden beim Paketbau erneut Shell-Syntax, Slint-Freiheit, ZIP-Rechte und Paket-Reimport geprüft.

## Neue Tests in 0.10.15

`tests/test_desktop_note_winforms_1015.py` prüft:

- alte `show2`-Geometrie,
- Hover-/Hidden-Geometrie,
- alte RichTextBox-Innengeometrie,
- Titelstreifen-Hide-/Close-Zonen,
- Move-/Resize-Mauszonen,
- Cursorzuordnung,
- Arbeitsbereich-Klemmung,
- 3-Pixel-MouseLeave-Toleranz.

## Einschränkung

Die Desktop-Notiz-Oberfläche wurde nicht visuell in GNOME geprüft. 0.10.15 ändert den Startpfad bewusst nicht, damit der zuletzt sichtbar funktionierende Start nicht erneut durch Display-/Wayland-Experimente destabilisiert wird.
