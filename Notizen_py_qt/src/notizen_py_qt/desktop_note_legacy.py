from __future__ import annotations


def legacy_opacity_percent_for_transparency_percent(transparency_percent: int | str | None) -> int:
    """Convert the old transparency menu value to a Qt opacity percentage.

    ``desknote_kontext_opacy.vb`` labels the entries as transparency values:
    ``90 %`` means very transparent and maps to window opacity ``0.1``;
    ``0 %`` means fully opaque and maps to opacity ``1.0``.
    """

    try:
        transparency = int(transparency_percent) if transparency_percent is not None else 0
    except (TypeError, ValueError):
        transparency = 0
    transparency = max(0, min(90, transparency))
    return max(10, min(100, 100 - transparency))


def legacy_transparency_menu_options() -> tuple[tuple[str, int], ...]:
    """Return ``(label, opacity_percent)`` pairs from the WinForms desk note menu."""

    return tuple(
        (f"{transparency} %", legacy_opacity_percent_for_transparency_percent(transparency))
        for transparency in range(90, -1, -10)
    )
