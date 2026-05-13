"""Modely pro databázové tabulky."""
from datetime import date, datetime, timezone

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class UserSettings(SQLModel, table=True):
    """Uživatelské nastavení."""

    id: int | None = Field(default=1, primary_key=True)
    base_currency: str = Field(default="EUR")
    selected_currencies: str = Field(default="USD,CZK,GBP")
    language: str = Field(default="cs")


class ExchangeRate(SQLModel, table=True):
    """Uložený kurz měny."""

    __table_args__ = (
        Index("ix_rate_base_target_date", "base", "target", "date"),
    )

    id: int | None = Field(default=None, primary_key=True)
    base: str
    target: str
    date: date
    rate: float
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class LogEntry(SQLModel, table=True):
    """Log událostí aplikace."""

    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    level: str
    message: str