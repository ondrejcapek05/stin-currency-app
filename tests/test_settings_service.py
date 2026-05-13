"""Testy pro app/settings_service.py."""
from sqlmodel import Session

from app.models import UserSettings
from app.settings_service import get_or_create_settings, update_settings


def test_get_or_create_creates_default_when_missing(db_session: Session) -> None:
    """Test vytvoření defaultního nastavení."""
    settings = get_or_create_settings(db_session)

    assert settings.id == 1
    assert settings.base_currency == "EUR"
    assert settings.selected_currencies == "USD,CZK,GBP"


def test_get_or_create_returns_existing(db_session: Session) -> None:
    """Test načtení existujícího nastavení."""
    db_session.add(UserSettings(base_currency="CZK", selected_currencies="USD,EUR"))
    db_session.commit()

    settings = get_or_create_settings(db_session)

    assert settings.base_currency == "CZK"
    assert settings.selected_currencies == "USD,EUR"


def test_update_settings_changes_fields(db_session: Session) -> None:
    """Test aktualizace nastavení."""
    db_session.add(UserSettings())
    db_session.commit()

    updated = update_settings(db_session, "CZK", ["USD", "EUR", "GBP"])

    assert updated.base_currency == "CZK"
    assert updated.selected_currencies == "USD,EUR,GBP"


def test_update_settings_joins_currencies_as_csv(db_session: Session) -> None:
    """Test serializace měn jako CSV."""
    db_session.add(UserSettings())
    db_session.commit()

    updated = update_settings(db_session, "EUR", ["USD", "EUR"])

    assert updated.selected_currencies == "USD,EUR"


def test_update_settings_creates_if_missing(db_session: Session) -> None:
    """Test vytvoření nastavení při prázdné databázi."""
    updated = update_settings(db_session, "USD", ["EUR", "CZK"])

    assert updated.id == 1
    assert updated.base_currency == "USD"
    assert updated.selected_currencies == "EUR,CZK"