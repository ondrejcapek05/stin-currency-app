"""Služba pro cachování kurzů."""
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from app.api_client import ExchangeRateClient
from app.models import ExchangeRate

BASE_CURRENCY = "USD" # základní měna API


class RateService:
    """Pracuje s kurzy a databázovou cache."""

    def __init__(self, client: ExchangeRateClient, session: Session) -> None:
        self._client = client
        self._session = session

    def get_live_rates(self, symbols: list[str]) -> dict[str, float]:
        """Vrátí dnešní kurzy měn."""
        if not symbols:
            return {}

        today = datetime.now(timezone.utc).date()

        stmt = select(ExchangeRate).where(
            ExchangeRate.base == BASE_CURRENCY,
            ExchangeRate.target.in_(symbols),
            ExchangeRate.date == today,
        )
        cached = self._session.exec(stmt).all()
        cached_map = {row.target: row.rate for row in cached}

        missing = [s for s in symbols if s not in cached_map]

        if not missing:
            return {s: cached_map[s] for s in symbols}

        quotes = self._client.get_live_rates(missing)
        fresh = {self._split_quote_key(k): v for k, v in quotes.items()}
        self._save_rates(fresh, today)

        combined = {**cached_map, **fresh}
        return {s: combined[s] for s in symbols}

    def get_rates_for_period(
        self,
        start: date,
        end: date,
        symbols: list[str],
    ) -> dict[date, dict[str, float]]:
        """Vrátí kurzy měn za období."""
        if not symbols:
            return {}

        days = self._date_range(start, end)

        stmt = select(ExchangeRate).where(
            ExchangeRate.base == BASE_CURRENCY,
            ExchangeRate.target.in_(symbols),
            ExchangeRate.date >= start,
            ExchangeRate.date <= end,
        )
        cached = self._session.exec(stmt).all()
        by_date: dict[date, dict[str, float]] = {}
        for row in cached:
            by_date.setdefault(row.date, {})[row.target] = row.rate

        symbols_set = set(symbols)
        full_cover = all(
            d in by_date and symbols_set.issubset(by_date[d].keys())
            for d in days
        )
        if full_cover:
            return {d: {s: by_date[d][s] for s in symbols} for d in days}

        quotes = self._client.get_timeframe_rates(start, end, symbols)
        result: dict[date, dict[str, float]] = {}
        for date_str, day_quotes in quotes.items():
            d = date.fromisoformat(date_str)
            rates = {self._split_quote_key(k): v for k, v in day_quotes.items()}
            self._save_rates(rates, d)
            result[d] = rates
        return result

    def _save_rates(self, quotes: dict[str, float], on_date: date) -> None:
        """Uloží nové kurzy do databáze."""
        if not quotes:
            return

        targets = list(quotes.keys())
        stmt = select(ExchangeRate).where(
            ExchangeRate.base == BASE_CURRENCY,
            ExchangeRate.target.in_(targets),
            ExchangeRate.date == on_date,
        )
        existing = {row.target for row in self._session.exec(stmt).all()}

        new_rows = [
            ExchangeRate(
                base=BASE_CURRENCY,
                target=target,
                rate=rate,
                date=on_date,
            )
            for target, rate in quotes.items()
            if target not in existing
        ]
        if new_rows:
            self._session.add_all(new_rows)
            self._session.commit()

    @staticmethod
    def _split_quote_key(key: str) -> str:
        """Vrátí cílovou měnu z API klíče."""
        if key.startswith(BASE_CURRENCY):
            return key[len(BASE_CURRENCY):]
        return key

    @staticmethod
    def _date_range(start: date, end: date) -> list[date]:
        """Vrátí seznam dat v období."""
        days = (end - start).days + 1
        return [start + timedelta(days=i) for i in range(days)]