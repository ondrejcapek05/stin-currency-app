"""Testy pro app/translations.py."""
from app.translations import TRANSLATIONS, t


def test_t_returns_translation_for_known_key() -> None:
    """Test překladu existujícího klíče."""
    assert t("app.title") == "Přehled měnových kurzů"


def test_t_returns_key_as_fallback_for_unknown_key() -> None:
    """Test fallbacku na klíč."""
    assert t("does.not.exist") == "does.not.exist"


def test_t_returns_key_as_fallback_for_unknown_language() -> None:
    """Test fallbacku na klíč pro neznámý jazyk."""
    assert t("app.title", lang="xx") == "app.title"


def test_translations_has_cs_dict_with_expected_keys() -> None:
    """Test hlavních českých překladů."""
    cs = TRANSLATIONS["cs"]

    for key in (
        "app.title",
        "login.title",
        "dashboard.title",
        "dashboard.average",
        "dashboard.fallback_warning",
        "settings.title",
        "settings.language",
        "settings.error_invalid_base",
        "settings.error_invalid_language",
        "error.title",
    ):
        assert key in cs


def test_t_returns_english_for_known_key() -> None:
    """Test překladu existujícího anglického klíče."""
    assert t("app.title", "en") == "Currency Analyzer"


def test_t_returns_english_for_settings_keys() -> None:
    """Test anglických překladů nastavení."""
    assert t("settings.title", "en") == "Settings"
    assert t("settings.language", "en") == "Language"


def test_translations_has_en_dict_with_all_cs_keys() -> None:
    """Test kompletnosti anglických překladů vůči českým."""
    cs_keys = set(TRANSLATIONS["cs"].keys())
    en_keys = set(TRANSLATIONS["en"].keys())

    assert cs_keys == en_keys, (
        f"missing in en: {cs_keys - en_keys}, "
        f"missing in cs: {en_keys - cs_keys}"
    )