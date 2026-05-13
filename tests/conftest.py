"""Společná konfigurace pro pytest testy."""
import os

# Nastavení testovací databáze
os.environ["DATABASE_URL"] = "sqlite://"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import Settings


@pytest.fixture
def fake_settings() -> Settings:
    """Testovací nastavení aplikace."""
    settings = Settings()
    settings.api_key = "test-key-for-mocks"
    settings.api_base_url = "https://api.exchangerate.host"
    settings.admin_username = "admin"
    settings.admin_password = "stin2026"
    settings.session_secret = "test-session-secret"
    return settings


@pytest.fixture
def db_engine() -> Engine:
    """Vytvoří testovací databázový engine."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """Vrátí testovací databázovou session."""
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def client(
    db_engine: Engine,
    fake_settings: Settings,
) -> Generator[TestClient, None, None]:
    """Vrátí testovacího klienta aplikace."""
    from app.config import get_settings
    from app.main import app, get_db_session

    def _override_session() -> Generator[Session, None, None]:
        with Session(db_engine) as session:
            yield session

    def _override_settings() -> Settings:
        return fake_settings

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_settings] = _override_settings

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
def auth_client(client: TestClient, fake_settings: Settings) -> TestClient:
    """Vrátí testovacího klienta přihlášeného jako admin."""
    response = client.post(
        "/login",
        data={
            "username": fake_settings.admin_username,
            "password": fake_settings.admin_password,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    return client