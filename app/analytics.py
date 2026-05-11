"""Výpočty nad měnovými kurzy."""
from datetime import date


def convert_to_base(rates_usd: dict[str, float], base: str) -> dict[str, float]:
    """Přepočítá kurzy na zvolenou základní měnu."""
    if not rates_usd:
        return {}
    if base != "USD" and base not in rates_usd:
        raise ValueError(f"base currency {base!r} not in rates")
    factor = rates_usd[base] if base != "USD" else 1.0
    return {
        currency: rate / factor
        for currency, rate in rates_usd.items()
        if currency != base
    }


def strongest_currency(rates: dict[str, float]) -> str:
    """Vrátí ekonomicky nejsilnější měnu."""
    if not rates:
        raise ValueError("rates cannot be empty")
    return min(rates, key=rates.get)


def weakest_currency(rates: dict[str, float]) -> str:
    """Vrátí ekonomicky nejslabší měnu."""
    if not rates:
        raise ValueError("rates cannot be empty")
    return max(rates, key=rates.get)


def average_rate(
    rates_by_date: dict[date, dict[str, float]],
    symbol: str,
) -> float:
    """Vrátí aritmetický průměr kurzu."""
    if not rates_by_date:
        raise ValueError("rates cannot be empty")
    values = [
        day_rates[symbol]
        for day_rates in rates_by_date.values()
        if symbol in day_rates
    ]
    if not values:
        raise ValueError(f"no data for symbol {symbol!r}")
    return sum(values) / len(values)