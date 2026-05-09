"""Testy pro app/config.py."""
import pytest

from app.config import Settings


def test_settings_loads_api_key_from_env(monkeypatch):
    """Test načítání API klíče."""
    monkeypatch.setenv("EXCHANGERATE_API_KEY", "my-test-key")

    settings = Settings()

    assert settings.api_key == "my-test-key"


def test_settings_default_base_url(monkeypatch):
    """Test výchozí API URL."""
    monkeypatch.delenv("EXCHANGERATE_API_URL", raising=False)

    settings = Settings()

    assert settings.api_base_url == "https://api.exchangerate.host"


def test_settings_custom_base_url(monkeypatch):
    """Test vlastní API URL."""
    monkeypatch.setenv("EXCHANGERATE_API_URL", "https://custom.example.com")

    settings = Settings()

    assert settings.api_base_url == "https://custom.example.com"


def test_validate_raises_when_api_key_missing(monkeypatch):
    """Test chybějícího API klíče."""
    monkeypatch.setenv("EXCHANGERATE_API_KEY", "")

    settings = Settings()

    with pytest.raises(ValueError, match="EXCHANGERATE_API_KEY"):
        settings.validate()


def test_validate_passes_when_api_key_present(monkeypatch):
    """Test správného API klíče."""
    monkeypatch.setenv("EXCHANGERATE_API_KEY", "some-key")

    settings = Settings()

    settings.validate()  # Nevyhodí výjimku