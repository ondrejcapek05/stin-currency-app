"""Testy pro app/auth.py."""
from app.auth import verify_credentials
from app.config import Settings


def _make_settings(username: str = "admin", password: str = "stin2026") -> Settings:
    """Vytvoří testovací nastavení."""
    settings = Settings()
    settings.admin_username = username
    settings.admin_password = password
    return settings


def test_verify_credentials_accepts_valid():
    """Test správných údajů."""
    settings = _make_settings("admin", "stin2026")

    assert verify_credentials("admin", "stin2026", settings) is True


def test_verify_credentials_rejects_wrong_password():
    """Test špatného hesla."""
    settings = _make_settings("admin", "stin2026")

    assert verify_credentials("admin", "wrong", settings) is False


def test_verify_credentials_rejects_wrong_username():
    """Test špatného jména."""
    settings = _make_settings("admin", "stin2026")

    assert verify_credentials("hacker", "stin2026", settings) is False


def test_verify_credentials_rejects_both_wrong():
    """Test špatného jména i hesla."""
    settings = _make_settings("admin", "stin2026")

    assert verify_credentials("hacker", "wrong", settings) is False