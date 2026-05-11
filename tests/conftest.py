"""Společná konfigurace pro pytest testy."""
import os

# Nastavení testovací databáze
os.environ["DATABASE_URL"] = "sqlite://"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
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


@pytest.fixture
def client() -> TestClient:
    """Vrátí testovacího klienta aplikace."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_client(client: TestClient, fake_settings: Settings) -> TestClient:
    """Vrátí testovacího klienta přihlášeného jako admin."""
    response = client.post(
        "/login",
        data={
            "username": fake_settings.admin_username,
            "password": fake_settings.admin_password,
        },
    )
    assert response.status_code == 200
    return client