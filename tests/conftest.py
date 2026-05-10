"""Společná konfigurace pro pytest testy."""
import os

# Nastavení testovací databáze
os.environ["DATABASE_URL"] = "sqlite://"

from collections.abc import Generator

import pytest
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel

from app.config import Settings
from app.database import make_engine


@pytest.fixture
def fake_settings() -> Settings:
    """Testovací nastavení s fake API klíčem a URL pro mocky."""
    settings = Settings()
    settings.api_key = "test-key-for-mocks"
    settings.api_base_url = "https://api.exchangerate.host"
    return settings


@pytest.fixture
def db_engine() -> Engine:
    """Vytvoří testovací databázový engine."""
    engine = make_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """Vrátí testovací databázovou session."""
    with Session(db_engine) as session:
        yield session