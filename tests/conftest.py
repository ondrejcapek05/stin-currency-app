"""Společná konfigurace pro pytest testy."""
import pytest

from app.config import Settings


@pytest.fixture
def fake_settings() -> Settings:
    """Testovací nastavení s fake API klíčem a URL pro mocky."""
    settings = Settings()
    settings.api_key = "test-key-for-mocks"
    settings.api_base_url = "https://api.exchangerate.host"
    return settings