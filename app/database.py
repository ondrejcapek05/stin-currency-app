"""Databáze aplikace."""
import os
from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app import models  # načte databázové modely

DEFAULT_DB_URL = "sqlite:///./app.db"

_engine: Engine | None = None


def make_engine(database_url: str | None = None) -> Engine:
    """Vytvoří databázový engine."""
    url = database_url or os.getenv("DATABASE_URL") or DEFAULT_DB_URL
    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args)


def get_engine() -> Engine:
    """Vrátí databázový engine."""
    global _engine
    if _engine is None:
        _engine = make_engine()
    return _engine


def init_db(engine: Engine | None = None) -> None:
    """Vytvoří databázové tabulky."""
    SQLModel.metadata.create_all(engine or get_engine())


def get_session(engine: Engine | None = None) -> Generator[Session, None, None]:
    """Vrátí databázovou session."""
    actual_engine = engine or get_engine()
    with Session(actual_engine) as session:
        yield session