# Validierung Notizen Python/Qt Port 0.10.16

## Ergebnis

Der Stand 0.10.16 wurde im Arbeitsbaum validiert. Die echte GNOME-/Qt-Oberfläche konnte in dieser Umgebung nicht visuell gestartet werden, weil keine Qt-Bindung installiert ist. Die regressionsrelevanten Änderungen sind dennoch über Python-Tests, Shell-Syntaxprüfung und Import-/Roundtrip-Probes abgesichert.

## Durchgeführte Prüfungen

```text
pytest: 154 passed, 3 skipped
compileall: OK
bash -n scripts/*.sh *.sh: OK
check_no_slint_strict.sh: OK
runtime probe ohne Qt-Import: OK
API probe: OK, Version 0.10.16
```

## Neue Tests in 0.10.16

`tests/test_desktop_menu_regressions_1016.py` prüft:

- ein gutes GNOME-Menü-`DISPLAY=:0` wird nicht durch stale systemd-Sessionwerte ersetzt,
- ein bekannt problematisches Shell-`DISPLAY=:1` kann weiterhin auf `:0` repariert werden,
- Menü- und installierte `.desktop`-Starter setzen `NOTIZEN_KEEP_DISPLAY=1`,
- die Desktop-Notiz-Klasse nutzt `startSystemMove`/`startSystemResize` und behält den manuellen Fallback.

`tests/test_legacy_config_passthrough_1016.py` prüft:

- unbekannte Root-Attribute,
- unbekannte Attribute an bekannten Top-Level-Config-Elementen,
- unbekannte Attribute an `open/once-opened` und `tool-stripes/*`,
- unbekannte Zusatz-Elemente.

## Einschränkung

Desktop-Notiz-Systemdrag und GNOME-Menüstart müssen lokal in einer echten GNOME-/Wayland-Sitzung bestätigt werden. Die Änderung verwendet jedoch den von Qt vorgesehenen System-Move/-Resize-Pfad für rahmenlose Fenster und vermeidet weitere riskante Display-Experimente.
