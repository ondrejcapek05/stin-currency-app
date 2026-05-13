"""Testy pro app/main.py."""
from fastapi.testclient import TestClient


def test_read_root_redirects_to_login(client: TestClient) -> None:
    """Test přesměrování rootu na login."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_health_check(client: TestClient) -> None:
    """Test kontroly stavu aplikace."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_with_missing_password_returns_422(client: TestClient) -> None:
    """Test přihlášení bez hesla."""
    response = client.post("/login", data={"username": "admin"})
    assert response.status_code == 422