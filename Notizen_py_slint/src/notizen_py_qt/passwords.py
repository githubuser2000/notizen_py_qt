from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from .des_compat import normalize_password, is_blank_password


@dataclass(slots=True, frozen=True)
class LegacyPasswordInfo:
    """Compatibility view of the old Notizen.NET password dialogs.

    Notizen.NET did not use a password hash.  The dialog normalized user input to
    exactly 24 characters, the DES cascade used three overlapping 8 byte ASCII
    windows, and the 24th normalized character was never read by the cipher.
    Keeping this behavior visible helps migrations avoid surprising passwords.
    """

    original_length: int
    normalized_length: int
    normalized: str
    padded: bool
    truncated: bool
    blank: bool
    ascii_only: bool
    key1: str
    key2: str
    key3: str
    unused_char: str
    warning: str = ""

    def as_dict(self, *, reveal: bool = False) -> dict[str, object]:
        payload = asdict(self)
        if not reveal:
            payload["normalized"] = _mask(self.normalized)
            payload["key1"] = _mask(self.key1)
            payload["key2"] = _mask(self.key2)
            payload["key3"] = _mask(self.key3)
            payload["unused_char"] = _mask(self.unused_char)
        return payload

    def to_json(self, *, reveal: bool = False) -> str:
        return json.dumps(self.as_dict(reveal=reveal), indent=2, ensure_ascii=False)

    def format(self, *, reveal: bool = False) -> str:
        value = self.as_dict(reveal=reveal)
        lines = [
            f"Original-Länge: {value['original_length']}",
            f"Normalisiert: {value['normalized']} ({value['normalized_length']} Zeichen)",
            f"Aufgefüllt: {'ja' if value['padded'] else 'nein'}; gekürzt: {'ja' if value['truncated'] else 'nein'}; leer: {'ja' if value['blank'] else 'nein'}",
            f"ASCII-kompatibel: {'ja' if value['ascii_only'] else 'nein'}",
            f"DES-1 Schlüssel/IV: {value['key1']}",
            f"DES-2 Schlüssel/IV: {value['key2']}  (beginnt wie im Original bei Zeichen 8/Index 7)",
            f"DES-3 Schlüssel/IV: {value['key3']}",
            f"Ungenutztes Zeichen 24: {value['unused_char']}",
        ]
        if self.warning:
            lines.append("Warnung: " + self.warning)
        elif not reveal:
            lines.append("Hinweis: Werte sind maskiert. Mit --reveal werden sie angezeigt.")
        return "\n".join(lines)


def legacy_password_info(password: str | None) -> LegacyPasswordInfo:
    original = password or ""
    normalized = normalize_password(password)
    ascii_only = True
    warning = ""
    try:
        normalized.encode("ascii")
    except UnicodeEncodeError:
        ascii_only = False
        warning = "Die alte DES-Verschlüsselung akzeptiert nur ASCII-Zeichen. Nicht-ASCII-Passwörter können alte Dateien nicht kompatibel öffnen."
    if len(original) > 24:
        warning = warning or "Das alte Dialogfeld akzeptierte höchstens 24 Zeichen; zusätzliche Zeichen werden abgeschnitten."
    elif len(original) < 24 and original:
        warning = warning or "Das alte Dialogfeld füllt Passwörter rechts mit Leerzeichen auf 24 Zeichen auf."
    elif not original:
        warning = warning or "Ein leeres Passwort wird als 24 Leerzeichen behandelt und bedeutet unverschlüsselt speichern."
    return LegacyPasswordInfo(
        original_length=len(original),
        normalized_length=len(normalized),
        normalized=normalized,
        padded=len(original) < 24,
        truncated=len(original) > 24,
        blank=is_blank_password(password),
        ascii_only=ascii_only,
        key1=normalized[0:8],
        key2=normalized[7:15],
        key3=normalized[15:23],
        unused_char=normalized[23],
        warning=warning,
    )


def normalize_legacy_password(password: str | None) -> str:
    return normalize_password(password)


def _mask(value: str) -> str:
    if value == "":
        return ""
    return "·" * len(value)
