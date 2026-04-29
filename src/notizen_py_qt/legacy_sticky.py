from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LegacyOpacityChoice:
    index: int
    label: str
    opacity: float
    transparency_percent: int

    def as_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "label": self.label,
            "opacity": self.opacity,
            "transparency_percent": self.transparency_percent,
        }


# Port of desknote_kontext_opacy.vb: the menu labels describe transparency
# (90 %, 80 %, ... 0 %), while WinForms Form.Opacity stores the visible opacity.
LEGACY_OPACITY_CHOICES: tuple[LegacyOpacityChoice, ...] = tuple(
    LegacyOpacityChoice(index=i, label=f"{90 - i * 10} %", opacity=round((i + 1) / 10, 1), transparency_percent=90 - i * 10)
    for i in range(10)
)


def legacy_opacity_choices() -> list[LegacyOpacityChoice]:
    return list(LEGACY_OPACITY_CHOICES)


def opacity_from_legacy_choice(value: str | int | float) -> float:
    text = str(value).strip().lower().replace("transparenz", "").strip()
    has_percent = text.endswith("%")
    if has_percent:
        text = text[:-1].strip()
    if text.isdigit():
        number = int(text)
        if has_percent:
            for choice in LEGACY_OPACITY_CHOICES:
                if choice.transparency_percent == number:
                    return choice.opacity
        elif 0 <= number <= 9:
            return LEGACY_OPACITY_CHOICES[number].opacity
        else:
            for choice in LEGACY_OPACITY_CHOICES:
                if choice.transparency_percent == number:
                    return choice.opacity
    try:
        number_f = float(text.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"Unbekannte alte Sticky-Transparenz: {value}") from exc
    if 0.0 <= number_f <= 1.0:
        return max(0.0, min(1.0, number_f))
    raise ValueError(f"Unbekannte alte Sticky-Transparenz: {value}")
