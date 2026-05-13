"""Klient pro exchangerate.host API."""
from datetime import date
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.exceptions import ApiConnectionError, ApiResponseError


class ExchangeRateClient:
    """Klient pro volání exchangerate.host API."""

    DEFAULT_TIMEOUT = 10.0

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._http_client = http_client or httpx.Client(timeout=self.DEFAULT_TIMEOUT)

    def get_live_rates(self, symbols: list[str] | None = None) -> dict[str, float]:
        """Vrátí aktuální kurzy měn."""
        params: dict[str, Any] = {"access_key": self._settings.api_key}
        if symbols:
            params["symbols"] = ",".join(symbols)

        data = self._get("/live", params)
        return data.get("quotes", {})

    def get_timeframe_rates(
        self,
        start_date: date,
        end_date: date,
        symbols: list[str] | None = None,
    ) -> dict[str, dict[str, float]]:
        """Vrátí kurzy v časovém rozsahu."""
        params: dict[str, Any] = {
            "access_key": self._settings.api_key,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if symbols:
            params["symbols"] = ",".join(symbols)

        data = self._get("/timeframe", params)
        return data.get("quotes", {})

    def _get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Zavolá API a zpracuje odpověď."""
        url = f"{self._settings.api_base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            response = self._http_client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ApiConnectionError(f"Failed to call {url}: {e}") from e

        data = response.json()

        if not data.get("success", False):
            error = data.get("error", {})
            raise ApiResponseError(
                code=error.get("code", 0),
                error_type=error.get("type", "unknown"),
                info=error.get("info", "Unknown API error"),
            )

        return data