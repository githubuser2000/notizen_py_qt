# Weitertranspilierung Notizen.NET → Python/Qt 0.10.17

## Schwerpunkt

Diese Runde geht die nächste Position aus der großen Rest-Transpilierungsuntersuchung an: RichTextBox-/RTF-Fidelity und ein robusterer Installations-/Startpfad, ohne den zuletzt sichtbaren GNOME-Start erneut zu verändern.

Der sichtbare Startpfad aus 0.10.13 bis 0.10.16 bleibt erhalten: `--show --reset-window --no-tray`, `QT_QPA_PLATFORM=wayland;xcb` und kein pauschales Löschen von `DISPLAY`. An GNOME-/Wayland-Displaylogik wurde in 0.10.17 bewusst nichts Neues experimentiert.

## RTF-Listenmarker aus alter RichTextBox

WinForms-`RichTextBox` speichert sichtbare Listenpräfixe häufig in RTF-Zielen wie `\*\pntext` und `\*\listtext`. Diese Ziele sind formal ignorierbar, enthalten aber den sichtbaren Bullet- oder Nummerntext.

Der PyQt-Port überspringt diese Gruppen nun nicht mehr vollständig. Dadurch bleiben alte Listenmarker erhalten in:

- Plaintext-Ausgabe,
- Suche,
- Statistik,
- HTML-Brücke,
- Baum-/Teilbaum-Zusammenfassungen,
- Exporten.

## RTF-Hyperlinks

Alte RTF-Hyperlinks werden über `\field`/`HYPERLINK`-Gruppen erkannt. Neu ist der Inhaltsteil `RtfHyperlink`.

Damit gilt jetzt:

- Plaintext nutzt den sichtbaren Linktext,
- HTML-Ausgabe schreibt `<a href="...">...</a>`,
- HTML-zu-RTF schreibt wieder RTF-`HYPERLINK`-Felder,
- kombinierter RTF-Export und Zusammenfassungen behalten diese Felder.

## HTML-Tabellen und Listen im RTF-Rückweg

Die HTML-zu-RTF-Brücke wurde so erweitert, dass einfache Tabellen und Listen nicht mehr zu einem ungetrennten Textstrom werden:

- Tabellenzellen werden durch Tabs getrennt,
- Tabellenzeilen durch Zeilenumbrüche,
- ungeordnete Listen bekommen Bullet-Präfixe,
- geordnete Listen bekommen stabile Nummernpräfixe.

Das ist kein vollständiger Tabellenrenderer, aber es erhält die textuelle Struktur alter Notizinhalte deutlich besser.

## OLE-/Objektgruppen

Alte RTF-Objekte (`\object`, `\objdata`) können von Qt nicht sinnvoll als WinForms-OLE-Objekte geöffnet werden. Bisher drohten solche Gruppen aber komplett zu verschwinden. 0.10.17 ersetzt sie deshalb sichtbar durch:

```text
[Objekt]
```

Damit ist wenigstens erkennbar, dass in der alten Notiz ein eingebettetes Objekt existierte.

## Optionaler venv-Starter

Neu ist:

```bash
./notizen-starten-venv.sh
```

Der Starter erstellt bei Bedarf eine lokale `.venv`, installiert das Paket im editierbaren Modus mit Crypto-Extra und delegiert dann an den bestehenden sichtbaren Starter `notizen-starten.sh`.

Der Linux-/GNOME-Starter-Installer kann optional diesen venv-Starter verwenden:

```bash
./scripts/install_linux_launcher.sh --venv
./scripts/install_linux_launcher.sh --desktop --venv
```

Der normale Starter bleibt unverändert erhalten.

## Neue Tests

Neu hinzugekommen sind:

- `tests/test_rtf_fidelity_1017.py`
- `tests/test_launchers_1017.py`

Sie prüfen Listenmarker, Hyperlink-Roundtrips, Tabellen-/Listenstruktur, OLE-Platzhalter, kombinierten RTF-Export mit Links und den optionalen venv-Starter.

## Bewusst nicht geändert

Der GNOME-Startpfad wurde nicht erneut umgebaut. Die Nutzeranforderung war, das sichtbar gewesene Startverhalten zu erhalten. 0.10.17 konzentriert sich deshalb auf RTF-Fidelity und optionale Installationshärtung.

## Validierung

Die Validierung steht in `VALIDATION_NET_PORT.md`.
