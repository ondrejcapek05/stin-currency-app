"""Testy pro app/rate_service.py."""
from datetime import date, datetime, timedelta, timezone

import httpx
import pytest
from sqlmodel import Session, select

from app.api_client import ExchangeRateClient
from app.config import Settings
from app.exceptions import ApiConnectionError
from app.models import ExchangeRate
from app.rate_service import BASE_CURRENCY, RateService


def make_mock_client(
    fake_settings: Settings,
    handler,
) -> tuple[ExchangeRateClient, list[httpx.Request]]:
    """Vytvoří testovacího API klienta."""
    requests: list[httpx.Request] = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    transport = httpx.MockTransport(wrapped)
    http_client = httpx.Client(transport=transport)
    client = ExchangeRateClient(settings=fake_settings, http_client=http_client)
    return client, requests


def _make_live_handler(quotes: dict[str, float]):
    """Vrátí odpověď pro live kurzy."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": True, "source": BASE_CURRENCY, "quotes": quotes},
        )
    return handler


def _make_timeframe_handler(quotes: dict[str, dict[str, float]]):
    """Vrátí odpověď pro historické kurzy."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": True, "quotes": quotes},
        )
    return handler


def test_live_rates_empty_symbols_returns_empty(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test prázdného vstupu pro live kurzy."""
    client, requests = make_mock_client(fake_settings, _make_live_handler({}))
    service = RateService(client=client, session=db_session)

    result = service.get_live_rates([])

    assert result == {}
    assert len(requests) == 0


def test_live_rates_cache_hit_skips_api(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test live kurzů z cache."""
    today = datetime.now(timezone.utc).date()
    db_session.add_all([
        ExchangeRate(base=BASE_CURRENCY, target="EUR", rate=0.92, date=today),
        ExchangeRate(base=BASE_CURRENCY, target="CZK", rate=24.5, date=today),
    ])
    db_session.commit()

    client, requests = make_mock_client(fake_settings, _make_live_handler({}))
    service = RateService(client=client, session=db_session)

    result = service.get_live_rates(["EUR", "CZK"])

    assert result == {"EUR": 0.92, "CZK": 24.5}
    assert len(requests) == 0


def test_live_rates_cache_miss_calls_api_and_saves(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test stažení a uložení live kurzů."""
    client, requests = make_mock_client(
        fake_settings,
        _make_live_handler({"USDEUR": 0.92, "USDCZK": 24.5}),
    )
    service = RateService(client=client, session=db_session)

    result = service.get_live_rates(["EUR", "CZK"])

    assert result == {"EUR": 0.92, "CZK": 24.5}
    assert len(requests) == 1

    today = datetime.now(timezone.utc).date()
    rows = db_session.exec(
        select(ExchangeRate).where(ExchangeRate.date == today)
    ).all()
    assert len(rows) == 2
    assert {r.target for r in rows} == {"EUR", "CZK"}


def test_live_rates_partial_cache_calls_api(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test částečné cache u live kurzů."""
    today = datetime.now(timezone.utc).date()
    db_session.add(
        ExchangeRate(base=BASE_CURRENCY, target="EUR", rate=0.92, date=today)
    )
    db_session.commit()

    client, requests = make_mock_client(
        fake_settings,
        _make_live_handler({"USDCZK": 24.5, "USDGBP": 0.78}),
    )
    service = RateService(client=client, session=db_session)

    result = service.get_live_rates(["EUR", "CZK", "GBP"])

    assert len(requests) == 1
    request_url = str(requests[0].url)
    assert "symbols=CZK%2CGBP" in request_url

    assert result == {"EUR": 0.92, "CZK": 24.5, "GBP": 0.78}
    assert list(result.keys()) == ["EUR", "CZK", "GBP"]


def test_live_rates_yesterday_cache_calls_api(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test staré cache u live kurzů."""
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    db_session.add(
        ExchangeRate(base=BASE_CURRENCY, target="EUR", rate=0.91, date=yesterday)
    )
    db_session.commit()

    client, requests = make_mock_client(
        fake_settings,
        _make_live_handler({"USDEUR": 0.92}),
    )
    service = RateService(client=client, session=db_session)

    result = service.get_live_rates(["EUR"])

    assert len(requests) == 1
    assert result == {"EUR": 0.92}


def test_live_rates_api_failure_propagates(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test chyby API u live kurzů."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection failed", request=request)

    client, _ = make_mock_client(fake_settings, handler)
    service = RateService(client=client, session=db_session)

    with pytest.raises(ApiConnectionError):
        service.get_live_rates(["EUR"])


def test_period_empty_symbols_returns_empty(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test prázdného vstupu pro historické kurzy."""
    client, requests = make_mock_client(fake_settings, _make_timeframe_handler({}))
    service = RateService(client=client, session=db_session)

    result = service.get_rates_for_period(
        start=date(2025, 1, 1),
        end=date(2025, 1, 2),
        symbols=[],
    )

    assert result == {}
    assert len(requests) == 0


def test_period_cache_hit_skips_api(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test historických kurzů z cache."""
    db_session.add_all([
        ExchangeRate(base=BASE_CURRENCY, target="EUR", rate=0.92, date=date(2025, 1, 1)),
        ExchangeRate(base=BASE_CURRENCY, target="EUR", rate=0.93, date=date(2025, 1, 2)),
    ])
    db_session.commit()

    client, requests = make_mock_client(fake_settings, _make_timeframe_handler({}))
    service = RateService(client=client, session=db_session)

    result = service.get_rates_for_period(
        start=date(2025, 1, 1),
        end=date(2025, 1, 2),
        symbols=["EUR"],
    )

    assert len(requests) == 0
    assert result == {
        date(2025, 1, 1): {"EUR": 0.92},
        date(2025, 1, 2): {"EUR": 0.93},
    }


def test_period_cache_miss_calls_api_and_saves(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test stažení a uložení historických kurzů."""
    client, requests = make_mock_client(
        fake_settings,
        _make_timeframe_handler({
            "2025-01-01": {"USDEUR": 0.92},
            "2025-01-02": {"USDEUR": 0.93},
        }),
    )
    service = RateService(client=client, session=db_session)

    result = service.get_rates_for_period(
        start=date(2025, 1, 1),
        end=date(2025, 1, 2),
        symbols=["EUR"],
    )

    assert len(requests) == 1
    assert result == {
        date(2025, 1, 1): {"EUR": 0.92},
        date(2025, 1, 2): {"EUR": 0.93},
    }
    rows = db_session.exec(select(ExchangeRate)).all()
    assert len(rows) == 2


def test_period_cache_miss_does_not_duplicate_existing_rate(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test proti duplicitnímu uložení."""
    db_session.add(
        ExchangeRate(base=BASE_CURRENCY, target="EUR", rate=0.92, date=date(2025, 1, 1))
    )
    db_session.commit()

    client, _ = make_mock_client(
        fake_settings,
        _make_timeframe_handler({
            "2025-01-01": {"USDEUR": 0.92},
            "2025-01-02": {"USDEUR": 0.93},
        }),
    )
    service = RateService(client=client, session=db_session)

    service.get_rates_for_period(
        start=date(2025, 1, 1),
        end=date(2025, 1, 2),
        symbols=["EUR"],
    )

    rows = db_session.exec(
        select(ExchangeRate).where(
            ExchangeRate.base == BASE_CURRENCY,
            ExchangeRate.target == "EUR",
            ExchangeRate.date == date(2025, 1, 1),
        )
    ).all()
    assert len(rows) == 1


def test_period_returns_rates_grouped_by_date(
    fake_settings: Settings,
    db_session: Session,
) -> None:
    """Test formátu výsledku."""
    client, _ = make_mock_client(
        fake_settings,
        _make_timeframe_handler({
            "2025-01-01": {"USDEUR": 0.92, "USDCZK": 24.5},
        }),
    )
    service = RateService(client=client, session=db_session)

    result = service.get_rates_for_period(
        start=date(2025, 1, 1),
        end=date(2025, 1, 1),
        symbols=["EUR", "CZK"],
    )

    assert list(result.keys()) == [date(2025, 1, 1)]
    assert result[date(2025, 1, 1)] == {"EUR": 0.92, "CZK": 24.5}