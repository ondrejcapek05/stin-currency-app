"""Testy pro app/models.py."""
from datetime import date, datetime, timezone

from sqlmodel import Session, select

from app.models import ExchangeRate, LogEntry, UserSettings


def test_user_settings_defaults():
    """Test výchozího nastavení uživatele."""
    settings = UserSettings()

    assert settings.id == 1
    assert settings.base_currency == "EUR"
    assert settings.selected_currencies == "USD,CZK,GBP"
    assert settings.language == "cs"


def test_user_settings_save_and_load(db_session: Session):
    """Test uložení a načtení nastavení uživatele."""
    settings = UserSettings(language="en")

    db_session.add(settings)
    db_session.commit()

    loaded = db_session.get(UserSettings, 1)
    assert loaded is not None
    assert loaded.language == "en"


def test_exchange_rate_save_and_load(db_session: Session):
    """Test uložení a načtení kurzu měny."""
    rate = ExchangeRate(
        base="USD",
        target="EUR",
        date=date(2025, 1, 1),
        rate=0.92,
    )

    db_session.add(rate)
    db_session.commit()

    rows = db_session.exec(select(ExchangeRate)).all()
    assert len(rows) == 1
    assert rows[0].base == "USD"
    assert rows[0].target == "EUR"
    assert rows[0].rate == 0.92


def test_exchange_rate_query_by_base_target_date(db_session: Session):
    """Test filtrování kurzu měny."""
    db_session.add(ExchangeRate(base="USD", target="EUR", date=date(2025, 1, 1), rate=0.92))
    db_session.add(ExchangeRate(base="USD", target="CZK", date=date(2025, 1, 1), rate=24.5))
    db_session.add(ExchangeRate(base="USD", target="EUR", date=date(2025, 1, 2), rate=0.93))
    db_session.commit()

    stmt = select(ExchangeRate).where(
        ExchangeRate.base == "USD",
        ExchangeRate.target == "EUR",
        ExchangeRate.date == date(2025, 1, 1),
    )
    result = db_session.exec(stmt).one()

    assert result.rate == 0.92


def test_log_entry_save_and_load(db_session: Session):
    """Test uložení a načtení logu."""
    entry = LogEntry(level="INFO", message="Test log")

    db_session.add(entry)
    db_session.commit()

    rows = db_session.exec(select(LogEntry)).all()
    assert len(rows) == 1
    assert rows[0].level == "INFO"
    assert rows[0].message == "Test log"


def test_log_entry_default_timestamp_is_recent():
    """Test výchozího času logu."""
    entry = LogEntry(level="INFO", message="x")

    delta = datetime.now(timezone.utc) - entry.timestamp
    assert delta.total_seconds() < 5