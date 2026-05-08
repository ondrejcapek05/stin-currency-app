"""Základní testy pro main.py."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_read_root():
    """Test, že root endpoint vrací správnou zprávu."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test, že health endpoint vrací 'ok'."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}