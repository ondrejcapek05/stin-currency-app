"""Logování chyb aplikace do databáze."""
from sqlmodel import Session

from app.models import LogEntry


def log_error(session: Session, message: str) -> LogEntry:
    """Uloží chybu do databáze."""
    entry = LogEntry(level="ERROR", message=message)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry