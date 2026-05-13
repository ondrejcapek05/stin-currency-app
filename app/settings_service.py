"""Servis pro uživatelské nastavení."""
from sqlmodel import Session

from app.models import UserSettings

AVAILABLE_CURRENCIES: list[str] = ["USD", "EUR", "CZK", "GBP", "JPY", "CHF", "AUD", "CAD"]


def get_or_create_settings(session: Session) -> UserSettings:
    """Vrátí nastavení, nebo vytvoří výchozí."""
    settings = session.get(UserSettings, 1)
    if settings is None:
        settings = UserSettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


def update_settings(
    session: Session,
    base_currency: str,
    selected_currencies: list[str],
) -> UserSettings:
    """Aktualizuje uživatelské nastavení."""
    settings = get_or_create_settings(session)
    settings.base_currency = base_currency
    settings.selected_currencies = ",".join(selected_currencies)
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings