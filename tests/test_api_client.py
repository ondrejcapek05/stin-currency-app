"""Testy pro app/api_client.py."""
from datetime import date

import httpx
import pytest

from app.api_client import ExchangeRateClient
from app.config import Settings
from app.exceptions import ApiConnectionError, ApiResponseError


def make_client(
    fake_settings: Settings,
    handler,
) -> tuple[ExchangeRateClient, list[httpx.Request]]:
    """Vytvoří klienta s mockovaným HTTP transportem."""
    requests = []

    def wrapped_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    transport = httpx.MockTransport(wrapped_handler)
    http_client = httpx.Client(transport=transport)

    client = ExchangeRateClient(
        settings=fake_settings,
        http_client=http_client,
    )

    return client, requests


def test_get_live_rates_returns_quotes(fake_settings: Settings) -> None:
    """Test aktuálních kurzů."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": True,
                "timestamp": 1700000000,
                "source": "USD",
                "quotes": {"USDEUR": 0.92, "USDCZK": 24.5},
            },
        )

    client, _ = make_client(fake_settings, handler)

    result = client.get_live_rates(symbols=["EUR", "CZK"])

    assert result == {"USDEUR": 0.92, "USDCZK": 24.5}


def test_get_live_rates_passes_symbols_as_csv(fake_settings: Settings) -> None:
    """Test předání měn do URL."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": True, "quotes": {}},
        )

    client, requests = make_client(fake_settings, handler)

    client.get_live_rates(symbols=["EUR", "CZK", "GBP"])

    request_url = str(requests[0].url)
    assert "symbols=EUR%2CCZK%2CGBP" in request_url


def test_get_live_rates_without_symbols(fake_settings: Settings) -> None:
    """Test požadavku bez zadaných měn."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": True, "quotes": {"USDEUR": 0.92}},
        )

    client, requests = make_client(fake_settings, handler)

    result = client.get_live_rates()

    assert result == {"USDEUR": 0.92}
    request_url = str(requests[0].url)
    assert "symbols" not in request_url


def test_get_live_rates_includes_access_key(fake_settings: Settings) -> None:
    """Test předání API klíče v URL."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": True, "quotes": {}},
        )

    client, requests = make_client(fake_settings, handler)

    client.get_live_rates()

    request_url = str(requests[0].url)
    assert "access_key=test-key-for-mocks" in request_url


def test_get_timeframe_rates_returns_quotes(fake_settings: Settings) -> None:
    """Test kurzu v časovém rozsahu."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": True,
                "timeframe": True,
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "quotes": {
                    "2025-01-01": {"USDEUR": 0.92, "USDCZK": 24.5},
                    "2025-01-02": {"USDEUR": 0.93, "USDCZK": 24.4},
                },
            },
        )

    client, _ = make_client(fake_settings, handler)

    result = client.get_timeframe_rates(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        symbols=["EUR", "CZK"],
    )

    assert "2025-01-01" in result
    assert result["2025-01-01"]["USDEUR"] == 0.92
    assert result["2025-01-02"]["USDCZK"] == 24.4


def test_get_timeframe_rates_passes_dates(fake_settings: Settings) -> None:
    """Test předání datumů do URL."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": True, "quotes": {}},
        )

    client, requests = make_client(fake_settings, handler)

    client.get_timeframe_rates(
        start_date=date(2025, 3, 15),
        end_date=date(2025, 3, 20),
    )

    request_url = str(requests[0].url)
    assert "start_date=2025-03-15" in request_url
    assert "end_date=2025-03-20" in request_url


def test_api_error_response_raises(fake_settings: Settings) -> None:
    """Test chybové odpovědi API."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": False,
                "error": {
                    "code": 101,
                    "type": "invalid_access_key",
                    "info": "You have not supplied a valid API Access Key.",
                },
            },
        )

    client, _ = make_client(fake_settings, handler)

    with pytest.raises(ApiResponseError) as exc_info:
        client.get_live_rates()

    assert exc_info.value.code == 101
    assert exc_info.value.error_type == "invalid_access_key"
    assert "valid API Access Key" in exc_info.value.info


def test_http_error_raises_connection_error(fake_settings: Settings) -> None:
    """Test HTTP chyby."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    client, _ = make_client(fake_settings, handler)

    with pytest.raises(ApiConnectionError):
        client.get_live_rates()


def test_network_error_raises_connection_error(fake_settings: Settings) -> None:
    """Test síťové chyby."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection failed", request=request)

    client, _ = make_client(fake_settings, handler)

    with pytest.raises(ApiConnectionError):
        client.get_live_rates()


def test_client_uses_default_settings_when_none_provided() -> None:
    """Test výchozího nastavení."""
    client = ExchangeRateClient()
    assert client._settings is not None


def test_client_creates_default_http_client_when_none_provided(fake_settings: Settings) -> None:
    """Test výchozího HTTP klienta."""
    client = ExchangeRateClient(settings=fake_settings)
    assert isinstance(client._http_client, httpx.Client)