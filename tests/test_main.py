"""Testy pro main.py a login."""
from fastapi.testclient import TestClient

from app.config import Settings


def test_read_root(client: TestClient):
    """Test úvodního endpointu."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check(client: TestClient):
    """Test health endpointu."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_with_valid_credentials_returns_200(
    client: TestClient, fake_settings: Settings
):
    """Test přihlášení se správnými údaji."""
    response = client.post(
        "/login",
        data={
            "username": fake_settings.admin_username,
            "password": fake_settings.admin_password,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "logged_in"}


def test_login_with_invalid_credentials_returns_401(client: TestClient):
    """Test přihlášení se špatnými údaji."""
    response = client.post(
        "/login",
        data={"username": "hacker", "password": "nope"},
    )
    assert response.status_code == 401


def test_login_with_missing_password_returns_422(client: TestClient):
    """Test přihlášení bez hesla."""
    response = client.post("/login", data={"username": "admin"})
    assert response.status_code == 422


def test_logout_clears_session(client: TestClient, fake_settings: Settings):
    """Test odhlášení uživatele."""
    client.post(
        "/login",
        data={
            "username": fake_settings.admin_username,
            "password": fake_settings.admin_password,
        },
    )
    logout_response = client.post("/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "logged_out"}
 
    protected = client.get("/protected")
    assert protected.status_code == 401


def test_protected_without_session_returns_401(client: TestClient):
    """Test chráněného endpointu bez přihlášení."""
    response = client.get("/protected")
    assert response.status_code == 401


def test_protected_with_session_returns_user(
    auth_client: TestClient, fake_settings: Settings
):
    """Test chráněného endpointu s přihlášením."""
    response = auth_client.get("/protected")
    assert response.status_code == 200
    assert response.json() == {"user": fake_settings.admin_username}


def test_root_remains_public(client: TestClient):
    """Test veřejného root endpointu."""
    response = client.get("/")
    assert response.status_code == 200


def test_health_remains_public(client: TestClient):
    """Test veřejného health endpointu."""
    response = client.get("/health")
    assert response.status_code == 200