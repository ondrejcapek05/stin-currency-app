"""Testy pro app/logger.py."""
from sqlmodel import Session, select

from app.logger import log_error
from app.models import LogEntry


def test_log_error_saves_entry_with_error_level(db_session: Session) -> None:
    """Test uložení chyby do databáze."""
    log_error(db_session, "API down")

    rows = db_session.exec(select(LogEntry)).all()
    assert len(rows) == 1
    assert rows[0].level == "ERROR"
    assert rows[0].message == "API down"


def test_log_error_returns_persisted_entry(db_session: Session) -> None:
    """Test návratové hodnoty s id a timestampem."""
    entry = log_error(db_session, "Connection refused")

    assert entry.id is not None
    assert entry.timestamp is not None


def test_log_error_multiple_entries(db_session: Session) -> None:
    """Test více chyb v databázi."""
    log_error(db_session, "first")
    log_error(db_session, "second")
    log_error(db_session, "third")

    rows = db_session.exec(select(LogEntry)).all()
    assert len(rows) == 3
    assert {row.message for row in rows} == {"first", "second", "third"}