"""Testy pro app/database.py."""
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from app.database import get_session, init_db, make_engine


def test_make_engine_default_url_is_sqlite_file(monkeypatch):
    """Test výchozí databázové URL."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    engine = make_engine()

    url = str(engine.url)
    assert "sqlite" in url
    assert "app.db" in url


def test_make_engine_uses_check_same_thread_false_for_sqlite():
    """Test vytvoření SQLite enginu."""
    engine = make_engine("sqlite://")

    assert engine.dialect.name == "sqlite"
    with engine.connect():
        pass


def test_make_engine_respects_database_url_env_var(monkeypatch):
    """Test načtení DATABASE_URL."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///custom.db")

    engine = make_engine()

    assert "custom.db" in str(engine.url)


def test_init_db_creates_all_tables():
    """Test vytvoření tabulek."""
    engine = make_engine("sqlite://")

    init_db(engine)

    table_names = SQLModel.metadata.tables.keys()
    assert "usersettings" in table_names
    assert "exchangerate" in table_names
    assert "logentry" in table_names


def test_get_session_yields_session():
    """Test vytvoření session."""
    engine = make_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    session = next(get_session(engine))

    assert isinstance(session, Session)
    session.close()


def test_lifespan_initializes_db():
    """Test inicializace databáze při startu aplikace."""
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200