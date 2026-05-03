from __future__ import annotations

from notizen_py_qt.i18n import (
    LEGACY_LANGUAGE_KEY_ORDER,
    TRANSLATIONS,
    legacy_language_key_for_index,
    legacy_language_translations,
    resolve_language,
    tr,
)


def test_all_legacy_languages_use_semantic_keys_not_generated_fallbacks() -> None:
    expected = set(LEGACY_LANGUAGE_KEY_ORDER)
    assert len(LEGACY_LANGUAGE_KEY_ORDER) == 118
    assert legacy_language_key_for_index(0) == "Strip1_1"
    assert legacy_language_key_for_index(117) == "scroll"
    assert legacy_language_key_for_index(999) is None
    for language, mapping in TRANSLATIONS.items():
        assert set(mapping) == expected, language
        assert not any(key.startswith("key_") for key in mapping), language


def test_french_spanish_and_russian_are_positionally_ported_from_languages_vb() -> None:
    assert tr("french", "Strip1_2") == "Nouveau fichier Ctrl + N"
    assert tr("français", "pass1") == "ancien mot de passe"
    assert tr("spanish", "Strip1_7") == "Configuración"
    assert tr("es", "kontext11") == "nuevo siguiente [Enter]"
    assert tr("russian", "Strip1_7") == "Настройки"
    assert tr("ru", "suche5") == "Результат:"


def test_legacy_language_array_order_is_available_for_old_index_based_ui_code() -> None:
    french = legacy_language_translations("french")
    spanish = legacy_language_translations("spanish")
    russian = legacy_language_translations("russian")
    assert french[0] == "Menu"
    assert french[1] == "Nouveau fichier Ctrl + N"
    assert spanish[28] == "ok"
    # The active Russian block in languages.vb contains this original string at
    # the desktop-note menu position; preserving it keeps the old array behavior
    # auditable even where the legacy translation quality is poor.
    assert russian[39] == "столе записки"


def test_language_aliases_keep_legacy_config_values() -> None:
    assert resolve_language("french") == "français"
    assert resolve_language("spanish") == "spanish"
    assert resolve_language("russian") == "russian"
    assert resolve_language("Chinese") == "Chinese"
