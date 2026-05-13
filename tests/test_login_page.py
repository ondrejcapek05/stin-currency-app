"""Testy pro app/templates/login.html."""
from fastapi.testclient import TestClient

from app.config import Settings


def test_login_get_renders_form(client: TestClient) -> None:
    """Test zobrazení formuláře."""
    response = client.get("/login")

    assert response.status_code == 200
    assert "<form" in response.text
    assert 'name="username"' in response.text
    assert 'name="password"' in response.text


def test_login_post_redirects_to_dashboard_on_success(
    client: TestClient,
    fake_settings: Settings,
) -> None:
    """Test přesměrování po přihlášení."""
    response = client.post(
        "/login",
        data={
            "username": fake_settings.admin_username,
            "password": fake_settings.admin_password,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


def test_login_post_renders_error_on_invalid(client: TestClient) -> None:
    """Test chybové hlášky."""
    response = client.post(
        "/login",
        data={
            "username": "hacker",
            "password": "wrong",
        },
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert "Neplatné přihlašovací údaje" in response.text


def test_root_redirects_to_login_when_not_authenticated(
    client: TestClient,
) -> None:
    """Test přesměrování rootu bez přihlášení."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_root_redirects_to_dashboard_when_authenticated(
    auth_client: TestClient,
) -> None:
    """Test přesměrování rootu po přihlášení."""
    response = auth_client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"