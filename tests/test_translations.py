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
        "settings.title",
        "settings.error_invalid_base",
    ):
        assert key in cs