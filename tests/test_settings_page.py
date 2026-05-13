"""Testy pro app/templates/settings.html."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import UserSettings


def test_settings_get_renders_form(auth_client: TestClient) -> None:
    """Test zobrazení formuláře."""
    response = auth_client.get("/settings")

    assert response.status_code == 200
    assert "<form" in response.text
    assert 'name="base_currency"' in response.text
    assert 'name="selected_currencies"' in response.text
    assert 'name="language"' in response.text


def test_settings_get_requires_login(client: TestClient) -> None:
    """Test, že settings vyžaduje přihlášení."""
    response = client.get("/settings", follow_redirects=False)

    assert response.status_code == 401


def test_settings_post_updates_db(
    auth_client: TestClient,
    db_session: Session,
) -> None:
    """Test uložení nastavení do databáze."""
    db_session.add(UserSettings())
    db_session.commit()

    response = auth_client.post(
        "/settings",
        data={
            "base_currency": "CZK",
            "selected_currencies": ["USD", "EUR"],
            "language": "cs",
        },
    )

    assert response.status_code == 200
    assert "Nastavení uloženo" in response.text

    db_session.expire_all()
    loaded = db_session.get(UserSettings, 1)

    assert loaded is not None
    assert loaded.base_currency == "CZK"
    assert loaded.selected_currencies == "USD,EUR"


def test_settings_post_rejects_base_not_in_available(
    auth_client: TestClient,
) -> None:
    """Test chyby při neplatné základní měně."""
    response = auth_client.post(
        "/settings",
        data={
            "base_currency": "XXX",
            "selected_currencies": ["USD", "EUR"],
            "language": "cs",
        },
    )

    assert response.status_code == 400
    assert "Neplatná základní měna" in response.text


def test_settings_post_rejects_currency_not_in_available(
    auth_client: TestClient,
) -> None:
    """Test chyby při neplatné vybrané měně."""
    response = auth_client.post(
        "/settings",
        data={
            "base_currency": "USD",
            "selected_currencies": ["EUR", "XXX"],
            "language": "cs",
        },
    )

    assert response.status_code == 400
    assert "Neplatná měna ve výběru" in response.text


def test_settings_post_requires_at_least_one_currency(
    auth_client: TestClient,
) -> None:
    """Test chyby při nevybrané měně."""
    response = auth_client.post(
        "/settings",
        data={"base_currency": "USD", "language": "cs"},
    )

    assert response.status_code == 400
    assert "Vyberte alespoň jednu měnu" in response.text
    assert "jinou než základní" not in response.text


def test_settings_post_requires_currency_other_than_base(
    auth_client: TestClient,
) -> None:
    """Test chyby při výběru pouze základní měny."""
    response = auth_client.post(
        "/settings",
        data={
            "base_currency": "USD",
            "selected_currencies": ["USD"],
            "language": "cs",
        },
    )

    assert response.status_code == 400
    assert "Vyberte alespoň jednu měnu jinou než základní" in response.text


def test_settings_post_updates_language(
    auth_client: TestClient,
    db_session: Session,
) -> None:
    """Test změny jazyka přes formulář."""
    db_session.add(UserSettings())
    db_session.commit()

    response = auth_client.post(
        "/settings",
        data={
            "base_currency": "USD",
            "selected_currencies": ["EUR"],
            "language": "en",
        },
    )

    assert response.status_code == 200

    db_session.expire_all()
    loaded = db_session.get(UserSettings, 1)
    assert loaded is not None
    assert loaded.language == "en"


def test_settings_post_rejects_invalid_language(
    auth_client: TestClient,
) -> None:
    """Test chyby při neplatném jazyku."""
    response = auth_client.post(
        "/settings",
        data={
            "base_currency": "USD",
            "selected_currencies": ["EUR"],
            "language": "xx",
        },
    )

    assert response.status_code == 400
    assert "Neplatný jazyk" in response.text


def test_settings_get_renders_english_when_user_lang_en(
    auth_client: TestClient,
    db_session: Session,
) -> None:
    """Test anglického vykreslení nastavení."""
    db_session.add(UserSettings(language="en"))
    db_session.commit()

    response = auth_client.get("/settings")

    assert response.status_code == 200
    assert "Settings" in response.text
    assert "Language" in response.text
    assert "Nastavení" not in response.text