"""Testy pro app/templates/dashboard.html."""
from collections.abc import Callable, Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app, get_rate_service
from app.models import UserSettings


class FakeService:
    """Fake RateService pro dashboard testy."""

    def __init__(
        self,
        live_rates: dict[str, float],
        period_rates: dict[date, dict[str, float]],
    ) -> None:
        self.live_rates = live_rates
        self.period_rates = period_rates

    def get_live_rates(self, symbols: list[str]) -> dict[str, float]:
        """Vrátí fake aktuální kurzy."""
        return self.live_rates

    def get_rates_for_period(
        self,
        start: date,
        end: date,
        symbols: list[str],
    ) -> dict[date, dict[str, float]]:
        """Vrátí fake historické kurzy."""
        return self.period_rates


@pytest.fixture
def override_rate_service() -> Generator[
    Callable[
        [dict[str, float], dict[date, dict[str, float]]],
        None,
    ],
    None,
    None,
]:
    """Nahradí RateService fake službou."""
    def _override(
        live_rates: dict[str, float],
        period_rates: dict[date, dict[str, float]],
    ) -> None:
        app.dependency_overrides[get_rate_service] = lambda: FakeService(
            live_rates,
            period_rates,
        )

    yield _override
    app.dependency_overrides.pop(get_rate_service, None)


def _seed_settings(
    db_session: Session,
    base: str = "USD",
    selected: str = "EUR,CZK,GBP",
) -> None:
    """Vloží testovací nastavení."""
    db_session.add(UserSettings(base_currency=base, selected_currencies=selected))
    db_session.commit()


def _period_rates(symbols: list[str], days: int) -> dict[date, dict[str, float]]:
    """Vrátí fake historické kurzy."""
    today = date.today()
    return {
        today - timedelta(days=i): {symbol: 1.0 + i * 0.01 for symbol in symbols}
        for i in range(days)
    }


def test_dashboard_requires_login(client: TestClient) -> None:
    """Test, že dashboard vyžaduje přihlášení."""
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 401


def test_dashboard_renders_navigation(
    auth_client: TestClient,
    db_session: Session,
    override_rate_service: Callable[
        [dict[str, float], dict[date, dict[str, float]]],
        None,
    ],
) -> None:
    """Test zobrazení navigace z base šablony."""
    _seed_settings(db_session, base="USD", selected="EUR")
    live = {"EUR": 0.9}
    period = _period_rates(["EUR"], 7)
    override_rate_service(live, period)

    response = auth_client.get("/dashboard")

    assert response.status_code == 200
    assert "Přehled" in response.text
    assert "Nastavení" in response.text
    assert "Odhlásit" in response.text


def test_dashboard_renders_live_rates(
    auth_client: TestClient,
    db_session: Session,
    override_rate_service: Callable[
        [dict[str, float], dict[date, dict[str, float]]],
        None,
    ],
) -> None:
    """Test zobrazení aktuálních kurzů."""
    _seed_settings(db_session, base="USD", selected="EUR,CZK")
    live = {"EUR": 0.9, "CZK": 24.0}
    period = _period_rates(["EUR"], 7)
    override_rate_service(live, period)

    response = auth_client.get("/dashboard")

    assert response.status_code == 200
    assert "EUR" in response.text
    assert "CZK" in response.text
    assert "0.9000" in response.text
    assert "24.0000" in response.text


def test_dashboard_renders_strongest_weakest(
    auth_client: TestClient,
    db_session: Session,
    override_rate_service: Callable[
        [dict[str, float], dict[date, dict[str, float]]],
        None,
    ],
) -> None:
    """Test zobrazení nejsilnější a nejslabší měny."""
    _seed_settings(db_session, base="USD", selected="EUR,CZK")
    live = {"EUR": 0.9, "CZK": 24.0}
    period = _period_rates(["EUR"], 7)
    override_rate_service(live, period)

    response = auth_client.get("/dashboard")

    assert response.status_code == 200
    assert "Nejsilnější měna" in response.text
    assert "Nejslabší měna" in response.text
    assert "<h2>EUR</h2>" in response.text
    assert "<h2>CZK</h2>" in response.text


def test_dashboard_renders_average(
    auth_client: TestClient,
    db_session: Session,
    override_rate_service: Callable[
        [dict[str, float], dict[date, dict[str, float]]],
        None,
    ],
) -> None:
    """Test zobrazení průměru za období."""
    _seed_settings(db_session, base="USD", selected="EUR")
    live = {"EUR": 0.9}
    today = date.today()
    period = {
        today - timedelta(days=i): {"EUR": 1.0 + i * 0.01}
        for i in range(7)
    }
    override_rate_service(live, period)

    response = auth_client.get("/dashboard")

    assert response.status_code == 200
    assert "Průměr za období" in response.text
    assert "1.0300" in response.text


def test_dashboard_default_period_is_7(
    auth_client: TestClient,
    db_session: Session,
    override_rate_service: Callable[
        [dict[str, float], dict[date, dict[str, float]]],
        None,
    ],
) -> None:
    """Test výchozí periody 7 dní."""
    _seed_settings(db_session, base="USD", selected="EUR")
    live = {"EUR": 0.9}
    period = _period_rates(["EUR"], 7)
    override_rate_service(live, period)

    response = auth_client.get("/dashboard")

    assert response.status_code == 200

    today = date.today()
    expected_dates = [(today - timedelta(days=i)).isoformat() for i in range(7)]
    for expected_date in expected_dates:
        assert expected_date in response.text


def test_dashboard_with_period_30(
    auth_client: TestClient,
    db_session: Session,
    override_rate_service: Callable[
        [dict[str, float], dict[date, dict[str, float]]],
        None,
    ],
) -> None:
    """Test periody 30 dní."""
    _seed_settings(db_session, base="USD", selected="EUR")
    live = {"EUR": 0.9}
    period = _period_rates(["EUR"], 30)
    override_rate_service(live, period)

    response = auth_client.get("/dashboard?period=30")

    assert response.status_code == 200

    oldest = (date.today() - timedelta(days=29)).isoformat()
    assert oldest in response.text


def test_dashboard_chart_symbol_default_is_strongest(
    auth_client: TestClient,
    db_session: Session,
    override_rate_service: Callable[
        [dict[str, float], dict[date, dict[str, float]]],
        None,
    ],
) -> None:
    """Test výchozího symbolu grafu."""
    _seed_settings(db_session, base="USD", selected="EUR,CZK")
    live = {"EUR": 0.9, "CZK": 24.0}
    period = _period_rates(["EUR", "CZK"], 7)
    override_rate_service(live, period)

    response = auth_client.get("/dashboard")

    assert response.status_code == 200
    assert "label: 'EUR'" in response.text


def test_dashboard_handles_usd_in_selected_with_non_usd_base(
    auth_client: TestClient,
    db_session: Session,
    override_rate_service: Callable[
        [dict[str, float], dict[date, dict[str, float]]],
        None,
    ],
) -> None:
    """Test zobrazení USD při jiné základní měně."""
    _seed_settings(db_session, base="EUR", selected="USD,CZK")

    live = {"CZK": 24.0, "EUR": 0.9}
    period = {
        date.today() - timedelta(days=i): {
            "CZK": 24.0 + i,
            "EUR": 0.9 + i * 0.01,
        }
        for i in range(7)
    }
    override_rate_service(live, period)

    response = auth_client.get("/dashboard")

    assert response.status_code == 200
    assert "USD" in response.text
    assert "CZK" in response.text