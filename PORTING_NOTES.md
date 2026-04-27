# Porting Notes

## Ausgangsprojekt

Das Archiv enthielt ein VB.NET/WinForms-Projekt. Die zentrale Datei war `Notizen.vb`; der Inhalt der einzelnen Notizen lag in `TreeNode.Tag.text` als `RichTextBox.Rtf`. Gespeichert wurde in `.alx`-Dateien.

## `.alx`-Format

Das moderne Notizen.NET-Format ist:

1. XML-Wurzel `<notizen-alx2>`
2. Verschachtelte `<Notiz>`-Elemente
3. Attribute wie `name`, `isexpanded`, Farben und Sticky-Window-Metadaten
4. Elementtext enthält RTF
5. Gesamtes XML wird als UTF-16 serialisiert
6. Bytes werden per GZip komprimiert
7. Optional wird der GZip-Payload historisch verschlüsselt

## Historische Verschlüsselung

Die alte Anwendung nutzt keine normale 3DES-Implementierung, sondern drei hintereinandergeschaltete `DESCryptoServiceProvider`-Streams. Jeder Layer hat eigenen CBC-Status und eigene PKCS#7-Padding-Phase.

Passwortlogik:

- Passwort auf 24 Zeichen auffüllen oder abschneiden
- Key/IV 1: Zeichen `0..7`
- Key/IV 2: Zeichen `7..14`
- Key/IV 3: Zeichen `15..22`
- Zeichen 23 bleibt effektiv unbenutzt
- ASCII-Passwörter wie in der alten Implementierung

Schreibreihenfolge:

```text
DES1(DES2(DES3(GZip(XML))))
```

Lesereihenfolge:

```text
DES1 decrypt -> DES2 decrypt -> DES3 decrypt -> GZip decompress
```

Der Port implementiert DES/CBC pure Python, damit der Kern ohne externe Kryptobibliothek unter PyPy läuft.

## Slint/PyPy-Entscheidung

Die Slint-Oberfläche ist bewusst von Kern und CLI getrennt. Der Kern importiert Slint nicht. Dadurch bleiben Dateiverarbeitung und Tests lauffähig, selbst wenn Slints native Python-Integration auf einer PyPy-Plattform nicht gebaut werden kann.

## RTF-Kompromiss

WinForms `RichTextBox` kann echtes RTF editieren. Slints Standard-`TextEdit` editiert Plain-Text. Deshalb:

- Beim Anzeigen wird RTF best-effort in Text gewandelt.
- Solange eine Notiz nicht verändert wird, bleibt ihr originaler RTF-String im Modell erhalten.
- Beim Bearbeiten wird der neue Text als einfaches RTF gespeichert.

Das ist für Notizen sinnvoll, aber nicht identisch mit dem alten RichTextBox-Verhalten bei Bildern, Tabellen, mehreren Fonts usw.
