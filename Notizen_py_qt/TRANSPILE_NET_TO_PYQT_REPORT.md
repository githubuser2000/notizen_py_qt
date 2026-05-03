# Weitertranspilierung Notizen.NET → Python/Qt 0.10.14

Ausgangsstand: 0.10.13. Schwerpunkt dieser Runde war ausdrücklich: **den sichtbar funktionierenden GNOME-Startpfad nicht wieder umbauen** und stattdessen genau die im Audit genannten Legacy-Restlücken weiter schließen.

## 1. Sichtbarer Startpfad bleibt erhalten

0.10.14 übernimmt die Startstrategie aus 0.10.13:

- `./Notizen\ starten.sh` und `./notizen-starten.sh` starten mit `--show --reset-window --no-tray`.
- GNOME/Wayland bleibt bei `QT_QPA_PLATFORM=wayland;xcb`.
- `DISPLAY` wird nicht pauschal gelöscht.
- `GDK_BACKEND=x11` und GTK2/GTK3-Platform-Themes werden weiterhin nur für sichtbaren GNOME/Wayland-Start entfernt.

Geändert wurde nur ein echter Bash-Syntaxfehler in `notizen-starten.sh`: Eine Hilfsfunktion wurde vorher innerhalb einer `[[ ... ]]`-Bedingung aufgerufen. Das ist in Bash ungültig und konnte den Starter aus der Shell blockieren. Die Bedingung wurde in zwei saubere Stufen zerlegt; die eigentliche sichtbare Startpolitik wurde nicht verändert.

## 2. ALX-Attributerhalt wie bei alten XML-Dateien

Der Audit hatte echte alte `.alx`-Dateien als entscheidenden nächsten Testblock markiert. 0.10.14 härtet dafür das ALX-Modell:

- unbekannte Attribute an `<Notiz>`-Elementen werden jetzt in `NoteNode.extra_attrs` gespeichert,
- diese Attribute werden beim Speichern wieder ausgegeben,
- `clone_deep(...)` erhält sie,
- der Teilbaum-Zwischenablagepfad erhält sie ebenfalls.

Damit werden alte/externe Zusatzattribute nicht mehr still verworfen. Bekannte moderne Attribute überschreiben weiterhin kontrolliert die jeweiligen Modellfelder.

Betroffene Dateien:

- `src/notizen_py_qt/models.py`
- `src/notizen_py_qt/alx_io.py`
- `src/notizen_py_qt/node_clipboard.py`

Neue Tests:

- `tests/test_alx_roundtrip_attrs_1014.py`

## 3. Sparse Legacy-Desktop-Notizen

Alte Notizen.NET-ALX-Dateien enthalten Desktop-Notizdaten nicht immer mit derselben Attributvollständigkeit wie der moderne Port. Vorher konnte ein reiner Laden/Speichern-Vorgang neue `opacity`-/`argb`-Attribute erzeugen, obwohl sie in der alten Datei nicht vorhanden waren.

0.10.14 merkt sich jetzt:

- ob ein Desktop-Notizzustand aus einer sparse Legacy-Struktur stammt,
- welche Desktop-Attribute ursprünglich vorhanden waren,
- ob `opacity` oder `argb` wirklich neu geschrieben werden müssen.

Ein unveränderter Roundtrip bleibt dadurch näher an der alten Datei. Sobald der Nutzer die Desktop-Notiz wirklich verändert, werden die modernen Werte kontrolliert geschrieben.

Betroffene Dateien:

- `src/notizen_py_qt/models.py`
- `src/notizen_py_qt/alx_io.py`
- `src/notizen_py_qt/node_clipboard.py`

## 4. Datenschutzarmer Legacy-ALX-Validator

Neu ist ein Prüfwerkzeug, mit dem echte alte ALX-Dateien getestet werden können, ohne Notizinhalte in Logs zu schreiben:

```bash
scripts/validate_legacy_alx.py alte_datei.alx
NOTIZEN_ALX_PASSWORD='...' scripts/validate_legacy_alx.py --password-env NOTIZEN_ALX_PASSWORD alte_datei.alx
```

Das Werkzeug führt aus:

1. ALX laden,
2. Datenschutz-Zusammenfassung bilden,
3. wieder als ALX schreiben,
4. erneut laden,
5. Zusammenfassungen vergleichen.

Ausgegeben werden nur Zähler und Hashes:

- Knotenzahl,
- maximale Tiefe,
- Desktop-Notiz-Anzahl,
- sichtbare Desktop-Notizen,
- RTF-/Plaintext-Zeichenzahl,
- Bildanzahl,
- Baumstruktur-Hash,
- Inhalts-Hash.

Keine Titel und keine Notiztexte werden ausgegeben. Das ist wichtig, weil die Debug-ALX-Dateien im alten Originalprojekt persönliche Inhalte enthalten können.

Betroffene Dateien:

- `src/notizen_py_qt/legacy_validation.py`
- `scripts/validate_legacy_alx.py`
- `src/notizen_py_qt/__init__.py`

Neue Tests:

- `tests/test_legacy_validation_1014.py`

Intern geprüft, ohne Inhalte auszugeben:

- alte `unbenannt.alx`: Roundtrip OK,
- alte Debug-`test.alx`: 65 Knoten, Tiefe 3, 3 Desktop-Notizen, Roundtrip OK.

Die große Debug-Datei wurde bewusst **nicht** ins Paket übernommen.

## 5. RTF-Codepage-Parität

Notizen.NET nutzte WinForms RichTextBox. Alte RTF-Fragmente können `\ansicpgNNNN` enthalten; hexadezimale RTF-Escapes wie `\'cf` müssen dann mit der angegebenen Windows-Codepage dekodiert werden, nicht pauschal mit `cp1252`.

0.10.14 ergänzt:

- `rtf_ansi_encoding(...)`,
- Codepage-Auswertung für Plaintext-Extraktion,
- Codepage-Auswertung für HTML-/Content-Parts-Brücke,
- Fallback auf `cp1252` bei fehlender oder ungültiger Codepage.

Damit werden zum Beispiel alte kyrillische RichTextBox-Fragmente mit `\ansicpg1251` in Suche, Statistik und Export nicht mehr zu Ersatzzeichen oder falschen Latin-1-Zeichen.

Betroffene Datei:

- `src/notizen_py_qt/rtf_utils.py`

Neuer Test:

- `tests/test_rtf_codepage_1014.py`

## 6. API/Paket

- Version auf `0.10.14` gesetzt.
- Neue öffentliche API-Exporte:
  - `LegacyAlxSummary`,
  - `LegacyAlxRoundtripResult`,
  - `summarize_document(...)`,
  - `summarize_alx_bytes(...)`,
  - `summarize_alx_file(...)`,
  - `validate_alx_roundtrip_bytes(...)`,
  - `validate_alx_roundtrip_file(...)`,
  - `rtf_ansi_encoding(...)`.

## Noch offen nach 0.10.14

Weiter offen bleiben vor allem:

- Bestätigung des sichtbaren Starts auf dem Nutzer-GNOME-System,
- echte verschlüsselte alte `.alx` mit bekanntem Passwort als Fixture oder externer Test,
- vollständige WinForms-artige Desktop-Notiz-Paint-/Resize-Logik,
- noch komplexere RTF-Fidelity mit echten Altdateien,
- FTP-Realtest,
- Installer/AppImage/venv-Paketierung.

0.10.14 schließt damit gezielt den Audit-Block „echte alte ALX-Dateien prüfen und Roundtrip-Verluste vermeiden“ weiter, ohne die sichtbare GNOME-Startstrategie wieder umzubauen.
