"""Testy pro app/analytics.py."""
from datetime import date

import pytest

from app.analytics import (
    average_rate,
    convert_to_base,
    strongest_currency,
    weakest_currency,
)


def test_convert_empty_returns_empty() -> None:
    """Test prázdného vstupu."""
    assert convert_to_base({}, "EUR") == {}


def test_convert_when_base_is_usd_excludes_usd_self() -> None:
    """Test přepočtu pro USD base."""
    rates = {"USD": 1.0, "EUR": 0.92, "CZK": 24.5}
    assert convert_to_base(rates, "USD") == {"EUR": 0.92, "CZK": 24.5}


def test_convert_to_eur_recalculates_rates() -> None:
    """Test přepočtu na EUR base."""
    rates = {"EUR": 0.92, "CZK": 24.5}
    result = convert_to_base(rates, "EUR")
    assert "EUR" not in result
    assert result["CZK"] == pytest.approx(24.5 / 0.92, rel=1e-9)


def test_convert_missing_base_raises() -> None:
    """Test chybějící base měny."""
    with pytest.raises(ValueError, match="base currency"):
        convert_to_base({"CZK": 24.5}, "EUR")


def test_convert_to_usd_when_usd_not_in_input_returns_unchanged() -> None:
    """Test přepočtu na USD bez USD v inputu."""
    rates = {"EUR": 0.92, "CZK": 24.5}
    assert convert_to_base(rates, "USD") == rates


def test_strongest_returns_currency_with_lowest_rate() -> None:
    """Test ekonomicky nejsilnější měny."""
    rates = {"EUR": 0.92, "CZK": 24.5, "GBP": 0.78}
    assert strongest_currency(rates) == "GBP"


def test_weakest_returns_currency_with_highest_rate() -> None:
    """Test ekonomicky nejslabší měny."""
    rates = {"EUR": 0.92, "CZK": 24.5, "GBP": 0.78}
    assert weakest_currency(rates) == "CZK"


def test_strongest_empty_raises() -> None:
    """Test prázdného vstupu u strongest."""
    with pytest.raises(ValueError, match="empty"):
        strongest_currency({})


def test_weakest_empty_raises() -> None:
    """Test prázdného vstupu u weakest."""
    with pytest.raises(ValueError, match="empty"):
        weakest_currency({})


def test_average_arithmetic_mean() -> None:
    """Test aritmetického průměru."""
    rates_by_date = {
        date(2025, 1, 1): {"EUR": 0.90},
        date(2025, 1, 2): {"EUR": 0.92},
        date(2025, 1, 3): {"EUR": 0.94},
    }
    assert average_rate(rates_by_date, "EUR") == pytest.approx(0.92)


def test_average_ignores_days_without_symbol() -> None:
    """Test ignorování chybějících dnů."""
    rates_by_date = {
        date(2025, 1, 1): {"EUR": 0.90},
        date(2025, 1, 2): {"CZK": 24.5},
        date(2025, 1, 3): {"EUR": 0.94},
    }
    assert average_rate(rates_by_date, "EUR") == pytest.approx(0.92)


def test_average_no_data_for_symbol_raises() -> None:
    """Test chybějících dat pro symbol."""
    rates_by_date = {
        date(2025, 1, 1): {"CZK": 24.5},
        date(2025, 1, 2): {"CZK": 24.6},
    }
    with pytest.raises(ValueError, match="no data for symbol"):
        average_rate(rates_by_date, "EUR")


def test_average_empty_dict_raises() -> None:
    """Test prázdného vstupu u průměru."""
    with pytest.raises(ValueError, match="empty"):
        average_rate({}, "EUR")